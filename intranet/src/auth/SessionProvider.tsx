import { createContext, useContext, useState, type ReactNode } from 'react';
import { findUser, type DirectoryUser } from './directory';

const storageKey = 'intranet.userId';

type Session = {
  user: DirectoryUser | null;
  signIn: (id: string) => void;
  signOut: () => void;
};

const Context = createContext<Session | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [userId, setUserId] = useState<string | null>(() => sessionStorage.getItem(storageKey));
  const user = findUser(userId);
  function signIn(id: string) {
    if (!findUser(id)) return;
    sessionStorage.setItem(storageKey, id);
    setUserId(id);
  }
  function signOut() {
    sessionStorage.removeItem(storageKey);
    setUserId(null);
  }
  return <Context.Provider value={{ user, signIn, signOut }}>{children}</Context.Provider>;
}

export function useSession() {
  const value = useContext(Context);
  if (!value) throw new Error('SessionProvider ausente');
  return value;
}
