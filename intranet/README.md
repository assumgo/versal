# Intranet

Página inicial dos sites internos. Ela abre para todo mundo, com a lista completa de atalhos. A permissão é conferida só no clique: com grupo compatível, o site abre; sem grupo, um aviso diz que não há permissão para o local.

Nesta pré-visualização a sessão começa como visitante. No SharePoint, `groups` passa a vir do usuário autenticado no Microsoft 365.

## Executar

Na pasta `intranet/`:

```bash
npm ci
npm run dev
```

Abra http://localhost:5174. O menu da conta troca o acesso de exemplo:

| Acesso | O que abre |
|---|---|
| Visitante | Nenhum atalho |
| Acesso geral | Documentos |
| Time financeiro | Documentos, Folha |
| RH e operação | Documentos, Pessoas, Benefícios, Operação |

`npm test -- --run` cobre o clique e o aviso. `npm run build` verifica o TypeScript e gera os arquivos estáticos.

## Definir os atalhos

Edite `src/shortcuts/catalog.ts`. Cada item precisa de `id`, `label`, `hint`, `href` http(s) e `groups`.

```ts
{
  id: 'folha',
  label: 'Folha',
  hint: 'Fechamento e relatórios financeiros',
  href: 'https://sharepoint.exemplo/sites/folha',
  groups: ['financeiro'],
  icon: 'finance',
}
```

O atalho aparece para todo mundo. Ele só abre quando a sessão tem pelo menos um grupo da lista. `todos` é o grupo de toda a empresa. Sem grupo compatível, a página mostra o aviso de permissão.

Os grupos de cada acesso de pré-visualização ficam em `src/auth/directory.ts`. O nome amigável de um grupo novo pode entrar em `groupLabels`, no mesmo arquivo.

## Comunicados

Na home, os atalhos ficam na coluna da esquerda. À direita, o quadro do canal do Teams fica em cima e os comunicados gerais ficam embaixo. Os textos em `src/announcements/feed.ts` são exemplo de layout. A integração com notícias do SharePoint e com o canal ainda não publica conteúdo real.
