import { SessionProvider } from './auth/SessionProvider';
import { RouteProvider, useRoute } from './components/RouteProvider';
import { Shell } from './components/Shell';
import { AnnouncementsPage } from './pages/AnnouncementsPage';
import { HomePage } from './pages/HomePage';

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
  const { path } = useRoute();
  return <Shell>{path === '/comunicados' ? <AnnouncementsPage /> : <HomePage />}</Shell>;
}
