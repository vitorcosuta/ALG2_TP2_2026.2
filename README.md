# Indexação Geoespacial com Geohash e Trie

Trabalho Prático de DCC207 – Algoritmos 2 (UFMG, 2026/2).

Motor de busca geoespacial para encontrar os entregadores mais próximos de um restaurante em Belo Horizonte, usando codificação Geohash armazenada em uma Trie compacta, com filtragem por raio e visualização em mapa interativo.

## Requisitos

- Python 3.12
- `make` (opcional, mas recomendado)

## Instalação

```bash
make install
```

Esse comando cria o ambiente virtual em `.venv/` (se ainda não existir) e instala as dependências de desenvolvimento. Para ativar o ambiente no terminal:

```bash
source .venv/bin/activate
```

Sem `make`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

- `requirements.txt`: dependências para executar a aplicação.
- `requirements-dev.txt`: as anteriores, mais as ferramentas de teste e análise estática.

## Contribuindo

### Antes de cada commit

```bash
make check
```

Esse comando roda, em sequência, todas as verificações abaixo e para na primeira que falhar. Rode `make help` para ver todos os comandos.

| Comando | Ferramenta | O que verifica |
|---|---|---|
| `make lint` | ruff | Erros, imports não usados ou fora de ordem, bugs comuns |
| `make format-check` | ruff | Se o código segue a formatação padrão |
| `make typecheck` | mypy | Consistência de tipos (modo `strict`) |
| `make complexity` | radon | Complexidade ciclomática e índice de manutenibilidade |
| `make test` | pytest | Testes unitários em `tests/` |
| `make fix` | ruff | Aplica correções automáticas e formata o código |
| `make clean` | — | Remove os caches das ferramentas |

As regras de cada ferramenta estão em [`pyproject.toml`](pyproject.toml), e as mesmas valem para todos os contribuidores.

### Lendo e corrigindo os resultados

**Ruff** informa `arquivo:linha:coluna: CÓDIGO mensagem`:

```
src/trie.py:3:8: F401 [*] `os` imported but unused
```

- Itens marcados com `[*]` são corrigidos automaticamente com `make fix`.
- Para entender uma regra: `.venv/bin/ruff rule F401`.
- Problemas de formatação são resolvidos com `make fix`; não formate à mão.

**Mypy** informa `arquivo:linha: error: mensagem [código]`:

```
src/geohash.py:12: error: Function is missing a return type annotation  [no-untyped-def]
```

- Não há correção automática: ajuste as anotações de tipo indicadas.
- Evite silenciar com `# type: ignore`. Se o erro vier de uma biblioteca sem tipos, adicione-a à lista `module` em `[[tool.mypy.overrides]]` no `pyproject.toml`.

**Radon** atribui notas de A (simples) a F (muito complexa) a cada função:

```
src/trie.py
    M 42:4 CompactTrie.insert - C (14)
```

- Só são listadas funções com nota B ou pior (`cc_min = "B"`).
- Funções com nota C ou pior devem ser divididas em funções menores.
- No índice de manutenibilidade (`radon mi`), A é bom; B ou C indicam arquivos difíceis de manter.

**Pytest** mostra quais testes falharam e o motivo. Para rodar um único arquivo ou teste:

```bash
.venv/bin/python -m pytest tests/test_trie.py
.venv/bin/python -m pytest tests/test_trie.py -k busca_prefixo
```

### Bibliotecas

As estruturas de dados centrais (Geohash e Trie) devem ser implementadas pelo grupo, sem bibliotecas prontas. Antes de adicionar qualquer nova dependência ao `requirements.txt`, confirme com o professor ou o monitor se ela é permitida.
