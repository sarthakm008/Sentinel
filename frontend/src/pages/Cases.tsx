// Cases Page - Investigation Queue

import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { casesApi } from '../api';
import { CasesListResponse } from '../types';
import { PageHeader } from '../components/PageHeader';
import { DataRow } from '../components/DataRow';
import { Pagination } from '../components/DataTable';

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

  const loadCases = useCallback(async () => {
    try {
      setLoading(true);
      const res = await casesApi.list(filters);
      setData(res);
    } catch (err) {
      console.error('Failed to load cases:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadCases();
  }, [loadCases]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handlePageSizeChange = (size: number) => {
    setFilters((prev) => ({ ...prev, size, page: 1 }));
  };

  return (
    <div>
      <PageHeader
        title="Cases"
        subtitle="Investigation queue"
      />

      {/* Toolbar */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 16px',
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        marginBottom: 'var(--space-loose)'
      }}>
        <select
          value={filters.status}
          onChange={(e) => handleFilterChange('status', e.target.value)}
          className="select select-sm"
          style={{ width: 'auto', minWidth: '140px' }}
          aria-label="Filter by status"
        >
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="decided">Decided</option>
        </select>
        <select
          value={filters.band}
          onChange={(e) => handleFilterChange('band', e.target.value)}
          className="select select-sm"
          style={{ width: 'auto', minWidth: '140px' }}
          aria-label="Filter by risk band"
        >
          <option value="">All Risk</option>
          <option value="LOW">LOW</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="HIGH">HIGH</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>
        <div style={{ flex: 1 }} />
        <button onClick={loadCases} className="btn btn-secondary btn-sm" disabled={loading}>
          Refresh
        </button>
      </div>

      {/* Investigation List */}
      <div style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden'
      }}>
        {loading && !data ? (
          <div style={{ padding: '32px', textAlign: 'center' }}>
            <div className="spinner" style={{ margin: '0 auto 8px' }} />
            <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>Loading cases...</span>
          </div>
        ) : data?.cases.length === 0 ? (
          <div className="empty-state" style={{ padding: '32px' }}>
            <p style={{ color: 'var(--color-text-muted)' }}>No cases found matching the current filters</p>
          </div>
        ) : (
          <>
            {data?.cases.map((c) => (
              <DataRow
                key={c.id}
                case={c}
                onClick={() => navigate(`/cases/${c.id}`)}
              />
            ))}
          </>
        )}
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <Pagination
          currentPage={data.page}
          totalPages={data.pages}
          totalItems={data.total}
          pageSize={data.size}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />
      )}
    </div>
  );
}