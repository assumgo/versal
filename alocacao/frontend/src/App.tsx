import { useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { AppShell } from './components/AppShell';
import { Categorias } from './pages/Categorias';
import { Colaboradores } from './pages/Colaboradores';
import { Dashboard } from './pages/Dashboard';
import { Fornecedores } from './pages/Fornecedores';
import { Login } from './pages/Login';
import { PlaceholderPage } from './pages/PlaceholderPage';

function ProtectedShell({
  children,
  ctaLabel,
  onCta,
}: {
  children: React.ReactNode;
  ctaLabel?: string;
  onCta?: () => void;
}) {
  return (
    <ProtectedRoute>
      <AppShell ctaLabel={ctaLabel} onCta={onCta}>
        {children}
      </AppShell>
    </ProtectedRoute>
  );
}

function CrudRoute({
  ctaLabel,
  children,
}: {
  ctaLabel: string;
  children: (createRequest: number) => React.ReactNode;
}) {
  const [createRequest, setCreateRequest] = useState(0);
  return (
    <ProtectedShell ctaLabel={ctaLabel} onCta={() => setCreateRequest((value) => value + 1)}>
      {children(createRequest)}
    </ProtectedShell>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedShell>
            <Dashboard />
          </ProtectedShell>
        }
      />
      <Route path="/cadastros" element={<Navigate to="/cadastros/categorias" replace />} />
      <Route
        path="/cadastros/categorias"
        element={
          <CrudRoute ctaLabel="+ Nova categoria">
            {(createRequest) => <Categorias createRequest={createRequest} />}
          </CrudRoute>
        }
      />
      <Route
        path="/cadastros/colaboradores"
        element={
          <CrudRoute ctaLabel="+ Novo colaborador">
            {(createRequest) => <Colaboradores createRequest={createRequest} />}
          </CrudRoute>
        }
      />
      <Route
        path="/cadastros/fornecedores"
        element={
          <CrudRoute ctaLabel="+ Novo fornecedor">
            {(createRequest) => <Fornecedores createRequest={createRequest} />}
          </CrudRoute>
        }
      />
      <Route
        path="/configuracoes"
        element={
          <ProtectedShell ctaLabel="Salvar">
            <PlaceholderPage
              title="Configurações"
              description="Parâmetros do tenant, integração Microsoft Entra ID e preferências de documentos TRE."
              features={[
                { title: 'Identidade 365', text: 'Client ID, tenant e grupos autorizados.' },
                { title: 'Numeração TRE', text: 'Sequência e modelo dos documentos de entrega/devolução.' },
                { title: 'Temas', text: 'Padrão claro/escuro por usuário ou organização.' },
              ]}
            />
          </ProtectedShell>
        }
      />
      <Route
        path="/notas-fiscais"
        element={
          <ProtectedShell ctaLabel="+ Nova NF">
            <PlaceholderPage
              title="Notas Fiscais"
              description="Dê entrada em recursos e equipamentos a partir de notas fiscais ou de forma avulsa."
              features={[
                { title: 'Entrada por NF', text: 'Importe itens e serial numbers a partir da nota.' },
                { title: 'Entrada avulsa', text: 'Registre equipamentos sem vínculo fiscal imediato.' },
                { title: 'Estoque', text: 'Itens entram como disponíveis para alocação.' },
              ]}
            />
          </ProtectedShell>
        }
      />
      <Route
        path="/tres"
        element={
          <ProtectedShell ctaLabel="+ Emitir TRE">
            <PlaceholderPage
              title="TREs"
              description="Emita o Termo de Responsabilidade de Equipamento na entrega e na devolução."
              features={[
                { title: 'TRE de entrega', text: 'Documento assinado ao alocar equipamentos.' },
                { title: 'TRE de devolução', text: 'Baixa com checklist de condição do item.' },
                { title: 'Histórico', text: 'Consulta e reimpressão dos termos emitidos.' },
              ]}
            />
          </ProtectedShell>
        }
      />
      <Route
        path="/alocacoes"
        element={
          <ProtectedShell ctaLabel="+ Nova alocação">
            <PlaceholderPage
              title="Alocações"
              description="Controle de saída e retorno de equipamentos para colaboradores."
              features={[
                { title: 'Saída', text: 'Reserve itens do estoque e vincule ao colaborador.' },
                { title: 'Retorno', text: 'Receba o item e atualize o inventário.' },
                { title: 'Pendências', text: 'Acompanhe alocações sem TRE ou com atraso.' },
              ]}
            />
          </ProtectedShell>
        }
      />
      <Route
        path="/equipamentos"
        element={
          <ProtectedShell ctaLabel="+ Novo equipamento">
            <PlaceholderPage
              title="Equipamentos"
              description="Inventário completo dos recursos com status, serial e localização."
              features={[
                { title: 'Inventário', text: 'Lista filtrável de todos os ativos.' },
                { title: 'Status', text: 'Disponível, alocado, manutenção ou baixa.' },
                { title: 'Histórico', text: 'Linha do tempo de entradas, alocações e TREs.' },
              ]}
            />
          </ProtectedShell>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
