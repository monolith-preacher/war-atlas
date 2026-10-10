/**
 * Map layer catalogue and visualisation modes.
 * A mode is only a preset of layer visibility; users can still toggle each layer.
 */

export type MapMode = 'political' | 'geographic' | 'military' | 'operations'

export type LayerId =
  | 'boundaries' | 'participants' | 'alliances' | 'labels' | 'places'
  | 'terrain' | 'rivers' | 'modern'
  | 'battles' | 'events' | 'front_lines' | 'axes' | 'defensive_lines' | 'objectives' | 'landing_zones'
  | 'fortifications' | 'airfields' | 'naval_bases' | 'land_forces' | 'air_forces' | 'naval_forces' | 'routes' | 'areas'
  | 'uncertainty'

export interface LayerDef {
  id: LayerId
  label: string
  group: 'Político' | 'Geografia' | 'Militar' | 'Leitura'
  description: string
  /** API feature layers (properties.layer) rendered by this toggle. */
  featureLayers?: string[]
  /** Optional branch filter for unit positions. */
  branch?: string
  swatch: { kind: 'fill' | 'line' | 'dash' | 'point' | 'icon'; color: string }
}

export const LAYERS: LayerDef[] = [
  { id: 'boundaries', label: 'Fronteiras históricas', group: 'Político', description: 'Limites do snapshot de fronteiras aplicável à data (ver aviso de precisão).', swatch: { kind: 'line', color: '#c9b48a' } },
  { id: 'participants', label: 'Países participantes', group: 'Político', description: 'Destaca entidades políticas em guerra na data selecionada.', swatch: { kind: 'fill', color: '#8a7f6a' } },
  { id: 'alliances', label: 'Alianças', group: 'Político', description: 'Colore os participantes pela aliança válida na data.', swatch: { kind: 'fill', color: '#4f72a8' } },
  { id: 'labels', label: 'Rótulos', group: 'Leitura', description: 'Nomes de países, batalhas e feições.', swatch: { kind: 'icon', color: '#e8dfc9' } },
  { id: 'places', label: 'Localidades históricas', group: 'Geografia', description: 'Localidades cadastradas ligadas a batalhas e eventos do conflito (aparecem com zoom).', swatch: { kind: 'point', color: '#b9b2a0' } },
  { id: 'terrain', label: 'Relevo (sombreamento)', group: 'Geografia', description: 'Modelo de elevação atual (Terrain Tiles, AWS Open Data).', swatch: { kind: 'fill', color: '#5a5a50' } },
  { id: 'rivers', label: 'Rios, lagos e costa', group: 'Geografia', description: 'Natural Earth 1:50m; com zoom, linha de costa e água detalhadas do OpenStreetMap (geografia física, sem fronteiras).', swatch: { kind: 'line', color: '#5b84a6' } },
  { id: 'modern', label: 'Referência moderna (OSM)', group: 'Geografia', description: 'Estradas e localidades ATUAIS (OpenStreetMap via OpenFreeMap). Não representa a situação histórica.', swatch: { kind: 'line', color: '#8f8f8f' } },
  { id: 'battles', label: 'Batalhas', group: 'Militar', description: 'Batalhas iniciadas até a data (ativas destacadas; encerradas atenuadas).', featureLayers: ['battle'], swatch: { kind: 'point', color: '#d9534f' } },
  { id: 'events', label: 'Eventos recentes', group: 'Militar', description: 'Eventos documentados na data e nos dias anteriores (janela configurável).', featureLayers: ['event'], swatch: { kind: 'point', color: '#e0b04f' } },
  { id: 'front_lines', label: 'Linhas de frente', group: 'Militar', description: 'Linhas de frente documentadas para a data.', featureLayers: ['front_line'], swatch: { kind: 'line', color: '#e06a4f' } },
  { id: 'axes', label: 'Eixos de avanço / retirada', group: 'Militar', description: 'Setas de movimentos documentados.', featureLayers: ['advance_axis', 'withdrawal_axis'], swatch: { kind: 'line', color: '#79a7d9' } },
  { id: 'defensive_lines', label: 'Linhas defensivas', group: 'Militar', description: 'Linhas fortificadas e posições defensivas.', featureLayers: ['defensive_line'], swatch: { kind: 'line', color: '#b08a5a' } },
  { id: 'objectives', label: 'Objetivos', group: 'Militar', description: 'Objetivos documentados de operações.', featureLayers: ['objective'], swatch: { kind: 'icon', color: '#e8c96a' } },
  { id: 'landing_zones', label: 'Desembarques e lançamentos', group: 'Militar', description: 'Setores de desembarque e zonas de lançamento.', featureLayers: ['landing_zone', 'drop_zone'], swatch: { kind: 'line', color: '#6fc3c9' } },
  { id: 'fortifications', label: 'Fortificações', group: 'Militar', description: 'Baterias, redutos e fortificações.', featureLayers: ['fortification'], swatch: { kind: 'icon', color: '#a89c84' } },
  { id: 'airfields', label: 'Aeródromos', group: 'Militar', description: 'Aeródromos documentados.', featureLayers: ['airfield'], swatch: { kind: 'icon', color: '#9fb7d6' } },
  { id: 'naval_bases', label: 'Bases navais e portos', group: 'Militar', description: 'Bases navais e portos (inclui portos artificiais).', featureLayers: ['naval_base'], swatch: { kind: 'icon', color: '#7fa6c4' } },
  { id: 'land_forces', label: 'Forças terrestres', group: 'Militar', description: 'Posições documentadas de unidades terrestres.', featureLayers: ['unit_position'], branch: 'army', swatch: { kind: 'icon', color: '#9bb07a' } },
  { id: 'air_forces', label: 'Forças aéreas', group: 'Militar', description: 'Posições documentadas de unidades aéreas.', featureLayers: ['unit_position'], branch: 'air_force', swatch: { kind: 'icon', color: '#9fb7d6' } },
  { id: 'naval_forces', label: 'Forças navais', group: 'Militar', description: 'Posições documentadas de unidades navais.', featureLayers: ['unit_position'], branch: 'navy', swatch: { kind: 'icon', color: '#7fa6c4' } },
  { id: 'routes', label: 'Rotas militares', group: 'Militar', description: 'Rotas documentadas (logística, comboios...).', featureLayers: ['route'], swatch: { kind: 'dash', color: '#c9a96a' } },
  { id: 'areas', label: 'Áreas de operação / controle', group: 'Militar', description: 'Áreas de atuação e controle territorial documentado.', featureLayers: ['area_of_operations', 'territorial_control'], swatch: { kind: 'fill', color: '#c96a5a' } },
  { id: 'uncertainty', label: 'Halos de incerteza', group: 'Leitura', description: 'Círculo proporcional à precisão declarada de cada posição.', swatch: { kind: 'point', color: '#ffffff' } },
]

export const LAYER_BY_ID = Object.fromEntries(LAYERS.map((l) => [l.id, l])) as Record<LayerId, LayerDef>

const ALL_MILITARY: LayerId[] = ['battles', 'events', 'front_lines', 'axes', 'defensive_lines', 'objectives', 'landing_zones', 'fortifications',
  'airfields', 'naval_bases', 'land_forces', 'air_forces', 'naval_forces', 'routes', 'areas']

export const MODES: Record<MapMode, { label: string; description: string; layers: LayerId[] }> = {
  political: {
    label: 'Político',
    description: 'Países e fronteiras históricas conforme a data, com alinhamentos e participação na guerra.',
    layers: ['boundaries', 'participants', 'alliances', 'labels', 'places', 'rivers', 'battles'],
  },
  geographic: {
    label: 'Geográfico',
    description: 'Relevo, rios, cidades e características naturais.',
    layers: ['terrain', 'rivers', 'modern', 'labels', 'places', 'boundaries'],
  },
  military: {
    label: 'Militar',
    description: 'Frentes, batalhas, unidades, posições conhecidas e fortificações.',
    layers: ['boundaries', 'participants', 'labels', 'places', 'rivers', 'uncertainty', ...ALL_MILITARY],
  },
  operations: {
    label: 'Operações',
    description: 'Campanhas e batalhas: objetivos, eixos de avanço, desembarques, mudanças territoriais e reprodução cronológica.',
    layers: ['boundaries', 'labels', 'places', 'rivers', 'terrain', 'uncertainty', ...ALL_MILITARY],
  },
}

export function presetFor(mode: MapMode): Record<LayerId, boolean> {
  const on = new Set(MODES[mode].layers)
  return Object.fromEntries(LAYERS.map((l) => [l.id, on.has(l.id)])) as Record<LayerId, boolean>
}
