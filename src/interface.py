import time
import unicodedata

from dash import Dash, Input, Output, State, callback, ctx, dcc, html, no_update

import busca
import mapa
import simulador
from painel_resultados import formatar_km, linhas_tabela, metricas_resumo, painel

GRAFO = simulador.carregar_grafo()
BARES = simulador.carregar_bares()
CENTROS = simulador.sortear_centros(BARES)

estado = {"trie": None, "entregadores": [], "consulta": None}

MAX_OPCOES_BUSCA = 50

def nome_exibicao(bar):
    """Nome fantasia quando existe; senao, a razao social."""
    return bar["NOME_FANTASIA"] if isinstance(bar["NOME_FANTASIA"], str) else bar["NOME"]


def sem_acentos(texto):
    """Maiusculas e sem acentos, para a busca ignorar essas diferencas."""
    normalizado = unicodedata.normalize("NFKD", texto.upper())
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def rotulo_bar(bar):
    """Texto do restaurante na lista de busca: nome, endereco e bairro."""
    endereco = f"{bar['DESC_LOGRADOURO']} {bar['NOME_LOGRADOURO']}, {bar['NUMERO_IMOVEL']}"
    return f"{nome_exibicao(bar)} — {endereco} — {bar['NOME_BAIRRO']}"


# Rotulos e texto de busca (nome fantasia, razao social e endereco) de cada bar
ROTULOS = BARES.apply(rotulo_bar, axis=1)
TEXTO_BUSCA = (
    BARES["NOME_FANTASIA"].fillna("") + " " + BARES["NOME"].fillna("") + " " + ROTULOS
).map(sem_acentos)

# Bares de origem da frota no mapa: (lat, lon, "nome — bairro")
PONTOS_CENTROS = [
    (bar["LATITUDE"], bar["LONGITUDE"], f"{nome_exibicao(bar)} — {bar['NOME_BAIRRO']}")
    for _, bar in CENTROS.iterrows()
]


def buscar_restaurantes(texto):
    """Indices dos bares que contem todas as palavras digitadas."""
    encontrados = TEXTO_BUSCA
    for palavra in sem_acentos(texto).split():
        encontrados = encontrados[encontrados.str.contains(palavra, regex=False)]
    return list(encontrados.index[:MAX_OPCOES_BUSCA])


app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Monitoramento de Frota"),

        # Area de insercao de dados
        html.Div(
            [
                html.Label("Quantidade de Entregadores (N):"),
                dcc.Input(id="input-n-entregadores",type="number",min=1,max=50000,step=1,value=1000),
                html.Label("Selecione o Restaurante:"),
                dcc.Dropdown(
                    id="dropdown-restaurante",
                    placeholder="Digite o nome ou o endereço do restaurante",
                    options=[],
                    searchable=True,
                ),
                html.Label("Raio de Atendimento:"),
                dcc.Slider(
                    id="slider-raio",
                    min=0.5,
                    max = 20,
                    step=0.5,
                    value=2.0,
                    marks={r: formatar_km(r) for r in (0.5, 1, 2, 3, 4, 5, 10,20)},
                ),
                html.Button("Gerar Entregadores", id="btn-gerar", n_clicks=0),
                html.Div(id="status-consulta", style={"marginTop": "12px"}),
            ],
            style={"padding": "20px", "backgroundColor":"#f9f9f9"},
        ),

        # Area de vizualização: mapa a esquerda e resultados a direita
        html.Div(
            [
                mapa.componente_mapa(PONTOS_CENTROS),
                painel,
            ],
            style={"display": "flex", "gap": "16px", "alignItems": "flex-start"},
        ),
    ]
)


@callback(
    Output("dropdown-restaurante", "options"),
    Input("dropdown-restaurante", "search_value"),
    State("dropdown-restaurante", "value"),
)
def atualizar_opcoes(texto, selecionado):
    """Filtra os restaurantes no servidor conforme o usuario digita."""
    indices = buscar_restaurantes(texto) if texto and len(texto.strip()) >= 2 else []

    if selecionado is not None and selecionado not in indices:
        indices.insert(0, selecionado)
    return [{"label": ROTULOS[i], "value": int(i)} for i in indices]


@callback(
    Output("mapa-principal", "figure"),
    Output("status-consulta", "children"),
    Output("tabela-entregadores", "data"),
    Output("metricas", "children"),
    Input("btn-gerar", "n_clicks"),
    Input("dropdown-restaurante", "value"),
    Input("slider-raio", "value"),
    State("input-n-entregadores", "value"),
)
def atualizar_mapa(n_clicks, indice_bar, raio_km, n_entregadores):

    if ctx.triggered_id == "btn-gerar" and n_clicks:
        if not n_entregadores or n_entregadores < 1:
            estado["entregadores"] = []
            estado["trie"] = None
        else:
            entregadores = simulador.gerar_entregadores(int(n_entregadores), GRAFO, CENTROS)
            estado["entregadores"] = entregadores
            estado["trie"] = simulador.construir_trie(entregadores)

    entregadores = estado["entregadores"]

    if indice_bar is None:
        estado["consulta"] = None
        mensagem = "Selecione um restaurante para buscar entregadores."
        fig = mapa.montar_figura(PONTOS_CENTROS, mapa.marcadores_entregadores(entregadores, {}), [])
        return fig, mensagem, [], []

    bar = BARES.loc[indice_bar]
    raio_m = raio_km * 1000
    restaurante = mapa.marcadores_restaurante(
        bar["LATITUDE"], bar["LONGITUDE"], raio_m, rotulo_bar(bar)
    )

    visualizacao = None
    if ctx.triggered_id == "dropdown-restaurante":
        visualizacao = mapa.visualizacao_restaurante(bar["LATITUDE"], bar["LONGITUDE"])

    if estado["trie"] is None:
        estado["consulta"] = None
        mensagem = "Gere os entregadores para fazer a consulta."
        fig = mapa.montar_figura(PONTOS_CENTROS, [], restaurante, visualizacao)
        return fig, mensagem, [], []

    # Runtime a ser incluído na tabela
    inicio = time.perf_counter()
    resultado = busca.filtragem_entregadores(
        estado["trie"], (bar["LATITUDE"], bar["LONGITUDE"]), raio_km
    )
    runtime_ms = (time.perf_counter() - inicio) * 1000
    estado["consulta"] = {
        "restaurante": indice_bar,
        "raio_km": raio_km,
        "resultado": resultado,
        "runtime_ms": runtime_ms,
    }

    distancias = {e["id"]: d for d, e in resultado}
    mensagem = (
        f"{len(resultado)} de {len(entregadores)} entregadores "
        f"no raio de {formatar_km(raio_km)} de {nome_exibicao(bar)}."
    )
    fig = mapa.montar_figura(
        PONTOS_CENTROS,
        mapa.marcadores_entregadores(entregadores, distancias),
        restaurante,
        visualizacao,
    )
    return (
        fig,
        mensagem,
        linhas_tabela(resultado),
        metricas_resumo(resultado, len(entregadores), runtime_ms),
    )
    
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
