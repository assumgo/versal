import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

type Route = { path: string; go: (to: string) => void };

const Context = createContext<Route | null>(null);

function currentPath() {
  const path = window.location.pathname;
  return path.length > 1 && path.endsWith('/') ? path.slice(0, -1) : path;
}

export function RouteProvider({ children }: { children: ReactNode }) {
  const [path, setPath] = useState(currentPath);
  useEffect(() => {
    const sync = () => setPath(currentPath());
    window.addEventListener('popstate', sync);
    return () => window.removeEventListener('popstate', sync);
  }, []);
  const go = useCallback((to: string) => {
    const next = to.length > 1 && to.endsWith('/') ? to.slice(0, -1) : to;
    if (window.location.pathname !== next) window.history.pushState({}, '', next);
    setPath(next);
  }, []);
  return <Context.Provider value={{ path, go }}>{children}</Context.Provider>;
}

export function useRoute() {
  const value = useContext(Context);
  if (!value) throw new Error('RouteProvider ausente');
  return value;
}

export function Link({ to, className, children }: { to: string; className?: string; children: ReactNode }) {
  const { go } = useRoute();
  return (
    <a
      href={to}
      className={className}
      onClick={event => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
        event.preventDefault();
        go(to);
      }}
    >
      {children}
    </a>
  );
}
