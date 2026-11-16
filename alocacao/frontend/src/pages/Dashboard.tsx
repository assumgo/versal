import { useEffect, useState } from 'react';
import { dashboardApi, type DashboardSummary } from '../api/dashboard';

const CATEGORY_COLORS = [
  'var(--status-green)',
  'var(--status-blue)',
  'var(--status-yellow)',
  'var(--status-orange)',
  'var(--status-purple)',
  'var(--accent)',
];

export function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    dashboardApi
      .summary()
      .then((data) => {
        if (!cancelled) {
          setSummary(data);
          setError('');
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Falha ao carregar o painel');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const stats = summary
    ? [
        {
          id: 'disponiveis',
          label: 'Saldo de Produtos Disponíveis',
          value: summary.disponiveis,
          color: 'var(--status-green)',
        },
        {
          id: 'alocados',
          label: 'Saldo Alocados',
          value: summary.alocados,
          color: 'var(--status-blue)',
        },
        {
          id: 'manutencao',
          label: 'Saldo em manutenção',
          value: summary.em_manutencao,
          color: 'var(--status-yellow)',
        },
        {
          id: 'total',
          label: 'Total de recursos',
          value: summary.total_recursos,
          color: 'var(--status-orange)',
        },
      ]
    : [];

  return (
    <section>
      <header className="page-header">
        <span className="eyebrow">Painel</span>
        <h1>Resumo do estoque</h1>
        <p>
          Saldos de equipamentos disponíveis, alocados e em manutenção, com visão consolidada por
          categoria de produto.
        </p>
      </header>

      {error && (
        <div className="form-alert error" role="alert">
          {error}
        </div>
      )}

      <div className="stats-grid">
        {loading && !summary
          ? Array.from({ length: 4 }).map((_, index) => (
              <article key={index} className="stat-card stat-card-skeleton">
                <div className="label">Carregando...</div>
                <div className="value">—</div>
              </article>
            ))
          : stats.map((stat) => (
              <article
                key={stat.id}
                className="stat-card"
                style={{ ['--stat-color' as string]: stat.color }}
              >
                <div className="label">{stat.label}</div>
                <div className="value">{stat.value}</div>
              </article>
            ))}
      </div>

      <div className="category-summary" aria-label="Resumo por categorias">
        <div className="category-summary-heading">
          <h2>Resumo por categorias</h2>
          <span>{loading ? '...' : `${summary?.categorias.length ?? 0} categoria(s)`}</span>
        </div>

        {loading && !summary ? (
          <p className="muted">Carregando categorias...</p>
        ) : !summary || summary.categorias.length === 0 ? (
          <div className="kanban-empty">Nenhuma categoria cadastrada.</div>
        ) : (
          <div className="kanban category-kanban">
            {summary.categorias.map((categoria, index) => {
              const color = CATEGORY_COLORS[index % CATEGORY_COLORS.length];
              return (
                <section key={categoria.id} className="kanban-column category-column">
                  <div className="kanban-column-header">
                    <span
                      className="dot"
                      style={{ ['--col-color' as string]: color, background: color }}
                    />
                    <span>{categoria.nome}</span>
                    <span className="count">{categoria.total}</span>
                  </div>
                  <article className="category-summary-card">
                    <div className="category-metric">
                      <span>Disponíveis</span>
                      <strong>{categoria.disponiveis}</strong>
                    </div>
                    <div className="category-metric">
                      <span>Alocados</span>
                      <strong>{categoria.alocados}</strong>
                    </div>
                    <div className="category-metric">
                      <span>Em manutenção</span>
                      <strong>{categoria.em_manutencao}</strong>
                    </div>
                    <div className="category-metric total">
                      <span>Total (disp. + aloc.)</span>
                      <strong>{categoria.total}</strong>
                    </div>
                  </article>
                </section>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
