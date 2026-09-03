// RefundSimulator component - allows simulating incoming refund events

import { useState } from 'react';
import { eventsApi } from '../api';
import { RefundEventRequest, RefundEventResponse } from '../types';

export function RefundSimulator({ onCaseCreated }: { onCaseCreated?: (caseId: number) => void }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ response: RefundEventResponse; request: RefundEventRequest } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'idle' | 'received' | 'scoring' | 'scored' | 'action' | 'case_created'>('idle');

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setStep('received');

    try {
      // Simulate the flow steps
      setStep('scoring');
      await new Promise(r => setTimeout(r, 800));

      const response = await eventsApi.ingestRefund(formData);

      setStep('scored');
      await new Promise(r => setTimeout(r, 400));

      setStep('action');
      await new Promise(r => setTimeout(r, 400));

      setStep('case_created');
      setResult({ response, request: formData });

      if (onCaseCreated) {
        onCaseCreated(response.case_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to ingest refund');
      setStep('idle');
    } finally {
      setLoading(false);
    }
  };

  const handlePresetClick = (data: RefundEventRequest) => {
    setFormData(data);
    setResult(null);
    setError(null);
    setStep('idle');
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setStep('idle');
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

  const stepLabels = {
    idle: 'Ready',
    received: 'Refund Received',
    scoring: 'Sentinel Scoring...',
    scored: 'Risk Scored',
    action: 'Action Determined',
    case_created: 'Case Created',
  };

  const stepOrder = ['idle', 'received', 'scoring', 'scored', 'action', 'case_created'];

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Simulate Incoming Refund</h2>
      <p className="text-sm text-gray-600 mb-6">
        Submit a refund event to see Sentinel score it in real-time and create a risk case.
      </p>

      {/* Step Progress Indicator */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          {stepOrder.map((s, i) => (
            <div key={s} className="flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                  stepOrder.indexOf(step) >= i
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {i + 1}
              </div>
              <span className={`mt-1 text-xs text-center ${stepOrder.indexOf(step) >= i ? 'text-blue-600 font-medium' : 'text-gray-400'}`}>
                {stepLabels[s as keyof typeof stepLabels]}
              </span>
            </div>
          ))}
          <div className="flex-1 h-1 bg-gray-200" />
        </div>
      </div>

      {/* Preset Scenarios */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Quick Scenarios</label>
        <div className="flex flex-wrap gap-2">
          {presets.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePresetClick(preset.data)}
              className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition text-gray-700"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
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

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : 'Submit Refund for Scoring'}
          </button>
          <button
            type="button"
            onClick={handleReset}
            disabled={loading}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition font-medium disabled:opacity-50"
          >
            Reset
          </button>
        </div>
      </form>

      {/* Result Display */}
      {result && (
        <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg animate-fade-in">
          <h3 className="font-semibold text-gray-900 mb-3">Refund Processed Successfully</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-white p-3 rounded border">
              <p className="text-sm text-gray-500">Risk Score</p>
              <p className="text-2xl font-bold text-gray-900">{(result.response.risk_score * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-white p-3 rounded border">
              <p className="text-sm text-gray-500">Risk Band</p>
              <p className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${bandColors[result.response.risk_band]}`}>
                {result.response.risk_band}
              </p>
            </div>
            <div className="bg-white p-3 rounded border">
              <p className="text-sm text-gray-500">Action</p>
              <p className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${actionColors[result.response.recommended_action]}`}>
                {result.response.recommended_action.toUpperCase()}
              </p>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Case <span className="font-mono font-medium">#{result.response.case_id}</span> created
            </div>
            <button
              onClick={() => window.location.href = `/cases/${result.response.case_id}`}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              View Case Details
            </button>
          </div>
        </div>
      )}

      {error && !result && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <p className="font-medium">Error</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}
    </div>
  );
}