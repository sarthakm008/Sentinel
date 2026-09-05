// WorkstationPane Component

import { ReactNode } from 'react';

interface WorkstationPaneProps {
  title: string;
  children: ReactNode;
  sticky?: boolean;
  className?: string;
}

export function WorkstationPane({ title, children, sticky = false, className = '' }: WorkstationPaneProps) {
  return (
    <div className={`workstation-pane ${sticky ? 'workstation-pane-sticky' : ''} ${className}`}>
      <div className="workstation-pane-header">
        <h3 className="workstation-pane-title">{title}</h3>
      </div>
      <div className="workstation-pane-body">
        {children}
      </div>
    </div>
  );
}