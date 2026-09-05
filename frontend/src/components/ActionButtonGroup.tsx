import { useCallback } from 'react';

interface ActionButtonProps {
  action: 'approve' | 'verify' | 'review' | 'hold';
  onClick: (action: string) => void;
  disabled?: boolean;
  loading?: boolean;
}

const actionStyles: Record<string, { base: string; hover: string }> = {
  approve: {
    base: 'bg-action-approve text-white border-action-approve',
    hover: 'hover:bg-emerald-700 hover:border-emerald-700',
  },
  verify: {
    base: 'bg-action-verify text-white border-action-verify',
    hover: 'hover:bg-blue-700 hover:border-blue-700',
  },
  review: {
    base: 'bg-action-review text-white border-action-review',
    hover: 'hover:bg-amber-700 hover:border-amber-700',
  },
  hold: {
    base: 'bg-action-hold text-white border-action-hold',
    hover: 'hover:bg-red-700 hover:border-red-700',
  },
};

const actionLabels: Record<string, string> = {
  approve: 'APPROVE',
  verify: 'VERIFY',
  review: 'REVIEW',
  hold: 'HOLD',
};

export function ActionButton({ action, onClick, disabled, loading }: ActionButtonProps) {
  const styles = actionStyles[action];
  const handleClick = useCallback(() => {
    if (!disabled && !loading) {
      onClick(action);
    }
  }, [action, onClick, disabled, loading]);

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled || loading}
      className={`btn btn-sm w-full border ${styles.base} ${styles.hover} disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-surface focus-visible:ring-primary`}
    >
      {loading ? 'PROCESSING...' : actionLabels[action]}
    </button>
  );
}

interface ActionButtonGroupProps {
  onAction: (action: string) => void;
  disabled?: boolean;
  loadingAction?: string | null;
}

export function ActionButtonGroup({ onAction, disabled, loadingAction }: ActionButtonGroupProps) {
  const actions: Array<'approve' | 'verify' | 'review' | 'hold'> = ['approve', 'verify', 'review', 'hold'];

  return (
    <div className="grid grid-cols-2 gap-2">
      {actions.map((action) => (
        <ActionButton
          key={action}
          action={action}
          onClick={onAction}
          disabled={disabled}
          loading={loadingAction === action}
        />
      ))}
    </div>
  );
}