import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './auth/AuthProvider';
import { ThemeProvider } from './theme/ThemeProvider';
import './styles/global.css';
import './styles/layout.css';
import './styles/login.css';
import './styles/dashboard.css';
import './styles/cadastros.css';
import './styles/equipamentos.css';

const routerBasename = (import.meta.env.VITE_BASE_PATH || '/').replace(/\/$/, '') || undefined;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter basename={routerBasename}>
          <App />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
);
