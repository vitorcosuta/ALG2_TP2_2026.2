from dash import Dash, Input, Output, State, callback, dcc, html
import dash_leaflet as dl

app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Monitoramento de Frota"),
        
        # Area de insercao de dados
        html.Div(
            [
                html.Label("Quantidade de Entregadores (N):"),
                dcc.Input(id="input-n-entregadores",type="number",min=1,max=20),
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
        html.Div(
            [
                # Mapa Leaflet
                dl.Map(
                    id="mapa-principal",
                    children=[
                        dl.TileLayer(),
                        # Camada onde os marcadores serão injetados
                        dl.LayerGroup(id="marcadores-layer"),
                    ],
                    style={"width": "65%", "height": "70vh", "display": "inline-block"},
                    center=[-19.9167, -43.9345],
                    zoom=13,
                ),
            ]
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
    
    # Realizar chamada de geração de entregadores e colocacao de marcadores no mapa
    


if __name__ == "__main__":
    app.run(debug=True)