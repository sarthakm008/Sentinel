// Cases list page

import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { casesApi } from '../api';
import { CaseResponse, CasesListResponse } from '../types';
import { CaseCard } from '../components/CaseCard';

export function Cases() {
  const navigate = useNavigate();
  const [data, setData] = useState<CasesListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    band: '',
    page: 1,
    size: 20,
  });

  useEffect(() => {
    loadCases();
  }, [filters]);

  const loadCases = async () => {
    try {
      setLoading(true);
      const res = await casesApi.list(filters);
      setData(res);
    } catch (err) {
      console.error('Failed to load cases:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Risk Cases</h1>
          <p className="text-text-secondary">All scored refund events with risk assessment</p>
        </div>
        <Link
          to="/"
          className="px-4 py-2 bg-bg-tertiary text-text-primary hover:bg-bg-hover transition rounded-lg"
        >
          Back to Dashboard
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Status</label>
            <select
              value={filters.status}
              onChange={e => handleFilterChange('status', e.target.value)}
              className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            >
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="decided">Decided</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Risk Band</label>
            <select
              value={filters.band}
              onChange={e => handleFilterChange('band', e.target.value)}
              className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            >
              <option value="">All</option>
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
        </div>
      </div>

      {/* Cases List */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary border-t-transparent mx-auto"></div>
          </div>
        ) : data?.cases.length === 0 ? (
          <div className="p-8 text-center text-text-muted">
            No cases found matching the current filters.
          </div>
        ) : (
          <div className="divide-y divide-border">
            {data?.cases.map((caseData) => (
              <CaseCard
                key={caseData.id}
                case={caseData}
                onClick={() => navigate(`/cases/${caseData.id}`)}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="px-4 py-3 border-t border-border flex items-center justify-between">
            <p className="text-sm text-text-secondary">
              Page {data.page} of {data.pages} — {data.total} total cases
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handlePageChange(data.page - 1)}
                disabled={data.page === 1}
                className="px-3 py-1 text-sm border border-border rounded hover:bg-bg-hover disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => handlePageChange(data.page + 1)}
                disabled={data.page === data.pages}
                className="px-3 py-1 text-sm border border-border rounded hover:bg-bg-hover disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function formatCurrency(n: number) {
  return `₹${n.toLocaleString(undefined, { minimumFractionDigits: 0 })}`;
}

const bandColors: Record<string, string> = {
  LOW: 'bg-success-light text-success-foreground',
  MEDIUM: 'bg-warning-light text-warning-foreground',
  HIGH: 'bg-danger-light text-danger-foreground',
  CRITICAL: 'bg-critical-light text-critical-foreground',
};

const actionColors: Record<string, string> = {
  approve: 'bg-success-light text-success-foreground',
  verify: 'bg-primary-light text-primary',
  review: 'bg-warning-light text-warning-foreground',
  hold: 'bg-danger-light text-danger-foreground',
};

function CaseCard({ case: caseData, onClick }: { case: any; onClick: () => void }) {
  return (
    <div
      className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:shadow-md transition cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-mono text-sm text-gray-600">{caseData.refund_id}</span>
            <span className="text-sm text-gray-500">{caseData.customer_id}</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${bandColors[caseData.risk_band] || 'bg-gray-100 text-gray-800'}`}>
              {caseData.risk_band}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${actionColors[caseData.recommended_action] || 'bg-gray-100 text-gray-800'}`}>
              {caseData.recommended_action.toUpperCase()}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${caseData.status === 'decided' ? 'bg-gray-100 text-gray-800' : 'bg-blue-100 text-blue-800'}`}>
              {caseData.status.toUpperCase()}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
            <span>Score: <span className="font-mono font-medium">{caseData.risk_score.toFixed(3)}</span></span>
            <span>Created: <span className="font-mono">{new Date(caseData.created_at).toLocaleString()}</span></span>
            {caseData.decided_at && (
              <span>Decided: <span className="font-mono">{new Date(caseData.decided_at).toLocaleString()}</span></span>
            )}
            {caseData.decision && (
              <span className="font-medium">Decision: <span className="text-gray-900">{caseData.decision.toUpperCase()}</span></span>
            )}
          </div>
        </div>
        <div className="text-right text-sm text-gray-500">
          <span className="font-mono">#{caseData.id}</span>
        </div>
      </div>
    </div>
  );
}