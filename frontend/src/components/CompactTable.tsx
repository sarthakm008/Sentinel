// CompactTable Component

import { ReactNode } from 'react';

export interface CompactTableColumn<T> {
  key: string;
  header: string;
  render: (row: T, index: number) => ReactNode;
  className?: string;
  headerClassName?: string;
  width?: string;
}

interface CompactTableProps<T> {
  columns: CompactTableColumn<T>[];
  data: T[];
  keyExtractor: (row: T) => string | number;
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  striped?: boolean;
  /** Enable horizontal scroll containment (default: true for safety) */
  scrollable?: boolean;
}

export function CompactTable<T>({
  columns,
  data,
  keyExtractor,
  loading,
  emptyMessage = 'No data available',
  onRowClick,
  striped = true,
  scrollable = true,
}: CompactTableProps<T>) {
  if (loading) {
    return (
      <div style={{ padding: '32px', textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto 8px' }} />
        <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>Loading...</span>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="empty-state">
        <span>{emptyMessage}</span>
      </div>
    );
  }

  const tableContent = (
    <table className="compact-table">
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col.key} className={col.headerClassName} style={{ width: col.width }}>
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, rowIndex) => (
          <tr
            key={keyExtractor(row)}
            className={[
              onRowClick ? 'cursor-pointer' : '',
              striped && rowIndex % 2 === 1 ? 'bg-bg-hover' : '',
            ].join(' ')}
            onClick={() => onRowClick?.(row)}
          >
            {columns.map((col) => (
              <td key={col.key} className={col.className}>
                {col.render(row, rowIndex)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );

  if (scrollable) {
    return (
      <div className="compact-table-wrapper" style={{ overflowX: 'auto', width: '100%' }}>
        {tableContent}
      </div>
    );
  }

  return tableContent;
}