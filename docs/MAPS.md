# Mapas, camadas e simbologia

## Fontes cartográficas

| Camada | Origem | Licença | Configuração |
|---|---|---|---|
| Terra, lagos, rios | Natural Earth 1:50m, simplificado (`frontend/public/basemap`) | domínio público | local, sem rede |
| Fronteiras históricas | historical-basemaps (`data/boundaries`, carregado no PostGIS) | GPL-3.0 | local |
| Relevo (hillshade) | Terrain Tiles (Terrarium), AWS Open Data | atribuição Mapzen/fontes | `VITE_TERRAIN_TILES_URL` (`off` desativa) |
| Costa/água detalhada e referência moderna | OpenFreeMap (OpenMapTiles schema) | ODbL © OpenStreetMap | `VITE_MODERN_TILES_URL` (`off` desativa) |
| Glifos dos rótulos | OpenFreeMap fonts (Noto Sans) | OFL | `VITE_GLYPHS_URL` (`off` remove rótulos de texto) |

Sem rede, o mapa continua funcionando com o basemap local e as fronteiras históricas (sem relevo, costa detalhada e rótulos de texto, a menos que glifos sejam servidos localmente).

O basemap **não contém fronteiras modernas**. A camada "Referência moderna" mostra apenas estradas e localidades atuais e é rotulada como tal.

## Modos

| Modo | Preset de camadas |
|---|---|
| Político | fronteiras, participantes, alianças, rótulos, localidades, rios, batalhas |
| Geográfico | relevo, rios/costa, referência moderna, rótulos, localidades, fronteiras |
| Militar | fronteiras, participantes, todas as camadas militares, halos de incerteza |
| Operações | relevo + todas as camadas militares, halos; ideal para reprodução de campanhas |

Mudar de modo reaplica o preset; cada camada pode ser ligada/desligada individualmente na aba **Camadas**.

## Simbologia

- **Batalhas**: círculo com espadas; vermelho = em andamento na data, cinza = encerrada. Fases só aparecem com zoom ≥ 8,5. Agrupamento automático em escalas pequenas.
- **Eventos**: losango dourado; tamanho = importância; opacidade decresce com os dias desde o evento (janela configurável).
- **Linhas de frente**: vermelho; **eixos**: cor do lado (azul = lado A, vermelho = lado B) com ponta de seta; **desembarques**: ciano; **defensivas**: bronze; **rotas**: tracejado dourado.
- **Ícones**: objetivo (alvo), fortificação (ameias), aeródromo, base naval/porto, unidade (moldura OTAN tingida pelo lado).
- **Tracejado** = geometria aproximada ou esquemática. **Halo** = precisão declarada (raio em metros, convertido por zoom).
- **Fronteiras**: preenchimento pela aliança (ou cor da entidade) válida na data; territórios dependentes em tom mais claro do soberano; não participantes em grafite. Snapshot desatualizado → bordas tracejadas e esmaecidas + aviso.

## Nível de detalhe

Rótulos de eventos a partir do zoom 7, de localidades a partir do 8, de linhas a partir do 8,5; preenchimento de países se atenua com o zoom; costa detalhada substitui o basemap a partir do zoom ~7,5.

## Adicionando cartografia

Feições militares são registros `map_features` com data de validade, `spatial_role`, `certainty`, `precision_m` e `method_note` obrigatoriamente explicando a origem (ex.: "digitalizado do mapa X da história oficial Y, p. Z"). Use `certainty = verified` apenas quando a geometria vier de digitalização de fonte cartográfica identificada.
