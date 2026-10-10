# WAR ATLAS

Plataforma web de exploração histórica e militar: um mapa-múndi interativo com linha do tempo, onde conflitos, teatros, campanhas, batalhas, unidades, comandantes e equipamentos estão ligados no espaço e no tempo — sempre com fontes identificáveis e com as incertezas sinalizadas.

> **Fase 1 implementada** (plataforma funcional de ponta a ponta), com partes das fases 2, 3 e 4 já operacionais. Veja o estado detalhado em [docs/ROADMAP.md](docs/ROADMAP.md) e na página **/sobre** da aplicação.

## O que já funciona

- **Mapa MapLibre** com basemap físico sem fronteiras modernas (Natural Earth), relevo, costa detalhada com zoom e **fronteiras históricas** por snapshot (1914 e 1938). O mapa sempre informa qual snapshot está na tela e o marca como **desatualizado** fora do período aplicável.
- **Seleção de conflito** (Primeira e Segunda Guerra Mundial) que ajusta período, teatros, participantes e camadas.
- **Linha do tempo** com passos de dia/mês/ano, eventos e batalhas no trilho, seletor de data, reprodução cronológica com velocidade ajustável e modo "evento a evento".
- **Modos de visualização** político, geográfico, militar e de operações, combináveis com **23 camadas** individuais (fronteiras, alianças, batalhas, eventos, linhas de frente, eixos de avanço com setas, desembarques, fortificações, bases navais, forças terrestres/aéreas/navais, halos de incerteza...). Legenda com contagem de registros por data. Agrupamento (cluster) de batalhas.
- **Pesquisa global** (Ctrl+K) agrupada por categoria, sem acentuação obrigatória, com filtros por conflito, tipo, país, teatro, período, categoria de equipamento/escalão e ramo; botão para centralizar no mapa.
- **Fichas** de conflito, teatro, campanha/operação, batalha (participantes, unidades, comandantes, fases, cronologia, números divergentes com fonte), evento, localidade, país (situação na data: governo, alianças, forças e **hierarquia militar na data**), força armada, **unidade** (situação na data + linha do tempo documentada de nomes, subordinação, comandantes e equipamentos), pessoa, equipamento e fonte. Navegação bidirecional entre todos.
- **Reprodução histórica** de campanhas e batalhas baseada exclusivamente em eventos e feições datados — sem interpolação de movimentos.
- **Enciclopédia de equipamentos** com especificações transcritas de fontes e vínculo explícito a unidades (serviço nacional nunca implica uso por todas as unidades).
- **Painel administrativo** protegido (JWT): CRUD gerado a partir do modelo, validações por campo, detecção de duplicados, fluxo rascunho → revisão → publicado (publicar exige fonte), histórico de alterações, relatório de integridade, **importação** do Wikidata e em lote para uma área de preparação com revisão humana.
- **Fundação para IA**: endpoint de recuperação de evidências com citações (sem modelo de IA), contratos documentados.
- **Dados iniciais verificáveis**: Batalha do Somme (1916) e Campanha da Normandia (1944) — 2 conflitos, 16 teatros, 19 batalhas, 11 campanhas/operações, 48 eventos, 50 unidades com relações temporais, 39 pessoas, 21 equipamentos, 53 fontes e 485 citações. Todos os identificadores Wikidata foram conferidos por script.

## Arquitetura em uma linha

`React + TypeScript + MapLibre (Vite)` → `nginx` → `FastAPI + SQLAlchemy 2 + GeoAlchemy2` → `PostgreSQL 16 + PostGIS 3.4`

Detalhes e justificativas em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```
war-atlas/
├── backend/               API FastAPI
│   ├── app/
│   │   ├── api/routes/    endpoints REST (história, organização militar, materiel, mapa, admin, pesquisa)
│   │   ├── models/        modelo ORM (temporal, proveniência, geometrias)
│   │   ├── services/      consultas temporais, serialização, seed, metadados do admin
│   │   ├── importers/     Wikidata e contrato de importadores
│   │   ├── ai/            pontos de extensão para assistente de pesquisa
│   │   └── cli/           seed, criação de usuários, bootstrap
│   ├── alembic/           migrações
│   ├── seed/              dados iniciais curados (JSON, com fontes)
│   └── tests/             testes (pytest, contra PostGIS real)
├── frontend/              aplicação React
│   ├── src/components/    mapa, linha do tempo, painéis, barra lateral, cabeçalho
│   ├── src/pages/         explorador, sobre, painel administrativo
│   └── public/basemap/    Natural Earth simplificado (domínio público)
├── data/boundaries/       snapshots de fronteiras históricas (GPL-3.0)
├── db/init/               extensões PostGIS na criação do volume
├── scripts/               preparação de geodados e verificação de QIDs do Wikidata
└── docs/                  documentação
```

## Início rápido (Docker)

Pré-requisitos: Docker com Compose v2.

```bash
cp .env.example .env
# edite .env: defina POSTGRES_PASSWORD, JWT_SECRET (>= 32 caracteres) e, opcionalmente, ADMIN_EMAIL/ADMIN_PASSWORD
docker compose up -d --build
```

- Aplicação: <http://localhost:8080>
- Documentação interativa da API: <http://localhost:8000/api/v1/docs>
- Painel administrativo: <http://localhost:8080/admin> (usuário criado a partir de `ADMIN_EMAIL`/`ADMIN_PASSWORD`)

Na primeira subida o backend aguarda o banco, aplica as migrações, carrega os dados iniciais (`SEED_ON_START=true`, idempotente) e cria o administrador se as variáveis estiverem definidas.

Para gerar um segredo: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## Desenvolvimento local (sem Docker para a aplicação)

Use o Compose só para o banco:

```bash
cp .env.example .env            # ajuste POSTGRES_PASSWORD e DATABASE_URL com a mesma senha
docker compose up -d db
```

Backend (Python 3.12):

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
set -a && . ../.env && set +a   # exporta as variáveis
alembic upgrade head
python -m app.cli seed           # dados iniciais (use --reset para recarregar)
python -m app.cli create-user voce@exemplo.org --role admin
uvicorn app.main:app --reload --port 8000
```

Frontend (Node 20+):

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173 (proxy de /api para localhost:8000)
```

Para apontar o proxy para outra porta: `VITE_DEV_API_TARGET=http://localhost:8011 npm run dev`.

## Dados iniciais

`python -m app.cli seed` carrega `backend/seed/*.json` numa única transação: qualquer referência quebrada ou campo desconhecido aborta tudo. Se o banco já tiver conteúdo, o comando não faz nada; `--reset` apaga o conteúdo (mantém usuários e histórico) e recarrega.

Os snapshots de fronteiras e o basemap já estão no repositório. Para regenerá-los a partir das fontes originais: `python scripts/prepare_geodata.py`. Para conferir os QIDs do Wikidata usados no seed: `python scripts/verify_wikidata_ids.py`.

## Testes e qualidade

```bash
# backend: cria/usa o banco <DATABASE_URL>_test, aplica as migrações reais e o seed real
cd backend && set -a && . ../.env && set +a && pytest
ruff check app tests

# frontend
cd frontend && npm test && npm run typecheck && npm run lint && npm run build
```

Os testes cobrem endpoints principais, filtros cronológicos (hierarquia, comandantes, nomes e equipamentos por data, limites "atestados" que não se estendem), restrições do banco (sobreposição de subordinação orgânica e de comandante titular, intervalos invertidos, mídia sem licença), fluxo administrativo (autenticação, validação, duplicados, revisão/publicação, importação) e o mapeamento do importador Wikidata.

## Variáveis de ambiente

| Variável | Uso |
|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` | banco PostGIS |
| `DATABASE_URL` | URL SQLAlchemy usada fora do Docker |
| `JWT_SECRET`, `JWT_EXPIRE_MINUTES` | autenticação administrativa (o backend recusa iniciar em produção com segredo fraco) |
| `ENVIRONMENT` | `development` / `production` |
| `CORS_ORIGINS` | origens permitidas (lista separada por vírgulas) |
| `SEED_ON_START` | carrega o seed na inicialização do container (idempotente) |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | cria o administrador inicial se não existir |
| `IMPORTERS_ENABLED` | permite que importadores (Wikidata) façam requisições externas |
| `VITE_API_URL` | URL da API para o frontend (padrão `/api/v1`) |
| `VITE_GLYPHS_URL`, `VITE_MODERN_TILES_URL`, `VITE_TERRAIN_TILES_URL` | fontes de glifos, vetores OSM e relevo; `off` desativa. Ver [docs/MAPS.md](docs/MAPS.md) |

Nenhuma senha, token ou chave está no código; `.env` está no `.gitignore`.

## Integridade histórica

Nada é inventado para preencher páginas. Campos sem documentação aparecem como "não documentado"; números divergentes são mantidos lado a lado com suas fontes; relações temporais só valem dentro de seus intervalos; geometrias declaram o que representam (localização exata, posição aproximada, área de atuação, rota, extensão territorial, esquema) e seu grau de certeza. Regras completas em [docs/DATA_POLICY.md](docs/DATA_POLICY.md).

## Documentação

- [Arquitetura e decisões técnicas](docs/ARCHITECTURE.md)
- [Modelo de dados](docs/DATA_MODEL.md)
- [Política de dados e fontes](docs/DATA_POLICY.md)
- [API REST](docs/API.md)
- [Painel administrativo e importações](docs/ADMIN.md)
- [Mapas, camadas e simbologia](docs/MAPS.md)
- [Integração futura de IA](docs/AI_INTEGRATION.md)
- [Roteiro e estado por fase](docs/ROADMAP.md)

## Licenças de dados de terceiros

Natural Earth (domínio público) · historical-basemaps, André Ourednik (GPL-3.0) · Terrain Tiles, AWS Open Data/Mapzen · OpenFreeMap / © colaboradores do OpenStreetMap (ODbL) · Wikidata (CC0) · textos da Wikipedia citados como fonte terciária (CC BY-SA 4.0).
