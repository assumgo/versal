import type { ReactNode, Key } from 'react';
export type Column<T> = { key: string; title: string; render: (row: T) => ReactNode };
export function DataTable<T>({ caption, columns, rows, rowKey, emptyMessage = 'Nenhum registro encontrado.' }: { caption: string; columns: Column<T>[]; rows: T[]; rowKey: (row: T, index: number) => Key; emptyMessage?: string }) {
  return <div className="table-scroll" role="region" aria-label={caption} tabIndex={0}><table><caption>{caption}</caption><thead><tr>{columns.map(column => <th key={column.key} scope="col">{column.title}</th>)}</tr></thead><tbody>{rows.length ? rows.map((row, index) => <tr key={rowKey(row, index)}>{columns.map(column => <td key={column.key}>{column.render(row)}</td>)}</tr>) : <tr><td colSpan={columns.length}>{emptyMessage}</td></tr>}</tbody></table></div>;
}
