import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  EventType,
  type AccountInfo,
  type AuthenticationResult,
} from '@azure/msal-browser';
import { allowDevLogin, azureConfigured, loginRequest, msalInstance } from './msalConfig';

export type AuthUser = {
  name: string;
  email: string;
  provider: 'microsoft' | 'dev';
};

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  azureConfigured: boolean;
  allowDevLogin: boolean;
  loginWithMicrosoft: () => Promise<void>;
  loginDev: (email: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const DEV_SESSION_KEY = 'versal-alocacao-dev-user';

function toUser(account: AccountInfo): AuthUser {
  return {
    name: account.name || account.username,
    email: account.username,
    provider: 'microsoft',
  };
}

function readDevUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(DEV_SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthUser;
    if (parsed?.email && parsed.provider === 'dev') return parsed;
  } catch {
    /* ignore */
  }
  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        const instance = msalInstance;
        if (instance) {
          await instance.initialize();
          const result = await instance.handleRedirectPromise();
          const account =
            result?.account ||
            instance.getActiveAccount() ||
            instance.getAllAccounts()[0] ||
            null;
          if (account) {
            instance.setActiveAccount(account);
            if (active) setUser(toUser(account));
          } else if (active) {
            setUser(readDevUser());
          }

          instance.addEventCallback((event) => {
            if (event.eventType === EventType.LOGIN_SUCCESS && event.payload) {
              const payload = event.payload as AuthenticationResult;
              if (payload.account) {
                instance.setActiveAccount(payload.account);
                setUser(toUser(payload.account));
                localStorage.removeItem(DEV_SESSION_KEY);
              }
            }
            if (event.eventType === EventType.LOGOUT_SUCCESS) {
              setUser(null);
            }
          });
        } else if (active) {
          setUser(readDevUser());
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void bootstrap();
    return () => {
      active = false;
    };
  }, []);

  const loginWithMicrosoft = useCallback(async () => {
    if (!msalInstance || !azureConfigured) {
      throw new Error(
        'Configure VITE_AZURE_CLIENT_ID e VITE_AZURE_TENANT_ID para autenticar com Microsoft 365 / AD.',
      );
    }
    await msalInstance.loginRedirect(loginRequest);
  }, []);

  const loginDev = useCallback(async (email: string) => {
    if (!allowDevLogin) {
      throw new Error('Login de desenvolvimento desabilitado.');
    }
    const next: AuthUser = {
      name: email.split('@')[0] || 'Usuário',
      email: email.trim().toLowerCase(),
      provider: 'dev',
    };
    localStorage.setItem(DEV_SESSION_KEY, JSON.stringify(next));
    setUser(next);
  }, []);

  const logout = useCallback(async () => {
    localStorage.removeItem(DEV_SESSION_KEY);
    if (msalInstance && user?.provider === 'microsoft') {
      await msalInstance.logoutRedirect({
        account: msalInstance.getActiveAccount(),
      });
      return;
    }
    setUser(null);
  }, [user]);

  const value = useMemo(
    () => ({
      user,
      loading,
      azureConfigured,
      allowDevLogin,
      loginWithMicrosoft,
      loginDev,
      logout,
    }),
    [user, loading, loginWithMicrosoft, loginDev, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used within AuthProvider');
  return value;
}
