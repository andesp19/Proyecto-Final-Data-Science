import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import seaborn as sns
import matplotlib.colors as mcolors
import json
import requests
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Obtener la fecha y hora actual
now = datetime.datetime.now()

#Formatear las fechas en el formato ISO8601 con zona horaria UTC
endtime = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
starttime = "2012-01-01T00:00:00+00:00"

# Definir los parámetros de consulta para cada país
chile_params = {
    "format": "geojson",
    "starttime": starttime,
    "endtime": endtime,
    "minlatitude": -56.8,
    "maxlatitude": -19.0,
    "minlongitude": -79.0,
    "maxlongitude": -69.9,
    "jsonerror": "true",
    "orderby": "time"
}

japan_params = {
    "format": "geojson",
    "starttime": starttime,
    "endtime": endtime,
    "minlatitude": 27.0,
    "maxlatitude": 44.0,
    "minlongitude": 132.78,
    "maxlongitude": 145.53,
    "jsonerror": "true",
    "orderby": "time"
}

usa_params = {
    "format": "geojson",
    "starttime": starttime,
    "endtime": endtime,
    "maxlatitude": 50,
    "minlatitude": 24.6,
    "maxlongitude": -65,
    "minlongitude": -125,
    "jsonerror": "true",
    "orderby": "time"
}

# Realizar las solicitudes a la API y guardar los datos en archivos GeoJSON
urls_params = [
    ("https://earthquake.usgs.gov/fdsnws/event/1/query", chile_params, "chile_earthquake_data_now.geojson"),
    ("https://earthquake.usgs.gov/fdsnws/event/1/query", japan_params, "japan_earthquake_data_now.geojson"),
    ("https://earthquake.usgs.gov/fdsnws/event/1/query", usa_params, "usa_earthquake_data_now.geojson")
]

for url, params, filename in urls_params:
    response = requests.get(url, params=params)

    if response.status_code == 200:
        # Si la solicitud fue exitosa, guardamos la respuesta en un archivo GeoJSON
        data = response.json()
        with open(filename, "w") as file:
            json.dump(data, file)
        print(f"Archivo GeoJSON de {filename.split('_')[0].capitalize()} descargado exitosamente.")
    else:
        print(f"Error al realizar la solicitud de {filename.split('_')[0].capitalize()}: {response.status_code}")
        

# Para ETL previo obtenemos los datos dentro de archivos .csv
# Juntamos los requests para obtener los datos de los tres paises que nos interesan a traves de la API

chile_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
chile_params = {
    "format": "csv",
    "starttime": starttime,
    "endtime": endtime,
    "minlatitude": -56.8,
    "maxlatitude": -19.0,
    "minlongitude": -79.0,
    "maxlongitude": -69.9,
    "jsonerror": "true",
    "orderby": "time-asc"
}

chile_response = requests.get(chile_url, params=chile_params)

if chile_response.status_code == 200:
    # Si la solicitud fue exitosa, guardamos la respuesta en un archivo CSV
    with open("chile_earthquake_data.csv", "w") as chile_file:
        chile_file.write(chile_response.text)
    print("Archivo CSV de Chile descargado exitosamente.")
else:
    print("Error al realizar la solicitud de Chile:", chile_response.status_code)

japan_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
japan_params = {
    "format": "csv",
    "starttime": starttime,
    "endtime": endtime,
    "minlatitude": 27.0,
    "maxlatitude": 44.0,
    "minlongitude": 132.78,
    "maxlongitude": 145.53,
    "jsonerror": "true",
    "orderby": "time-asc"
}

japan_response = requests.get(japan_url, params=japan_params)

if japan_response.status_code == 200:
    # Si la solicitud fue exitosa, guardamos la respuesta en un archivo CSV
    with open("japan_earthquake_data.csv", "w", encoding="utf-8") as japan_file:
        japan_file.write(japan_response.text)
    print("Archivo CSV de Japón descargado exitosamente.")
else:
    print("Error al realizar la solicitud de Japón:", japan_response.status_code)


usa_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
usa_params = {
    "format": "csv",
    "starttime": starttime,
    "endtime": endtime,
    "maxlatitude": 50,
    "minlatitude": 24.6,
    "maxlongitude": -65,
    "minlongitude": -125,
    "minmagnitude": 3,
    "orderby": "time-asc"
}

usa_response = requests.get(usa_url, params=usa_params)

if usa_response.status_code == 200:
    # Si la solicitud fue exitosa, guardamos la respuesta en un archivo CSV
    with open("usa_earthquake_data.csv", "w") as usa_file:
        usa_file.write(usa_response.text)
    print("Archivo CSV de Estados Unidos descargado exitosamente.")
else:
    print("Error al realizar la solicitud de Estados Unidos:", usa_response.status_code)


# Leer los archivos CSV y asignar el nombre del país a cada DataFrame
df_chile = pd.read_csv('chile_earthquake_data.csv', encoding='latin-1')
df_chile['Country'] = 'Chile'

df_japan = pd.read_csv('japan_earthquake_data.csv', encoding='utf-8')
df_japan['Country'] = 'Japan'

df_usa = pd.read_csv('usa_earthquake_data.csv', encoding='latin-1')
df_usa['Country'] = 'USA'

# Mostrar los valores únicos en una columna específica
columna_unica = df_usa['type'].unique()
print(columna_unica)

valores_a_borrar = ['explosion', 'rock burst', 'mining explosion', 'mine collapse', 'experimental explosion', 'quarry blast']
df_usa = df_usa.drop(df_usa[df_usa['type'].isin(valores_a_borrar)].index)

df_chile.info()
df_japan.info()
df_usa.info()

# Definir el diccionario de mapeo de nombres de columnas
nombres_columnas = {
    'time': 'dt_sismo',
    'depth':'profundidad',
    'magType': 'tipo_magnitud',
    'updated': 'dt_actualizacion',
    'place': 'ubicacion',
    'type': 'tipo',
    'horizontalError': 'error_horizontal',
    'depthError': 'error_profundidad',
    'magError': 'error_magnitud',
    'status': 'estado',
    'locationSource': 'fuente_localizacion',
    'magSource': 'fuente_mag',
    'Country': 'pais'
}

# Renombrar las columnas del DataFrame
df_chile = df_chile.rename(columns=nombres_columnas)
df_japan = df_japan.rename(columns=nombres_columnas)
df_usa = df_usa.rename(columns=nombres_columnas)

# Convertir la columna 'dt_sismo' en un objeto datetime
df_chile['dt_sismo'] = pd.to_datetime(df_chile['dt_sismo'])
df_japan['dt_sismo'] = pd.to_datetime(df_japan['dt_sismo'])
df_usa['dt_sismo'] = pd.to_datetime(df_usa['dt_sismo'])

# Extraer la fecha de la columna 'dt_sismo'
df_chile['fecha_sismo'] = df_chile['dt_sismo'].dt.strftime('%Y-%m-%d')
df_japan['fecha_sismo'] = df_japan['dt_sismo'].dt.strftime('%Y-%m-%d')
df_usa['fecha_sismo'] = df_usa['dt_sismo'].dt.strftime('%Y-%m-%d')

# Extraer hora de la columna 'dt_sismo'
df_chile['hora_sismo'] = pd.to_datetime(df_chile['dt_sismo'], format='%H:%M:%S').dt.time
df_japan['hora_sismo'] = pd.to_datetime(df_japan['dt_sismo'], format='%H:%M:%S').dt.time
df_usa['hora_sismo'] = pd.to_datetime(df_usa['dt_sismo'], format='%H:%M:%S').dt.time

# Obtener la lista de columnas del DataFrame
columnas_chile = df_chile.columns.tolist()
columnas_japan = df_japan.columns.tolist()
columnas_usa = df_usa.columns.tolist()

# Mover las columnas 'fecha_sismo' y 'hora_sismo'
columnas_chile.remove('fecha_sismo')
columnas_japan.remove('fecha_sismo')
columnas_usa.remove('fecha_sismo')

columnas_chile.remove('hora_sismo')
columnas_japan.remove('hora_sismo')
columnas_usa.remove('hora_sismo')

columnas_chile.insert(1, 'fecha_sismo')
columnas_japan.insert(1, 'fecha_sismo')
columnas_usa.insert(1, 'fecha_sismo')

columnas_chile.insert(2, 'hora_sismo')
columnas_japan.insert(2, 'hora_sismo')
columnas_usa.insert(2, 'hora_sismo')

# Reindexar los DataFrames con las columnas en el nuevo orden
df_chile = df_chile.reindex(columns=columnas_chile)
df_japan = df_japan.reindex(columns=columnas_japan)
df_usa = df_usa.reindex(columns=columnas_usa)

# Convertir la columna 'dt_actualizacion' en un objeto datetime
df_chile['dt_actualizacion'] = pd.to_datetime(df_chile['dt_actualizacion'])
df_japan['dt_actualizacion'] = pd.to_datetime(df_japan['dt_actualizacion'])
df_usa['dt_actualizacion'] = pd.to_datetime(df_usa['dt_actualizacion'])


# Extraer la fecha de la columna 'dt_actualizacion'
df_chile['fecha_actualizacion'] = df_chile['dt_actualizacion'].dt.strftime('%Y-%m-%d')
df_japan['fecha_actualizacion'] = df_japan['dt_actualizacion'].dt.strftime('%Y-%m-%d')
df_usa['fecha_actualizacion'] = df_usa['dt_actualizacion'].dt.strftime('%Y-%m-%d')


# Extraer hora de la columna 'dt_actualizacion'
df_chile['hora_actualizacion'] = pd.to_datetime(df_chile['dt_actualizacion'], format='%H:%M:%S').dt.time
df_japan['hora_actualizacion'] = pd.to_datetime(df_japan['dt_actualizacion'], format='%H:%M:%S').dt.time
df_usa['hora_actualizacion'] = pd.to_datetime(df_usa['dt_actualizacion'], format='%H:%M:%S').dt.time


# Obtener la lista de columnas del DataFrame
columnas_chile = df_chile.columns.tolist()
columnas_japan = df_japan.columns.tolist()
columnas_usa = df_usa.columns.tolist()

# Mover las columnas 'fecha_sismo' y 'hora_sismo'
columnas_chile.remove('fecha_actualizacion')
columnas_japan.remove('fecha_actualizacion')
columnas_usa.remove('fecha_actualizacion')

columnas_chile.remove('hora_actualizacion')
columnas_japan.remove('hora_actualizacion')
columnas_usa.remove('hora_actualizacion')

columnas_chile.insert(15, 'fecha_actualizacion')
columnas_japan.insert(15, 'fecha_actualizacion')
columnas_usa.insert(15, 'fecha_actualizacion')

columnas_chile.insert(16, 'hora_actualizacion')
columnas_japan.insert(16, 'hora_actualizacion')
columnas_usa.insert(16, 'hora_actualizacion')

# Reindexar el DataFrame con las columnas en el nuevo orden
df_chile = df_chile.reindex(columns=columnas_chile)
df_japan = df_japan.reindex(columns=columnas_japan)
df_usa = df_usa.reindex(columns=columnas_usa)


# Mostramos en un gráfico de barras los porcentajes de datos por columna de cada df

# Definimos una función para generar la paleta de colores personalizada
def custom_palette(n, start_color, end_color):
    start_rgb = np.array(mcolors.hex2color(start_color))
    end_rgb = np.array(mcolors.hex2color(end_color))
    colors = [mcolors.rgb2hex(start_rgb + (i * (end_rgb - start_rgb)))
              for i in np.linspace(0, 1, n)]
    return colors

# Definimos los colores de la paleta
start_color = "#00FFFF"  # Verde agua
end_color = "#808080"    # Gris

# Definimos el número de columnas
num_columns = df_chile.shape[1]

# Creamos la paleta de colores personalizada
paleta = custom_palette(num_columns, start_color, end_color)

# Crea el gráfico de barras con los colores personalizados de Chile
ax = sns.barplot(x=(round(df_chile.notnull().sum() * 100 / df_chile.shape[0])).values, y = df_chile.columns, palette=paleta)
ax.bar_label(ax.containers[0])
plt.title('Porcentaje de datos por columna')

# Muestra el gráfico
plt.show()

# Crea el gráfico de barras con los colores personalizados de Japón
ax = sns.barplot(x=(round(df_japan.notnull().sum() * 100 / df_japan.shape[0])).values, y = df_japan.columns, palette=paleta)
ax.bar_label(ax.containers[0])
plt.title('Porcentaje de datos por columna')

# Muestra el gráfico
plt.show()

# Crea el gráfico de barras con los colores personalizados de USA
ax = sns.barplot(x=(round(df_usa.notnull().sum() * 100 / df_usa.shape[0])).values, y = df_usa.columns, palette=paleta)
ax.bar_label(ax.containers[0])
plt.title('Porcentaje de datos por columna')

# Muestra el gráfico
plt.show()

#Eliminamos las columnas que no utilizaremos de cada dataframe: tipo_magnitud, nst, gap, dmin, ms, net, id, dt_actualizacion, fecha_actualizacion, hora_actualizacion, ubicacion, tipo, error_horizontal, error_profundidad, error_magnitud, magNst, estado, fuente_localizacion,
#fuente_mag

columnas_eliminar = ['tipo_magnitud', 'nst', 'gap', 'dmin', 'rms', 'net', 'id', 'dt_actualizacion', 'fecha_actualizacion', 'hora_actualizacion', 'ubicacion', 'tipo', 'error_horizontal', 'error_profundidad', 'error_magnitud', 'magNst', 'estado', 'fuente_localizacion', 'fuente_mag']

df_chile = df_chile.drop(columnas_eliminar, axis=1)
df_japan = df_japan.drop(columnas_eliminar, axis=1)
df_usa = df_usa.drop(columnas_eliminar, axis=1)

# Concatenar los DataFrames en uno solo
df_combined = pd.concat([df_usa, df_japan, df_chile], ignore_index=True)

# Crear una figura de tipo Scattergeo
fig = go.Figure(data=go.Scattergeo(
    lat = df_combined['latitude'],
    lon = df_combined['longitude'],
    mode = 'markers',
    marker = dict(
        size = df_combined['mag']*5,  # Ajustar el tamaño de los puntos
        color = df_combined['mag'],
        colorscale = 'Viridis',
        cmin = df_combined['mag'].min(),
        cmax = df_combined['mag'].max(),
        colorbar_title = 'Magnitud',
        opacity = 0.7  # Ajustar la opacidad de los puntos
    ),
    hovertext = df_combined['pais']
))

# Configurar el tamaño y título del mapa
fig.update_layout(
    title={
        'text': 'Mapa de sismos por magnitud',
        'x': 0.5  # Centrar el título horizontalmente
    },
    height=800,  # Ajustar la altura del mapa
    margin={"r": 0, "t": 30, "l": 0, "b": 0}  # Ajustar los márgenes del mapa
)

# Mostrar el mapa
fig.show()
