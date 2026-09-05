// InjectRefundModal Component

import { useState, useCallback, FormEvent } from 'react';
import { integrationApi, eventsApi, casesApi } from '../api';
import { RefundEventRequest, RefundEventResponse } from '../types';
import { StatusBadge } from './StatusBadge';

interface InjectRefundModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCaseCreated?: (caseId: number) => void;
}

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

export function InjectRefundModal({ isOpen, onClose, onCaseCreated }: InjectRefundModalProps) {
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ response: RefundEventResponse & { case_id: number }; request: RefundEventRequest } | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

  const [formData, setFormData] = useState<RefundEventRequest>(presets[0].data);

  const handlePresetClick = useCallback((data: RefundEventRequest) => {
    setFormData(data);
    setTestResult(null);
    setTestError(null);
  }, []);

  const handleReset = useCallback(() => {
    setFormData(presets[0].data);
    setTestResult(null);
    setTestError(null);
  }, []);

  const handleTestSubmit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    setTestLoading(true);
    setTestError(null);
    setTestResult(null);

    try {
      await integrationApi.enqueueRefund(formData);

      let attempts = 0;
      while (attempts < 30) {
        await new Promise((r) => setTimeout(r, 1000));
        const statusData = await integrationApi.getStatus();
        if (statusData.events_processed > 0 || statusData.events_failed > 0) {
          break;
        }
        attempts++;
      }

      const casesRes = await casesApi.list();
      const newCase = casesRes.cases.find((c: any) => c.refund_id === formData.refund_id);

      if (newCase) {
        await new Promise((r) => setTimeout(r, 400));
        const scoreResult = await eventsApi.getRefundStatus(formData.refund_id);
        if (scoreResult.processed) {
          const caseDetail = await casesApi.get(newCase.id);
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
    } finally {
      setTestLoading(false);
    }
  }, [formData, onCaseCreated]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 id="modal-title" className="modal-title">Inject Test Refund</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <div className="modal-body">
          {!testResult ? (
            <>
              <div style={{ marginBottom: '16px' }}>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>Quick Presets</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {presets.map((preset, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handlePresetClick(preset.data)}
                      disabled={testLoading}
                      className="btn btn-secondary btn-sm"
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              <form onSubmit={handleTestSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                  {Object.entries(formData).map(([key]) => (
                    <div key={key}>
                      <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 'var(--font-medium)', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                        {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} *
                      </label>
                      <input
                        type={key.includes('amount') ? 'number' : 'text'}
                        step={key.includes('amount') ? '0.01' : undefined}
                        value={(formData as any)[key]}
                        onChange={(e) => setFormData({ ...formData, [key]: key.includes('amount') ? parseFloat(e.target.value) : e.target.value })}
                        className="input input-sm"
                        required
                      />
                    </div>
                  ))}
                </div>

                {testError && (
                  <div style={{ padding: '8px', fontSize: 'var(--text-xs)', color: 'var(--color-risk-high-text)', backgroundColor: 'var(--color-risk-high-bg)', border: '1px solid var(--color-risk-high-border)', borderRadius: 'var(--radius-md)' }}>
                    {testError}
                  </div>
                )}

                <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                  <button type="submit" disabled={testLoading} className="btn btn-primary btn-sm" style={{ flex: 1 }}>
                    {testLoading ? 'Processing...' : 'Inject Refund'}
                  </button>
                  <button type="button" onClick={handleReset} disabled={testLoading} className="btn btn-secondary btn-sm">
                    Reset
                  </button>
                </div>
              </form>
            </>
          ) : (
            <div style={{ backgroundColor: 'var(--color-risk-low-bg)', border: '1px solid var(--color-risk-low-border)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'spaceBetween', marginBottom: '12px' }}>
                <h3 style={{ fontWeight: 'var(--font-semibold)', color: 'var(--color-risk-low-text)' }}>Test Refund Processed</h3>
                <button onClick={() => setTestResult(null)} style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}>×</button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '12px' }}>
                <div style={{ textAlign: 'center', padding: '8px', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
                  <p style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)' }}>Risk Score</p>
                  <p style={{ fontFamily: 'var(--font-mono)', fontWeight: 'var(--font-bold)', fontSize: 'var(--text-xl)', color: 'var(--color-text-primary)', marginTop: '4px' }}>
                    {(testResult.response.risk_score * 100).toFixed(1)}%
                  </p>
                </div>
                <div style={{ textAlign: 'center', padding: '8px', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
                  <p style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)' }}>Risk Band</p>
                  <p style={{ marginTop: '4px' }}>
                    <StatusBadge variant="risk" value={testResult.response.risk_band} />
                  </p>
                </div>
                <div style={{ textAlign: 'center', padding: '8px', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
                  <p style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)' }}>Action</p>
                  <p style={{ marginTop: '4px' }}>
                    <StatusBadge variant="action" value={testResult.response.recommended_action} />
                  </p>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'spaceBetween' }}>
                <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>
                  Case <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 'var(--font-medium)' }}>#{testResult.response.case_id}</span> created
                </span>
                <button
                  onClick={() => { onClose(); window.location.href = `/cases/${testResult.response.case_id}`; }}
                  className="btn btn-primary btn-sm"
                >
                  View Case
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}