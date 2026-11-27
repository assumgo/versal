export type Route =
  | { name: 'login' }
  | { name: 'portfolio' }
  | { name: 'project'; projectId: number; filtro: string | null }
  | { name: 'phase'; projectId: number; phaseId: number; filtro: string | null }
  | { name: 'task'; projectId: number; phaseId: number; taskId: number };

export function parseRoute(path: string, search: string): Route {
  const filtro = new URLSearchParams(search).get('filtro');
  if (path === '/login') return { name: 'login' };
  const task = path.match(/^\/projects\/(\d+)\/phases\/(\d+)\/tasks\/(\d+)$/);
  if (task) return { name: 'task', projectId: Number(task[1]), phaseId: Number(task[2]), taskId: Number(task[3]) };
  const phase = path.match(/^\/projects\/(\d+)\/phases\/(\d+)$/);
  if (phase) return { name: 'phase', projectId: Number(phase[1]), phaseId: Number(phase[2]), filtro };
  const project = path.match(/^\/projects\/(\d+)$/);
  if (project) return { name: 'project', projectId: Number(project[1]), filtro };
  return { name: 'portfolio' };
}

export function currentRoute(): Route {
  return parseRoute(window.location.pathname, window.location.search);
}

export function navigate(path: string) {
  window.history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}

export const PORTFOLIO_QUERY = 'gestao.portfolio.query';

export function rememberPortfolio(search: string) {
  sessionStorage.setItem(PORTFOLIO_QUERY, search);
}

export function portfolioHref() {
  const search = sessionStorage.getItem(PORTFOLIO_QUERY) ?? '';
  return `/projects${search}`;
}
