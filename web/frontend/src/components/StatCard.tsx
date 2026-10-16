import type { ReactNode } from 'react';
export function StatCard({ title, value, detail }: { title: string; value: ReactNode; detail?: string }) {
  return <article className="stat-card"><h2>{title}</h2><strong>{value}</strong>{detail && <p>{detail}</p>}</article>;
}
