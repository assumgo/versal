import { Alert } from '../components/Alert';
import { FormField } from '../components/FormField';
export function Login() {
  return <main className="login-page"><section className="panel login-card"><img src="/assets/logo_versal_agro.png" alt="Versal Agro Contabilidade" /><h1>Acessar o Integrador Folha TXT</h1><Alert>Prévia visual. Autenticação disponível na próxima etapa.</Alert><form onSubmit={event => event.preventDefault()}><FormField label="E-mail" type="email" autoComplete="username" required /><FormField label="Senha" type="password" autoComplete="current-password" required /><button type="submit" disabled>Entrar · em breve</button></form></section></main>;
}
