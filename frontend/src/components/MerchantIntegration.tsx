// MerchantIntegration component - Live refund monitoring and test refund injection

import { useEffect, useState } from 'react';
import { integrationApi, eventsApi } from '../api';
import { IntegrationStatusResponse, RefundEventRequest, RefundEventResponse } from '../types';

interface MerchantIntegrationProps {
  onCaseCreated?: (caseId: number) => void;
}

export function MerchantIntegration({ onCaseCreated }: MerchantIntegrationProps) {
  const [status, setStatus] = useState<IntegrationStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ response: RefundEventResponse; request: RefundEventRequest } | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [testStep, setTestStep] = useState<'idle' | 'enqueued' | 'processing' | 'scored' | 'action' | 'case_created'>('idle');

  // Test refund form data (using real benchmark data)
  const [formData, setFormData] = useState<RefundEventRequest>({
    refund_id: 'REF_0028458',
    customer_id: 'CUS_049306',
    order_id: 'ORD_00206922',
    amount_inr: 1831.11,
    event_time: '2026-01-20T14:11:51.650Z',
    device_id: 'DEV_045153',
    address_id: 'ADDR_041914',
    payment_token: 'PM_045121',
    product_category: 'beauty',
    order_amount_inr: 1831.11,
    order_time: '2026-01-18T15:48:25.886Z',
  });

  // Preset scenarios for quick testing
  const presets = [
    {
      label: 'High Risk (Abuse)',
      data: {
        refund_id: 'REF_0028458',
        customer_id: 'CUS_049306',
        order_id: 'ORD_00206922',
        amount_inr: 1831.11,
        event_time: '2026-01-20T14:11:51.650Z',
        device_id: 'DEV_045153',
        address_id: 'ADDR_041914',
        payment_token: 'PM_045121',
        product_category: 'beauty',
        order_amount_inr: 1831.11,
        order_time: '2026-01-18T15:48:25.886Z',
      },
    },
    {
      label: 'High Risk (Temporal)',
      data: {
        refund_id: 'REF_0007580',
        customer_id: 'CUS_021764',
        order_id: 'ORD_00087811',
        amount_inr: 2499.0,
        event_time: '2026-03-15T10:30:00.000Z',
        device_id: 'DEV_012345',
        address_id: 'ADDR_009876',
        payment_token: 'PM_005432',
        product_category: 'electronics',
        order_amount_inr: 2499.0,
        order_time: '2026-03-14T09:15:00.000Z',
      },
    },
    {
      label: 'Low Risk (Legitimate)',
      data: {
        refund_id: 'REF_0025456',
        customer_id: 'CUS_048639',
        order_id: 'ORD_00203350',
        amount_inr: 1299.0,
        event_time: '2026-04-10T16:20:00.000Z',
        device_id: 'DEV_067890',
        address_id: 'ADDR_054321',
        payment_token: 'PM_098765',
        product_category: 'apparel',
        order_amount_inr: 1299.0,
        order_time: '2026-04-08T14:10:00.000Z',
      },
    },
  ];

  useEffect(() => {
    loadStatus();
    // Poll for status updates
    const interval = setInterval(loadStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const data = await integrationApi.getStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to load integration status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleControl = async (action: 'start' | 'stop' | 'pause' | 'resume') => {
    try {
      await integrationApi.control(action);
      await loadStatus();
    } catch (err) {
      console.error(`Failed to ${action} monitoring:`, err);
    }
  };

  const handleTestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTestLoading(true);
    setTestError(null);
    setTestResult(null);
    setTestStep('idle');

    try {
      // Step 1: Enqueue
      setTestStep('enqueued');
      const enqueueResult = await integrationApi.enqueueRefund(formData);
      
      // Step 2: Wait for processing
      setTestStep('processing');
      let attempts = 0;
      while (attempts < 30) { // Max 30 seconds
        await new Promise(r => setTimeout(r, 1000));
        const status = await integrationApi.getStatus();
        if (status.events_processed > 0 || status.events_failed > 0) {
          break;
        }
        attempts++;
      }

      // Step 3: Get the result
      setTestStep('scored');
      // Get the case from the cases list
      const casesRes = await fetch('/api/cases').then(r => r.json());
      const newCase = casesRes.cases.find((c: any) => c.refund_id === formData.refund_id);
      
      if (newCase) {
        setTestStep('action');
        await new Promise(r => setTimeout(r, 400));
        setTestStep('case_created');
        
        // Get the full response by calling the scoring endpoint
        const scoreResult = await eventsApi.getRefundStatus(formData.refund_id);
        if (scoreResult.processed) {
          // Get full details from the case
          const caseDetail = await fetch(`/api/cases/${newCase.id}`).then(r => r.json());
          setTestResult({ 
            response: { ...caseDetail, case_id: newCase.id } as any, 
            request: formData 
          });
        }
      }

      if (onCaseCreated && testResult) {
        onCaseCreated(testResult.response.case_id);
      }
    } catch (err: any) {
      setTestError(err.message || 'Failed to process test refund');
      setTestStep('idle');
    } finally {
      setTestLoading(false);
    }
  };

  const handlePresetClick = (data: RefundEventRequest) => {
    setFormData(data);
    setTestResult(null);
    setTestError(null);
    setTestStep('idle');
  };

  const handleReset = () => {
    setTestResult(null);
    setTestError(null);
    setTestStep('idle');
  };

  const bandColors: Record<string, string> = {
    LOW: 'bg-green-100 text-green-800',
    MEDIUM: 'bg-yellow-100 text-yellow-800',
    HIGH: 'bg-orange-100 text-orange-800',
    CRITICAL: 'bg-red-100 text-red-800',
  };

  const actionColors: Record<string, string> = {
    approve: 'bg-green-100 text-green-800',
    verify: 'bg-blue-100 text-blue-800',
    review: 'bg-orange-100 text-orange-800',
    hold: 'bg-red-100 text-red-800',
  };

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Merchant Integration / Live Refund Monitoring</h2>
      <p className="text-sm text-gray-600 mb-6">
        Synthetic merchant data source connected. Incoming refund events are automatically scored by Sentinel.
      </p>

      {/* Connection Status */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-gray-900 mb-3">Connection Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">Data Source</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`w-3 h-3 rounded-full ${status?.connected ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className={status?.connected ? 'text-green-600' : 'text-red-600'}>
                {status?.connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500">Monitoring</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`w-3 h-3 rounded-full ${status?.monitoring ? 'bg-green-500' : 'bg-gray-400'}`}></span>
              <span className={status?.monitoring ? 'text-green-600' : 'text-gray-600'}>
                {status?.monitoring ? 'Active' : 'Paused'}
              </span>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500">Queue Pending</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{status?.queue_pending ?? 0}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Processed</p>
            <p className="text-2xl font-bold text-green-600 mt-1">{status?.events_processed ?? 0}</p>
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          {!status?.monitoring ? (
            <button
              onClick={() => handleControl('start')}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
            >
              Start Monitoring
            </button>
          ) : (
            <button
              onClick={() => handleControl('stop')}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium"
            >
              Stop Monitoring
            </button>
          )}
        </div>
      </div>

      {/* Statistics */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-gray-900 mb-3">Processing Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-sm text-blue-600">Received</p>
            <p className="text-2xl font-bold text-blue-800">{status?.events_received ?? 0}</p>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <p className="text-sm text-green-600">Processed</p>
            <p className="text-2xl font-bold text-green-800">{status?.events_processed ?? 0}</p>
          </div>
          <div className="bg-red-50 p-3 rounded">
            <p className="text-sm text-red-600">Failed</p>
            <p className="text-2xl font-bold text-red-800">{status?.events_failed ?? 0}</p>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <p className="text-sm text-gray-600">Last Event</p>
            <p className="text-sm font-mono text-gray-900">
              {status?.last_processed_refund_id ?? 'None'}
            </p>
          </div>
        </div>

        {status?.last_processed_event && (
          <div className="mt-3 p-3 bg-gray-50 rounded text-sm">
            <span className="text-gray-500">Last processed: </span>
            <span className="font-mono">{status.last_processed_event}</span>
            {' | Band: '}
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${bandColors[status.last_processed_risk_band as keyof typeof bandColors] || 'bg-gray-100 text-gray-800'}`}>
              {status.last_processed_risk_band}
            </span>
            {' | Action: '}
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${actionColors[status.last_processed_action as keyof typeof actionColors] || 'bg-gray-100 text-gray-800'}`}>
              {status.last_processed_action?.toUpperCase()}
            </span>
          </div>
        )}
      </div>

      {/* Send Test Refund */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Send Test Refund</h3>
        <p className="text-sm text-gray-600 mb-4">
          Inject a test refund into the merchant event stream. It will be automatically enqueued, processed by Sentinel, and turned into a risk case.
        </p>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Quick Scenarios</label>
          <div className="flex flex-wrap gap-2">
            {presets.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handlePresetClick(preset.data)}
                disabled={testLoading}
                className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition text-gray-700 disabled:opacity-50"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleTestSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Refund ID *</label>
              <input
                type="text"
                value={formData.refund_id}
                onChange={e => setFormData({ ...formData, refund_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Customer ID *</label>
              <input
                type="text"
                value={formData.customer_id}
                onChange={e => setFormData({ ...formData, customer_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Order ID *</label>
              <input
                type="text"
                value={formData.order_id}
                onChange={e => setFormData({ ...formData, order_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Amount (INR) *</label>
              <input
                type="number"
                step="0.01"
                value={formData.amount_inr}
                onChange={e => setFormData({ ...formData, amount_inr: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Event Time (ISO8601) *</label>
              <input
                type="text"
                value={formData.event_time}
                onChange={e => setFormData({ ...formData, event_time: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Device ID *</label>
              <input
                type="text"
                value={formData.device_id}
                onChange={e => setFormData({ ...formData, device_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Address ID *</label>
              <input
                type="text"
                value={formData.address_id}
                onChange={e => setFormData({ ...formData, address_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Payment Token *</label>
              <input
                type="text"
                value={formData.payment_token}
                onChange={e => setFormData({ ...formData, payment_token: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Product Category *</label>
              <input
                type="text"
                value={formData.product_category}
                onChange={e => setFormData({ ...formData, product_category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Order Amount (INR) *</label>
              <input
                type="number"
                step="0.01"
                value={formData.order_amount_inr}
                onChange={e => setFormData({ ...formData, order_amount_inr: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Order Time (ISO8601) *</label>
              <input
                type="text"
                value={formData.order_time}
                onChange={e => setFormData({ ...formData, order_time: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
          </div>

          {testError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {testError}
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={testLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {testLoading ? 'Processing...' : 'Inject Refund into Stream'}
            </button>
            <button
              type="button"
              onClick={handleReset}
              disabled={testLoading}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition font-medium disabled:opacity-50"
            >
              Reset
            </button>
          </div>
        </form>

        {/* Test Result Display */}
        {testResult && (
          <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg animate-fade-in">
            <h3 className="font-semibold text-gray-900 mb-3">Test Refund Processed Successfully</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-white p-3 rounded border">
                <p className="text-sm text-gray-500">Risk Score</p>
                <p className="text-2xl font-bold text-gray-900">{(testResult.response.risk_score * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-white p-3 rounded border">
                <p className="text-sm text-gray-500">Risk Band</p>
                <p className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${bandColors[testResult.response.risk_band]}`}>
                  {testResult.response.risk_band}
                </p>
              </div>
              <div className="bg-white p-3 rounded border">
                <p className="text-sm text-gray-500">Action</p>
                <p className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${actionColors[testResult.response.recommended_action]}`}>
                  {testResult.response.recommended_action.toUpperCase()}
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Case <span className="font-mono font-medium">#{testResult.response.case_id}</span> created
              </div>
              <button
                onClick={() => window.location.href = `/cases/${testResult.response.case_id}`}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
              >
                View Case Details
              </button>
            </div>
          </div>
        )}

        {testError && !testResult && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <p className="font-medium">Error</p>
            <p className="text-sm mt-1">{testError}</p>
          </div>
        )}
      </div>
    </div>
  );
}

const bandColors: Record<string, string> = {
  LOW: 'bg-green-100 text-green-800',
  MEDIUM: 'bg-yellow-100 text-yellow-800',
  HIGH: 'bg-orange-100 text-orange-800',
  CRITICAL: 'bg-red-100 text-red-800',
};

const actionColors: Record<string, string> = {
  approve: 'bg-green-100 text-green-800',
  verify: 'bg-blue-100 text-blue-800',
  review: 'bg-orange-100 text-orange-800',
  hold: 'bg-red-100 text-red-800',
};