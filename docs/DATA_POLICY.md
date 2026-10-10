# Política de dados e integridade histórica

A precisão histórica tem prioridade sobre a apresentação visual. Quando houver conflito, a interface sinaliza a limitação em vez de escondê-la.

## Regras

1. **Nada inventado.** Acontecimentos, números, comandantes, unidades, equipamentos, coordenadas e relações só entram com fonte identificável. Campos sem documentação ficam vazios e aparecem como "não documentado no acervo atual".
2. **Ausência de dados ≠ ausência histórica.** A legenda mostra "—" para camadas sem registros na data e explica isso; a pesquisa sem resultados diz "nenhum registro cadastrado".
3. **Toda afirmação importante é citável.** Registros principais só podem ser publicados com ao menos uma citação (regra aplicada pela API). O relatório de integridade lista publicados sem fonte.
4. **Divergências são preservadas.** Cada número (`figures`) pertence a uma única fonte; números diferentes para a mesma métrica ficam lado a lado, marcados como "divergente". Ex.: baixas alemãs no Somme (237.159 / 335.688 / 429.209 / 440.000–600.000).
5. **Tempo explícito.** Relações têm intervalo de validade e precisão. A situação numa data nunca mistura dados de outra (uma divisão em 1941 não exibe o comandante de 1944). Limites "atestados" não são estendidos.
6. **Geometria com significado e certeza.** Cada geometria declara se é localização exata, posição aproximada, área de atuação, rota, extensão territorial ou esquema, e traz `precision_m` e `method_note`. Esquemas e aproximações são desenhados tracejados e explicados na ficha.
7. **Sem movimentos fictícios.** A reprodução avança por eventos e feições datados. Nenhuma posição é interpolada entre dois pontos.
8. **Serviço nacional ≠ uso por unidade.** Um equipamento só aparece numa unidade se houver vínculo documentado em `unit_equipment`.
9. **Imagens só com procedência.** Mídia exige autoria, licença e atribuição; o banco impede publicar mídia sem licença verificada. A Fase 1 não inclui imagens (nenhuma foi verificada ainda).
10. **Importações passam por revisão.** Dados externos ficam em `import_records`; aprovados viram rascunhos com `provenance_note` e citação da origem, sujeitos ao fluxo normal.

## Fontes do conjunto inicial

- Histórias oficiais: Edmonds (1932) e Miles (1938) para o Somme; Harrison (1951), Blumenson (1961), Ellis (1962) e Stacey (1960) para a Normandia.
- Obras de referência: Philpott (2009).
- **Wikipedia como fonte terciária**, com data de acesso: números retirados de infoboxes são citados ao artigo e a nota registra a referência subjacente indicada pelo artigo (ex.: "Wikipedia cita Zetterling (2000), p. 408"). Para listas de comandantes alemães com datas, a Wikipedia em alemão.
- **Wikidata** (CC0): identificadores, datas de nascimento/morte e coordenadas de referência de localidades. Todos os QIDs do seed foram conferidos com `scripts/verify_wikidata_ids.py` (o script encontrou e permitiu corrigir três QIDs errados antes da publicação).

Divergências encontradas durante a curadoria e registradas no próprio dado:
- Morte de Günther von Kluge: Wikidata 17/08/1944; historiografia corrente 19/08/1944 (adotada, com nota).
- Fim da Campanha da Normandia: Wikidata 25/08; adotado 30/08/1944 (periodização usual), com nota.
- Batalha de Pozières e da Crista de Thiepval: datas do Wikidata divergem da historiografia britânica; adotadas as datas usuais, com nota.
- Transferências de comando alemãs: as páginas de OB West (16/08) e do Grupo de Exércitos B (17/08) divergem sobre a data de Model; ambas registradas.

## Limitações conhecidas dos dados geográficos

- **historical-basemaps** (GPL-3.0): fronteiras aproximadas (campo de precisão 1–3), simplificadas a ~1 km. O snapshot de 1914 contém entidades possivelmente anacrônicas (p. ex. "Manchu Empire"); o de 1938 contém rótulos anacrônicos (p. ex. "Israel"). Os snapshots não representam ocupações durante as guerras. O de 1938 é marcado como **desatualizado** após 14/03/1939.
- Rótulos de feições não ligadas a entidades curadas aparecem como no dataset (em inglês, cor atenuada).
- Linha de frente do Somme (1º jul 1916): **reconstrução esquemática** pelas localidades citadas na história oficial; erro esperado de até ~2 km. Setores e eixos de desembarque da Normandia: **esquemáticos**, centrados nas coordenadas de referência do Wikidata; indicam apenas a direção documentada do assalto.
- Basemap Natural Earth 1:50m é grosseiro em escala local; com zoom, a costa vem dos polígonos de água do OpenStreetMap (geografia atual).
- Cores de uniformes e camuflagens são aproximações visuais.

## Como contribuir com dados

1. Cadastre a **fonte** primeiro (admin → Fontes).
2. Crie o registro como rascunho, preencha datas com a precisão correta e ligue-o às fontes (citações, se possível com páginas e campo sustentado).
3. Use `attested` quando a fonte só comprova a relação numa data.
4. Envie para revisão; um revisor confere e publica.
