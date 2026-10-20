import time
import unicodedata

from dash import Dash, Input, Output, State, callback, ctx, dcc, html, no_update
import dash_leaflet as dl

import busca
import simulador
from painel_resultados import formatar_km, linhas_tabela, metricas_resumo, painel

GRAFO = simulador.carregar_grafo()
BARES = simulador.carregar_bares()
CENTROS = simulador.sortear_centros(BARES)

estado = {"trie": None, "entregadores": [], "consulta": None}

COR_BAR = "#1d4ed8"
COR_BAR_PREENCHIMENTO = "#3b82f6"
COR_ENTREGADOR = "#6b7280"
COR_NO_RAIO = "#dc2626"
COR_RESTAURANTE = "#b45309"
COR_RESTAURANTE_PREENCHIMENTO = "#f59e0b"

MAX_OPCOES_BUSCA = 50
ZOOM_CONSULTA = 14

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


def buscar_restaurantes(texto):
    """Indices dos bares que contem todas as palavras digitadas."""
    encontrados = TEXTO_BUSCA
    for palavra in sem_acentos(texto).split():
        encontrados = encontrados[encontrados.str.contains(palavra, regex=False)]
    return list(encontrados.index[:MAX_OPCOES_BUSCA])


def marcadores_centros():
    """Bares sorteados como centros da distribuicao dos entregadores."""
    marcadores = []
    for _, bar in CENTROS.iterrows():
        marcadores.append(
            dl.CircleMarker(
                center=[bar["LATITUDE"], bar["LONGITUDE"]],
                radius=6,
                color=COR_BAR,
                fillColor=COR_BAR_PREENCHIMENTO,
                fillOpacity=0.9,
                weight=2,
                children=dl.Tooltip(f"{nome_exibicao(bar)} — {bar['NOME_BAIRRO']}"),
            )
        )
    return marcadores


def marcadores_entregadores(entregadores, distancias):
    """Entregadores no raio em vermelho e os demais em cinza."""
    fora = [e for e in entregadores if e["id"] not in distancias]
    dentro = [e for e in entregadores if e["id"] in distancias]

    marcadores = [
        dl.CircleMarker(
            center=[e["lat"], e["lon"]],
            radius=4,
            color=COR_ENTREGADOR,
            fillOpacity=0.7,
            weight=1,
            children=dl.Tooltip(e["id"]),
        )
        for e in fora
    ]
    marcadores += [
        dl.CircleMarker(
            center=[e["lat"], e["lon"]],
            radius=5,
            color=COR_NO_RAIO,
            fillColor=COR_NO_RAIO,
            fillOpacity=0.9,
            weight=1,
            children=dl.Tooltip(f"{e['id']} — {distancias[e['id']]:.0f} m"),
        )
        for e in dentro
    ]
    return marcadores


def marcadores_restaurante(bar, raio_m):
    """Destaque do restaurante consultado e o circulo do raio de atendimento."""
    centro = [float(bar["LATITUDE"]), float(bar["LONGITUDE"])]
    return [
        dl.Circle(
            center=centro,
            radius=raio_m,
            color=COR_NO_RAIO,
            weight=2,
            dashArray="6 6",
            fillOpacity=0.05,
        ),
        dl.CircleMarker(
            center=centro,
            radius=10,
            color=COR_RESTAURANTE,
            fillColor=COR_RESTAURANTE_PREENCHIMENTO,
            fillOpacity=1.0,
            weight=3,
            children=dl.Tooltip(rotulo_bar(bar)),
        ),
    ]


def item_legenda(cor, preenchimento, texto, tracejado=False):
    """Linha da legenda: um circulo colorido seguido do texto."""
    circulo = html.Span(
        style={
            "display": "inline-block",
            "width": "12px",
            "height": "12px",
            "borderRadius": "50%",
            "border": f"2px {'dashed' if tracejado else 'solid'} {cor}",
            "backgroundColor": preenchimento,
            "marginRight": "8px",
            "verticalAlign": "middle",
        }
    )
    return html.Div([circulo, html.Span(texto)], style={"marginBottom": "4px"})


legenda = html.Div(
    [
        html.Strong("Legenda", style={"display": "block", "marginBottom": "6px"}),
        item_legenda(COR_RESTAURANTE, COR_RESTAURANTE_PREENCHIMENTO, "Restaurante consultado"),
        item_legenda(COR_NO_RAIO, "transparent", "Raio de atendimento", tracejado=True),
        item_legenda(COR_NO_RAIO, COR_NO_RAIO, "Entregador no raio"),
        item_legenda(COR_ENTREGADOR, COR_ENTREGADOR, "Entregador fora do raio"),
        item_legenda(COR_BAR, COR_BAR_PREENCHIMENTO, "Bar de origem da frota"),
    ],
    style={
        "position": "absolute",
        "bottom": "24px",
        "left": "12px",
        "zIndex": 1000,
        "backgroundColor": "rgba(255, 255, 255, 0.92)",
        "padding": "10px 12px",
        "borderRadius": "6px",
        "boxShadow": "0 1px 4px rgba(0, 0, 0, 0.3)",
        "fontSize": "13px",
        "lineHeight": "1.4",
    },
)

app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Monitoramento de Frota"),

        # Area de insercao de dados
        html.Div(
            [
                html.Label("Quantidade de Entregadores (N):"),
                dcc.Input(id="input-n-entregadores",type="number",min=1,max=10000,step=1,value=1000),
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
                    max=5.0,
                    step=0.5,
                    value=2.0,
                    marks={r: formatar_km(r) for r in (0.5, 1, 2, 3, 4, 5)},
                ),
                html.Button("Gerar Entregadores", id="btn-gerar", n_clicks=0),
                html.Div(id="status-consulta", style={"marginTop": "12px"}),
            ],
            style={"padding": "20px", "backgroundColor":"#f9f9f9"},
        ),

        # Area de vizualização: mapa a esquerda e resultados a direita
        html.Div(
            [
                dcc.Loading(
                    type="circle",
                    overlay_style={"visibility": "visible", "opacity": 0.6},
                    parent_style={"flex": "0 0 65%"},
                    children=html.Div(
                        [
                            # Mapa Leaflet
                            dl.Map(
                                id="mapa-principal",
                                children=[
                                    dl.TileLayer(),
                                    dl.LayersControl(
                                        [
                                            dl.Overlay(
                                                dl.LayerGroup(id="marcadores-layer"),
                                                name="Entregadores",
                                                checked=True,
                                            ),
                                            # Bares usados como centros da distribuicao
                                            dl.Overlay(
                                                dl.LayerGroup(id="centros-layer", children=marcadores_centros()),
                                                name="Bares de origem da frota",
                                                checked=True,
                                            ),
                                        ],
                                        position="topright",
                                    ),
                                    dl.LayerGroup(id="restaurante-layer"),
                                ],
                                style={"width": "100%", "height": "100%"},
                                center=[-19.9167, -43.9345],
                                zoom=13,
                            ),
                            legenda,
                        ],
                        style={"position": "relative", "width": "100%", "height": "70vh"},
                    ),
                ),
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
    Output("marcadores-layer", "children"),
    Output("restaurante-layer", "children"),
    Output("mapa-principal", "viewport"),
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
        return marcadores_entregadores(entregadores, {}), [], no_update, mensagem, [], []

    bar = BARES.loc[indice_bar]
    raio_m = raio_km * 1000
    restaurante = marcadores_restaurante(bar, raio_m)

    viewport = no_update
    if ctx.triggered_id == "dropdown-restaurante":
        viewport = {
            "center": [float(bar["LATITUDE"]), float(bar["LONGITUDE"])],
            "zoom": ZOOM_CONSULTA,
            "transition": "flyTo",
        }

    if estado["trie"] is None:
        estado["consulta"] = None
        mensagem = "Gere os entregadores para fazer a consulta."
        return [], restaurante, viewport, mensagem, [], []

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
    return (
        marcadores_entregadores(entregadores, distancias),
        restaurante,
        viewport,
        mensagem,
        linhas_tabela(resultado),
        metricas_resumo(resultado, len(entregadores), runtime_ms),
    )


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
