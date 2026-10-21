"""Mapa interativo: camadas, marcadores, circulo do raio e legenda.

As funcoes recebem coordenadas e textos ja prontos, sem depender das colunas
da base de bares.
"""

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html

COR_BAR = "#1d4ed8"
COR_BAR_PREENCHIMENTO = "#3b82f6"
COR_ENTREGADOR = "#6b7280"
COR_NO_RAIO = "#dc2626"
COR_RESTAURANTE = "#b45309"
COR_RESTAURANTE_PREENCHIMENTO = "#f59e0b"

CENTRO_BH = [-19.9167, -43.9345]
ZOOM_INICIAL = 13
ZOOM_CONSULTA = 14
METROS_POR_GRAU_LAT = 111_320


def marcadores_centros(centros):
    """Bares sorteados como centros da distribuicao dos entregadores.

    centros: lista de (lat, lon, texto do tooltip).
    """
    if not centros:
        return []
    return [
        go.Scattermap(lat=[float(lat) for lat, _, _ in centros],lon=[float(lon) for _, lon, _ in centros],mode="markers",marker=dict(size=9, color=COR_BAR_PREENCHIMENTO),text=[texto for _, _, texto in centros],hoverinfo="text",showlegend=False,)
    ]


def marcadores_entregadores(entregadores, distancias):
    """Entregadores no raio em vermelho e os demais em cinza.

    distancias: {id do entregador: distancia em metros} dos que estao no raio.
    Os vermelhos sao desenhados por ultimo para ficarem por cima dos cinzas.
    """
    fora = [e for e in entregadores if e["id"] not in distancias]
    dentro = [e for e in entregadores if e["id"] in distancias]

    marcadores = []
    if fora:
        marcadores.append(
            go.Scattermap(lat=[e["lat"] for e in fora],lon=[e["lon"] for e in fora],mode="markers",marker=dict(size=6, color=COR_ENTREGADOR, opacity=0.7),text=[e["id"] for e in fora],hoverinfo="text",showlegend=False,)
        )
    if dentro:
        marcadores.append(
            go.Scattermap(lat=[e["lat"] for e in dentro],lon=[e["lon"] for e in dentro],mode="markers",marker=dict(size=8, color=COR_NO_RAIO, opacity=0.9),text=[f"{e['id']} — {distancias[e['id']]:.0f} m" for e in dentro],hoverinfo="text",showlegend=False,)
        )
    return marcadores


def marcadores_restaurante(lat, lon, raio_m, texto):
    #marcacao do restaurante consultado e do raio de busca
    lat_c, lon_c = float(lat), float(lon)
    
    raio_terra = 6371000.0
    dist_angular = raio_m / raio_terra
    lat_rad = np.radians(lat_c)
    lon_rad = np.radians(lon_c)

    angulos = np.linspace(0, 2 * np.pi, 360)

    lat_circ_rad = np.arcsin(
        np.sin(lat_rad) * np.cos(dist_angular)
        + np.cos(lat_rad) * np.sin(dist_angular) * np.cos(angulos)
    )
    lon_circ_rad = lon_rad + np.arctan2(
        np.sin(angulos) * np.sin(dist_angular) * np.cos(lat_rad),
        np.cos(dist_angular) - np.sin(lat_rad) * np.sin(lat_circ_rad),
    )

    lat_circ = np.degrees(lat_circ_rad).tolist()
    lon_circ = np.degrees(lon_circ_rad).tolist()

    return [
        go.Scattermap(lat=lat_circ,lon=lon_circ,mode="lines",line=dict(width=2, color=COR_NO_RAIO),fill="toself",fillcolor="rgba(220, 38, 38, 0.05)",hoverinfo="skip",showlegend=False,),
        go.Scattermap(lat=[lat_c],lon=[lon_c],mode="markers",marker=dict(size=14, color=COR_RESTAURANTE_PREENCHIMENTO),text=[texto],hoverinfo="text",showlegend=False,        ),
    ]


def visualizacao_restaurante(lat, lon):
    #centralizacao do restaurante no mapa
    return {
        "center": {"lat": float(lat), "lon": float(lon)},
        "zoom": ZOOM_CONSULTA,
    }


def montar_figura(centros, entregadores, restaurante, viewport=None):
    # geracao dos dos dados no mapa
    v = viewport or {
        "center": {"lat": CENTRO_BH[0], "lon": CENTRO_BH[1]},
        "zoom": ZOOM_INICIAL,
    }
    fig = go.Figure(data=marcadores_centros(centros) + entregadores + restaurante)
    fig.update_layout(
        map=dict(style="open-street-map", center=v["center"], zoom=v["zoom"]),
        margin=dict(l=0, r=0, t=0, b=0),
        uirevision=str(v["center"]) if viewport else "manter_camera",
    )
    return fig


def item_legenda(cor, preenchimento, texto, tracejado=False):
    # definicao da legenda com base nas cores pre-definidas
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
    """Mapa com as camadas, a legenda e o indicador de carregamento."""
    mapa_fig = dcc.Graph(
        id="mapa-principal",
        figure=montar_figura(centros, [], []),
        style={"width": "100%", "height": "100%"},
        config={"scrollZoom": True, "displayModeBar": False},
    )
    return dcc.Loading(
        type="circle",
        overlay_style={"visibility": "visible", "opacity": 0.6},
        parent_style={"flex": "0 0 65%"},
        children=html.Div(
            [mapa_fig, legenda],
            style={"position": "relative", "width": "100%", "height": "70vh"},
        ),
    )