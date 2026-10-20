"""Mapa interativo: camadas, marcadores, circulo do raio e legenda.

As funcoes recebem coordenadas e textos ja prontos, sem depender das colunas
da base de bares.
"""

from dash import dcc, html
import dash_leaflet as dl

COR_BAR = "#1d4ed8"
COR_BAR_PREENCHIMENTO = "#3b82f6"
COR_ENTREGADOR = "#6b7280"
COR_NO_RAIO = "#dc2626"
COR_RESTAURANTE = "#b45309"
COR_RESTAURANTE_PREENCHIMENTO = "#f59e0b"

CENTRO_BH = [-19.9167, -43.9345]
ZOOM_INICIAL = 13
ZOOM_CONSULTA = 14


def marcadores_centros(centros):
    """Bares sorteados como centros da distribuicao dos entregadores.

    centros: lista de (lat, lon, texto do tooltip).
    """
    return [
        dl.CircleMarker(
            center=[float(lat), float(lon)],
            radius=6,
            color=COR_BAR,
            fillColor=COR_BAR_PREENCHIMENTO,
            fillOpacity=0.9,
            weight=2,
            children=dl.Tooltip(texto),
        )
        for lat, lon, texto in centros
    ]


def marcadores_entregadores(entregadores, distancias):
    """Entregadores no raio em vermelho e os demais em cinza.

    distancias: {id do entregador: distancia em metros} dos que estao no raio.
    Os vermelhos sao desenhados por ultimo para ficarem por cima dos cinzas.
    """
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


def marcadores_restaurante(lat, lon, raio_m, texto):
    """Destaque do restaurante consultado e o circulo do raio de atendimento."""
    centro = [float(lat), float(lon)]
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
            children=dl.Tooltip(texto),
        ),
    ]


def viewport_restaurante(lat, lon):
    """Centraliza o mapa no restaurante com uma animacao."""
    return {
        "center": [float(lat), float(lon)],
        "zoom": ZOOM_CONSULTA,
        "transition": "flyTo",
    }


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
        item_legenda(
            COR_RESTAURANTE, COR_RESTAURANTE_PREENCHIMENTO, "Restaurante consultado"
        ),
        item_legenda(COR_NO_RAIO, "transparent", "Raio de atendimento", tracejado=True),
        item_legenda(COR_NO_RAIO, COR_NO_RAIO, "Entregador no raio"),
        item_legenda(COR_ENTREGADOR, COR_ENTREGADOR, "Entregador fora do raio"),
        item_legenda(COR_BAR, COR_BAR_PREENCHIMENTO, "Bar de origem da frota"),
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


def componente_mapa(centros):
    """Mapa com as camadas, a legenda e o indicador de carregamento.

    Camadas atualizadas pelos callbacks: "marcadores-layer" (entregadores) e
    "restaurante-layer" (restaurante consultado e raio). O id do mapa e
    "mapa-principal".
    """
    mapa = dl.Map(
        id="mapa-principal",
        children=[
            dl.TileLayer(),
            # Controle no canto superior direito para ligar/desligar camadas
            dl.LayersControl(
                [
                    dl.Overlay(
                        dl.LayerGroup(id="marcadores-layer"),
                        name="Entregadores",
                        checked=True,
                    ),
                    dl.Overlay(
                        dl.LayerGroup(
                            id="centros-layer", children=marcadores_centros(centros)
                        ),
                        name="Bares de origem da frota",
                        checked=True,
                    ),
                ],
                position="topright",
            ),
            # Restaurante consultado e circulo do raio (sempre visiveis)
            dl.LayerGroup(id="restaurante-layer"),
        ],
        style={"width": "100%", "height": "100%"},
        center=CENTRO_BH,
        zoom=ZOOM_INICIAL,
    )
    # Mostra um indicador durante a geracao, mantendo o mapa visivel por baixo
    return dcc.Loading(
        type="circle",
        overlay_style={"visibility": "visible", "opacity": 0.6},
        parent_style={"flex": "0 0 65%"},
        children=html.Div(
            [mapa, legenda],
            # position relative para a legenda ficar presa ao mapa
            style={"position": "relative", "width": "100%", "height": "70vh"},
        ),
    )
