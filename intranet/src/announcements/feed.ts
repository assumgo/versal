export type Announcement = {
  id: string;
  title: string;
  summary: string;
  publishedAt: string;
  source: 'oficial' | 'teams';
  channel: string;
};

/**
 * Textos de exemplo para ocupar o painel.
 * A coluna oficial passa a ser notícia do SharePoint; a do Teams,
 * o canal único de comunicados, quando a integração estiver ligada.
 */
export const announcements: readonly Announcement[] = [
  {
    id: 'fechamento',
    title: 'Prazos do fechamento de novembro',
    summary: 'Envie alterações de folha e benefícios até o dia 20 para entrar neste fechamento.',
    publishedAt: '2026-11-10T12:00:00-03:00',
    source: 'oficial',
    channel: 'Comunicado geral',
  },
  {
    id: 'biblioteca',
    title: 'Biblioteca de documentos em novo endereço',
    summary: 'Os arquivos compartilhados da empresa estão no site Documentos. Os links antigos deixam de abrir na sexta.',
    publishedAt: '2026-11-04T12:00:00-03:00',
    source: 'oficial',
    channel: 'Comunicado geral',
  },
  {
    id: 'calendario',
    title: 'Calendário de reuniões gerais',
    summary: 'A reunião mensal fica na primeira terça, às 9h, com pauta publicada no dia anterior.',
    publishedAt: '2026-10-28T12:00:00-03:00',
    source: 'oficial',
    channel: 'Comunicado geral',
  },
  {
    id: 'manutencao',
    title: 'Manutenção no compartilhamento nesta sexta',
    summary: 'O acesso aos sites internos fica interrompido das 19h às 21h para atualização.',
    publishedAt: '2026-11-11T09:00:00-03:00',
    source: 'teams',
    channel: 'Comunicados',
  },
  {
    id: 'ata',
    title: 'Novo modelo de ata na biblioteca',
    summary: 'Usem o arquivo Modelo de ata daqui em diante. A versão anterior fica só para consulta.',
    publishedAt: '2026-11-09T11:00:00-03:00',
    source: 'teams',
    channel: 'Comunicados',
  },
  {
    id: 'comprovantes',
    title: 'Comprovantes de benefícios até sexta',
    summary: 'Quem ainda não anexou o comprovante deste mês envia pelo site Benefícios.',
    publishedAt: '2026-11-07T15:00:00-03:00',
    source: 'teams',
    channel: 'Comunicados',
  },
];

export function bySource(source: Announcement['source']) {
  return announcements
    .filter(item => item.source === source)
    .sort((left, right) => right.publishedAt.localeCompare(left.publishedAt));
}
