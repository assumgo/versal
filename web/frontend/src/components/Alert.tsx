import type { ReactNode } from 'react';
export function Alert({ children, variant = 'info' }: { children: ReactNode; variant?: 'info' | 'error' | 'success' }) {
  return <div className={`alert alert-${variant}`} role={variant === 'error' ? 'alert' : 'status'}>{children}</div>;
}
