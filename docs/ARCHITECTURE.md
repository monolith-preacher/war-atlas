# Arquitetura

## Visão geral

```
Navegador ──► nginx (frontend estático + proxy /api) ──► FastAPI ──► PostgreSQL + PostGIS
   │                                                       │
   ├─ MapLibre: basemap físico (/basemap/*.geojson)        ├─ consultas temporais (valid_at)
   ├─ relevo e água detalhada (tiles externos, opcionais)  ├─ GeoJSON via ST_AsGeoJSON
   └─ estado: Zustand (UI) + TanStack Query (servidor)     └─ admin com metadados derivados do ORM
```

Uma única origem (nginx) serve o SPA e encaminha `/api/` ao backend: sem CORS em produção, cookies/tokens não atravessam domínios. Em desenvolvimento, o Vite faz o mesmo proxy.

## Backend

| Escolha | Justificativa |
|---|---|
| **FastAPI** | validação de entrada com Pydantic, OpenAPI automática (`/api/v1/docs`), desempenho adequado. |
| **SQLAlchemy 2 (síncrono) + psycopg 3** | consultas relacionais complexas e legíveis; a carga é dominada por leitura; o modo síncrono simplifica transações e testes. |
| **GeoAlchemy2 + PostGIS** | geometrias tipadas (ponto, multipolígono, genérica), índices GiST, `ST_PointOnSurface`, `ST_AsGeoJSON`. |
| **Alembic** | migrações versionadas; a 0001 foi gerada do modelo e revisada; a 0002 cria a view de pesquisa e índices trigram. |
| **Enums como VARCHAR + CHECK** | vocabulários controlados extensíveis com uma migração simples (sem `ALTER TYPE`). |
| **btree_gist** | restrições de exclusão temporais no próprio banco (sem sobreposição de subordinação orgânica nem de comandante titular). |
| **pg_trgm + unaccent** | pesquisa tolerante a acentos e erros de digitação, sem dependência externa. |
| **JWT (HS256) + bcrypt** | autenticação administrativa sem estado; papéis editor < revisor < admin. |

Organização:

- `app/models` — ORM. `base.py` define mixins (`TemporalMixin`, `PublicationMixin`, `ProvenanceMixin`) e convenções de nomes.
- `app/services/temporal.py` — o único lugar onde "válido na data D" é definido.
- `app/services/serialize.py` — formatos padronizados de intervalo, proveniência, citações, números e mídia.
- `app/api/routes` — endpoints públicos (somente registros `published`) e administrativos.
- `app/services/admin_registry.py` — formulários do admin derivados das colunas: uma nova coluna aparece automaticamente no painel.
- `app/services/seed.py` — carga estrita dos JSON curados (referências por slug, uma transação).
- `app/importers` — importadores que só escrevem na área de preparação.
- `app/ai` — contratos e recuperação lexical de evidências (sem IA).

Erros seguem um formato único: `{"error": {"code", "message", "details"}}`. Violações de integridade são traduzidas em mensagens claras (ex.: sobreposição temporal → 409).

## Frontend

| Escolha | Justificativa |
|---|---|
| **React 19 + TypeScript + Vite** | ecossistema maduro, tipagem forte, build rápido. |
| **MapLibre GL JS 6** | renderização vetorial WebGL open source, sem chave; suporta camadas GeoJSON, clusters, símbolos, hillshade. |
| **TanStack Query** | cache de dados do servidor por data/conflito, `keepPreviousData` evita "piscar" ao mover a linha do tempo. |
| **Zustand** | estado da exploração (conflito, data, modo, camadas, pilha de seleção) com persistência das preferências. |
| **Tailwind CSS 4** | tema próprio por tokens (`@theme`); componentes leves sem biblioteca de UI pesada. |
| **React Router** | rotas `/`, `/sobre`, `/admin/*` (admin carregado sob demanda). |

O estado da exploração é sincronizado com a URL (`?c=&d=&m=&sel=`), permitindo compartilhar uma visão exata.

Nenhuma lógica histórica fica nos componentes: tudo vem da API. O frontend só decide **como** exibir (estilo, agrupamento, nível de detalhe por zoom).

### Mapa

- `mapStyle.ts` — estilo base construído em código: fontes GeoJSON locais, camadas militares, rótulos.
- `icons.ts` — símbolos desenhados em canvas (sem sprite externo); setas de eixo calculadas no cliente a partir do último segmento.
- `MapView.tsx` — sincroniza dados → fontes, camadas ligadas → visibilidade, estado político da data → cores, seleção → destaque.
- O basemap físico não contém fronteiras modernas. A "referência moderna" (estradas/localidades OSM) é uma camada separada e rotulada como atual.

## Escalabilidade e próximos passos técnicos

- A view `search_documents` é uma view comum (sempre consistente). Com volume maior, pode virar `MATERIALIZED VIEW` atualizada pelo fluxo de publicação, sem mudar a API.
- `/map/features` devolve tudo o que vale na data para o conflito; com milhares de feições, acrescentar filtro por `bbox` e simplificação por zoom (`ST_SimplifyPreserveTopology`), ou servir vector tiles (`ST_AsMVT`).
- O snapshot de fronteiras é servido uma vez e cacheado (`Cache-Control`); a coloração por data vem de um endpoint pequeno (`/map/state`).
- Para publicação: `ENVIRONMENT=production`, segredo forte, HTTPS no proxy, backups do volume PostGIS, limitação de taxa no login (recomendado no proxy).
