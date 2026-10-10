# Painel administrativo

Endereço: `/admin`. A exploração pública não exige login; qualquer alteração exige autenticação.

## Usuários e papéis

| Papel | Pode |
|---|---|
| `editor` | criar registros (sempre como rascunho), editar rascunhos e registros em revisão, enviar para revisão, remover rascunhos, colocar dados em importação |
| `reviewer` | tudo do editor + editar publicados, publicar, arquivar, despublicar, remover, aprovar/rejeitar importações |
| `admin` | tudo do revisor (reservado para gestão) |

Criação de usuários (não há cadastro público):

```bash
python -m app.cli create-user pessoa@exemplo.org --role reviewer   # pede a senha (mín. 10 caracteres)
```

No Docker, `ADMIN_EMAIL`/`ADMIN_PASSWORD` criam o primeiro administrador na inicialização (se ainda não existir).

## Fluxo de publicação

```
rascunho ──(editor)──► em revisão ──(revisor)──► publicado ──(revisor)──► arquivado
    ▲                       │                        │
    └────── devolver ───────┘◄──── despublicar ──────┘
```

- Publicar conflitos, entidades políticas, teatros, campanhas, batalhas, eventos, feições, unidades, pessoas, equipamentos, uniformes e camuflagens exige **ao menos uma citação**.
- Mídia exige licença informada e verificada (também garantido por CHECK no banco).
- Toda criação, alteração (com diff por campo), remoção e mudança de status vai para o **histórico** com usuário, data e comentário.

## Validações

- Tipos por campo (datas, enums, números, referências existentes, GeoJSON válido e do tipo esperado, coordenadas no intervalo, QID `Q\d+`, cor `#RRGGBB`).
- Coerência de intervalos (início ≤ fim) antes de chegar ao banco.
- **Duplicados**: nomes com similaridade trigram > 0,6 ou mesmo QID retornam a lista de candidatos; o usuário confirma explicitamente se não for duplicado. Slugs são gerados e mantidos únicos.
- **Integridade temporal** garantida pelo banco: sobreposição de subordinação orgânica ou de comandante titular retorna 409 com mensagem explicativa.

## Relações

A ficha de cada registro lista todas as tabelas que o referenciam (ex.: uma unidade mostra nomes, subordinações, comandos, batalhas, equipamentos, eventos) com atalho "+ adicionar" que pré-preenche a chave. Citações e números são adicionados pelo painel lateral.

## Importações (área de preparação)

- **Wikidata** (CC0): informe o QID e o tipo. São propostos rótulo (pt → en), descrição curta, datas **somente com precisão de dia** (as demais geram aviso) e coordenadas (com aviso sobre o significado do ponto). Se já existir registro com o mesmo QID, um aviso aparece.
- **Lote JSON**: lista de objetos com os campos da entidade (e `external_id` opcional) — base para futuras importações de planilhas e outros repositórios.
- O revisor aprova (informando campos obrigatórios faltantes em `overrides`, ex.: `{"conflict_id": 2}`) ou rejeita. A aprovação cria um **rascunho** com `provenance_note` e citação da origem; nada é publicado automaticamente.

## Relatório de integridade

`/admin/integridade`: registros publicados sem citação e unidades publicadas sem nenhuma subordinação documentada.
