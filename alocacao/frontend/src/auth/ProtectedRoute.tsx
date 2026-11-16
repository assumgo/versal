import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthProvider';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  const location = useLocation();

  if (auth.loading) {
    return (
      <div className="login-page" role="status" aria-live="polite">
        <div className="login-card" style={{ textAlign: 'center' }}>
          <img src="/logo2.png" alt="" width={64} height={64} style={{ margin: '0 auto 1rem' }} />
          <p>Carregando sessão...</p>
        </div>
      </div>
    );
  }

  if (!auth.user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}
