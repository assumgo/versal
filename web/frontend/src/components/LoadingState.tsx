export function LoadingState({ label = 'Carregando…' }: { label?: string }) {
  return <div className="loading-state" role="status"><span className="spinner" aria-hidden="true" />{label}</div>;
}
