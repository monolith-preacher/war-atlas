# API REST (`/api/v1`)

Documentação interativa (OpenAPI): `/api/v1/docs`. Endpoints públicos retornam apenas registros publicados. Datas no formato `AAAA-MM-DD`. Erros: `{"error": {"code", "message", "details"}}`.

## Sistema
| Método | Caminho | Descrição |
|---|---|---|
| GET | `/health` | estado da API, do banco e se há conteúdo |
| POST | `/auth/login` | formulário OAuth2 (`username`, `password`) → `access_token` |
| GET | `/auth/me` | usuário autenticado |

## História
| GET | Caminho | Descrição |
|---|---|---|
| | `/conflicts` | conflitos com contagens |
| | `/conflicts/{slug}` | teatros (com campanhas e batalhas), alianças, participantes, snapshots de fronteiras, fontes |
| | `/conflicts/{slug}/timeline` | eventos, batalhas e campanhas para a linha do tempo; dias com eventos de precisão diária |
| | `/conflicts/{slug}/participants?date=` | participantes e alianças válidos na data |
| | `/theaters/{slug}` · `/campaigns/{slug}` · `/battles/{slug}` · `/events/{slug}` · `/places/{slug}` | fichas |

## Organização militar (sensível à data)
| GET | Caminho | Descrição |
|---|---|---|
| | `/polities?conflict=` | entidades políticas |
| | `/polities/{slug}?date=&conflict=` | governo, participação, alianças, forças com **árvore na data**, comandantes, batalhas, equipamentos |
| | `/forces/{slug}?date=` | força armada e hierarquia documentada na data + unidades sem subordinação documentada |
| | `/units/{slug}?date=` | `at_date` (nomes, superiores, subordinadas, comandantes, equipamentos na data) + histórico completo |
| | `/units/{slug}/tree?date=&depth=` | subárvore (data obrigatória) |
| | `/persons/{slug}?date=` | funções na data, trajetória, batalhas, eventos |

## Equipamentos, uniformes e fontes
| GET | Caminho | Descrição |
|---|---|---|
| | `/equipment?category=&polity=&conflict=&q=` | enciclopédia filtrável |
| | `/equipment/{slug}?date=` | especificações, variantes, usuários nacionais, unidades com uso documentado |
| | `/uniforms?polity=&conflict=` · `/camouflages` | uniformes e camuflagens |
| | `/sources` · `/sources/{slug}` | fontes e registros que as citam |

## Mapa, reprodução e pesquisa
| GET | Caminho | Descrição |
|---|---|---|
| | `/map/boundary-datasets/{slug}/geojson` | geometrias do snapshot + pontos de rótulo (cacheável) |
| | `/map/state?conflict=&date=` | snapshot aplicável (com `stale`) e participantes/alianças na data |
| | `/map/features?conflict=&date=&window=` | batalhas iniciadas, eventos recentes, feições cartográficas válidas na data e localidades |
| | `/map/features/{slug}` | ficha de feição (método e incerteza) |
| | `/replay/{campaign\|battle}/{slug}` | passos documentados (datas de eventos e feições) — sem interpolação |
| | `/search?q=&types=&conflict=&polity=&theater=&date_from=&date_to=&category=&branch=&limit=` | pesquisa agrupada por tipo |
| | `/research/evidence?q=&conflict=` | recuperação de evidências com citações (fundação para RAG, sem IA) |

## Administração (Bearer token)
Papéis: `editor` < `reviewer` < `admin`.

| Método | Caminho | Descrição |
|---|---|---|
| GET | `/admin/meta` | metadados dos formulários (campos, tipos, enums, referências) |
| GET | `/admin/stats` · `/admin/review-queue` · `/admin/revisions` · `/admin/integrity/report` | painel |
| GET | `/admin/lookup/{entity}?q=` | busca para campos de referência |
| GET/POST | `/admin/{entity}` | listar / criar (sempre rascunho; 409 `possible_duplicate` se houver nomes semelhantes ou mesmo QID) |
| GET/PATCH/DELETE | `/admin/{entity}/{id}` | ler (com relações, citações, números) / atualizar / remover |
| POST | `/admin/{entity}/{id}/status` | `draft`/`in_review`/`published`/`archived` (publicar exige revisor e citação) |
| POST | `/admin/imports/wikidata` | `{qid, entity_type}` → área de preparação |
| POST | `/admin/imports/batch` | `{entity_type, source_name, records[]}` → área de preparação |
| GET | `/admin/imports/records?status=` | registros em preparação |
| POST | `/admin/imports/records/{id}/approve` · `/reject` | revisor decide; aprovação cria rascunho (`overrides` completa campos obrigatórios) |

`entity` é qualquer chave de `app/models/registry.py` (ex.: `battle`, `unit`, `unit_subordination`, `citation`, `figure`).
