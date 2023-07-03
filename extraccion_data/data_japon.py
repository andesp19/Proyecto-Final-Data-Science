import requests
import json

url = "https://www.jma.go.jp/bosai/quake/data/list.json"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    sismos = data
    
    sismos_list = []  # Lista para almacenar la información de los sismos
    
    for sismo in sismos:
        fecha = sismo["rdt"]
        magnitud = sismo["mag"]
        profundidad = sismo["acd"]
        
        # Verificar si hay información de latitud y longitud
        if len(sismo["cod"].split("+")) >= 3:
            latitud = sismo["cod"].split("+")[1]
            longitud = sismo["cod"].split("+")[2].split("-")[0]
        else:
            latitud = "Información no disponible"
            longitud = "Información no disponible"
        
        sismo_info = {
            "Fecha": fecha,
            "Magnitud": magnitud,
            "Profundidad": profundidad,
            "Latitud": latitud,
            "Longitud": longitud
        }
        
        sismos_list.append(sismo_info)  # Agregar información del sismo a la lista
    
    # Guardar la lista de sismos en un archivo JSON
    with open('sismos_japon.json', 'w') as f:
        json.dump(sismos_list, f)
        
    print("Se ha guardado la información en el archivo 'sismos_japon.json'")
else:
    print("Error al obtener los datos de la API")
