import { useEffect, type ReactNode } from 'react';
import { useAuth } from './AuthProvider';
import { LoadingState } from '../components/LoadingState';
export function ProtectedRoute({ children, onLogin }: { children: ReactNode; onLogin: () => void }) {
  const { user, loading } = useAuth();
  useEffect(() => { if (!loading && !user) onLogin(); }, [loading, user, onLogin]);
  if (loading) return <LoadingState />;
  return user ? children : null;
}
