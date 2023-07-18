import pandas as pd
import datetime
import json
import requests

# Obtener la fecha y hora actual
now = datetime.datetime.now()

# Formatear las fechas en el formato ISO8601 con zona horaria UTC
endtime = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")  # Usamos la fecha y hora actual
starttime = "2012-01-01T00:00:00+00:00"

# Para ETL previo obtenemos los datos dentro de archivos .csv
# Juntamos los requests para obtener los datos de los tres paises que nos interesan a través de la API

countries = [
    {
        "country_name": "Chile",
        "url": "https://earthquake.usgs.gov/fdsnws/event/1/query",
        "params": {
            "format": "geojson",
            "starttime": starttime,
            "endtime": endtime,
            "minlatitude": -56.8,
            "maxlatitude": -19.0,
            "minlongitude": -79.0,
            "maxlongitude": -69.9,
            "jsonerror": "true",
            "orderby": "time-asc"
        }
    },
    {
        "country_name": "Japan",
        "url": "https://earthquake.usgs.gov/fdsnws/event/1/query",
        "params": {
            "format": "geojson",
            "starttime": starttime,
            "endtime": endtime,
            "minlatitude": 27.0,
            "maxlatitude": 44.0,
            "minlongitude": 132.78,
            "maxlongitude": 145.53,
            "jsonerror": "true",
            "orderby": "time-asc"
        }
    },
    {
        "country_name": "USA",
        "url": "https://earthquake.usgs.gov/fdsnws/event/1/query",
        "params": {
            "format": "geojson",
            "starttime": starttime,
            "endtime": endtime,
            "maxlatitude": 50,
            "minlatitude": 24.6,
            "maxlongitude": -65,
            "minlongitude": -125,
            "minmagnitude": 3,
            "orderby": "time-asc"
        }
    }
]

df_combined = pd.DataFrame()

for country in countries:
    country_name = country["country_name"]
    url = country["url"]
    params = country["params"]

    response = requests.get(url, params=params)

    if response.status_code == 200:
        # Si la solicitud fue exitosa, convertimos la respuesta a un objeto JSON
        data = json.loads(response.text)
        features = data.get("features", [])

        # Iteramos sobre las características y extraemos los campos relevantes
        country_data = []
        for feature in features:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [])

            dt_sismo = datetime.datetime.utcfromtimestamp(properties.get("time") / 1000).strftime("%Y-%m-%d %H:%M:%S+00:00")
            fecha_sismo = datetime.datetime.utcfromtimestamp(properties.get("time") / 1000).strftime("%Y-%m-%d")
            hora_sismo = datetime.datetime.utcfromtimestamp(properties.get("time") / 1000).strftime("%H:%M:%S")
            latitude = coordinates[1]
            longitude = coordinates[0]
            profundidad = coordinates[2]
            mag = properties.get("mag")
            ubicacion = properties.get("place")

            # Asignación de categorías de peligrosidad según magnitud y profundidad
            if mag > 7 and profundidad < 200:
                peligrosidad = "muy fuerte"
            elif (mag > 5 and mag <= 7 and profundidad < 200) or (mag > 7 and profundidad >= 200):
                peligrosidad = "fuerte"
            elif (mag > 3 and mag <= 5 and profundidad < 200) or (mag > 5 and profundidad >= 200):
                peligrosidad = "moderado"
            elif mag <= 3 and profundidad < 200 or (mag > 3 and profundidad >= 200):
                peligrosidad = "leve"
            else:
                peligrosidad = "desconocido"
                print(f"Sismo de peligrosidad desconocida: magnitud {mag}, profundidad {profundidad}")

            country_data.append({
                "dt_sismo": dt_sismo,
                "fecha_sismo": fecha_sismo,
                "hora_sismo": hora_sismo,
                "latitude": latitude,
                "longitude": longitude,
                "profundidad": profundidad,
                "mag": mag,
                "ubicacion": ubicacion,
                "pais": country_name,
                "peligrosidad": peligrosidad
            })

        # Creamos un DataFrame con los datos del país actual
        df_country = pd.DataFrame(country_data)
        df_combined = pd.concat([df_combined, df_country], ignore_index=True)

        print(f"Archivo GeoJSON de {country_name} descargado exitosamente.")
    else:
        print(f"Error al realizar la solicitud de {country_name}: {response.status_code}")

# Guardar el DataFrame combinado en un archivo CSV
df_combined.to_csv("combined_earthquake_data.csv", index=False)

print("Archivo CSV combinado guardado exitosamente.")
