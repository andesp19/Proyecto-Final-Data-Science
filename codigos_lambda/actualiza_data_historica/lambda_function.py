import boto3
import json
import requests
from datetime import datetime, timedelta

def lambda_handler(event, context):
    # Obtener sismos de Chile, Estados Unidos y Japón
    sismos_chile = obtener_sismos('chile')
    sismos_usa = obtener_sismos('usa')
    sismos_japon = obtener_sismos('japon')

    if sismos_chile or sismos_usa or sismos_japon:
        # Combinar los sismos de los tres países
        sismos_combinados = sismos_chile + sismos_usa + sismos_japon
        # Filtrar sismos duplicados
        sismos_combinados_filtrados = filtrar_sismos_duplicados(sismos_combinados)

        if sismos_combinados_filtrados:
            # Guardar los sismos en S3
            guardar_sismos_en_s3(sismos_combinados_filtrados)

            return {
                'statusCode': 200,
                'body': json.dumps(sismos_combinados_filtrados)
            }
        else:
            return {
                'statusCode': 200,
                'body': 'No hay sismos nuevos para guardar'
            }
    else:
        return {
            'statusCode': 500,
            'body': 'Error al obtener los datos de los sismos'
        }

def obtener_sismos(pais):
    fecha_actual = datetime.utcnow()
    fecha_anterior = fecha_actual - timedelta(days=1)
    fecha_anterior_str = fecha_anterior.strftime("%Y-%m-%d")

    # Definir los límites geográficos y el nombre del país
    if pais == 'chile':
        min_latitude = -56.05
        max_latitude = -17.5
        min_longitude = -109.45
        max_longitude = -66.93
        pais_nombre = 'Chile'
    elif pais == 'usa':
        min_latitude = 24.6
        max_latitude = 50
        min_longitude = -125
        max_longitude = -65
        pais_nombre = 'USA'
    elif pais == 'japon':
        min_latitude = 27.0
        max_latitude = 44.0
        min_longitude = 132.78
        max_longitude = 145.53
        pais_nombre = 'Japón'
    else:
        return []

    starttime = f"{fecha_anterior_str}T00:00:00"
    endtime = f"{fecha_anterior_str}T23:59:59"

    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={starttime}&endtime={endtime}&minlatitude={min_latitude}&maxlatitude={max_latitude}&minlongitude={min_longitude}&maxlongitude={max_longitude}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        sismos = data["features"]
        sismos_pais = []
        for sismo in sismos:
            properties = sismo["properties"]
            lugar = properties["place"]
            magnitud = properties["mag"]
            fecha_hora = properties["time"]
            coordenadas = sismo["geometry"]["coordinates"]
            latitud = coordenadas[1]
            longitud = coordenadas[0]
            profundidad = coordenadas[2]  # Obtener la profundidad del sismo

            ubicacion = obtener_ubicacion(lugar)

            if ubicacion is not None:
                sismo_info = {
                    "dt_sismo": datetime.utcfromtimestamp(fecha_hora / 1000).strftime("%Y-%m-%d %H:%M:%S.%f") + "+00:00",
                    "fecha_sismo": datetime.utcfromtimestamp(fecha_hora / 1000).strftime("%Y-%m-%d"),
                    "hora_sismo": datetime.utcfromtimestamp(fecha_hora / 1000).strftime("%H:%M:%S.%f"),
                    "latitude": latitud,
                    "longitude": longitud,
                    "profundidad": profundidad,
                    "mag": magnitud,
                    "ubicacion": ubicacion,
                    "pais": pais_nombre
                }
                sismos_pais.append(sismo_info)

        return sismos_pais
    else:
        return []

def obtener_ubicacion(lugar):
    try:
        if lugar:
            ubicacion = lugar.split(" of ")[-1].strip()
            return ubicacion
        else:
            return None
    except Exception as e:
        print("Error al obtener la ubicación del sismo:", e)
        return None

def filtrar_sismos_duplicados(sismos):
    s3_client = boto3.client('s3')
    bucket_name = 'chile-usa-japon'
    dataset_file_name = 'combined_earthquake_data.csv'
    try:
        # Obtener el dataset existente de S3
        response = s3_client.get_object(Bucket=bucket_name, Key=dataset_file_name)
        dataset = response['Body'].read().decode('utf-8')

        sismos_filtrados = []
        for sismo in sismos:
            registro = '{},{},{},{},{},{},{},{},{}'.format(
                sismo["dt_sismo"],
                sismo["fecha_sismo"],
                sismo["hora_sismo"],
                sismo["latitude"],
                sismo["longitude"],
                sismo["profundidad"],
                sismo["mag"],
                f'"{sismo["ubicacion"]}"',
                sismo["pais"]
            )

            if registro not in dataset:
                sismos_filtrados.append(sismo)

        return sismos_filtrados

    except Exception as e:
        print("Error al filtrar los sismos duplicados:", e)
        return sismos

def guardar_sismos_en_s3(sismos):
    s3_client = boto3.client('s3')
    bucket_name = 'chile-usa-japon'
    dataset_file_name = 'combined_earthquake_data.csv'

    try:
        # Generar los datos a guardar en formato CSV
        sismos_data = []
        for sismo in sismos:
            sismo_data = '{},{},{},{},{},{},{},{},{}\n'.format(
                sismo["dt_sismo"],
                sismo["fecha_sismo"],
                sismo["hora_sismo"],
                sismo["latitude"],
                sismo["longitude"],
                sismo["profundidad"] if sismo["profundidad"] is not None else '',
                sismo["mag"],
                f'"{sismo["ubicacion"]}"',
                sismo["pais"]
            )
            sismos_data.append(sismo_data)

        # Guardar los datos en S3
        response = s3_client.get_object(Bucket=bucket_name, Key=dataset_file_name)
        dataset = response['Body'].read().decode('utf-8')
        dataset += ''.join(sismos_data)

        s3_client.put_object(
            Body=dataset.encode('utf-8'),
            Bucket=bucket_name,
            Key=dataset_file_name
        )

    except Exception as e:
        print("Error al guardar los sismos en S3:", e)