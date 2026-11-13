import { useMemo, useState } from 'react';
import { filterChips, kanbanColumns, stockStats } from '../data/mock';

export function Dashboard() {
  const [activeFilter, setActiveFilter] = useState('todas');

  const columns = useMemo(() => {
    if (activeFilter === 'todas') return kanbanColumns;
    if (activeFilter === 'estoque') {
      return kanbanColumns.map((column) =>
        column.id === 'disponivel' ? column : { ...column, items: [] },
      );
    }
    if (activeFilter === 'alocadas') {
      return kanbanColumns.map((column) =>
        column.id === 'alocado' ? column : { ...column, items: [] },
      );
    }
    if (activeFilter === 'entrega' || activeFilter === 'devolucao') {
      return kanbanColumns.map((column) =>
        column.id === 'devolucao' || column.id === 'entrada'
          ? column
          : { ...column, items: [] },
      );
    }
    return kanbanColumns;
  }, [activeFilter]);

  return (
    <section>
      <header className="page-header">
        <span className="eyebrow">Painel</span>
        <h1>Resumo do estoque</h1>
        <p>
          Acompanhe entradas por nota fiscal ou avulsas, alocações para colaboradores e a emissão
          dos documentos TRE de entrega e devolução.
        </p>
      </header>

      <div className="stats-grid">
        {stockStats.map((stat) => (
          <article key={stat.id} className="stat-card" style={{ ['--stat-color' as string]: stat.color }}>
            <div className="label">{stat.label}</div>
            <div className="value">{stat.value}</div>
          </article>
        ))}
      </div>

      <div className="filter-row" role="tablist" aria-label="Filtros do estoque">
        {filterChips.map((chip) => (
          <button
            key={chip.id}
            type="button"
            role="tab"
            aria-selected={activeFilter === chip.id}
            className={`chip${activeFilter === chip.id ? ' active' : ''}`}
            onClick={() => setActiveFilter(chip.id)}
          >
            {chip.label}
            <span className="count">{chip.count}</span>
          </button>
        ))}
      </div>

      <div className="kanban" aria-label="Fluxo de alocação">
        {columns.map((column) => (
          <section key={column.id} className="kanban-column">
            <div className="kanban-column-header">
              <span className="dot" style={{ ['--col-color' as string]: column.color, background: column.color }} />
              <span>{column.title}</span>
              <span className="count">{column.items.length}</span>
            </div>
            {column.items.length === 0 ? (
              <div className="kanban-empty">Nenhum item nesta etapa</div>
            ) : (
              column.items.map((item, index) => (
                <article
                  key={item.id}
                  className="kanban-card"
                  style={{ animationDelay: `${index * 40}ms` }}
                >
                  <div className="meta">
                    <span>{item.id}</span>
                    <span>{item.age}</span>
                  </div>
                  <h3>{item.title}</h3>
                  <p>{item.serial}</p>
                  <p>{item.collaborator}</p>
                </article>
              ))
            )}
          </section>
        ))}
      </div>
    </section>
  );
}
