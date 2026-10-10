/** Portuguese labels for controlled vocabularies returned by the API. */

export const ENTITY_LABELS: Record<string, [string, string]> = {
  conflict: ['Conflito', 'Conflitos'],
  theater: ['Teatro de operações', 'Teatros de operações'],
  campaign: ['Campanha / operação', 'Campanhas e operações'],
  battle: ['Batalha', 'Batalhas'],
  event: ['Evento', 'Eventos'],
  place: ['Localidade', 'Localidades'],
  polity: ['País / entidade política', 'Países e entidades políticas'],
  unit: ['Unidade militar', 'Unidades militares'],
  person: ['Comandante / personalidade', 'Comandantes e personalidades'],
  equipment: ['Equipamento', 'Equipamentos'],
  armed_force: ['Força armada', 'Forças armadas'],
  source: ['Fonte', 'Fontes'],
  map_feature: ['Feição cartográfica', 'Feições cartográficas'],
  alliance: ['Aliança', 'Alianças'],
  uniform: ['Uniforme', 'Uniformes'],
  camouflage_pattern: ['Camuflagem', 'Camuflagens'],
}

export const entityLabel = (t: string, plural = false) => (ENTITY_LABELS[t] ?? [t, t])[plural ? 1 : 0]

export const PRECISION_LABELS: Record<string, string> = {
  day: 'dia exato',
  month: 'mês',
  year: 'ano',
  circa: 'aproximada',
  attested: 'atestada nesta data (limite real não documentado)',
}

export const CERTAINTY: Record<string, { label: string; tone: string; description: string }> = {
  verified: { label: 'Verificado', tone: 'ok', description: 'Afirmado por fontes identificáveis e confiáveis.' },
  estimated: { label: 'Estimativa', tone: 'info', description: 'Número ou posição estimados por uma fonte.' },
  interpreted: { label: 'Interpretação', tone: 'info', description: 'Interpretação historiográfica.' },
  reconstructed: { label: 'Reconstrução', tone: 'warn', description: 'Reconstrução cartográfica ou esquemática; não é uma representação exata.' },
  disputed: { label: 'Divergente', tone: 'warn', description: 'As fontes divergem; consulte os números e referências registrados.' },
  unverified: { label: 'Não verificado', tone: 'danger', description: 'Registro ainda sem fonte associada ou não revisado.' },
}

export const SPATIAL_ROLES: Record<string, string> = {
  exact_location: 'Localização exata',
  approximate_position: 'Posição aproximada',
  area_of_operations: 'Área de atuação',
  route: 'Rota',
  territorial_extent: 'Extensão territorial',
  schematic: 'Representação esquemática',
}

export const ECHELONS: Record<string, string> = {
  supreme_command: 'Comando supremo', theater_command: 'Comando de teatro', army_group: 'Grupo de exércitos', field_force: 'Força de campanha',
  army: 'Exército', corps: 'Corpo de exército', division: 'Divisão', brigade: 'Brigada', regiment: 'Regimento', battalion: 'Batalhão',
  company: 'Companhia', platoon: 'Pelotão', fleet: 'Frota', squadron: 'Esquadrão', flotilla: 'Flotilha', air_command: 'Comando aéreo',
  wing: 'Ala', group: 'Grupo', other: 'Outra formação',
}

export const BRANCHES: Record<string, string> = {
  army: 'Exército', navy: 'Marinha', air_force: 'Força aérea', marines: 'Fuzileiros', combined: 'Forças armadas (conjunto)',
  paramilitary: 'Paramilitar / partidária', other: 'Outra',
}

export const RELATIONS: Record<string, string> = {
  organic: 'subordinação orgânica', attached: 'agregada', operational_control: 'controle operacional', administrative: 'administrativa',
}

export const POSITION_KINDS: Record<string, string> = {
  commander: 'Comandante', acting_commander: 'Comandante interino', chief_of_staff: 'Chefe do estado-maior', deputy: 'Subcomandante',
  staff: 'Estado-maior', political: 'Cargo político', other: 'Outra função',
}

export const EQUIPMENT_CATEGORIES: Record<string, string> = {
  small_arm: 'Armas individuais', machine_gun: 'Metralhadoras', artillery: 'Artilharia', tank: 'Tanques', armored_vehicle: 'Veículos blindados',
  transport_vehicle: 'Veículos de transporte', aircraft: 'Aeronaves', ship: 'Navios', submarine: 'Submarinos', landing_craft: 'Embarcações de desembarque',
  communications: 'Comunicações', personal_equipment: 'Equipamento individual', other: 'Outros',
}

export const METRICS: Record<string, string> = {
  strength: 'Efetivo', casualties: 'Baixas', killed: 'Mortos', wounded: 'Feridos', missing: 'Desaparecidos', captured: 'Prisioneiros',
  tanks_lost: 'Tanques perdidos', aircraft_lost: 'Aeronaves perdidas', civilian_deaths: 'Mortes de civis', other: 'Outro',
}

export const BATTLE_KINDS: Record<string, string> = {
  battle: 'Batalha', landing: 'Desembarque', siege: 'Cerco', engagement: 'Combate', airborne_operation: 'Operação aerotransportada',
  naval_battle: 'Batalha naval', liberation: 'Libertação',
}

export const CAMPAIGN_KINDS: Record<string, string> = { campaign: 'Campanha', operation: 'Operação', offensive: 'Ofensiva' }

export const SIDES: Record<string, string> = { a: 'Lado A', b: 'Lado B', other: 'Outro' }

export const SOURCE_KINDS: Record<string, string> = {
  book: 'Livro', official_history: 'História oficial', article: 'Artigo', archive: 'Arquivo', website: 'Site', dataset: 'Conjunto de dados',
  encyclopedia: 'Enciclopédia (fonte terciária)', map: 'Mapa', other: 'Outro',
}

export const EXISTENCE: Record<string, string> = {
  active: 'Em existência nesta data',
  not_yet_formed: 'Ainda não formada nesta data',
  disbanded: 'Já dissolvida nesta data',
  existence_undocumented: 'Datas de existência não documentadas',
  unknown_date: '',
}
