// Case Detail page

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { casesApi, riskApi } from '../api';
import { CaseResponse, GraphResponse, EvidenceItem } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { EvidenceCard } from '../components/EvidenceCard';
import { GraphViz } from '../components/GraphViz';

export function CaseDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState<CaseResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState(false);
  const [activeTab, setActiveTab] = useState<'evidence' | 'graph' | 'decision' | 'timeline'>('evidence');

  useEffect(() => {
    if (id) {
      loadCase();
    }
  }, [id]);

  const loadCase = async () => {
    try {
      setLoading(true);
      const [caseRes, graphRes] = await Promise.all([
        casesApi.get(parseInt(id!)),
        riskApi.getGraph(parseInt(id!)),
      ]);
      setCaseData(caseRes);
      setGraphData(graphRes);
    } catch (err) {
      console.error('Failed to load case:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision: 'approve' | 'verify' | 'review' | 'hold') => {
    if (!caseData) return;
    try {
      setDeciding(true);
      await casesApi.decide(caseData.id, decision);
      await loadCase();
    } catch (err) {
      console.error('Decision failed:', err);
    } finally {
      setDeciding(false);
    }
  };

  const groupEvidence = (evidence: EvidenceItem[]) => {
    return {
      behavioral: evidence.filter(e => e.category === 'behavioral'),
      graph: evidence.filter(e => e.category === 'graph'),
      temporal: evidence.filter(e => e.category === 'temporal'),
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Case not found</p>
        <button
          onClick={() => navigate('/cases')}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Back to Cases
        </button>
      </div>
    );
  }

  const evidenceGroups = groupEvidence(caseData.evidence);

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate('/cases')}
            className="text-gray-500 hover:text-gray-700 mb-2"
          >
            ← Back to Cases
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Case #{caseData.id}</h1>
          <p className="text-gray-600">{caseData.refund_id} • {caseData.customer_id}</p>
        </div>
        <div className="flex items-center gap-4">
          <Link to={`/cases/${caseData.id}`} className="text-sm text-blue-600 hover:text-blue-700">
            Refresh
          </Link>
        </div>
      </div>

      {/* Risk Summary */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <RiskBadge
              score={caseData.risk_score}
              band={caseData.risk_band}
              action={caseData.recommended_action}
            />
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Order ID</p>
                <p className="font-mono font-medium">{caseData.order_id}</p>
              </div>
              <div>
                <p className="text-gray-500">Threshold</p>
                <p className="font-mono font-medium">{caseData.risk_score > 0.41 ? '0.41 (exceeded)' : '0.41'}</p>
              </div>
              <div>
                <p className="text-gray-500">Status</p>
                <p className={`font-medium capitalize ${caseData.status === 'decided' ? 'text-gray-900' : 'text-blue-600'}`}>
                  {caseData.status}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Created</p>
                <p className="font-mono font-medium">{new Date(caseData.created_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
          <div className="lg:col-span-1">
            <div className="space-y-3">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Recommended Action</p>
                <p className={`font-semibold ${actionColors[caseData.recommended_action] || 'bg-gray-100 text-gray-800'} px-3 py-1 rounded inline-block`}>
                  {caseData.recommended_action.toUpperCase()}
                </p>
              </div>
              {caseData.status === 'pending' && (
                <div className="space-y-2">
                  {(['approve', 'verify', 'review', 'hold'] as const).map((action) => (
                    <button
                      key={action}
                      onClick={() => handleDecision(action)}
                      disabled={deciding}
                      className={`w-full px-4 py-2 rounded-lg font-medium transition ${
                        action === 'approve' ? 'bg-green-600 text-white hover:bg-green-700' :
                        action === 'verify' ? 'bg-blue-600 text-white hover:bg-blue-700' :
                        action === 'review' ? 'bg-orange-600 text-white hover:bg-orange-700' :
                        'bg-red-600 text-white hover:bg-red-700'
                      }`}
                    >
                      {deciding ? 'Processing...' : action.charAt(0).toUpperCase() + action.slice(1)}
                    </button>
                  ))}
                </div>
              )}
              {caseData.status === 'decided' && (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Decision Made</p>
                  <p className={`font-semibold ${actionColors[caseData.decision!] || 'bg-gray-100 text-gray-800'} px-3 py-1 rounded inline-block`}>
                    {caseData.decision?.toUpperCase()}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Decided: {caseData.decided_at ? new Date(caseData.decided_at).toLocaleString() : 'N/A'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px" aria-label="Tabs">
            {([
              { key: 'evidence', label: 'Evidence' },
              { key: 'graph', label: 'Network Graph' },
              { key: 'decision', label: 'Decision' },
              { key: 'timeline', label: 'Timeline' },
            ] as const).map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition ${
                  activeTab === tab.key
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'evidence' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <EvidenceCard
                title="Behavioral Evidence"
                category="behavioral"
                items={evidenceGroups.behavioral}
              />
              <EvidenceCard
                title="Graph Evidence"
                category="graph"
                items={evidenceGroups.graph}
              />
              <EvidenceCard
                title="Temporal Evidence"
                category="temporal"
                items={evidenceGroups.temporal}
              />
            </div>
          )}

          {activeTab === 'graph' && (
            <div>
              <GraphViz data={graphData} width={800} height={500} />
              {graphData && (
                <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-gray-500">Connected Customers</p>
                    <p className="font-bold text-gray-900">{graphData.stats.connected_customers}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-gray-500">Shared Devices</p>
                    <p className="font-bold text-gray-900">{graphData.stats.shared_devices}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-gray-500">Shared Addresses</p>
                    <p className="font-bold text-gray-900">{graphData.stats.shared_addresses}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-gray-500">Shared Payments</p>
                    <p className="font-bold text-gray-900">{graphData.stats.shared_payments}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'decision' && (
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">Risk Assessment Summary</h3>
                <p className="text-gray-700">
                  This refund event was scored <strong>{caseData.risk_score.toFixed(3)}</strong>
                  by the Sentinel production model (39 features: 18 behavioral + 15 graph + 6 temporal).
                  The frozen decision threshold is <strong>0.41</strong>.
                </p>
                <p className="text-gray-700 mt-2">
                  Based on the ActionPolicy, this places the event in the
                  <strong className={bandColors[caseData.risk_band] || ''} px-2 py-0.5 rounded inline-block">
                    {caseData.risk_band}
                  </strong>
                  band, recommending <strong className={actionColors[caseData.recommended_action] || ''} px-2 py-0.5 rounded inline-block">
                    {caseData.recommended_action.toUpperCase()}
                  </strong>.
                </p>
              </div>

              {caseData.status === 'decided' && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <h3 className="font-semibold text-green-800 mb-2">Decision Recorded</h3>
                  <p className="text-green-700">
                    Action: <strong>{caseData.decision?.toUpperCase()}</strong>
                    {caseData.decided_at && ` • ${new Date(caseData.decided_at).toLocaleString()}`}
                  </p>
                </div>
              )}

              <div className="p-4 bg-gray-50 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">Feature Values (Production Model)</h3>
                <details className="text-sm">
                  <summary className="cursor-pointer text-blue-600 hover:text-blue-700">Show all 39 features</summary>
                  <pre className="mt-2 p-3 bg-white border border-gray-200 rounded overflow-auto text-xs">
                    {JSON.stringify(caseData, null, 2)}
                  </pre>
                </details>
              </div>
            </div>
          )}

          {activeTab === 'timeline' && (
            <div className="text-gray-500 text-center py-8">
              Timeline view showing cluster events over time (to be implemented)
            </div>
          )}
        </div>
      </div>
    </div>
  );
}