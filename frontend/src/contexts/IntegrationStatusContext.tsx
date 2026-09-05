// Integration Status Context - Shared monitoring state across the application

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { integrationApi } from '../api';
import { IntegrationStatusResponse } from '../types';

interface IntegrationStatusContextType {
  status: IntegrationStatusResponse | null;
  isLoading: boolean;
  refresh: () => Promise<void>;
  control: (action: 'start' | 'stop') => Promise<void>;
}

const IntegrationStatusContext = createContext<IntegrationStatusContextType | undefined>(undefined);

export function IntegrationStatusProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<IntegrationStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await integrationApi.getStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to load integration status:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    await fetchStatus();
  }, [fetchStatus]);

  const control = useCallback(async (action: 'start' | 'stop') => {
    try {
      await integrationApi.control(action);
      await fetchStatus();
    } catch (err) {
      console.error(`Failed to ${action} monitoring:`, err);
    }
  }, [fetchStatus]);

  // Initial load and polling
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  return (
    <IntegrationStatusContext.Provider value={{ status, isLoading, refresh, control }}>
      {children}
    </IntegrationStatusContext.Provider>
  );
}

export function useIntegrationStatus() {
  const context = useContext(IntegrationStatusContext);
  if (!context) {
    throw new Error('useIntegrationStatus must be used within an IntegrationStatusProvider');
  }
  return context;
}