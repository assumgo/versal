# Intranet

Página inicial dos sites internos. A grade mostra apenas os atalhos que os grupos da pessoa logada permitem abrir. O endereço direto de um atalho sem grupo também é recusado.

Nesta pré-visualização a sessão é local. No SharePoint, `groups` passa a vir do usuário autenticado no Microsoft 365.

## Executar

Na pasta `intranet/`:

```bash
npm ci
npm run dev
```

Abra http://localhost:5174. Há três acessos de exemplo:

| Acesso | Grupos | Atalhos visíveis |
|---|---|---|
| Acesso geral | Toda a empresa | Documentos |
| Time financeiro | Toda a empresa, Financeiro | Documentos, Folha |
| RH e operação | Toda a empresa, RH, Operação | Documentos, Pessoas, Benefícios, Operação |

`npm test -- --run` cobre a filtragem. `npm run build` verifica o TypeScript e gera os arquivos estáticos.

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

A pessoa vê e abre o atalho quando a sessão dela tem pelo menos um grupo da lista. `todos` é o grupo de toda a empresa. Sem grupo na lista, o atalho não aparece.

Os grupos de cada acesso de pré-visualização ficam em `src/auth/directory.ts`. O nome amigável de um grupo novo pode entrar em `groupLabels`, no mesmo arquivo.

## Comunicados

A home tem duas colunas: comunicados gerais e o quadro do canal do Teams. Os textos em `src/announcements/feed.ts` são exemplo de layout. A integração com notícias do SharePoint e com o canal ainda não publica conteúdo real.
