# Integração futura de um assistente de pesquisa (IA)

Nenhuma API de IA é usada nesta fase. A plataforma já oferece a infraestrutura de consulta e os contratos para que um assistente futuro responda com base em registros e fontes verificáveis.

## O que já existe

- `GET /api/v1/research/evidence?q=&conflict=` — recuperação **lexical determinística** (trigram + correspondência de termos distintivos) sobre registros publicados, devolvendo para cada item: tipo, slug, título, texto (resumo, contexto, objetivos...), período, grau de certeza, pontuação e **citações** (fonte, páginas, nota, URL). Quando nada é encontrado, a resposta diz explicitamente que ausência de registro não é ausência histórica.
- `app/ai/contracts.py` — `EvidenceItem`, `EvidenceCitation`, protocolos `Retriever` e `ResearchAssistant`.
- `app/ai/evidence.py` — `LexicalRetriever`, implementação atual do `Retriever`.
- Todos os dados que um assistente precisaria cruzar já estão estruturados e consultáveis pela API (relações temporais, números com fontes, divergências).

## Garantias exigidas de qualquer implementação

1. **Somente leitura.** O assistente acessa registros publicados e fontes. Sugestões de correção ou novos dados vão para `import_records` (área de preparação) e passam por revisão humana — nunca alteram conteúdo publicado.
2. **Fundamentação.** Cada afirmação da resposta deve apontar para um `EvidenceItem` e suas citações; respostas sem evidência devem dizer "não encontrei evidências no acervo".
3. **Respeito ao tempo.** Perguntas sobre "a situação em uma data" devem usar os endpoints sensíveis à data (`/units/{slug}?date=`, `/polities/{slug}?date=`...).
4. **Transparência de incerteza.** Repassar `certainty` e divergências (`figures`) em vez de escolher um número silenciosamente.

## Caminho sugerido

1. Adicionar `pgvector` e uma tabela de *chunks* (texto dos registros + citações), atualizada no fluxo de publicação.
2. Implementar um `VectorRetriever` (mesmo protocolo) combinando busca vetorial e lexical.
3. Implementar `ResearchAssistant.answer()` com um modelo de linguagem, injetando apenas as evidências recuperadas e exigindo citações no formato da plataforma.
4. Expor `POST /api/v1/research/ask` com limitação de taxa e registro das perguntas/respostas para auditoria.
5. Ferramenta para o assistente propor importações (cria `import_records` com `external_source = "assistant"`).
