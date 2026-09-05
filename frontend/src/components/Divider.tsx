// Divider Component

interface DividerProps {
  label?: string;
}

export function Divider({ label }: DividerProps) {
  if (label) {
    return (
      <div className="divider-with-label">
        <span>{label}</span>
      </div>
    );
  }
  return <hr className="divider" />;
}