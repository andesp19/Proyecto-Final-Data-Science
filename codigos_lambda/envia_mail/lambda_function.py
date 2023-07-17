import boto3
import json
import requests
from datetime import datetime, timedelta
import csv

def send_email(recipient, subject, body):
    # Función para enviar un correo electrónico utilizando el servicio SES de AWS
    client = boto3.client('ses', region_name='us-east-2')

    response = client.send_email(
        Source='josegerchinhoren97@gmail.com',
        Destination={
            'ToAddresses': [
                recipient,
            ],
        },
        Message={
            'Subject': {
                'Data': subject,
            },
            'Body': {
                'Text': {
                    'Data': body,
                },
            },
        }
    )

    return response

def lambda_handler(event, context):
    # Función principal invocada por AWS Lambda

    # Obtener sismos de Chile, USA y Japón
    sismos_chile = obtener_sismos('chile')
    sismos_usa = obtener_sismos('usa')
    sismos_japon = obtener_sismos('japon')

    if sismos_chile or sismos_usa or sismos_japon:
        # Combinar los sismos de los diferentes países
        sismos_combinados = sismos_chile + sismos_usa + sismos_japon

        # Filtrar los sismos de la última hora
        sismos_combinados_filtrados = filtrar_sismos_ultima_hora(sismos_combinados)

        if sismos_combinados_filtrados:
            # Enviar correos electrónicos con los sismos filtrados
            enviar_emails(sismos_combinados_filtrados)

            return {
                'statusCode': 200,
                'body': json.dumps(sismos_combinados_filtrados)
            }
        else:
            return {
                'statusCode': 200,
                'body': 'No hay sismos nuevos en la última hora'
            }
    else:
        return {
            'statusCode': 500,
            'body': 'Error al obtener los datos de los sismos'
        }

def obtener_sismos(pais):
    # Obtener sismos de un país específico dentro de un rango de tiempo

    # Calcular la fecha y hora actual y la fecha y hora anterior
    fecha_actual = datetime.utcnow()
    fecha_anterior = fecha_actual - timedelta(hours=1)
    fecha_anterior_str = fecha_anterior.strftime("%Y-%m-%d")

    # Definir los límites de latitud y longitud y el nombre del país
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

    # Construir la URL para obtener los sismos del servicio USGS Earthquake
    starttime = f"{fecha_anterior_str}T{fecha_anterior.strftime('%H:%M:%S')}"
    endtime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={starttime}&endtime={endtime}&minlatitude={min_latitude}&maxlatitude={max_latitude}&minlongitude={min_longitude}&maxlongitude={max_longitude}"
    response = requests.get(url)

    if response.status_code == 200:
        # Parsear los datos de respuesta y obtener los sismos
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

            profundidad = properties.get("depth")
            ubicacion = obtener_ubicacion(lugar)

            # Verificar si el sismo pertenece al país deseado
            if ubicacion is not None and pais == 'chile' and 'Chile' not in ubicacion:
                continue

            # Crear un diccionario con la información del sismo
            sismo_info = {
                "dt_sismo": datetime.utcfromtimestamp(fecha_hora / 1000).strftime("%Y-%m-%d %H:%M:%S.%f") + "+00:00",
                "fecha_sismo": datetime.utcfromtimestamp(fecha_hora / 1000).strftime("%Y-%m-%d"),
                "hora_sismo": datetime.utcfromtimestamp(fecha_hora / 1000).strftime("%H:%M:%S.%f"),
                "latitude": latitud,
                "longitude": longitud,
                "profundidad": profundidad if profundidad is not None else '',
                "mag": magnitud,
                "ubicacion": ubicacion,
                "pais": pais_nombre
            }
            sismos_pais.append(sismo_info)

        return sismos_pais
    else:
        return []

def obtener_ubicacion(lugar):
    # Obtener la ubicación a partir del campo "place" del sismo

    try:
        if lugar:
            ubicacion = lugar.split(" of ")[-1].strip()
            return ubicacion
        else:
            return None
    except Exception as e:
        print("Error al obtener la ubicación del sismo:", e)
        return None

def filtrar_sismos_ultima_hora(sismos):
    # Filtrar los sismos para obtener solo los de la última hora

    fecha_actual = datetime.utcnow()
    fecha_anterior = fecha_actual - timedelta(hours=1)

    sismos_filtrados = []
    for sismo in sismos:
        dt_sismo = datetime.strptime(sismo["dt_sismo"], "%Y-%m-%d %H:%M:%S.%f+00:00")
        if dt_sismo >= fecha_anterior and dt_sismo <= fecha_actual:
            sismos_filtrados.append(sismo)

    return sismos_filtrados

def enviar_emails(sismos):
    # Enviar correos electrónicos a los destinatarios con los sismos correspondientes

    bucket_name = 'chile-usa-japon'
    file_name = 'lista_emails.csv'

    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    csv_data = response['Body'].read().decode('iso-8859-1')

    # Leer el archivo CSV de destinatarios de correo electrónico
    reader = csv.DictReader(csv_data.splitlines())
    destinatarios_paises = [(row['correo_electronico'].strip(), row['pais'].strip()) for row in reader]

    for recipient, pais_destino in destinatarios_paises:
        recipient_email = recipient.strip()
        body = crear_cuerpo_email(sismos)
        subject = f"Últimos sismos en {pais_destino}"

        # Enviar correo electrónico a cada destinatario con los sismos correspondientes
        send_email(recipient_email, subject, body)

def crear_cuerpo_email(sismos):
    # Crear el cuerpo del correo electrónico con la información de los sismos

    cuerpo = "Últimos sismos:\n\n"
    for sismo in sismos:
        cuerpo += f"Fecha y hora: {sismo['dt_sismo']}\n"
        cuerpo += f"Magnitud: {sismo['mag']}\n"
        cuerpo += f"Lugar: {sismo['ubicacion']}\n"
        cuerpo += f"Latitud: {sismo['latitude']}\n"
        cuerpo += f"Longitud: {sismo['longitude']}\n"
        cuerpo += f"Profundidad: {sismo['profundidad']}\n"
        cuerpo += f"País: {sismo['pais']}\n"
        cuerpo += "\n"

    return cuerpo
