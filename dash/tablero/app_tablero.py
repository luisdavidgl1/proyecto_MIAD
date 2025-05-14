import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import datetime as dt
import requests
import json
import os
from loguru import logger

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Dashboard pronóstico ventas"

server = app.server
app.config.suppress_callback_exceptions = True

# PREDICTION API URL 
api_url = os.getenv('API_URL')
#api_url = '52.21.110.235'
api_url = "http://{}:8001/predict".format(api_url)

# Load data from gold folder
def load_data_analisis_descriptivo():
    data = pd.read_csv("ExporteCOL2022_2023_2024_top_products.csv", sep=',')
    #data = pd.read_csv("ExporteCOL2022_2023_2024_top_products.csv", sep=',')
    return data
    

# Cargar datos
#data = load_data()
data_ad = load_data_analisis_descriptivo()

def plot_bar_1(data_ad):

    ventas_por_canal = data_ad.groupby("Canal Comercial")["Ventas"].sum().reset_index()
    ventas_por_canal = ventas_por_canal.sort_values(by="Ventas", ascending=False)

    fig = go.Figure(
        data=[
            go.Bar(
                x=ventas_por_canal["Canal Comercial"],
                y=ventas_por_canal["Ventas"],
                marker=dict(color="#3498db"),
                name="Ventas por Canal"
            )
        ]
    )

    # Configuración del diseño del gráfico
    fig.update_layout(
        title="Total de Ventas por Canal Comercial",
        xaxis_title="Canal Comercial",
        yaxis_title="Ventas",
        paper_bgcolor="rgba(0,0,0,0)",  # Fondo transparente (usa color hexadecimal si prefieres)
        plot_bgcolor="#E8E8E8",  # Fondo del área de la gráfica
        font=dict(color="#FFFFFF")  # Color de texto de los ejes y título
    )

    return fig

def plot_bar_2(data_ad):

    ventas_por_marquilla = data_ad.groupby("Marquilla")["Ventas"].sum().reset_index()
    ventas_por_marquilla = ventas_por_marquilla.sort_values(by="Ventas", ascending=False)
    ventas_por_marquilla = ventas_por_marquilla.head(10)

    fig = go.Figure(
        data=[
            go.Bar(
                x=ventas_por_marquilla["Marquilla"],
                y=ventas_por_marquilla["Ventas"],
                marker=dict(color="#3498db"),
                name="Ventas por Marquilla"
            )
        ]
    )

    # Configuración del diseño del gráfico
    fig.update_layout(
        title="Total de Ventas por Marquilla",
        xaxis_title="Marquilla",
        yaxis_title="Ventas",
        paper_bgcolor="rgba(0,0,0,0)",  # Fondo transparente (usa color hexadecimal si prefieres)
        plot_bgcolor="#E8E8E8",  # Fondo del área de la gráfica
        font=dict(color="#FFFFFF")  # Color de texto de los ejes y título
    )

    return fig

def plot_pie_chart(data_ad):

    ventas_por_negocio = data_ad.groupby("Uen")["Ventas"].sum().reset_index()
    ventas_por_negocio = ventas_por_negocio.sort_values(by="Ventas", ascending=False)


    fig = go.Figure(
        data=[
            go.Pie(
                labels=ventas_por_negocio["Uen"],
                values=ventas_por_negocio["Ventas"],
                hole=0.25,
                #marker=dict(colors=["#3498db"]),
                name="Ventas por Unidad de Negocio"
            )
        ]
    )

    # Configuración del diseño del gráfico
    fig.update_layout(
        title="Distribución de Ventas por Unidad de Negocio UEN",
        title_x=0.5,
        paper_bgcolor="rgba(0,0,0,0)",  # Fondo transparente (usa color hexadecimal si prefieres)
        plot_bgcolor="#E8E8E8",  # Fondo del área de la gráfica
        font=dict(color="#FFFFFF")  # Color de texto de los ejes y título
    )

    return fig


def generate_control_card():
    """
    :return: A Div containing controls for graphs.
    """
    return html.Div(
        id="control-card",
        children=[
            html.Div(
                id="componentes-prediccion",
                children=[
                    html.Div(
                        id="componente-uen2",
                        children=[
                            html.P("UEN"),
                            dcc.Dropdown(
                                id="uen-prediccion",
                                options=[{'label': uen, 'value': uen} for uen in data_ad['Uen'].unique()],
                                placeholder="Seleccione una Unidad de Negocio",
                                value=data_ad['Uen'].unique()[0],
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),

                    html.Div(
                        id="componente-regional2",
                        children=[
                            html.P("Regional"),
                            dcc.Dropdown(
                                id="regional-prediccion",
                                options=[{'label': regional, 'value': regional} for regional in data_ad['Regional'].unique()],
                                placeholder="Seleccione una Regional",
                                value=data_ad['Regional'].unique()[0],
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),
                    
                    html.Div(
                        id="componente-canal",
                        children=[
                            html.P("Canal"),
                            dcc.Dropdown(
                                id="canal-prediccion",
                                options=[{'label': canal, 'value': canal} for canal in data_ad['Canal Comercial'].unique()],
                                placeholder="Seleccione un canal",
                                value=data_ad['Canal Comercial'].unique()[0],
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),

                    html.Div(
                        id="componente-marquilla2",
                        children=[
                            html.P("Marquilla"),
                            dcc.Dropdown(
                                id="marquilla-prediccion",
                                options=[{'label': marquilla, 'value': marquilla} for marquilla in data_ad['Marquilla'].unique()],
                                placeholder="Seleccione una Marquilla",
                                value=data_ad['Marquilla'].unique()[0],
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),

                    html.Div(
                        id="componente-codigo",
                        children=[
                            html.P("Código_producto"),
                            dcc.Dropdown(
                                id="codigo-prediccion",
                                options=[{'label': codigo, 'value': codigo} for codigo in data_ad['Código Producto'].unique()],
                                placeholder="Seleccione un Código de Producto",
                                value=data_ad['Código Producto'].unique()[0],
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),

                    html.Div(
                        id="componente-producto2",
                        children=[
                            html.P("Producto"),
                            dcc.Dropdown(
                                id="producto-prediccion",
                                options=[{'label': producto, 'value': producto} for producto in data_ad['Producto'].unique()],
                                placeholder="Seleccione un Producto",
                                value=data_ad['Producto'].unique()[0],
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),

                    html.Div(
                        id="componente-proyeccion",
                        children=[
                            html.P("Meses_a_proyectar"),
                            dcc.Dropdown(
                                id="meses-prediccion",
                                options=list(range(1,25)),
                                placeholder="Meses a proyectar",
                                value=5,
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
                                options=[{'label': anio, 'value': anio} for anio in data_ad['Año'].unique()],
                                placeholder="Seleccione un Año",
                                value=[data_ad['Año'].unique()[0]],
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
                                options=[{'label': mes, 'value': mes} for mes in data_ad['Mes'].unique()],
                                placeholder="Seleccione uno o varios Mes",
                                value=[data_ad['Mes'].unique()[0]],
                                multi = True,
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),
                    html.Div(
                        id="componente-uen",
                        children=[
                            html.P("UEN"),
                            dcc.Dropdown(
                                id="uen-dropdown",
                                options=[{'label': uen, 'value': uen} for uen in data_ad['Uen'].unique()],
                                placeholder="Seleccione una Unidad de Negocio",
                                value=[data_ad['Uen'].unique()[0]],
                                multi = True,
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),

                    html.Div(
                        id="componente-canal2",
                        children=[
                            html.P("Canal"),
                            dcc.Dropdown(
                                id="canal2-dropdown",
                                options=[{'label': canal, 'value': canal} for canal in data_ad['Canal Comercial'].unique()],
                                placeholder="Seleccione un canal",
                                value=[data_ad['Canal Comercial'].unique()[0]],
                                multi = True,
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),

                    html.Div(
                        id="componente-regional",
                        children=[
                            html.P("Regional"),
                            dcc.Dropdown(
                                id="regional-dropdown",
                                options=[{'label': regional, 'value': regional} for regional in data_ad['Regional'].unique()],
                                placeholder="Seleccione una Regional",
                                value=[data_ad['Regional'].unique()[0]],
                                multi = True,
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),
                    html.Div(
                        id="componente-marquilla",
                        children=[
                            html.P("Marquilla"),
                            dcc.Dropdown(
                                id="marquilla-dropdown",
                                options=[{'label': marquilla, 'value': marquilla} for marquilla in data_ad['Marquilla'].unique()],
                                placeholder="Seleccione una Marquilla",
                                value=[data_ad['Marquilla'].unique()[0]],
                                multi = True,
                                style=dict(width='50%', minWidth='300px')
                            )
                        ],
                        style=dict(width='20%')
                    ),
                    html.Div(
                        id="componente-producto",
                        children=[
                            html.P("Producto"),
                            dcc.Dropdown(
                                id="producto-dropdown",
                                options=[{'label': producto, 'value': producto} for producto in data_ad['Producto'].unique()],
                                placeholder="Seleccione un Producto",
                                value=[data_ad['Producto'].unique()[0]],
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


def generate_KPI(data_ad):
    """
    Función para generar 4 KPIs, cada uno en su propia tarjeta.
    :return: Una lista de Divs que representan los 4 KPIs.
    """

    if data_ad["Ventas"].sum() >= 1e6:
        kpi_total_ventas = (data_ad["Ventas"].sum()) #/1e6
    else: 
        kpi_total_ventas = (data_ad["Ventas"].sum())


    if data_ad["Ventas Galones"].sum() >= 1e6:
        kpi_total_ventas_gl = (data_ad["Ventas Galones"].sum())  #/1e6
    else: 
        kpi_total_ventas_gl = (data_ad["Ventas Galones"].sum())


    if data_ad["Utilidad Bruta"].sum() >= 1e6:
        kpi_utilidad_bruta = (data_ad["Utilidad Bruta"].sum())  #/1e6
    else: 
        kpi_utilidad_bruta = (data_ad["Utilidad Bruta"].sum())

    
    if data_ad["Ventas"].sum() == 0:
        kpi_margen = 0
    else: 
        kpi_margen = (data_ad["Utilidad Bruta"].sum() / data_ad["Ventas"].sum())*100


    return html.Div(
        className="row",  # Utilizamos un 'row' para alinear los KPIs horizontalmente
        children=[
            # KPI 1
            html.Div(
                className="two columns",  # Cada KPI ocupa 3 columnas de 12 (1/4 del espacio total)
                style={"flex":"1","width":"25%"},
                children=[
                    html.Div(
                        className="kpi-card",  # Clase para estilizar cada tarjeta de KPI
                        children=[
                            html.H4("Total Ventas COP", style={"textAlign": "center", "color": "#FFFFFF"}),
                            html.P(f"{kpi_total_ventas:,.0f}",  # Un valor aleatorio para ejemplo
                                   style={"textAlign": "center", "fontSize": "25px", "color": "#FFFFFF"}),
                        ],
                        style={
                            "padding": "20px",
                            "borderRadius": "8px",
                            "color": "#FFFFFF",
                            "textAlign": "center",
                        },
                    )
                ],
            ),
            # KPI 2
            html.Div(
                className="two columns",
                style={"flex":"1","width":"25%"},
                children=[
                    html.Div(
                        className="kpi-card",
                        children=[
                            html.H4("Total Ventas gl", style={"textAlign": "center", "color": "#FFFFFF"}),
                            html.P(f"{kpi_total_ventas_gl:,.0f}",  # Un valor aleatorio
                                   style={"textAlign": "center", "fontSize": "25px", "color": "#FFFFFF"}),
                        ],
                        style={
                            "padding": "20px",
                            "borderRadius": "8px",
                            "color": "#FFFFFF",
                            "textAlign": "center",
                        },
                    )
                ],
            ),
            # KPI 3
            html.Div(
                className="two columns",
                style={"flex":"1","width":"30%"},
                children=[
                    html.Div(
                        className="kpi-card",
                        children=[
                            html.H4("Utilidad Bruta COP", style={"textAlign": "center", "color": "#FFFFFF"}),
                            html.P(f"{kpi_utilidad_bruta:,.0f}",  # Un valor aleatorio
                                   style={"textAlign": "center", "fontSize": "25px", "color": "#FFFFFF"}),
                        ],
                        style={
                            "padding": "20px",
                            "borderRadius": "8px",
                            "color": "#FFFFFF",
                            "textAlign": "center",
                        },
                    )
                ],
            ),
            # KPI 4
            html.Div(
                className="two columns",
                style={"flex":"1","width":"10%"},
                children=[
                    html.Div(
                        className="kpi-card",
                        children=[
                            html.H4("Margen", style={"textAlign": "center", "color": "#FFFFFF"}),
                            html.P(f"{kpi_margen:,.1f}%",  # Un valor aleatorio
                                   style={"textAlign": "center", "fontSize": "25px", "color": "#FFFFFF"}),
                        ],
                        style={
                            "padding": "10px",
                            "borderRadius": "8px",
                            "color": "#FFFFFF",
                            "textAlign": "center",
                        },
                    )
                ],
            ),
        ]
    )

def plot_time_series_1(data_ad, uen, canal2, regional, marquilla, producto):
    data_ad['Año'] = data_ad["Año"].astype(int)
    data_ad['Mes'] = data_ad["Mes"].astype(int)
    data_ad['Dia'] = 1
    data_ad['Fecha'] = pd.to_datetime(data_ad['Año'].astype(str) + '-' + data_ad['Mes'].astype(str) + '-' + data_ad['Dia'].astype(str))
    data_ad = data_ad[(data_ad['Uen'].isin(uen)) & (data_ad['Canal Comercial'].isin(canal2)) & (data_ad['Regional'].isin(regional)) & 
                      (data_ad['Marquilla'].isin(marquilla)) & (data_ad['Producto'].isin(producto))]
    serie_ventas = data_ad.groupby('Fecha')['Ventas'].sum().reset_index()

    fig = go.Figure(
        data=[
            go.Scatter(
                x=serie_ventas['Fecha'],
                y=serie_ventas['Ventas'],
                mode = 'lines+markers',
                line=dict(color="#3498db"),
                name="Ventas por Fecha"
            )
        ]
    )

    # Configuración del diseño del gráfico
    fig.update_layout(
        title="Histórico de Ventas COP",
        xaxis_title="Fecha",
        yaxis_title="Ventas COP",
        paper_bgcolor="rgba(0,0,0,0)",  # Fondo transparente (usa color hexadecimal si prefieres)
        plot_bgcolor="#E8E8E8",  # Fondo del área de la gráfica
        font=dict(color="#FFFFFF"),  # Color de texto de los ejes y título
        xaxis = dict(   tickformat="%Y-%m",  # Formato de fecha para mostrar año y mes
                        tickangle=45
                        )  # Ángulo para evitar solapamiento de fechas)
    )

    return fig


def plot_time_series_2(data_ad, uen, canal2, regional, marquilla, producto):
    data_ad['Año'] = data_ad["Año"].astype(int)
    data_ad['Mes'] = data_ad["Mes"].astype(int)
    data_ad['Dia'] = 1
    data_ad['Fecha'] = pd.to_datetime(data_ad['Año'].astype(str) + '-' + data_ad['Mes'].astype(str) + '-' + data_ad['Dia'].astype(str))
    data_ad = data_ad[(data_ad['Uen'].isin(uen)) & (data_ad['Canal Comercial'].isin(canal2)) & (data_ad['Regional'].isin(regional)) & 
                      (data_ad['Marquilla'].isin(marquilla)) & (data_ad['Producto'].isin(producto))]
    serie_margen = data_ad.groupby('Fecha')['Margen'].mean().reset_index()

    fig = go.Figure(
        data=[
            go.Scatter(
                x=serie_margen['Fecha'],
                y=serie_margen['Margen']*100,
                mode = 'lines+markers',
                line=dict(color="#3498db"),
                name="Margen por Fecha"
            )
        ]
    )

    # Configuración del diseño del gráfico
    fig.update_layout(
        title="Histórico del Margen",
        xaxis_title="Fecha",
        yaxis_title="% Margen",
        paper_bgcolor="rgba(0,0,0,0)",  # Fondo transparente (usa color hexadecimal si prefieres)
        plot_bgcolor="#E8E8E8",  # Fondo del área de la gráfica
        font=dict(color="#FFFFFF"),  # Color de texto de los ejes y título
        xaxis = dict(   tickformat="%Y-%m",  # Formato de fecha para mostrar año y mes
                        tickangle=45
                        )  # Ángulo para evitar solapamiento de fechas)
    )

    return fig

def plot_time_series_predict(data_ad, datos_prediccion, uen_p, regional_p, canal, marq_p, codigo_p, producto_p):
    data_ad['Año'] = data_ad["Año"].astype(int)
    data_ad['Mes'] = data_ad["Mes"].astype(int)
    data_ad['Dia'] = 1
    data_ad['Fecha'] = pd.to_datetime(data_ad['Año'].astype(str) + '-' + data_ad['Mes'].astype(str) + '-' + data_ad['Dia'].astype(str))
    data_ad = data_ad[(data_ad['Uen'] == uen_p) & (data_ad['Canal Comercial'] == canal) & (data_ad['Regional'] == regional_p) & 
                      (data_ad['Marquilla'] == marq_p) & (data_ad['Producto'] == producto_p) & (data_ad['Código Producto'] == codigo_p)]
    serie_ventas = data_ad.groupby('Fecha')['Ventas'].sum().reset_index()

    # Manejar el caso de datos vacíos
    if data_ad.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No hay datos para la combinación de campos ingresada!",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#E8E8E8",
            font=dict(color="#FFFFFF"), 
        )
        return fig

    fig = go.Figure(
        data=[
            go.Scatter(
                x=serie_ventas['Fecha'],
                y=serie_ventas['Ventas'],
                mode = 'lines+markers',
                line=dict(color="#3498db"),
                name="Ventas por Fecha"
            )
        ]
    )

    # Agregar predicción si está disponible
    if not datos_prediccion.empty:
        datos_prediccion['Año'] = datos_prediccion["Año"].astype(int)
        datos_prediccion['Mes'] = datos_prediccion["Mes"].astype(int)
        datos_prediccion['Dia'] = 1
        datos_prediccion['Fecha'] = pd.to_datetime(datos_prediccion['Año'].astype(str) + '-' + datos_prediccion['Mes'].astype(str) + '-' + datos_prediccion['Dia'].astype(str))
        ultimo_hist = serie_ventas.iloc[-1]

        datos_prediccion = pd.concat([
            pd.DataFrame({'Fecha': [ultimo_hist['Fecha']], 'Ventas': [ultimo_hist['Ventas']]}),
            datos_prediccion
        ]).reset_index(drop=True)

        fig.add_trace(
            go.Scatter(
                x=datos_prediccion['Fecha'],
                y=datos_prediccion['Ventas'],
                mode='lines',
                line=dict(color="#e74c3c", dash='dot'),
                name="Predicción"
            )
        )

    # Configuración del diseño del gráfico
    fig.update_layout(
        title="Pronóstico de Ventas COP",
        xaxis_title="Fecha",
        yaxis_title="Ventas COP",
        paper_bgcolor="rgba(0,0,0,0)",  # Fondo transparente (usa color hexadecimal si prefieres)
        plot_bgcolor="#E8E8E8",  # Fondo del área de la gráfica
        font=dict(color="#FFFFFF"),  # Color de texto de los ejes y título
        xaxis = dict(   tickformat="%Y-%m",  # Formato de fecha para mostrar año y mes
                        tickangle=45
                        )  # Ángulo para evitar solapamiento de fechas)
    )

    return fig

app.layout = html.Div(
    id="app-container",

    children=[
        #dcc.Interval(id="interval", interval=1000, n_intervals=0),

        html.Div(
            id="brand-section",
            style={
                "display": "flex",
                "justify-content": "space-between",  # Para alinear la imagen a la izquierda y el título a la derecha
                "align-items": "center",
                "padding": "5px 20px",  # Padding para dar espacio
                "background-color": "#2c3e50",  # Color de fondo, puedes cambiarlo
            },
            children=[
                # Imagen del Brand (logo)
                html.Img(
                    src="/assets/logo.png",  # Asegúrate de tener la imagen en la carpeta 'assets'
                    style={"height": "150px", "width": "auto"}  # Ajusta el tamaño de la imagen
                ),
                
                # Título del Brand
                html.H1(
                    "Tablero de Seguimiento de Ventas y Utilidades",  # Título que deseas mostrar
                    style={
                        "color": "#ecf0f1",  # Color de texto
                        "font-size": "30px",  # Tamaño de la fuente
                        "font-weight": "bold",  # Negrita
                        "margin": "0",  # Eliminar márgenes
                    }
                ),
            ],
        ),

        # Sección 1 - Filtros
        html.Div(
            id="section-1",
            # style={
            #     "backgroundColor": "#E10110",  # Cambia este valor al color que prefieras
            #     "color": "#FFFFFF",  # Color del texto en la página para que contraste con el fondo
            #     "padding": "10px",   # Espaciado interno opcional
            # },
            children=[
                # Título de la sección de gráficos
                html.H2(
                    "KPIs",  # Cambia este texto al título que desees
                    style={
                        "textAlign": "center",
                        "marginBottom": "20px",
                        "color": "#FFFFFF",  # Puedes cambiar el color si lo deseas
                    }
                ),
                
                # First row with two side-by-side graphs
                html.Div(
                    className="row",
                    children=[
                        # First graph on the left
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
                        # Second graph on the right
                        html.Div(
                            className="nine columns",    
                            #style={"display": "flex"},
                            children=[
                                html.Div(
                                    id="kpi-container",
                                    children = generate_KPI(data_ad)
                                ),                            
                                html.Hr(),

                                html.Div(
                                    className="twelve columns",
                                    children=[
                                        html.Div(
                                            className="six columns",
                                            children =[dcc.Graph(
                                                id = 'plot_time_series_1',
                                                #figure = plot_time_series_1(data_ad)
                                            )
                                            ]
                                        ),

                                        html.Div(
                                            className="six columns",
                                            children =[dcc.Graph(
                                                id = 'plot_time_series_2',
                                                #figure = plot_time_series_2(data_ad)
                                            )
                                            ]
                                        )

                                    ]

                                )  



                            ],
                        ),
                    ],
                ),
            ],
        ),

        # Sección 2 - Análisis descriptivo de venta
        html.Div(
            id="section-2",
            className="twelve columns",
            # style={
            #     "backgroundColor": "#E10110",  # Cambia este valor al color que prefieras
            #     "color": "#FFFFFF",  # Color del texto en la página para que contraste con el fondo
            #     "padding": "10px",   # Espaciado interno opcional
            # },
            children=[
                # Título de la sección de gráficos
                html.H2(
                    "Análisis descriptivo",  # Cambia este texto al título que desees
                    style={
                        "textAlign": "center",
                        "marginBottom": "20px",
                        "color": "#FFFFFF",  # Puedes cambiar el color si lo deseas
                    }
                ),
                
                # First row with two side-by-side graphs
                html.Div(
                    className="row",
                    children=[
                        # First graph on the left
                        html.Div(
                            className="six columns",
                            children=[
                                #html.B("Ventas por Canal Comercial"),
                                html.Hr(),
                                dcc.Graph(id="plot_series_1"),
                            ],
                        ),
                        # Second graph on the right
                        html.Div(
                            className="six columns",
                            children=[
                                #html.B("Ventas por Marquilla"),
                                html.Hr(),
                                dcc.Graph(id="plot_series_2"),
                            ],
                        ),
                    ],
                ),

                # Second row with a single centered graph
                html.Div(
                    className="row",
                    style={"display": "flex", "justify-content": "center", "margin-top": "20px"},
                    children=[
                        html.Div(
                            style={"width": "70%"},
                            children=[
                                #html.B("Distribución de Ventas por Unidad de Negocio UEN"),
                                html.Hr(),
                                dcc.Graph(id="plot_series_3"),
                            ],
                        ),
                    ],
                ),
            ],
        ),

        # Sección 3 - Gráfica de análisis predictivo
        html.Div(
            id="section-3",
            # style={
            #     "backgroundColor": "#E10110",  # Cambia este valor al color que prefieras
            #     "color": "#FFFFFF",  # Color del texto en la página para que contraste con el fondo
            #     "padding": "10px",   # Espaciado interno opcional
            # },
            children=[
                # Título de la sección de gráficos
                html.H2(
                    "Análisis predictivo",  # Cambia este texto al título que desees
                    style={
                        "textAlign": "center",
                        "marginBottom": "20px",
                        "color": "#FFFFFF",  # Puedes cambiar el color si lo deseas
                    }
                ),
                
                # First row with two side-by-side graphs
                html.Div(
                    className="row",
                    children=[
                        # First graph on the left
                        html.Div(
                            className="four columns",
                            style={"display": "flex", "justify-content": "center", "align-items": "center", 'height': '70vh'},
                            children=[generate_control_card()]
                            + [
                                html.Div(
                                    ["initial child"], id="output-clientside2", style={"display": "none"}
                                )
                            ],
                        ),
                        # Second graph on the right
                        html.Div(
                            className="eight columns",
                            children=[
                                html.Hr(),
                                dcc.Graph(id="plot_series_5"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)



@app.callback(
    [Output(component_id="plot_series_1", component_property="figure"),
     Output(component_id="plot_series_2", component_property="figure"),
     Output(component_id="plot_series_3", component_property="figure"),
     Output(component_id="plot_series_5", component_property="figure"),
     Output(component_id="plot_time_series_1", component_property="figure"),
     Output(component_id="plot_time_series_2", component_property="figure"),
     Output("kpi-container", "children")],
    [#Input("interval", "n_intervals"),
     Input(component_id="canal-prediccion", component_property="value"),
     Input(component_id="anio-dropdown", component_property="value"),
     Input(component_id="mes-dropdown", component_property="value"),
     Input(component_id="uen-dropdown", component_property="value"),
     Input(component_id="canal2-dropdown", component_property="value"),
     Input(component_id="regional-dropdown", component_property="value"),
     Input(component_id="marquilla-dropdown", component_property="value"),
     Input(component_id="producto-dropdown", component_property="value"),
     Input(component_id="uen-prediccion", component_property="value"),
     Input(component_id="regional-prediccion", component_property="value"),
     Input(component_id="marquilla-prediccion", component_property="value"),
     Input(component_id="codigo-prediccion", component_property="value"),
     Input(component_id="producto-prediccion", component_property="value"),
     Input(component_id="meses-prediccion", component_property="value")
     ]
)
def update_output_div(canal, anio, mes, uen, canal2, regional, marquilla, producto, uen_p, regional_p, marq_p, codigo_p, producto_p, meses_p):

    print(uen)
    fig1 = plot_bar_1(data_ad)   
    fig2 = plot_bar_2(data_ad)  
    fig3 = plot_pie_chart(data_ad)
    fig5 = plot_time_series_1(data_ad, uen, canal2, regional, marquilla, producto)
    fig6 = plot_time_series_2(data_ad, uen, canal2, regional, marquilla, producto)

    filtered_data = data_ad[(data_ad['Uen'].isin(uen)) & (data_ad['Canal Comercial'].isin(canal2)) & (data_ad['Regional'].isin(regional)) & 
                      (data_ad['Marquilla'].isin(marquilla)) & (data_ad['Producto'].isin(producto)) & (data_ad['Año'].isin(anio)) & 
                      (data_ad['Mes'].isin(mes))]
    
    datos_prediccion = pd.DataFrame()

    if ((meses_p is not None) & (uen_p is not None) & (regional_p is not None) &
        (canal is not None) & (marq_p is not None) & (codigo_p is not None) & (producto_p is not None)):
        myreq = {
            
                "meses_a_proyectar": int(meses_p),
                "Uen": str(uen_p),
                "Regional": str(regional_p),
                "Canal_Comercial": str(canal),
                "Marquilla": str(marq_p),
                "Codigo_Producto": str(codigo_p),
                "Producto": str(producto_p)
        }
        headers =  {"Content-Type":"application/json", "accept": "application/json"}

        # POST call to the API
        response = requests.post(api_url, data=json.dumps(myreq), headers=headers)

        if response.status_code == 200:
            data = response.json()
            logger.info("Response: {}".format(data))

            datos_prediccion = pd.DataFrame(data['result'])
            datos_prediccion.iloc[0,1] = datos_prediccion.iloc[0,1] - 1

    fig4 = plot_time_series_predict(data_ad, datos_prediccion, uen_p, regional_p, canal, marq_p, codigo_p, producto_p)

    return fig1, fig2, fig3, fig4, fig5, fig6, generate_KPI(filtered_data)


# Run the server
if __name__ == "__main__":
    logger.info("Running dash")
    app.run_server(host="0.0.0.0",debug=True)
