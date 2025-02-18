# -*- coding: utf-8 -*-
"""
@author: guzma
"""
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

import os

# Definir la ruta correcta
file_path_pronostico = "C:/UNAL_MINMINAS/Blackboard/Lectura_archivos/Valores_Pronosticados_Precipitacion_2025-2_Colombia.csv"
df_pronostico = pd.read_csv(file_path_pronostico, sep="\t")

file_path_probabilidades = "C:/UNAL_MINMINAS/Blackboard/Lectura_archivos/Probabilidades_Pronosticadas_Precipitacion_2025-2_Colombia.csv"
df_probabilidades = pd.read_csv(file_path_probabilidades, sep="\t")



# Filtrar valores de -999
df_pronostico = df_pronostico[df_pronostico["Pronostico"] != -999]
df_probabilidades = df_probabilidades[df_probabilidades["Porcentaje"] != -999]

# Definir escala de color global con valores bajos en azul y altos en rojo
color_scale_pronostico = "RdBu"

# Obtener los valores mínimo y máximo globales para la escala de colores del pronóstico
color_min_pronostico = df_pronostico["Pronostico"].min()
color_max_pronostico = df_pronostico["Pronostico"].max()

# Escalas de colores según el índice en la tabla de probabilidades
color_scales_probabilidad = {
    3: "Blues",  # Índice 3: Escala de azul claro a azul oscuro
    2: "Greens",  # Índice 2: Escala de verde claro a verde oscuro
    1: "Reds"  # Índice 1: Escala de rojo claro a rojo oscuro
}

# Inicializar Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # ✅ Render necesita esta línea

# Layout de la app
app.layout = html.Div([
    html.H1("\U0001F327️ Tablero de Pronóstico de Precipitación en Colombia", style={'text-align': 'center'}),
    dcc.Tabs(id="tabs", value='tab1', children=[
        dcc.Tab(label='Pronóstico de Precipitación', value='tab1'),
        dcc.Tab(label='Probabilidades de Precipitación', value='tab2')
    ]),
    html.Div(id='tab_content')
])

# Callback para actualizar el contenido de las pestañas
@app.callback(
    Output('tab_content', 'children'),
    [Input('tabs', 'value')]
)
def update_tab(tab):
    if tab == 'tab1':
        return html.Div([
            html.Label("Selecciona un filtro"),
            dcc.RadioItems(
                id="filtro_selector",
                options=[
                    {"label": "Región", "value": "Region_Homogenea"},
                    {"label": "Departamento", "value": "Departamento"},
                    {"label": "Municipio", "value": "Municipio"}
                ],
                value="Region_Homogenea",
                inline=True
            ),
            dcc.Dropdown(id="selector_filtro", clearable=False),
            dcc.Graph(id="mapa_precipitacion"),
            dcc.Graph(id="histograma_pronostico"),
            dcc.Graph(id="violin_precipitacion")

        ])
    elif tab == 'tab2':
        return html.Div([
            html.Label("Selecciona un filtro"),
            dcc.RadioItems(
                id="filtro_selector_probabilidades",
                options=[
                    {"label": "Región", "value": "Region_Homogenea"},
                    {"label": "Departamento", "value": "Departamento"},
                    {"label": "Municipio", "value": "Municipio"}
                ],
                value="Region_Homogenea",
                inline=True
            ),
            dcc.Dropdown(id="selector_filtro_probabilidades", clearable=False),
            dcc.Graph(id="mapa_probabilidades"),
            dcc.Graph(id="grafico_distribucion_probabilidades")
        ])

# Callback para actualizar opciones del filtro dinámico en Pronóstico
@app.callback(
    Output("selector_filtro", "options"),
    [Input("filtro_selector", "value")]
)
def update_dropdown_options_pronostico(filtro):
    opciones = sorted([{"label": val, "value": val} for val in df_pronostico[filtro].dropna().unique()], key=lambda x: x["label"])
    return [{"label": "Todas", "value": "Todas"}] + opciones

# Callback para actualizar opciones del filtro dinámico en Probabilidades
@app.callback(
    Output("selector_filtro_probabilidades", "options"),
    [Input("filtro_selector_probabilidades", "value")]
)
def update_dropdown_options_probabilidades(filtro):
    opciones = sorted([{"label": val, "value": val} for val in df_probabilidades[filtro].dropna().unique()], key=lambda x: x["label"])
    return [{"label": "Todas", "value": "Todas"}] + opciones

# Callback para actualizar el gráfico de pronóstico
@app.callback(
    [Output("mapa_precipitacion", "figure"), Output("histograma_pronostico", "figure"),Output("violin_precipitacion", "figure")],
    [Input("filtro_selector", "value"), Input("selector_filtro", "value")]
)
def update_pronostico(filtro, valor):
    df_filtrado = df_pronostico.copy()
    if valor and valor != "Todas":
        df_filtrado = df_filtrado[df_filtrado[filtro] == valor]
    
    if df_filtrado.empty:
        return px.scatter_mapbox(title="No hay datos disponibles"), px.histogram(), px.violin()

    # Mapa de pronóstico
    fig_mapa = px.scatter_mapbox(
        df_filtrado, lat="Latitud", lon="Longitud", size="Pronostico", color="Pronostico",
        hover_data=["Departamento", "Municipio", "Pronostico"],
        title=f"Pronóstico de Precipitación - {valor}",
        mapbox_style="carto-positron", zoom=5,
        color_continuous_scale=color_scale_pronostico,
        range_color=[color_min_pronostico, color_max_pronostico]
    )
    fig_mapa.update_layout(
        margin={"r":0, "t":40, "l":0, "b":0}, 
        height=700,
        coloraxis_colorbar=dict(title="Precipitación (mm)")  # <---- Se agregó aquí dentro de update_layout
    )

    # Histograma
    fig_hist = px.histogram(
        df_filtrado, x="Pronostico", nbins=20, histnorm='percent',
        title="Distribución de la Precipitación Pronosticada (%)",
        labels={"Pronostico": "Precipitación (mm)", "percent": "Porcentaje"}
    )

    # Gráfico de violines
    fig_violin = px.violin(
        df_filtrado, y="Pronostico", box=True, points="all",
        title="Distribución de Precipitación",
        labels={"Pronostico": "Precipitación (mm)"}
    )

    return fig_mapa, fig_hist, fig_violin


# Callback para actualizar el gráfico de probabilidades
# @app.callback(
#     Output("mapa_probabilidades", "figure"),
#     [Input("filtro_selector_probabilidades", "value"), Input("selector_filtro_probabilidades", "value")]
# )
# def update_probabilidades(filtro, valor):
#     df_filtrado = df_probabilidades.copy()
#     if valor and valor != "Todas":
#         df_filtrado = df_filtrado[df_filtrado[filtro] == valor]
    
#     if df_filtrado.empty:
#         return px.scatter_mapbox(title="No hay datos disponibles")

#     color_scale = df_filtrado["Indice"].map(color_scales_probabilidad).iloc[0] if not df_filtrado["Indice"].isna().all() else "Greys"

#     fig_mapa_prob = px.scatter_mapbox(
#         df_filtrado, lat="Latitud", lon="Longitud", size="Porcentaje", color="Porcentaje",
#         hover_data=df_probabilidades.columns,
#         title="Mapa de Probabilidades de Precipitación",
#         mapbox_style="carto-positron", zoom=5,
#         color_continuous_scale=color_scale
#     )
#     fig_mapa_prob.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=700)

#     return fig_mapa_prob
# Callback para actualizar el mapa de probabilidades y el gráfico de distribución de categorías
@app.callback(
    [Output("mapa_probabilidades", "figure"), Output("grafico_distribucion_probabilidades", "figure")],
    [Input("filtro_selector_probabilidades", "value"), Input("selector_filtro_probabilidades", "value")]
)
def update_probabilidades(filtro, valor):
    df_filtrado = df_probabilidades.copy()

    # Aplicar el filtro seleccionado
    if valor and valor != "Todas":
        df_filtrado = df_filtrado[df_filtrado[filtro] == valor]

    # Manejar caso de datos vacíos
    if df_filtrado.empty:
        return px.scatter_mapbox(title="No hay datos disponibles"), px.bar(title="No hay datos disponibles")
   
    # Agrupar por el filtro seleccionado y calcular los promedios por categoría
    df_grouped = df_filtrado.groupby(filtro).agg({
        "Inferior": "mean",
        "Normal": "mean",
        "Superior": "mean"
    }).reset_index()
    
    # Seleccionar escala de color adecuada según el índice
    color_scale = df_filtrado["Indice"].map(color_scales_probabilidad).iloc[0] if not df_filtrado["Indice"].isna().all() else "Greys"

    # 📌 Crear el mapa de probabilidades
    fig_mapa_prob = px.scatter_mapbox(
        df_filtrado, lat="Latitud", lon="Longitud", size="Porcentaje", color="Porcentaje",
        hover_data=df_probabilidades.columns,
        title="Mapa de Probabilidades de Precipitación",
        mapbox_style="carto-positron", zoom=5,
        color_continuous_scale=color_scale
    )
    # 📌 Asegurar que las probabilidades sumen 100%
    df_grouped["Total"] = df_grouped["Inferior"] + df_grouped["Normal"] + df_grouped["Superior"]
    df_grouped["Inferior"] = (df_grouped["Inferior"] / df_grouped["Total"]) * 100
    df_grouped["Normal"] = (df_grouped["Normal"] / df_grouped["Total"]) * 100
    df_grouped["Superior"] = (df_grouped["Superior"] / df_grouped["Total"]) * 100

    # Definir colores personalizados para cada categoría
    colores_personalizados = {
        "Inferior": "#DC143C",  # Rojo Carmesí
        "Normal": "#66CDAA",    # Verde Agua Marina
        "Superior": "#4682B4"   # Azul Acero
    }

    # Crear gráfico de barras apiladas con colores armoniosos
    fig_bar_prob = px.bar(
        df_grouped, 
        x=filtro,
        y=["Inferior", "Normal", "Superior"],  
        barmode="stack",  
        title=f"Distribución Promedio de Probabilidades por Categoría en {valor}",
        labels={"value": "Probabilidad (%)", "variable": "Categoría"},
        color_discrete_map=colores_personalizados  
    )

    fig_bar_prob.update_layout(
        xaxis_title=filtro,
        yaxis_title="Probabilidad (%)",
        height=500
    )
    
    return fig_mapa_prob, fig_bar_prob

# if __name__ == '__main__':
#     app.run_server(debug=True, host='127.0.0.1', port=8050)

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0')



# app = Dash(__name__)
# server = app.server



