export function formatCurrency(n: number): string {
  return `₹${n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function formatScore(score: number): string {
  return (score * 100).toFixed(1) + '%';
}

export function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatTimestampFull(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatRelativeTime(isoString: string, referenceIsoString: string): string {
  const eventTime = new Date(isoString).getTime();
  const refTime = new Date(referenceIsoString).getTime();
  const diffMinutes = Math.round((eventTime - refTime) / 60000);

  if (diffMinutes < 0) {
    return `${Math.abs(diffMinutes)} min before`;
  } else if (diffMinutes > 0) {
    return `${diffMinutes} min after`;
  }
  return 'at refund time';
}

export function formatLossVsBaseline(lossAvoided: number): { label: string; value: string; color: 'success' | 'danger' } {
  if (lossAvoided >= 0) {
    return { label: 'Loss Avoided', value: formatCurrency(lossAvoided), color: 'success' };
  }
  return { label: 'Additional Loss', value: formatCurrency(Math.abs(lossAvoided)), color: 'danger' };
}

export function formatNumber(n: number): string {
  return n.toLocaleString();
}

export function formatPercent(n: number): string {
  return `${(n * 100).toFixed(1)}%`;
}