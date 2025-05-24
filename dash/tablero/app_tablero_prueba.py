import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import openpyxl
import datetime as dt
import requests
import json
import os
from loguru import logger
import joblib
from datetime import datetime, timedelta
import warnings
import io
import base64
warnings.filterwarnings("ignore")

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Dashboard Template"

server = app.server

# Cargar datos de ejemplo (reemplaza con tus propios datos)
def load_historical_data():
    clientes = pd.read_excel('./DATOSCONTUGAS.xlsx', sheet_name=None)  # None carga todas las hojas
    # Inicializar una lista para cargar los dataframe
    df = []

    # Crear columna con el nombre del cliente
    for nombre_cliente, df_cliente in clientes.items():
        df_cliente['CLIENTE'] = nombre_cliente  # Agregar columna con nombre del cliente
        df.append(df_cliente)

    # Unir todos los DataFrames en uno solo
    df = pd.concat(df, ignore_index=True)

    df['anio'] = df['Fecha'].dt.year
    df['mes'] = df['Fecha'].dt.month
    df['dia'] = df['Fecha'].dt.day
    df['hora'] = df['Fecha'].dt.hour
    df['dia_semana'] = df['Fecha'].dt.dayofweek
    
    return df

# Cargar los nuevos datos
def load_new_data():
    clientes = pd.read_excel('./NUEVOS_DATOS_DETECCION.xlsx', sheet_name=None)  # None carga todas las hojas
    # Inicializar una lista para cargar los dataframe
    df = []

    # Crear columna con el nombre del cliente
    for nombre_cliente, df_cliente in clientes.items():
        df_cliente['CLIENTE'] = nombre_cliente  # Agregar columna con nombre del cliente
        df.append(df_cliente)

    # Unir todos los DataFrames en uno solo
    df = pd.concat(df, ignore_index=True)

    df['anio'] = df['Fecha'].dt.year
    df['mes'] = df['Fecha'].dt.month
    df['dia'] = df['Fecha'].dt.day
    df['hora'] = df['Fecha'].dt.hour
    df['dia_semana'] = df['Fecha'].dt.dayofweek
    
    return df

data_hist = load_historical_data()
data_new = load_new_data()
data = pd.concat([data_hist,data_new], ignore_index =True)

# Funciones para predicción y uso de los modelos
def cargar_recursos(cliente):
    """Carga modelo y escalador para un cliente específico"""
    try:
        # Cargar escalador
        scaler = joblib.load(f"./escaladores_cliente/scaler_{cliente}.pkl")
        
        # Cargar modelo
        model = joblib.load(f"./modelos_combinados/modelo_IF_{cliente}.pkl")
            
        return scaler, model
    except Exception as e:
        print(f"Error cargando recursos para {cliente}: {e}")
        return None, None

def escalar_variables(df):
    data_scaled = df.copy()
    clientes = list(data_scaled['CLIENTE'].unique())
    cols_to_scale = ['Presion', 'Temperatura', 'Volumen']

    for cliente in clientes:
        mask_cliente = data_scaled['CLIENTE'] == cliente
        scaler, _ = cargar_recursos(cliente)
        data_scaled.loc[mask_cliente, cols_to_scale] = scaler.transform(data_scaled.loc[mask_cliente, cols_to_scale])
        print(f"escalado cliente: {cliente}")

    return data_scaled


def predecir_anomalias(df):
    resultados_anomalias = pd.DataFrame()
    clientes = list(df['CLIENTE'].unique())
    clientes_if = {'CLIENTE15', 'CLIENTE18', 'CLIENTE13', 'CLIENTE10', 'CLIENTE9'}

    for cliente in clientes:
        df_cliente = df[df['CLIENTE'] == cliente].copy()
        _, modelo = cargar_recursos(cliente)

        if cliente in clientes_if:
            features = ['Presion', 'Temperatura', 'Volumen']
            df_cliente.rename(columns = {"Presion_resid": "Presion",
                              "Temperatura_resid": "Temperatura",
                              "Volumen_resid": "Volumen"},
                             inplace = True)
            df_cliente['anomalia'] = modelo.predict(df_cliente[features])
            df_cliente.rename(columns = {"Presion": "Presion_resid",
                              "Temperatura": "Temperatura_resid",
                              "Volumen": "Volumen_resid"},
                             inplace = True)
        else:
            features = ['Presion_resid', 'Volumen_resid', 'Temperatura_resid']
            df_cliente['anomalia'] = modelo.predict(df_cliente[features])

        resultados_anomalias = pd.concat([resultados_anomalias,df_cliente])   
        print(f"predicción realizada para cliente: {cliente}")

    return resultados_anomalias


def generate_filters():
    """
    :return: A Div dropdown lists for filters.
    """
    min_date = data['Fecha'].min()
    max_date = data['Fecha'].max()

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
                        id="componente-rango-fechas",
                        children=[
                            html.P("Rango_de_Fechas"),
                            dcc.DatePickerRange(
                                id='date-picker-range',
                                min_date_allowed=min_date,
                                max_date_allowed=max_date,
                                initial_visible_month=min_date,
                                start_date=min_date,
                                end_date=max_date,
                                display_format='YYYY-MM-DD',
                                style={'width': '100%', 'color': '#333'}
                            )
                        ],
                        style=dict(width='30%', marginBottom='15px')
                    ),

                    html.Div(
                        id="componente-horario",
                        children=[
                            html.P("Rango_Horario"),
                            dcc.Dropdown(
                                id="horario-dropdown",
                                options=[{'label': hora, 'value': hora} for hora in data['hora'].unique()],
                                placeholder="Seleccione un horario",
                                value=[data['hora'].unique()[0]],
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
                                options=[{'label': cliente, 'value': cliente} for cliente in data['CLIENTE'].unique()],
                                placeholder="Seleccione un cliente",
                                value=[data['CLIENTE'].unique()[0]],
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

def generate_client_filter():
    """
    :return: A Div dropdown lists for filters.
    """

    return html.Div(
        id="filters-2",
        children=[
            # Canal
            html.H2("Filtro para visualización de anomalías",style={
                        "textAlign": "Left",
                        "marginBottom": "20px",
                        "color": "#FFFFFF",  # Puedes cambiar el color si lo deseas
                    }),
            html.Div(
                id="componentes-filtros-2",
                children=[
                    html.Div(
                        id="componente-cliente-2",
                        children=[
                            html.P("Cliente"),
                            dcc.Dropdown(
                                id="cliente-dropdown-anomaly",
                                options=[{'label': cliente, 'value': cliente} for cliente in data['CLIENTE'].unique()],
                                placeholder="Seleccione un cliente",
                                value=[data['CLIENTE'].unique()[0]],
                                multi = False,
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

def generate_KPI(data, start_date, end_date, horario, cliente):
    """
    Función para generar 6 KPIs, organizados en 2 filas (3 KPIs por fila).
    :return: Una lista de Divs que representan los 6 KPIs.
    """
    data_ad = data[(data['Fecha'] >= start_date) & (data['Fecha'] <= end_date)]
    data_ad = data_ad[(data_ad['hora'].isin(horario)) & (data_ad['CLIENTE'].isin(cliente))]

    # Valores de ejemplo para los KPIs
    volumen_promedio = data_ad['Volumen'].mean()
    presion_promedio = data_ad['Presion'].mean()
    temperatura_promedio = data_ad['Temperatura'].mean()
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
def generar_alertas(data_new):
    data_new['Presion_orig'] = data_new['Presion']
    data_new['Temperatura_orig'] = data_new['Temperatura']
    data_new['Volumen_orig'] = data_new['Volumen']
    data_scaled = escalar_variables(data_new)
    data_scaled.rename(columns = {"Presion": "Presion_resid",
                              "Temperatura": "Temperatura_resid",
                              "Volumen": "Volumen_resid"},
                             inplace = True)
    
    resultados = predecir_anomalias(data_scaled)

    anomalias = resultados[resultados['anomalia'] == -1]
    ultimas_anomalias = anomalias.sort_values('Fecha').groupby('CLIENTE').last().reset_index()
    alertas = []

    for idx, row in ultimas_anomalias.iterrows():
        alertas.append({
            "tipo": f"Advertencia {row['CLIENTE']}",
            "mensaje": f"Anomalía detectada en {row['Fecha']} (Vol: {row['Volumen_orig']:.2f}, Pres: {row['Presion_orig']:.2f}, Temp: {row['Temperatura_orig']:.2f})",
            "color": "#d74d1f", 
            "icono": "⚠️",  # Icono diferente
            "timestamp": f"{row['Fecha']}"
        })
    
    # Ordenar alertas por timestamp (más reciente primero)
    alertas.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return  alertas[:20], resultados # Solo las 20 más recientes

def plot_time_series_anomalies_volumen(df, cliente):

    cliente_serie = df[df['CLIENTE']==cliente][['Fecha','Volumen_orig','anomalia']].set_index('Fecha')

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=cliente_serie.index,
            y=cliente_serie['Volumen_orig'],
            mode='lines',
            name='Volumen',
            line=dict(color='blue')
        )
    )

    anomalias = cliente_serie[cliente_serie['anomalia'] == -1]
    fig.add_trace(
        go.Scatter(
            x=anomalias.index,
            y=anomalias['Volumen_orig'],
            mode='markers',
            name='Anomalías',
            marker=dict(color='red', size=8)
        )
    )

    fig.update_layout(
        title=f'Anomalías detectadas - {cliente} - Variable Volumen',
        xaxis_title='Fecha',
        yaxis_title='Volumen',
        legend_title='Leyenda',
        hovermode='x unified'
    )


    return fig

def plot_time_series_anomalies_temperatura(df, cliente):

    cliente_serie = df[df['CLIENTE']==cliente][['Fecha','Temperatura_orig','anomalia']].set_index('Fecha')

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=cliente_serie.index,
            y=cliente_serie['Temperatura_orig'],
            mode='lines',
            name='Temperatura',
            line=dict(color='blue')
        )
    )

    anomalias = cliente_serie[cliente_serie['anomalia'] == -1]
    fig.add_trace(
        go.Scatter(
            x=anomalias.index,
            y=anomalias['Temperatura_orig'],
            mode='markers',
            name='Anomalías',
            marker=dict(color='red', size=8)
        )
    )

    fig.update_layout(
        title=f'Anomalías detectadas - {cliente} - Variable Temperatura',
        xaxis_title='Fecha',
        yaxis_title='Temperatura',
        legend_title='Leyenda',
        hovermode='x unified'
    )


    return fig

def plot_time_series_anomalies_presion(df, cliente):

    cliente_serie = df[df['CLIENTE']==cliente][['Fecha','Presion_orig','anomalia']].set_index('Fecha')

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=cliente_serie.index,
            y=cliente_serie['Presion_orig'],
            mode='lines',
            name='Presión',
            line=dict(color='blue')
        )
    )

    anomalias = cliente_serie[cliente_serie['anomalia'] == -1]
    fig.add_trace(
        go.Scatter(
            x=anomalias.index,
            y=anomalias['Presion_orig'],
            mode='markers',
            name='Anomalías',
            marker=dict(color='red', size=8)
        )
    )

    fig.update_layout(
        title=f'Anomalías detectadas - {cliente} - Variable Presión',
        xaxis_title='Fecha',
        yaxis_title='Presión',
        legend_title='Leyenda',
        hovermode='x unified'
    )


    return fig
    

def plot_time_series_volumen(data, start_date, end_date, horario, cliente):

    data_ad = data[(data['Fecha'] >= start_date) & (data['Fecha'] <= end_date)]
    data_ad = data_ad[(data_ad['hora'].isin(horario)) & (data_ad['CLIENTE'].isin(cliente))]
    serie_volumen = data_ad.groupby('Fecha')['Volumen'].sum().reset_index()

    fig = go.Figure(
        data=[
            go.Scatter(
                x=serie_volumen['Fecha'],
                y=serie_volumen['Volumen'],
                mode = 'lines+markers',
                line=dict(color="#3498db"),
                name="Volumen por Fecha"
            )
        ]
    )

    # Configuración del diseño del gráfico
    fig.update_layout(
        title="Histórico de Volumen m3",
        xaxis_title="Fecha",
        yaxis_title="Volumen m3",
        paper_bgcolor="rgba(0,0,0,0)",  # Fondo transparente (usa color hexadecimal si prefieres)
        plot_bgcolor="#E8E8E8",  # Fondo del área de la gráfica
        font=dict(color="#FFFFFF"),  # Color de texto de los ejes y título
        xaxis = dict(   tickformat="%Y-%m",  # Formato de fecha para mostrar año y mes
                        tickangle=45
                        )  # Ángulo para evitar solapamiento de fechas)
    )

    return fig

def plot_time_series_temperatura(data, start_date, end_date, horario, cliente):

    data_ad = data[(data['Fecha'] >= start_date) & (data['Fecha'] <= end_date)]
    data_ad = data_ad[(data_ad['hora'].isin(horario)) & (data_ad['CLIENTE'].isin(cliente))]
    serie_temperatura = data_ad.groupby('Fecha')['Temperatura'].sum().reset_index()

    fig = go.Figure(
        data=[
            go.Scatter(
                x=serie_temperatura['Fecha'],
                y=serie_temperatura['Temperatura'],
                mode = 'lines+markers',
                line=dict(color="#3498db"),
                name="Temperatura por Fecha"
            )
        ]
    )

    # Configuración del diseño del gráfico
    fig.update_layout(
        title="Histórico de Temperatura m3",
        xaxis_title="Fecha",
        yaxis_title="Temperatura m3",
        paper_bgcolor="rgba(0,0,0,0)",  # Fondo transparente (usa color hexadecimal si prefieres)
        plot_bgcolor="#E8E8E8",  # Fondo del área de la gráfica
        font=dict(color="#FFFFFF"),  # Color de texto de los ejes y título
        xaxis = dict(   tickformat="%Y-%m",  # Formato de fecha para mostrar año y mes
                        tickangle=45
                        )  # Ángulo para evitar solapamiento de fechas)
    )

    return fig

def plot_time_series_presion(data, start_date, end_date, horario, cliente):

    data_ad = data[(data['Fecha'] >= start_date) & (data['Fecha'] <= end_date)]
    data_ad = data_ad[(data_ad['hora'].isin(horario)) & (data_ad['CLIENTE'].isin(cliente))]
    serie_presion = data_ad.groupby('Fecha')['Presion'].sum().reset_index()

    fig = go.Figure(
        data=[
            go.Scatter(
                x=serie_presion['Fecha'],
                y=serie_presion['Presion'],
                mode = 'lines+markers',
                line=dict(color="#3498db"),
                name="Presion por Fecha"
            )
        ]
    )

    # Configuración del diseño del gráfico
    fig.update_layout(
        title="Histórico de Presión m3",
        xaxis_title="Fecha",
        yaxis_title="Presión m3",
        paper_bgcolor="rgba(0,0,0,0)",  # Fondo transparente (usa color hexadecimal si prefieres)
        plot_bgcolor="#E8E8E8",  # Fondo del área de la gráfica
        font=dict(color="#FFFFFF"),  # Color de texto de los ejes y título
        xaxis = dict(   tickformat="%Y-%m",  # Formato de fecha para mostrar año y mes
                        tickangle=45
                        )  # Ángulo para evitar solapamiento de fechas)
    )

    return fig

def plot_bar_volumen_ultimos_7d(data):

    fecha_max = max(data['Fecha'])
    fecha_inicio = fecha_max - pd.Timedelta(days=7)

    data_reciente = data[data['Fecha'] >= fecha_inicio]
    promedios = data_reciente.groupby('CLIENTE')['Volumen'].mean().reset_index()
    promedios['num_cliente'] = promedios['CLIENTE'].str.extract('(\d+)').astype(int)
    promedios = promedios.sort_values('num_cliente')
    
    # Crear gráfico de barras
    fig = go.Figure(
        data=[
            go.Bar(
                x=promedios['CLIENTE'],
                y=promedios['Volumen'],
                marker_color="#3498db",
                text=promedios['Volumen'].round(2),
                textposition='auto',
                name='Promedio 7d'
            )
        ]
    )
    
    # Configuración del diseño
    fig.update_layout(
        title={
            'text': "Promedio de Volumen (Últimos 7 días) por Cliente",
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=16, color="#FFFFFF")  # Opcional: estilo de fuente
        },
        xaxis_title="Cliente",
        yaxis_title="Volumen Promedio",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#E8E8E8",
        font=dict(color="#FFFFFF"),
        xaxis=dict(tickangle=45),
        hovermode="x"
    )
    
    return fig

def plot_bar_temperatura_ultimos_7d(data):

    fecha_max = max(data['Fecha'])
    fecha_inicio = fecha_max - pd.Timedelta(days=7)

    data_reciente = data[data['Fecha'] >= fecha_inicio]
    promedios = data_reciente.groupby('CLIENTE')['Temperatura'].mean().reset_index()
    promedios['num_cliente'] = promedios['CLIENTE'].str.extract('(\d+)').astype(int)
    promedios = promedios.sort_values('num_cliente')
    
    # Crear gráfico de barras
    fig = go.Figure(
        data=[
            go.Bar(
                x=promedios['CLIENTE'],
                y=promedios['Temperatura'],
                marker_color="#3498db",
                text=promedios['Temperatura'].round(2),
                textposition='auto',
                name='Promedio 7d'
            )
        ]
    )
    
    # Configuración del diseño
    fig.update_layout(
        title={
            'text': "Promedio de Temperatura (Últimos 7 días) por Cliente",
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=16, color="#FFFFFF")  # Opcional: estilo de fuente
        },
        xaxis_title="Cliente",
        yaxis_title="Temperatura Promedio",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#E8E8E8",
        font=dict(color="#FFFFFF"),
        xaxis=dict(tickangle=45),
        hovermode="x"
    )
    
    return fig

def plot_bar_presion_ultimos_7d(data):

    fecha_max = max(data['Fecha'])
    fecha_inicio = fecha_max - pd.Timedelta(days=7)

    data_reciente = data[data['Fecha'] >= fecha_inicio]
    promedios = data_reciente.groupby('CLIENTE')['Presion'].mean().reset_index()
    promedios['num_cliente'] = promedios['CLIENTE'].str.extract('(\d+)').astype(int)
    promedios = promedios.sort_values('num_cliente')
    
    # Crear gráfico de barras
    fig = go.Figure(
        data=[
            go.Bar(
                x=promedios['CLIENTE'],
                y=promedios['Presion'],
                marker_color="#3498db",
                text=promedios['Presion'].round(2),
                textposition='auto',
                name='Promedio 7d'
            )
        ]
    )
    
    # Configuración del diseño
    fig.update_layout(
        title={
            'text': "Promedio de Presión (Últimos 7 días) por Cliente",
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=16, color="#FFFFFF")  # Opcional: estilo de fuente
        },
        xaxis_title="Cliente",
        yaxis_title="Presión Promedio",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#E8E8E8",
        font=dict(color="#FFFFFF"),
        xaxis=dict(tickangle=45),
        hovermode="x"
    )
    
    return fig

# Layout del dashboard
app.layout = html.Div(
    id="app-container",
    children=[
    #dcc.Interval(id="interval", interval=1000, n_intervals=0),

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
                                    id="kpi-container"
                                    #children = generate_KPI()
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
                    children=[
                        # Filtros
                        html.Div(
                            className="three columns",
                            style={"display": "flex", "justify-content": "center", "align-items": "center", 'height': '70vh'},
                            children=[generate_client_filter()]
                            + [
                                html.Div(
                                    ["initial child 2"], id="output-clientside-2", style={"display": "none"}
                                )
                            ],
                        ),
                        
                        # KPIs y gráficos
                        html.Div(
                            className="nine columns",
                            children=[
                                # Gráficos de series de tiempo
                                html.Div(
                                    className="twelve columns",
                                    children=[
                                        html.Div(
                                            className="six columns",
                                            children=[dcc.Graph(id='plot_anomalias_1')]
                                        ),
                                        html.Div(
                                            className="six columns",
                                            children=[dcc.Graph(id='plot_anomalias_2')]
                                        )
                                    ]
                                ),
                                html.Div(
                                    className="twelve columns",
                                    style={"display": "flex", "justify-content": "center", "margin-top": "20px"},
                                    children=[
                                        html.Div(
                                            style={"width": "60%"},
                                            children=[dcc.Graph(id="plot_anomalias_3")]
                                        )
                                    ]
                                )
                            ]
                        ),
                    ]
                )
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
        ),
        # Sección para cargar archivo Excel con la info de 20 cientes para la detección de anomalías
        html.Div(
            id="upload-section",
            style={
                "textAlign": "center",
                "padding": "20px",
                "backgroundColor": "#2c3e50",
                "color": "#ecf0f1"
            },
            children=[
                html.H4("Cargar archivo Excel (.xlsx)"),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Arrastra y suelta o ',
                        html.A('selecciona un archivo Excel')
                    ]),
                    style={
                        'width': '60%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': 'auto',
                        'color': '#FFFFFF'
                    },
                    accept='.xlsx',
                    multiple=False
                ),
                html.Div(id='output-data-upload')
            ]
        ),


        # Sección para descargar archivo Excel con la info de consumo de los 20 clientes
        html.Div(
            id="download-section",
            style={
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
                "justifyContent": "flex-start",  # Cambiado de center a flex-start
                "padding": "20px",
                "backgroundColor": "#2c3e50",
                "color": "#ecf0f1",
                "textAlign": "center",
                "minHeight": "300px"  # Asegura altura suficiente
            },
            children=[
                html.H4("Descargar Datos de Consumo"),
                html.Button(
                    "Descargar Excel",
                    id="btn-download-excel",
                    style={
                        "color": "#ffffff",
                        "backgroundColor": "#2980b9",
                        "border": "none",
                        "padding": "10px 20px",
                        "fontSize": "16px",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "marginBottom": "15px"  # Esto evita que se corte abajo
                    }
                ),
                html.Div(id="status-msg", style={
                    "color": "#ffcc00",
                    "marginTop": "10px",
                    "fontWeight": "bold",
                    "fontSize": "16px"
                }),
                dcc.Download(id="download-excel")
            ]
        )
    ]
)

@app.callback(
    [Output('alert-container', 'children'),
     Output(component_id="plot_anomalias_1", component_property="figure"),
     Output(component_id="plot_anomalias_2", component_property="figure"),
     Output(component_id="plot_anomalias_3", component_property="figure")],
    [Input('alert-interval', 'n_intervals'),
     Input(component_id="cliente-dropdown-anomaly", component_property="value")]
     #Input('datos-filtrados', 'data')]
)
def actualizar_alertas(n_intervals, cliente):
 
    # Generar nuevas alertas
    alertas, resultados = generar_alertas(data_new)
    
    # Generar elementos HTML para las alertas
    alertas_html = []
    for alerta in alertas:
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
    
    fig1 = plot_time_series_anomalies_volumen(resultados, cliente)
    fig2 = plot_time_series_anomalies_temperatura(resultados, cliente)
    fig3 = plot_time_series_anomalies_presion(resultados, cliente)
    
    return alertas_html, fig1, fig2, fig3
        
@app.callback(
    [Output(component_id="plot_time_series_1", component_property="figure"),
     Output(component_id="plot_time_series_2", component_property="figure"),
     Output(component_id="plot_time_series_3", component_property="figure"),
     Output(component_id="plot_series_1", component_property="figure"),
     Output(component_id="plot_series_2", component_property="figure"),
     Output(component_id="plot_series_3", component_property="figure"),
     Output(component_id="kpi-container", component_property="children")],
    [#Input("interval", "n_intervals"),
     Input(component_id='date-picker-range', component_property='start_date'),
     Input(component_id='date-picker-range', component_property='end_date'),
     Input(component_id="horario-dropdown", component_property="value"),
     Input(component_id="cliente-dropdown", component_property="value")
     ]
)




def update_output_div(start_date_str, end_date_str, horario, cliente):

    start_date = pd.to_datetime(start_date_str)
    end_date = pd.to_datetime(end_date_str)
    fig1 = plot_time_series_volumen(data, start_date, end_date, horario, cliente)
    fig2 = plot_time_series_temperatura(data, start_date, end_date, horario, cliente)
    fig3 = plot_time_series_presion(data, start_date, end_date, horario, cliente)
    fig4 = plot_bar_volumen_ultimos_7d(data)
    fig5 = plot_bar_temperatura_ultimos_7d(data)
    fig6 = plot_bar_presion_ultimos_7d(data)

    return fig1, fig2, fig3, fig4, fig5, fig6, generate_KPI(data, start_date, end_date, horario, cliente)



@app.callback( #Callback para manejar el cargue del archivo xlsx
    Output('output-data-upload', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(contents, filename):
    print("Callback ejecutado con archivo:", filename)
    if contents is not None:
        return parse_contents(contents, filename)
    return html.Div("Aún no se ha cargado ningún archivo.")


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if filename.endswith('.xlsx'):
            save_path = os.path.join(os.getcwd(), 'NUEVOS_DATOS_DETECCION.xlsx')
            with open(save_path, 'wb') as f:
                f.write(decoded)
            return html.Div([
                html.P(f"✅ Archivo '{filename}' cargado y guardado correctamente.")
            ])
        else:
            return html.Div([
                html.P("❌ Formato no válido. Solo se aceptan archivos .xlsx.")
            ])
    except Exception as e:
        return html.Div([
            html.P(f"❌ Error al guardar el archivo: {str(e)}")
        ])




@app.callback( #Callback para manejar la descarga del archivo xlsx con la info de consumo de los clientes
    Output("status-msg", "children", allow_duplicate=True),
    Input("btn-download-excel", "n_clicks"),
    prevent_initial_call=True
)
def mostrar_mensaje_cargando(n_clicks):
    return "⏳ Generando archivo..."




@app.callback(
    Output("download-excel", "data"),
    Output("status-msg", "children"),
    Input("btn-download-excel", "n_clicks"),
    prevent_initial_call=True
)
def generar_excel_por_cliente(n_clicks):
    print("⏳ Generando archivo...")

    output = io.BytesIO()
    clientes_unicos = sorted(data['CLIENTE'].unique())
    print(f"➡️ Procesando {len(clientes_unicos)} clientes")

    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for i, cliente in enumerate(clientes_unicos, start=1):
                nombre_hoja = f"CLIENTE{i}"
                df_cliente = data[data['CLIENTE'] == cliente]
                print(f"✍️ CLIENTE{i}: {len(df_cliente)} filas")
                df_cliente.to_excel(writer, sheet_name=nombre_hoja, index=False)

        output.seek(0)
        ahora = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"DatosConsumoClientes_{ahora}.xlsx"

        print(f"✅ Archivo generado: {filename}")

        # Al finalizar, borra el mensaje de estado en la app
        return dcc.send_bytes(output.read(), filename=filename), ""

    except Exception as e:
        error_msg = f"❌ Error al generar el archivo: {str(e)}"
        print(error_msg)
        return None, error_msg


    
    


if __name__ == "__main__":
    logger.info("Running dash")
    app.run_server(host="0.0.0.0",debug=True)