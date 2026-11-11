import { directory, groupsLabel } from '../auth/directory';
import { useSession } from '../auth/SessionProvider';

export function SignIn() {
  const { signIn } = useSession();
  return (
    <main className="signin">
      <section className="signin-card">
        <img src="/assets/logo_versal_agro.png" alt="Versal Agro Contabilidade" />
        <h1>Intranet</h1>
        <p>Escolha um acesso para abrir a página inicial. Os atalhos seguem os grupos de quem entra.</p>
        <div className="profile-list">
          {directory.map(person => (
            <button key={person.id} type="button" onClick={() => signIn(person.id)}>
              <strong>{person.name}</strong>
              <small>{groupsLabel(person.groups)}</small>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
