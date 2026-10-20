from dash import Dash, Input, Output, State, callback, dcc, html
import dash_leaflet as dl

import simulador


GRAFO = simulador.carregar_grafo()
CENTROS = simulador.sortear_centros(simulador.carregar_bares())

estado = {"trie": None, "entregadores": []}

# Cores usadas nos marcadores e na legenda
COR_BAR = "#1d4ed8"
COR_BAR_PREENCHIMENTO = "#3b82f6"
COR_ENTREGADOR = "#6b7280"


def marcadores_centros():
    """Bares sorteados como centros da distribuicao dos entregadores."""
    marcadores = []
    for _, bar in CENTROS.iterrows():
        nome = bar["NOME_FANTASIA"] if isinstance(bar["NOME_FANTASIA"], str) else bar["NOME"]
        bairro = bar["NOME_BAIRRO"]
        marcadores.append(
            dl.CircleMarker(
                center=[bar["LATITUDE"], bar["LONGITUDE"]],
                radius=6,
                color=COR_BAR,
                fillColor=COR_BAR_PREENCHIMENTO,
                fillOpacity=0.9,
                weight=2,
                children=dl.Tooltip(f"{nome} — {bairro}"),
            )
        )
    return marcadores


def item_legenda(cor, preenchimento, texto):
    """Linha da legenda: um circulo colorido seguido do texto."""
    circulo = html.Span(
        style={
            "display": "inline-block",
            "width": "12px",
            "height": "12px",
            "borderRadius": "50%",
            "border": f"2px solid {cor}",
            "backgroundColor": preenchimento,
            "marginRight": "8px",
            "verticalAlign": "middle",
        }
    )
    return html.Div([circulo, html.Span(texto)], style={"marginBottom": "4px"})


legenda = html.Div(
    [
        html.Strong("Legenda", style={"display": "block", "marginBottom": "6px"}),
        item_legenda(COR_BAR, COR_BAR_PREENCHIMENTO, "Bar de origem da frota"),
        item_legenda(COR_ENTREGADOR, COR_ENTREGADOR, "Entregador"),
    ],
    # Posicionada sobre o canto inferior esquerdo do mapa
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
                dcc.Dropdown(id="dropdown-restaurante",placeholder="Selecione um restaurante",),
                html.Label("Raio de Atendimento:"),
                dcc.Slider(id="slider-raio",min=0.5, max=5.0, step=0.5,value=2.0, marks={i: f"{i}km" for i in range(1, 10)},
                ),
                html.Button("Gerar Entregadores", id="btn-gerar", n_clicks=0),
            ],
            style={"padding": "20px", "backgroundColor":"#f9f9f9"},
        ),
        
        # Area de vizualização
        dcc.Loading(
            type="circle",
            overlay_style={"visibility": "visible", "opacity": 0.6},
            children=html.Div(
                [
                    # Mapa Leaflet
                    dl.Map(
                        id="mapa-principal",
                        children=[
                            dl.TileLayer(),
                            # Controle no canto superior direito para ligar/desligar camadas
                            dl.LayersControl(
                                [
                                    # Camada onde os marcadores serão injetados
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
                        ],
                        style={"width": "100%", "height": "100%"},
                        center=[-19.9167, -43.9345],
                        zoom=13,
                    ),
                    legenda,
                ],
                # position relative para a legenda ficar presa ao mapa
                style={"position": "relative", "width": "65%", "height": "70vh", "display": "inline-block"},
            ),
        ),
    ]
)

@callback(
    Output("marcadores-layer", "children"),
    Input("btn-gerar","n_clicks"),
    State("input-n-entregadores","value")
)
def atualizar_mapa(n_clicks,n_entregadores):
    # Condicao de nao agir sem nenhum click
    if n_clicks is None or n_clicks == 0:
        return []
    
    if not n_entregadores or n_entregadores < 1:
        estado["entregadores"] = []
        estado["trie"] = None
        return []

    entregadores = simulador.gerar_entregadores(int(n_entregadores), GRAFO, CENTROS)
    estado["entregadores"] = entregadores
    estado["trie"] = simulador.construir_trie(entregadores)

    return [
        dl.CircleMarker(
            center=[e["lat"], e["lon"]],
            radius=4,
            color=COR_ENTREGADOR,
            fillOpacity=0.7,
            weight=1,
            children=dl.Tooltip(e["id"]),
        )
        for e in entregadores
    ]

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)