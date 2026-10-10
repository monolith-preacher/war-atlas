# Modelo de dados

PostgreSQL 16 + PostGIS 3.4. SRID 4326 (WGS84) em todas as geometrias. Migrações em `backend/alembic/versions`.

## Convenções transversais

| Mixin / padrão | Colunas | Significado |
|---|---|---|
| `TemporalMixin` | `valid_from`, `valid_from_precision`, `valid_to`, `valid_to_precision` | intervalo **inclusivo** de validade; `NULL` = não documentado (tratado como aberto nas consultas, mas sempre rotulado na interface). CHECK `valid_from <= valid_to`. |
| `DatePrecision` | `day`, `month`, `year`, `circa`, `attested` | `attested` = válido comprovadamente nesta data, limite real desconhecido; **nunca é estendido**. |
| `PublicationMixin` | `status` (`draft`, `in_review`, `published`, `archived`), `reviewed_at`, `review_note` | a API pública só expõe `published`. |
| `ProvenanceMixin` | `certainty`, `provenance_note`, `wikidata_id` | grau de certeza (`verified`, `estimated`, `interpreted`, `reconstructed`, `disputed`, `unverified`) e notas de procedência. |
| Polimórfico | `entity_type` + `entity_id` | usado por `citations`, `figures`, `media_links`, `revisions` (tipos válidos em `app/models/registry.py`). |

## Entidades

### Contexto político
- `conflicts` — guerras (hierarquizáveis por `parent_id`), período, visão padrão do mapa.
- `polities` — entidades políticas históricas com intervalo de existência (o Reino Unido de 1801–1927 e o de 1927– são registros distintos).
- `polity_periods` — governo, chefes de Estado/governo e capital por intervalo.
- `alliances`, `alliance_memberships` (temporal) — coalizões e adesões.
- `conflict_participations` (temporal) — entrada e saída de cada entidade em cada conflito, com notas.
- `boundary_datasets` — snapshot de fronteiras com `reference_date` e janela de aplicabilidade (`valid_from`/`valid_to`), licença, notas de precisão e limitações conhecidas.
- `historical_boundaries` — multipolígonos do snapshot; `polity_id` só quando o rótulo do dataset foi ligado a uma entidade curada.

### Estrutura militar e operacional
- `theaters` → `campaigns` (campanha/operação/ofensiva, aninháveis) → `battles` (com fases via `parent_id`).
- `battle_participants`, `battle_units` (temporal), `battle_commanders`.
- `events` — acontecimentos datados (com precisão e horário quando documentado); base das linhas do tempo e da reprodução.
- `event_units`, `event_persons`.
- `places` — localidades (ponto = **localização**), com precisão em metros.
- `map_features` — cartografia militar temporal: `feature_type` (frente, eixo de avanço/retirada, linha defensiva, objetivo, posição de unidade, fortificação, aeródromo, base naval, zona de desembarque/lançamento, área de operações, controle territorial, rota), `spatial_role`, `certainty`, `precision_m` e `method_note` (como a geometria foi produzida).

### Organização militar (temporal)
- `armed_forces` — forças por entidade política (hierarquizáveis: Wehrmacht → Heer).
- `units` — escalão genérico (`echelon`, para ordenar) + designação nacional livre (`type_label`) — não se pressupõe estrutura idêntica entre países. `polity_id` só pode ser nulo em comandos multinacionais (`is_multinational`).
- `unit_names` (temporal) — nomes oficiais, traduções, apelidos e redesignações.
- `unit_subordinations` (temporal) — unidade → unidade superior **ou** → força armada; tipo `organic`, `attached`, `operational_control`, `administrative`.
  - **EXCLUDE** (GiST): uma unidade não pode ter duas subordinações **orgânicas** sobrepostas.
- `persons`, `person_ranks` (temporal), `person_positions` (temporal; comando de unidade, força ou cargo político).
  - **EXCLUDE**: uma unidade não pode ter dois comandantes titulares (`kind = 'commander'`) sobrepostos. Interinos usam `acting_commander`.

### Materiel
- `equipment` (especificações em JSONB `[{key,label,value,unit,note}]`, período de serviço), `equipment_variants`.
- `equipment_users` (temporal) — serviço **nacional**.
- `unit_equipment` (temporal) — uso **documentado por unidade**. Nunca é derivado de `equipment_users`.
- `camouflage_patterns`, `equipment_camouflages`, `uniforms`, `insignia` (temporais).

### Proveniência e mídia
- `sources` — referência bibliográfica ou conjunto de dados, licença, data de acesso, nota de confiabilidade.
- `citations` — liga uma fonte a qualquer registro (opcionalmente a um campo específico, com páginas, citação literal e nota).
- `figures` — números atribuídos a **uma** fonte cada (efetivos, baixas...). Vários registros para a mesma métrica/lado = **divergência registrada**.
- `media`, `media_links` — imagens/documentos com autoria, licença e atribuição. CHECK: não pode ser `published` sem `license_verified` e `license`.

### Administração
- `users` (papéis), `revisions` (log append-only de criações, alterações, remoções e mudanças de status), `import_batches`, `import_records` (área de preparação com payload bruto, proposta de mapeamento, avisos e decisão).

## Pesquisa

Migração 0002:
- função `wa_unaccent()` IMMUTABLE e índices GIN trigram em `lower(wa_unaccent(name))` nas tabelas principais;
- view `search_documents` (UNION ALL de conflitos, teatros, campanhas, batalhas, eventos, localidades, entidades políticas, unidades, pessoas e equipamentos **publicados**) com `conflict_ids[]`, `polity_id`, `theater_id`, período, coordenadas, categoria e ramo — base dos filtros.

Migração 0003: unidades, pessoas e equipamentos só são associados a um conflito por **relações documentadas e datadas** (batalhas, eventos, subordinações/comandos com data, serviço nacional ou uso por unidade com data) — nunca por um período de existência ou serviço em aberto.

## Regras de consulta temporal

```python
valid_at(model, D)  ≡  (valid_from IS NULL OR valid_from <= D) AND (valid_to IS NULL OR valid_to >= D)
```

A hierarquia de uma força na data D é montada **apenas** com subordinações válidas em D. Unidades existentes em D sem subordinação documentada são listadas à parte ("sem subordinação documentada nesta data"), nunca encaixadas por suposição.

## Limitações conhecidas do modelo (planejadas)

- Existência descontínua de unidades (dissolução e reconstituição) — hoje um único intervalo; o caso do 1. Armee alemão está documentado em `provenance_note`.
- Decisões estratégicas como registros próprios.
- Fronteiras e controle territorial em séries temporais finas (hoje: snapshots).
