import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import datetime as dt
import requests
import json
import os
from loguru import logger
from datetime import datetime, timedelta

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Dashboard Template"

server = app.server

# Cargar datos de ejemplo (reemplaza con tus propios datos)
def load_data():
    # Datos de ejemplo - reemplazar con tu propia carga de datos
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(24)][::-1]

# Dataset de prueba con patrones intencionales para disparar alertas
    data = pd.DataFrame({
        'timestamp': timestamps,
        'presion': [16.5, 16.3, 16.1, 15.8, 15.5, 15.2, 14.9, 14.6, 14.3, 14.0,  # Presión descendente <15
                    13.7, 13.4, 17.0, 19.0, 20.0, 19.5, 18.0, 17.5, 17.0, 16.5,   # Recuperación
                    16.0, 15.5, 17.8, 14.2],                                      # Variabilidad final
        
        'temperatura': [32.0, 32.1, 32.3, 32.5, 32.8, 33.0, 33.2, 33.5, 33.8, 34.0,
                        34.2, 34.5, 34.8, 35.1, 35.5, 36.0, 36.5, 37.0, 37.5, 38.0,  # >35°C
                        36.0, 34.0, 32.0, 35.5],                                   # Fluctuación
        
        'volumen': np.concatenate([
            np.random.normal(100, 5, 18),  # Valores normales
            [150, 160, 170, 180, 190, 200] # Valores extremos (>2σ)
        ])[-24:]  # Tomamos los últimos 24 valores
    })
    return data

data = load_data()

def generate_filters():
    """
    :return: A Div dropdown lists for filters.
    """
    return html.Div(
        id="filters",
        children=[
            # Canal
            html.H2("Filtros",style={
                        "textAlign": "Left",
                        "marginBottom": "20px",
                        "color": "#FFFFFF",  # Puedes cambiar el color si lo deseas
                    }),
            html.Div(
                id="componentes-filtros",
                children=[
                    
                    html.Div(
                        id="componente-anio",
                        children=[
                            html.P("Año"),
                            dcc.Dropdown(
                                id="anio-dropdown",
                                options=[{'label': 2025, 'value': 2025}],
                                placeholder="Seleccione un Año",
                                value= [2025],
                                multi = True,
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),
                    html.Div(
                        id="componente-mes",
                        children=[
                            html.P("Mes"),
                            dcc.Dropdown(
                                id="mes-dropdown",
                                options=[{'label': 5, 'value': 5}],
                                placeholder="Seleccione uno o varios Mes",
                                value=[5],
                                multi = True,
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),
                    html.Div(
                        id="componente-dia",
                        children=[
                            html.P("Día"),
                            dcc.Dropdown(
                                id="dia-dropdown",
                                options=[{'label': 14, 'value': 14}],
                                placeholder="Seleccione una Unidad de Negocio",
                                value=[14],
                                multi = True,
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),

                    html.Div(
                        id="componente-horario",
                        children=[
                            html.P("Rango_Horario"),
                            dcc.Dropdown(
                                id="horario-dropdown",
                                options=[{'label': "12-13", 'value': "12-13"} ],
                                placeholder="Seleccione un canal",
                                value=["12-13"],
                                multi = True,
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),

                    html.Div(
                        id="componente-cliente",
                        children=[
                            html.P("Cliente"),
                            dcc.Dropdown(
                                id="cliente-dropdown",
                                options=[{'label': "cliente1", 'value': "cliente1"}],
                                placeholder="Seleccione una Regional",
                                value=["cliente1"],
                                multi = True,
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),
                ],
                style=dict(display='flex',flexDirection='column',gap='10px',marginBottom = '20px') # Organiza los filtros en columna
            ),
        ]
    )

def generate_KPI():
    """
    Función para generar 6 KPIs, organizados en 2 filas (3 KPIs por fila).
    :return: Una lista de Divs que representan los 6 KPIs.
    """
    # Valores de ejemplo para los KPIs
    volumen_promedio = 20.98
    presion_promedio = 17.68
    temperatura_promedio = 27.54
    rango_vol = "20.54 - 21.58"
    rango_pre = "16.00 - 19.85"
    rango_temp = "26.98 - 32.58"

    # Estilo común para las tarjetas KPI
    kpi_card_style = {
        "padding": "20px",
        "borderRadius": "8px",
        "color": "#FFFFFF",
        "textAlign": "center",
        "margin": "10px",
        "flex": "1",
        "minWidth": "200px"
    }

    kpi_title_style = {"textAlign": "center", "color": "#FFFFFF"}
    kpi_value_style = {"textAlign": "center", "fontSize": "25px", "color": "#FFFFFF"}

    return html.Div(
        style={"display": "flex", "flexDirection": "column", "width": "100%"},
        children=[
            # Primera fila con 3 KPIs
            html.Div(
                style={"display": "flex", "flexWrap": "wrap", "justifyContent": "space-around"},
                children=[
                    # KPI 1
                    html.Div(
                        className="kpi-card",
                        children=[
                            html.H4("Volumen Promedio m3", style=kpi_title_style),
                            html.P(f"{volumen_promedio:,.2f}", style=kpi_value_style),
                        ],
                        style=kpi_card_style
                    ),
                    # KPI 2
                    html.Div(
                        className="kpi-card",
                        children=[
                            html.H4("Presión Promedio bar", style=kpi_title_style),
                            html.P(f"{presion_promedio:,.2f}", style=kpi_value_style),
                        ],
                        style=kpi_card_style
                    ),
                    # KPI 3
                    html.Div(
                        className="kpi-card",
                        children=[
                            html.H4("Temperatura Promedio °C", style=kpi_title_style),
                            html.P(f"{temperatura_promedio:,.2f}", style=kpi_value_style),
                        ],
                        style=kpi_card_style
                    ),
                ]
            ),
            # Segunda fila con otros 3 KPIs
            html.Div(
                style={"display": "flex", "flexWrap": "wrap", "justifyContent": "space-around"},
                children=[
                    # KPI 4
                    html.Div(
                        className="kpi-card",
                        children=[
                            html.H4("Rango Volumen", style=kpi_title_style),
                            html.P(rango_vol, style=kpi_value_style),
                        ],
                        style=kpi_card_style
                    ),
                    # KPI 5
                    html.Div(
                        className="kpi-card",
                        children=[
                            html.H4("Rango Presión", style=kpi_title_style),
                            html.P(rango_pre, style=kpi_value_style),
                        ],
                        style=kpi_card_style
                    ),
                    # KPI 6
                    html.Div(
                        className="kpi-card",
                        children=[
                            html.H4("Rango Temperatura", style=kpi_title_style),
                            html.P(rango_temp, style=kpi_value_style),
                        ],
                        style=kpi_card_style
                    ),
                ]
            )
        ]
    )

# Función para generar las alertas al comparar con los datos
# Se puede modificar respecto a como se vaya a manejar
def generar_alertas(data, ultimo_estado=None):
    alertas = []
    ultimos_valores = {
        'presion': data['presion'].iloc[-1],
        'temperatura': data['temperatura'].iloc[-1],
        'volumen': data['volumen'].iloc[-1]
    }
    
    # Solo genera alertas si los valores cambiaron
    if ultimo_estado is None or ultimos_valores != ultimo_estado:
        presion_actual = ultimos_valores['presion']
        if presion_actual < 15:
            alertas.append({
                "tipo": "CRÍTICA",
                "mensaje": f"Presión peligrosamente baja: {presion_actual} psi",
                "color": "#e74c3c",
                "icono": "⚠️"
            })
        elif presion_actual < 18:
            alertas.append({
                "tipo": "Advertencia",
                "mensaje": f"Presión por debajo del nivel óptimo: {presion_actual} psi",
                "color": "#f39c12",
                "icono": "❗"
            })
        
        temp_actual = ultimos_valores['temperatura']
        if temp_actual > 35:
            alertas.append({
                "tipo": "CRÍTICA",
                "mensaje": f"Temperatura crítica: {temp_actual}°C",
                "color": "#e74c3c",
                "icono": "🔥"
            })
        
        vol_actual = ultimos_valores['volumen']
        vol_mean = data['volumen'].mean()
        vol_std = data['volumen'].std()
        if vol_actual > vol_mean + 2*vol_std:
            alertas.append({
                "tipo": "Advertencia",
                "mensaje": f"Volumen anormalmente alto: {vol_actual} (μ={vol_mean:.1f}, σ={vol_std:.1f})",
                "color": "#f39c12",
                "icono": "📈"
            })
    
    return alertas, ultimos_valores

# Layout del dashboard
app.layout = html.Div(
    id="app-container",
    children=[
    # Header con logo y título centrado
    html.Div(
            id="brand-section",
            style={
                "display": "flex",
                "justify-content": "space between",  # Centra todo el contenido horizontalmente
                "align-items": "center",
                "padding": "5px 20px",
                "background-color": "#2c3e50",
            },
            children=[
                # Logo posicionado a la izquierda
                html.Img(
                    src="/assets/contugas.png",
                    style={
                        "height": "150px",
                        "width": "auto",
                        "left": "2px",  # Distancia desde la izquierda
                    }
                ),
                # Título centrado
                html.H1(
                    "Tablero de Control de Anomalías en Consumo",
                    style={
                        "textAlign": "center",
                        "color": "#ecf0f1",
                        "font-size": "30px",
                        "font-weight": "bold",
                        "margin": "0 auto",  # Centra el título en el espacio disponible
                    }
                ),
            ],
        ),


        # Sección 1 - Filtros y KPIs
        html.Div(
            id="section-1",
            children=[
                # html.H2(
                #     "KPIs",
                #     style={
                #         "textAlign": "center",
                #         "marginBottom": "20px",
                #         "color": "#FFFFFF",
                #     }
                # ),
                
                html.Div(
                    className="row",
                    children=[
                        # Filtros
                        html.Div(
                            className="three columns",
                            style={"display": "flex", "justify-content": "center", "align-items": "center", 'height': '70vh'},
                            children=[generate_filters()]
                            + [
                                html.Div(
                                    ["initial child"], id="output-clientside", style={"display": "none"}
                                )
                            ],
                        ),
                        
                        # KPIs y gráficos
                        html.Div(
                            className="nine columns",
                            children=[
                                # Espacio para KPIs
                                html.Div(
                                    id="kpi-container",
                                    children = generate_KPI()
                                ),
                                html.Hr(),
                                
                                # Gráficos de series de tiempo
                                html.Div(
                                    className="twelve columns",
                                    children=[
                                        html.Div(
                                            className="six columns",
                                            children=[dcc.Graph(id='plot_time_series_1')]
                                        ),
                                        html.Div(
                                            className="six columns",
                                            children=[dcc.Graph(id='plot_time_series_2')]
                                        )
                                    ]
                                ),
                                html.Div(
                                    className="twelve columns",
                                    style={"display": "flex", "justify-content": "center", "margin-top": "20px"},
                                    children=[
                                        html.Div(
                                            style={"width": "60%"},
                                            children=[dcc.Graph(id="plot_time_series_3")]
                                        )
                                    ]
                                )
                            ]
                        ),
                    ]
                )
            ]
        ),

        # Sección 2 - Análisis descriptivo
        html.Div(
            id="section-2",
            className="twelve columns",
            children=[
                html.H2(
                    "Promedio Móvil Últimos 7 días",
                    style={
                        "textAlign": "center",
                        "marginBottom": "20px",
                        "color": "#FFFFFF",
                    }
                ),
                
                html.Div(
                    className="row",
                    style={"display": "flex", "justify-content": "center", "margin-top": "20px"},
                    children=[
                        html.Div(
                            style={"width": "70%"},
                            children=[dcc.Graph(id="plot_series_1")]
                        )
                    ]
                ),
                html.Div(
                    className="row",
                    style={"display": "flex", "justify-content": "center", "margin-top": "20px"},
                    children=[
                        html.Div(
                            style={"width": "70%"},
                            children=[dcc.Graph(id="plot_series_2")]
                        )
                    ]
                ),
                html.Div(
                    className="row",
                    style={"display": "flex", "justify-content": "center", "margin-top": "20px"},
                    children=[
                        html.Div(
                            style={"width": "70%"},
                            children=[dcc.Graph(id="plot_series_3")]
                        )
                    ]
                )
            ]
        ),

        # Sección 3 - Análisis predictivo
        html.Div(
            id="section-3",
            children=[
                html.H2(
                    "Detección de Anomalías",
                    style={
                        "textAlign": "center",
                        "marginBottom": "20px",
                        "color": "#FFFFFF",
                    }
                ),
                
                html.Div(
                    className="row",
                    style={"display": "flex", "justify-content": "center", "margin-top": "20px"},
                    children=[
                        html.Div(
                            style={"width": "70%"},
                            children=[dcc.Graph(id="plot_anomalias")]
                        )
                    ]
                ),
            ]
        ),

        # Sección 4 - Mensajes/Alertas
        html.Div(
            id="section-alertas",
            style={
                "margin": "20px",
                "padding": "20px",
                "backgroundColor": "#1e1e1e",
                "borderRadius": "10px",
                "border": "1px solid #444"
            },
            children=[
                html.H2(
                    "Sistema de Alertas",
                    style={
                        "textAlign": "center",
                        "marginBottom": "20px",
                        "color": "#FFFFFF",
                    }
                ),
                
                # Contenedor de alertas con scroll
                html.Div(
                    id="alert-container",
                    style={
                        "maxHeight": "300px",
                        "overflowY": "auto",
                        "padding": "10px",
                        "backgroundColor": "#2a2a2a",
                        "borderRadius": "5px"
                    },
                    children=[
                        # Las alertas se generarán dinámicamente aquí
                        html.Div(
                            id="alert-placeholder",
                            children="No hay alertas recientes",
                            style={"color": "#777", "textAlign": "center"}
                        )
                    ]
                ),
                
                # Almacenamiento para las alertas
                dcc.Store(id='alert-store', data=[]),
                
                # Intervalo para chequeo periódico
                dcc.Interval(
                    id='alert-interval',
                    interval=60*1000,  # Chequear cada minuto
                    n_intervals=0
                )
            ]
        )
    ]
)

@app.callback(
    [Output('alert-container', 'children'),
     Output('alert-store', 'data')],
    [Input('alert-interval', 'n_intervals'),
     #Input('datos-filtrados', 'data')
     ],  # Asume que tienes un Store con los datos
    [State('alert-store', 'data')]
)
def actualizar_alertas(n_intervals, alertas_anteriores):
 
    # Generar nuevas alertas
    nuevas_alertas, ultimos_valores = generar_alertas(data)
    
    # Combinar con alertas anteriores (limitar a las últimas 20)
    todas_alertas = (nuevas_alertas + alertas_anteriores)[:20]
    
    # Generar elementos HTML para las alertas
    alertas_html = []
    for alerta in todas_alertas:
        alerta_html = html.Div(
            style={
                "padding": "10px",
                "marginBottom": "8px",
                "borderLeft": f"4px solid {alerta['color']}",
                "backgroundColor": "#252525",
                "display": "flex",
                "alignItems": "center"
            },
            children=[
                html.Span(
                    alerta['icono'],
                    style={"fontSize": "20px", "marginRight": "10px"}
                ),
                html.Div(
                    children=[
                        html.Strong(
                            f"{alerta['tipo']}: ",
                            style={"color": alerta['color']}
                        ),
                        html.Span(alerta['mensaje'])
                    ]
                )
            ]
        )
        alertas_html.append(alerta_html)
    
    if not alertas_html:
        return [html.Div("No hay alertas recientes", style={"color": "#777"})], []
    
    return alertas_html, todas_alertas
        

if __name__ == "__main__":
    logger.info("Running dash")
    app.run_server(host="0.0.0.0",debug=True)