import { useEffect, useState } from 'react';
import { api, getToken, onSessionChange, setToken, type User } from './api';
import { Login } from './pages/Login';
import { PhasePage } from './pages/PhasePage';
import { Portfolio } from './pages/Portfolio';
import { ProjectPage } from './pages/ProjectPage';
import { TaskPage } from './pages/TaskPage';
import { currentRoute, navigate, type Route } from './router';
import { Shell } from './ui';

export function App() {
  const [route, setRoute] = useState<Route>(() => currentRoute());
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(!getToken());

  useEffect(() => {
    const sync = () => setRoute(currentRoute());
    window.addEventListener('popstate', sync);
    return () => window.removeEventListener('popstate', sync);
  }, []);

  useEffect(() => onSessionChange(() => {
    if (!getToken()) setUser(null);
  }), []);

  useEffect(() => {
    if (!getToken()) return;
    let active = true;
    api<User>('/api/auth/me').then(person => {
      if (active) setUser(person);
    }).catch(() => {
      if (active) setUser(null);
    }).finally(() => { if (active) setReady(true); });
    return () => { active = false; };
  }, [user === null && Boolean(getToken())]);

  useEffect(() => {
    if (!ready) return;
    if (!user && route.name !== 'login') navigate('/login');
    if (user && route.name === 'login') navigate('/projects');
    if (user && window.location.pathname === '/') navigate('/projects');
  }, [ready, user, route]);

  if (!ready) return <p className="muted loading-screen">Carregando…</p>;
  if (!user || route.name === 'login') return <Login onSuccess={person => { setUser(person); navigate('/projects'); }} />;

  let page;
  if (route.name === 'project') page = <ProjectPage key={route.projectId} projectId={route.projectId} filtro={route.filtro} />;
  else if (route.name === 'phase') page = <PhasePage key={route.phaseId} projectId={route.projectId} phaseId={route.phaseId} filtro={route.filtro} />;
  else if (route.name === 'task') page = <TaskPage key={route.taskId} projectId={route.projectId} phaseId={route.phaseId} taskId={route.taskId} />;
  else page = <Portfolio user={user} search={window.location.search} />;

  return <Shell user={user} onLogout={() => { setToken(null); navigate('/login'); }}>{page}</Shell>;
}
