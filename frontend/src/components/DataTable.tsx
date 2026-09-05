import { ReactNode } from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T, index: number) => ReactNode;
  className?: string;
  headerClassName?: string;
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string | number;
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  striped?: boolean;
  hoverable?: boolean;
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  loading,
  emptyMessage = 'No data available',
  onRowClick,
  striped = true,
  hoverable = true,
  className = '',
}: DataTableProps<T>) {
  const tableClasses = [
    'w-full border-collapse',
    className,
  ].join(' ');

  const thClasses = 'text-xs font-semibold uppercase tracking-wider text-text-secondary bg-bg-tertiary border-b border-border px-3 py-2 text-left';
  const tdClasses = 'text-sm text-text-primary border-b border-border px-3 py-2';

  if (loading) {
    return (
      <div className="table-container">
        <table className={tableClasses}>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key} className={thClasses} style={{ width: col.width }}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={columns.length} className="px-3 py-8 text-center text-text-muted">
                <div className="flex items-center justify-center gap-2">
                  <div className="spinner" />
                  <span>Loading...</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="table-container">
        <table className={tableClasses}>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key} className={thClasses} style={{ width: col.width }}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={columns.length} className="px-3 py-8 text-center text-text-muted">
                {emptyMessage}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className={tableClasses}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`${thClasses} ${col.headerClassName || ''}`}
                style={{ width: col.width }}
              >
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
                onRowClick && hoverable ? 'cursor-pointer' : '',
                striped && rowIndex % 2 === 1 ? 'bg-bg-tertiary/50' : '',
                hoverable && onRowClick ? 'hover:bg-bg-hover' : '',
              ].join(' ')}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((col) => (
                <td key={col.key} className={`${tdClasses} ${col.className || ''}`}>
                  {col.render(row, rowIndex)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
  pageSizeOptions?: number[];
}

export function Pagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 50, 100],
}: PaginationProps) {
  if (totalPages <= 1) return null;

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  return (
    <div className="flex items-center justify-between px-3 py-2 border-t border-border bg-bg-tertiary/50">
      <div className="flex items-center gap-3 text-xs text-text-secondary">
        <span>
          Showing <span className="font-mono font-medium">{startItem}</span>–<span className="font-mono font-medium">{endItem}</span> of <span className="font-mono font-medium">{totalItems}</span>
        </span>
        {onPageSizeChange && (
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="select select-sm w-auto px-6"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>{size} per page</option>
            ))}
          </select>
        )}
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="btn btn-sm btn-secondary disabled:opacity-50"
          aria-label="Previous page"
        >
          Previous
        </button>
        <span className="text-xs text-text-secondary px-2">
          Page <span className="font-mono font-medium">{currentPage}</span> of <span className="font-mono font-medium">{totalPages}</span>
        </span>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="btn btn-sm btn-secondary disabled:opacity-50"
          aria-label="Next page"
        >
          Next
        </button>
      </div>
    </div>
  );
}