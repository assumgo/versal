import { SessionProvider, useSession } from './auth/SessionProvider';
import { RouteProvider, useRoute } from './components/RouteProvider';
import { Shell } from './components/Shell';
import { AnnouncementsPage } from './pages/AnnouncementsPage';
import { HomePage } from './pages/HomePage';
import { ShortcutGate } from './pages/ShortcutGate';
import { SignIn } from './pages/SignIn';

export function App() {
  return (
    <SessionProvider>
      <RouteProvider>
        <Frame />
      </RouteProvider>
    </SessionProvider>
  );
}

function Frame() {
  const { user } = useSession();
  const { path } = useRoute();
  if (!user) return <SignIn />;
  const shortcut = /^\/atalhos\/([^/]+)$/.exec(path);
  const page = shortcut ? <ShortcutGate id={decodeURIComponent(shortcut[1])} /> : path === '/comunicados' ? <AnnouncementsPage /> : <HomePage />;
  return <Shell>{page}</Shell>;
}
