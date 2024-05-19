import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
import matplotlib.colorbar as colorbar
import numpy as np

# Ruta al archivo CSV
csv_path = '/Users/freddypeaz/Desktop/geodata/geodata_mx/data_tinsa/geoloc_tinsa_mx.csv'

# Cargar los datos
data = pd.read_csv(csv_path)

# Convertir las columnas relevantes a cadenas, remover comas y luego convertir a numérico
columns_to_convert = ['STOCK_DISPONIBLE', 'TICKET', 'PRECIO_M2', 'AREA', 'STOCK_INICIAL', 'VENTAS_PERIODO',
                      'ABS_PERIODO', 'ABS_PARCIAL_PERIODO', 'ABS_ACUMULADA_TOTAL']

for column in columns_to_convert:
    data[column] = data[column].astype(str).str.replace(',', '')
    data[column] = pd.to_numeric(data[column], errors='coerce')

# Filtrar las columnas necesarias
data = data[['LAT', 'LON', 'NOMBRE_PROYECTO', 'DESARROLLADOR', 'YEAR', 'ESTADO', 'ALCALDIA', 'COLONIA', 'SEGMENTO',
             'ROOMS', 'BATH', 'GARAGE', 'MESES_EN_VENTA', 'TICKET', 'PRECIO_M2', 'AREA', 'STOCK_INICIAL', 'STOCK_DISPONIBLE',
             'VENTAS_PERIODO', 'ABS_PERIODO', 'ABS_PARCIAL_PERIODO', 'ABS_ACUMULADA_TOTAL']]

# Filtrar registros con valores nulos, cero o menores a cero
data = data.dropna(subset=columns_to_convert)
data = data[(data[columns_to_convert] > 0).all(axis=1)]

# Añadir un control deslizante en la barra lateral para seleccionar el año
st.sidebar.header("Filtrar por año")
selected_year = st.sidebar.slider("Año", int(data['YEAR'].min()), int(data['YEAR'].max()), int(data['YEAR'].min()))

# Filtrar los datos según el año seleccionado
filtered_data = data[data['YEAR'] == selected_year]

# Añadir un selectbox en la barra lateral para seleccionar la capa
st.sidebar.header("Seleccionar capa")
selected_layer = st.sidebar.selectbox(
    "Selecciona la capa a visualizar",
    ["STOCK_DISPONIBLE", "TICKET", "PRECIO_M2", "AREA", "STOCK_INICIAL", "VENTAS_PERIODO", "ABS_PERIODO", "ABS_PARCIAL_PERIODO", "ABS_ACUMULADA_TOTAL"]
)

# Coordenadas de la Colonia Roma, Ciudad de México
latitude_roma = 19.4194
longitude_roma = -99.1616

# Definir una escala de colores basada en el valor de la capa seleccionada
cmap = plt.get_cmap('RdBu_r')

def get_color(value, min_value, max_value, is_percentage=False):
    if is_percentage:
        norm_value = value / 100  # Normalizar porcentajes entre 0 y 1
    else:
        norm_value = (value - min_value) / (max_value - min_value)  # Normalizar el valor entre 0 y 1
    color = cmap(norm_value)
    return [int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255]  # Convertir de 0-1 a 0-255 y añadir transparencia

# Determinar si la capa seleccionada es un porcentaje
is_percentage = selected_layer in ["ABS_PERIODO", "ABS_PARCIAL_PERIODO", "ABS_ACUMULADA_TOTAL"]

# Obtener el rango de valores de la capa seleccionada usando los datos filtrados
min_value = filtered_data[selected_layer].min()
max_value = filtered_data[selected_layer].max()

# Verificar los valores mínimos y máximos
st.write(f"Min value for {selected_layer}: {min_value}")
st.write(f"Max value for {selected_layer}: {max_value}")

# Aplicar la escala de colores a los datos
filtered_data['color'] = filtered_data[selected_layer].apply(lambda x: get_color(x, min_value, max_value, is_percentage))

# Aplicar la escala de elevación a los datos
filtered_data['elevation'] = filtered_data[selected_layer].apply(lambda x: (x - min_value) / (max_value - min_value))

# Configurar la capa de puntos en PyDeck
layer = pdk.Layer(
    'HexagonLayer',
    data=filtered_data,
    get_position='[LON, LAT]',
    get_elevation='elevation',
    elevation_scale=500,  # Ajusta este valor según sea necesario para la altura de los hexágonos
    get_fill_color='color',
    coverage=0.95,  # Ajusta el tamaño relativo de los hexágonos
    opacity=0.5,    # Ajusta la transparencia de los hexágonos
    pickable=True,
    auto_highlight=True,
)

# Configurar el mapa en PyDeck
view_state = pdk.ViewState(
    latitude=latitude_roma,
    longitude=longitude_roma,
    zoom=10,
    bearing=0,
    pitch=45
)

# Crear el mapa en PyDeck
deck = pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=view_state,
    layers=[layer],
    tooltip={
        "html": """
        <b>Nombre del Proyecto:</b> {NOMBRE_PROYECTO}<br/>
        <b>Desarrollador:</b> {DESARROLLADOR}<br/>
        <b>Stock Inicial:</b> {STOCK_INICIAL}<br/>
        <b>Stock Disponible:</b> {STOCK_DISPONIBLE}<br/>
        """,
        "style": {
            "backgroundColor": "steelblue",
            "color": "white",
            "fontSize": "12px",  # Ajusta el tamaño del texto
            "padding": "10px"    # Ajusta el tamaño del tooltip
        }
    }
)

# Mostrar el mapa en Streamlit
st.title("Visualización de Datos Geoespaciales")
st.sidebar.write(f"Mostrando datos para el año: {selected_year}")
st.sidebar.write(f"Mostrando capa: {selected_layer}")
st.pydeck_chart(deck)

# Crear la barra de colores
fig, ax = plt.subplots(figsize=(4, 0.5))  # Ajusta el tamaño de la barra de colores
fig.subplots_adjust(bottom=0.3)

norm = plt.Normalize(vmin=min_value, vmax=max_value)
cb1 = colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='horizontal')

# Añadir etiquetas a la barra de colores
label = f'{selected_layer} {"(%)" if is_percentage else ""}'
cb1.set_label(label, fontsize=8)  # Ajusta el tamaño de la etiqueta

# Ajustar el tamaño de las etiquetas de los ticks
cb1.ax.tick_params(labelsize=8)

# Mostrar la barra de colores en Streamlit
st.pyplot(fig)
