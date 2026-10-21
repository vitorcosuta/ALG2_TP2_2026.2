# Indexação Geoespacial com Geohash e Trie

Trabalho Prático de DCC207 – Algoritmos 2 (UFMG, 2026/2).

Motor de busca geoespacial para encontrar os entregadores mais próximos de um restaurante em Belo Horizonte, usando codificação Geohash armazenada em uma Trie compacta, com filtragem por raio e visualização em mapa interativo.

## Requisitos

- **Python 3.12** (versão usada no desenvolvimento e nos testes)
- **Git**, para clonar o repositório
- Conexão com a internet na instalação (para baixar as bibliotecas) e durante o uso (para carregar o mapa de fundo)

Os dados necessários já estão no repositório: os bares com coordenadas (`bares_cruzada.csv`) e o grafo viário de Belo Horizonte (`data/bh_drive.graphml`).

## Como rodar

Todos os comandos abaixo devem ser executados **na pasta raiz do projeto**.

### 1. Clonar o repositório

```bash
git clone https://github.com/vitorcosuta/ALG2_TP2_2026.2.git
cd ALG2_TP2_2026.2
```

### 2. Criar o ambiente virtual

O ambiente virtual isola as bibliotecas do projeto das demais instaladas no computador. Ele só precisa ser criado uma vez:

```bash
python3 -m venv .venv
```

No Windows, use `python` no lugar de `python3`.

### 3. Ativar o ambiente virtual

É preciso ativar o ambiente **sempre que abrir um novo terminal**:

| Sistema | Comando |
|---|---|
| Linux / macOS | `source .venv/bin/activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (Prompt de Comando) | `.venv\Scripts\activate.bat` |

Com o ambiente ativo, o nome `(.venv)` aparece no início da linha do terminal. Para desativar, use `deactivate`.

> No PowerShell, se aparecer um erro de permissão ao ativar, rode antes `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e tente de novo.

### 4. Instalar as bibliotecas

Com o ambiente ativo, instale as dependências (também só na primeira vez):

```bash
pip install -r requirements.txt
```

### 5. Abrir a interface

```bash
python src/interface.py
```

A aplicação leva alguns segundos para iniciar, porque carrega o grafo viário da cidade. Quando o terminal mostrar a mensagem abaixo, ela está pronta:

```
Dash is running on http://127.0.0.1:8050/
```

Acesse no navegador: **<http://127.0.0.1:8050>**

Para encerrar a aplicação, volte ao terminal e pressione `Ctrl + C`.

## Como usar a interface

1. Informe a **quantidade de entregadores (N)** e clique em **Gerar Entregadores**. A frota anterior é descartada e os novos entregadores aparecem no mapa, distribuídos ao redor dos bares de origem (em azul).
2. Em **Selecione o Restaurante**, digite parte do nome ou do endereço do restaurante e escolha uma das opções. O mapa se centraliza nele.
3. Ajuste o **raio de atendimento** (de 0,5 a 5 km). Os entregadores dentro do raio ficam em destaque (vermelho) e os demais em cinza.
4. Ao lado do mapa, a tabela mostra o ID, a distância e o tempo estimado de chegada de cada entregador no raio, junto com as métricas resumo e o tempo da consulta.

## Scripts auxiliares (opcional)

Os scripts em `scripts/` não são necessários para usar a interface. Eles regeneram os dados e produzem os gráficos do relatório. Rode-os com o ambiente virtual ativo, a partir da raiz do projeto:

| Script | O que faz |
|---|---|
| `python scripts/cruzar_bares.py` | Gera `bares_cruzada.csv` cruzando `bares.csv` com a base de Atividades Econômicas da PBH ([dados.pbh.gov.br](https://dados.pbh.gov.br/dataset/atividades-economicas)), que precisa ser baixada antes |
| `python scripts/baixar_grafo.py` | Baixa novamente o grafo viário de Belo Horizonte do OpenStreetMap (~2 min) |
| `python scripts/experimentos.py` | Executa os experimentos de desempenho e salva os resultados em CSV (~3 min) |
| `python scripts/graficos.py` | Gera os gráficos do relatório a partir desses CSVs |
| `python scripts/validar_simulador.py` | Gera o histograma que valida a distribuição dos entregadores |

Use `--help` em qualquer script para ver as opções disponíveis.
