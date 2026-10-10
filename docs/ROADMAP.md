# Roteiro e estado por fase

Legenda: ✅ pronto · 🟡 parcial · ⏳ planejado

## Fase 1 — Plataforma funcional ✅

- ✅ Identidade visual (tema grafite/azul-acinzentado/oliva/latão), layout responsivo (desktop prioritário; barra lateral e painéis se sobrepõem em telas pequenas).
- ✅ Frontend ↔ backend ↔ PostGIS integrados; Docker Compose; migrações; seed idempotente; tratamento de falha de conexão (banner, tentativas automáticas, healthchecks).
- ✅ Mapa navegável, modos, camadas, legenda com contagens, cluster de batalhas, nível de detalhe por zoom.
- ✅ Seleção de conflito, linha do tempo dia/mês/ano, reprodução e velocidade, data direta, eventos do dia.
- ✅ Pesquisa global com filtros e centralização no mapa.
- ✅ Navegação por países com situação na data e fichas históricas de todas as entidades.
- ✅ Dados iniciais verificáveis (Somme 1916, Normandia 1944).
- ✅ Testes automatizados (backend 41 testes; frontend utilitários de datas).

## Fase 2 — Organização militar e enciclopédias 🟡

- ✅ Hierarquia temporal de unidades (árvore na data, unidades sem subordinação documentada, histórico completo), restrições de exclusão no banco.
- ✅ Fichas de equipamentos com especificações citadas e vínculos explícitos a unidades/países.
- 🟡 Uniformes e camuflagens: modelo, API e aba com registros citados; **galerias de imagens licenciadas pendentes** (nenhuma imagem verificada cadastrada).
- ⏳ Insígnias com imagens; filtros por teatro/função para uniformes.
- ⏳ Existência descontínua de unidades; redesignações com vínculo entre unidades predecessoras/sucessoras.
- ⏳ Ampliar ordens de batalha (abaixo de divisão) e comandantes de todas as unidades cadastradas.

## Fase 3 — Reprodução histórica de campanhas 🟡

- ✅ Primeira versão: passos = datas de eventos e feições documentadas; voo até o local; método explicado; sem interpolação.
- ⏳ Digitalização de linhas de frente e controle territorial a partir de mapas das histórias oficiais (com `method_note` citando mapa e página).
- ⏳ Posições de unidades por data (`unit_position`) com proveniência.
- ⏳ Snapshots de fronteiras para 1939–1945 (anexações e ocupações) e para o pós-guerra.

## Fase 4 — Catalogação, importação e expansão 🟡

- ✅ Área de preparação com revisão (Wikidata, lote JSON), relatório de integridade, histórico de alterações.
- ⏳ Importadores adicionais (CSV, SPARQL em lote, repositórios de arquivos com licença), deduplicação assistida, mesclagem de registros.
- ⏳ View de pesquisa materializada, vector tiles para grandes volumes.
- ⏳ Novos conflitos (a estrutura já é genérica: conflitos, teatros e campanhas são registros cadastráveis).

## Fase 5 — Assistente de pesquisa (IA) ⏳

- ✅ Fundação: recuperação de evidências com citações e contratos (ver [AI_INTEGRATION.md](AI_INTEGRATION.md)).
- ⏳ Busca vetorial e assistente com respostas fundamentadas.

## Débitos e cuidados conhecidos

- Rótulos de entidades não curadas nos snapshots aparecem em inglês (nome do dataset).
- O snapshot de 1938 é exibido (marcado como desatualizado) durante toda a Segunda Guerra até que existam snapshots de 1939–1945.
- O bundle JS principal tem ~1,5 MB (MapLibre); divisão de código adicional é possível.
- Limitação de taxa no login deve ser configurada no proxy em produção.
