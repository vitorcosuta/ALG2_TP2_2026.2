from dash import dash_table, html
from dash.dash_table.Format import Format, Scheme

# Velocidade media de um entregador de moto na rua
VELOCIDADE_MEDIA_KMH = 25


def formatar_km(km):
    """Raio no formato brasileiro: 0,5 km; 2 km."""
    return f"{km:g}".replace(".", ",") + " km"


def formatar_numero(valor, casas=0):
    """Numero no formato brasileiro: 1.234,5."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def tempo_estimado_min(distancia_m):
    """Tempo de chegada em minutos, em linha reta, na velocidade media."""
    return distancia_m / 1000 / VELOCIDADE_MEDIA_KMH * 60


def linhas_tabela(resultado):
    """Linhas da tabela: ID, distancia e tempo estimado de cada entregador no raio."""
    return [
        {
            "id": e["id"],
            "distancia": round(d),
            "tempo": round(tempo_estimado_min(d), 1),
        }
        for d, e in resultado
    ]


def cartao_metrica(titulo, valor, detalhe=None):
    """Bloco com o nome da metrica, o valor em destaque e um detalhe opcional."""
    conteudo = [
        html.Div(titulo, style={"fontSize": "12px", "color": "#4b5563"}),
        html.Div(valor, style={"fontSize": "20px", "fontWeight": "bold"}),
    ]
    if detalhe:
        conteudo.append(
            html.Div(detalhe, style={"fontSize": "12px", "color": "#4b5563"})
        )
    return html.Div(
        conteudo,
        style={
            "backgroundColor": "white",
            "border": "1px solid #e5e7eb",
            "borderRadius": "6px",
            "padding": "8px 10px",
        },
    )


def metricas_resumo(resultado, total_entregadores, runtime_ms):
    """Metricas resumo dos entregadores no raio e o tempo da consulta."""
    cartoes = [
        cartao_metrica(
            "Entregadores no raio",
            f"{len(resultado)}",
            f"de {formatar_numero(total_entregadores)} na frota",
        ),
        cartao_metrica("Tempo da consulta", f"{formatar_numero(runtime_ms, 2)} ms"),
    ]
    if resultado:
        distancias = [d for d, _ in resultado]
        media = sum(distancias) / len(distancias)
        d_min, e_min = resultado[0]
        d_max, e_max = resultado[-1]
        cartoes += [
            cartao_metrica(
                "Mais próximo",
                f"{formatar_numero(d_min)} m",
                f"{e_min['id']} · {formatar_numero(tempo_estimado_min(d_min), 1)} min",
            ),
            cartao_metrica(
                "Mais distante",
                f"{formatar_numero(d_max)} m",
                f"{e_max['id']} · {formatar_numero(tempo_estimado_min(d_max), 1)} min",
            ),
            cartao_metrica("Distância média", f"{formatar_numero(media)} m"),
            cartao_metrica(
                "Tempo médio", f"{formatar_numero(tempo_estimado_min(media), 1)} min"
            ),
        ]
    return cartoes


FORMATO_INTEIRO = Format(group=True, group_delimiter=".", decimal_delimiter=",")
FORMATO_DECIMAL = Format(
    precision=1,
    scheme=Scheme.fixed,
    group=True,
    group_delimiter=".",
    decimal_delimiter=",",
)

painel = html.Div(
    [
        html.H3("Entregadores no raio", style={"marginTop": 0}),
        html.Div(
            id="metricas",
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "8px",
                "marginBottom": "12px",
            },
        ),
        dash_table.DataTable(
            id="tabela-entregadores",
            columns=[
                {"name": "ID", "id": "id"},
                {
                    "name": "Distância (m)",
                    "id": "distancia",
                    "type": "numeric",
                    "format": FORMATO_INTEIRO,
                },
                {
                    "name": "Tempo estimado (min)",
                    "id": "tempo",
                    "type": "numeric",
                    "format": FORMATO_DECIMAL,
                },
            ],
            data=[],
            sort_action="native",
            page_size=12,
            style_table={"overflowX": "auto"},
            style_header={"fontWeight": "bold", "backgroundColor": "#f3f4f6"},
            style_cell={"padding": "6px", "fontFamily": "inherit", "fontSize": "14px"},
            style_cell_conditional=[{"if": {"column_id": "id"}, "textAlign": "left"}],
        ),
        html.Div(
            f"Tempo estimado em linha reta, a {VELOCIDADE_MEDIA_KMH} km/h.",
            style={"fontSize": "12px", "color": "#4b5563", "marginTop": "6px"},
        ),
    ],
    style={
        "flex": "1",
        "minWidth": "300px",
        "padding": "12px 16px",
        "backgroundColor": "#f9f9f9",
        "overflowY": "auto",
        "maxHeight": "70vh",
    },
)
