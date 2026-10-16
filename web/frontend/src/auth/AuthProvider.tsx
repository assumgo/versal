import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import * as auth from '../api/auth';
import { onSessionExpired, refreshSession, setToken } from '../api/client';
type Session = { user: auth.User | null; loading: boolean; login: typeof auth.login; logout: () => Promise<void> };
const Context = createContext<Session | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<auth.User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    const unsubscribe = onSessionExpired(() => setUser(null));
    refreshSession().then(auth.me).then(value => { if (active) setUser(value); }).catch(() => { if (active) { setToken(null); setUser(null); } }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; unsubscribe(); };
  }, []);
  return <Context.Provider value={{ user, loading, login: async (email, password) => { const value = await auth.login(email, password); setUser(value); return value; }, logout: async () => { await auth.logout(); setUser(null); } }}>{children}</Context.Provider>;
}
export function useAuth() { const value = useContext(Context); if (!value) throw new Error('AuthProvider ausente'); return value; }
