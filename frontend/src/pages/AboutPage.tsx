import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import { SourceLine } from '../components/common/docs'
import { CertaintyBadge, Loading } from '../components/common/ui'
import { Logo } from '../components/layout/Header'
import { useSources } from '../hooks/queries'
import { CERTAINTY, PRECISION_LABELS, SPATIAL_ROLES } from '../lib/labels'

const PHASES: { n: number; title: string; status: 'pronto' | 'parcial' | 'planejado'; items: string[] }[] = [
  { n: 1, title: 'Plataforma funcional', status: 'pronto', items: [
    'Mapa MapLibre com basemap físico sem fronteiras modernas e snapshots de fronteiras históricas',
    'Seleção de conflito, linha do tempo (dia/mês/ano), reprodução com velocidade ajustável',
    'Modos político, geográfico, militar e de operações + camadas individuais com legenda e contagem',
    'Pesquisa global com filtros (conflito, tipo, país, teatro, período, categoria, ramo)',
    'Fichas de conflito, teatro, campanha, batalha, evento, localidade, país, força, unidade, pessoa, equipamento e fonte',
    'Dados iniciais verificáveis: Batalha do Somme (1916) e Campanha da Normandia (1944)',
    'Painel administrativo com autenticação, revisão/publicação, detecção de duplicados e histórico',
  ] },
  { n: 2, title: 'Organização militar e enciclopédias', status: 'parcial', items: [
    'Hierarquia temporal de unidades (pronto, com restrições de integridade no banco)',
    'Fichas de equipamentos com especificações e vínculos explícitos a unidades (pronto)',
    'Galerias de uniformes, insígnias e camuflagens com imagens licenciadas (estrutura pronta; galerias pendentes)',
    'Existência descontínua de unidades e relações temporais mais complexas (planejado)',
  ] },
  { n: 3, title: 'Reprodução de campanhas', status: 'parcial', items: [
    'Primeira versão: reprodução por eventos documentados, sem interpolação (pronto)',
    'Linhas de frente digitalizadas de mapas históricos e controle territorial por data (planejado)',
  ] },
  { n: 4, title: 'Catalogação e expansão', status: 'parcial', items: [
    'Área de preparação para importações (Wikidata e lotes JSON) com revisão humana (pronto)',
    'Importadores adicionais, deduplicação assistida e novos conflitos (planejado)',
  ] },
  { n: 5, title: 'Assistente de pesquisa (IA)', status: 'planejado', items: [
    'Endpoint de recuperação de evidências com fontes (fundação pronta, sem IA)',
    'Assistente com respostas fundamentadas em registros e citações (não implementado)',
  ] },
]

export function AboutPage() {
  const sources = useSources()
  return (
    <div className="h-full overflow-y-auto">
      <header className="wa-panel sticky top-0 z-10 flex items-center gap-4 border-x-0 border-t-0 px-4 py-2">
        <Link to="/" className="wa-icon-btn" aria-label="Voltar ao mapa">
          <ArrowLeft size={18} />
        </Link>
        <Logo />
      </header>
      <div className="mx-auto max-w-3xl space-y-10 px-5 py-8 text-[14px] leading-relaxed text-steel-200">
        <section>
          <h1 className="wa-heading text-3xl">Metodologia e integridade histórica</h1>
          <p className="mt-3">
            O War Atlas é uma plataforma de exploração, não um jogo nem uma simulação. Todo conteúdo exibido vem do banco de dados e pode ser rastreado até uma fonte identificável. Quando
            um dado não está cadastrado, a interface diz isso — ausência de registro não significa ausência histórica.
          </p>
        </section>
        <section>
          <h2 className="wa-heading text-xl">Dimensão temporal</h2>
          <p className="mt-2">
            Relações (subordinação, comando, nomes, equipamentos, alianças, participação) têm intervalos de validade. A situação “em uma data” mostra somente o que é documentado como válido nessa
            data. Cada limite tem uma precisão:
          </p>
          <ul className="mt-2 list-disc pl-5">
            {Object.entries(PRECISION_LABELS).map(([k, v]) => (
              <li key={k}>
                <b className="font-mono text-[12px]">{k}</b> — {v}
              </li>
            ))}
          </ul>
          <p className="mt-2 text-steel-400">Um limite “atestado” nunca é estendido: se uma subordinação só é documentada em 1º de julho de 1916, ela não aparece em 2 de julho.</p>
        </section>
        <section>
          <h2 className="wa-heading text-xl">Graus de certeza</h2>
          <ul className="mt-2 space-y-1.5">
            {Object.entries(CERTAINTY).map(([k, v]) => (
              <li key={k} className="flex items-start gap-2">
                <CertaintyBadge value={k} /> <span>{v.description}</span>
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h2 className="wa-heading text-xl">Geometrias</h2>
          <p className="mt-2">Cada geometria declara o que significa:</p>
          <ul className="mt-2 list-disc pl-5">
            {Object.entries(SPATIAL_ROLES).map(([k, v]) => (
              <li key={k}>{v}</li>
            ))}
          </ul>
          <p className="mt-2">
            Linhas tracejadas indicam geometria aproximada ou esquemática; halos indicam a precisão declarada. A reprodução de campanhas avança apenas por eventos e feições datados — nenhum
            movimento é interpolado entre dois pontos. As fronteiras vêm de snapshots com precisão limitada, sempre identificados no mapa; quando um snapshot está fora do período aplicável, o mapa
            o marca como desatualizado.
          </p>
        </section>
        <section>
          <h2 className="wa-heading text-xl">Estado do projeto por fase</h2>
          <div className="mt-3 space-y-4">
            {PHASES.map((p) => (
              <div key={p.n} className="wa-panel rounded-md p-4">
                <p className="flex items-center gap-2">
                  <span className="wa-heading text-lg">
                    Fase {p.n} · {p.title}
                  </span>
                  <span className={`wa-chip ${p.status === 'pronto' ? 'border-ok/60 text-ok' : p.status === 'parcial' ? 'border-warn/60 text-warn' : ''}`}>{p.status}</span>
                </p>
                <ul className="mt-2 list-disc pl-5 text-[13px] text-steel-300">
                  {p.items.map((i) => (
                    <li key={i}>{i}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
        <section>
          <h2 className="wa-heading text-xl">Fontes cadastradas ({sources.data?.length ?? '…'})</h2>
          {sources.isLoading && <Loading />}
          <ul className="mt-3 space-y-2 text-[13px]">
            {sources.data?.map((s) => (
              <li key={s.slug}>
                <SourceLine s={s} /> <span className="font-mono text-[11px] text-steel-400">· {s.citation_count} citações</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="text-[12.5px] text-steel-400">
          <h2 className="wa-heading text-xl text-parchment">Dados geográficos e licenças</h2>
          <p className="mt-2">
            Basemap físico: Natural Earth (domínio público). Fronteiras históricas: historical-basemaps, de André Ourednik (GPL-3.0). Relevo: Terrain Tiles (AWS Open Data). Referência moderna
            opcional: OpenFreeMap / © colaboradores do OpenStreetMap (ODbL). Identificadores: Wikidata (CC0). Textos da Wikipedia usados como fonte terciária (CC BY-SA 4.0).
          </p>
        </section>
      </div>
    </div>
  )
}
