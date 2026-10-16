# Sessão e cadastros — Task 8

O frontend usa `VITE_API_BASE_URL` (padrão local: `http://localhost:8000/api/v1`).
Todas as requisições incluem credenciais. O access token permanece somente em
memória; o cookie HttpOnly é gerenciado pela API. Recarregar a página tenta
restaurar a sessão por refresh e `/auth/me`. Um 401 permite uma renovação e um
reenvio; 403 apresenta a negativa sem renovar. Requisições simultâneas compartilham
a renovação. Mudanças de sessão impedem reenvios de operações da conta anterior.
Sair aguarda a revogação no servidor; uma falha mantém a sessão e mostra o erro.

Rotas `/`, `/empresas` e `/colaboradores` são protegidas; `/login` retorna à rota
solicitada após autenticar. A navegação usa a History API, incluindo voltar/avançar.
Em hospedagem estática, configurar fallback para `index.html` nas rotas do SPA.

Empresas lista apenas os vínculos retornados pela API. Administrador pode criar,
editar, inativar e reativar pelo status. Colaboradores usa a empresa ativa e
permite escrita para Administrador/Operador em empresas não inativas. Exclusão
exige confirmação. A API continua sendo a autoridade para papel e vínculo.
Trocar empresa descarta formulários e respostas anteriores. Erros de validação
mantêm o formulário preenchido. Listas vazias, carregamento, falha e acesso
negado têm estados próprios e falhas permitem nova tentativa.

A competência é contexto local editável: não há endpoint de competências nesta
fase, nem influência sobre os cadastros. Dashboard e módulos futuros informam
indisponibilidade; indicadores simulados da Task 7 não aparecem na sessão real.
Administração de usuários e vínculos continua pela API.

Verificação automatizada usa respostas sintéticas, sem banco operacional.
Capturas desktop/mobile: `screenshots/task8-*.png`.
