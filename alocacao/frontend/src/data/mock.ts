export type StockStat = {
  id: string;
  label: string;
  value: number;
  color: string;
};

export type FilterChip = {
  id: string;
  label: string;
  count: number;
};

export type AllocationCard = {
  id: string;
  title: string;
  serial: string;
  collaborator: string;
  age: string;
  status: string;
};

export type KanbanColumn = {
  id: string;
  title: string;
  color: string;
  items: AllocationCard[];
};

export const stockStats: StockStat[] = [
  { id: 'disponivel', label: 'Disponíveis', value: 48, color: 'var(--status-green)' },
  { id: 'alocado', label: 'Alocados', value: 23, color: 'var(--status-blue)' },
  { id: 'manutencao', label: 'Em manutenção', value: 4, color: 'var(--status-yellow)' },
  { id: 'aguardando', label: 'Aguardando TRE', value: 6, color: 'var(--status-orange)' },
];

export const filterChips: FilterChip[] = [
  { id: 'todas', label: 'Todas', count: 81 },
  { id: 'estoque', label: 'Em estoque', count: 48 },
  { id: 'alocadas', label: 'Alocadas', count: 23 },
  { id: 'entrega', label: 'TRE entrega', count: 5 },
  { id: 'devolucao', label: 'TRE devolução', count: 3 },
  { id: 'avarias', label: 'Com avaria', count: 2 },
];

export const kanbanColumns: KanbanColumn[] = [
  {
    id: 'entrada',
    title: '1. Entrada / NF',
    color: 'var(--status-blue)',
    items: [
      {
        id: 'EQ-1042',
        title: 'Notebook Dell Latitude 5440',
        serial: 'SN-DL-88921',
        collaborator: 'Entrada NF 4521',
        age: 'há 1 d',
        status: 'entrada',
      },
      {
        id: 'EQ-1043',
        title: 'Monitor LG 27"',
        serial: 'SN-LG-12009',
        collaborator: 'Entrada avulsa',
        age: 'há 3 h',
        status: 'entrada',
      },
    ],
  },
  {
    id: 'disponivel',
    title: '2. Disponível',
    color: 'var(--status-green)',
    items: [
      {
        id: 'EQ-0988',
        title: 'Headset Logitech Zone',
        serial: 'SN-LG-44102',
        collaborator: 'Estoque central',
        age: 'há 5 d',
        status: 'disponivel',
      },
    ],
  },
  {
    id: 'alocado',
    title: '3. Alocado',
    color: 'var(--status-purple)',
    items: [
      {
        id: 'EQ-0871',
        title: 'iPhone 14',
        serial: 'SN-AP-77812',
        collaborator: 'Ana Souza',
        age: 'há 12 d',
        status: 'alocado',
      },
      {
        id: 'EQ-0902',
        title: 'MacBook Pro 14"',
        serial: 'SN-AP-99120',
        collaborator: 'Carlos Mendes',
        age: 'há 2 d',
        status: 'alocado',
      },
    ],
  },
  {
    id: 'devolucao',
    title: '4. Devolução / TRE',
    color: 'var(--status-orange)',
    items: [
      {
        id: 'EQ-0755',
        title: 'Tablet Samsung S9',
        serial: 'SN-SS-33011',
        collaborator: 'Paula Lima',
        age: 'há 6 h',
        status: 'devolucao',
      },
    ],
  },
];
