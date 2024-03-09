# Librerías a importar
import os
import gpxpy
import json
import pytz
from datetime import datetime
import numpy as np
import time
from geopy.distance import geodesic

def read_gpx_file(file_path):
    '''
    :param file_path: Dirección del fichero
    :return: Objeto gpxpy.gpx
    '''
    with open(file_path, 'r', encoding='utf-8') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    return gpx

def distance(coord1, coord2):
    '''
    :param coord1: Latitud y Longitud de la 1a coordenada
    :param coord2: Latitud y Longitud de la 2a coordenada
    :return: Distancia en metros de las 2 coordenadas
    '''
    return geodesic(coord1, coord2).meters


def serialize_date(obj):
    '''
    Convierte los objetos datetime en cadenas de texto con formato ISO 8601.
    '''
    if isinstance(obj, datetime):
        return obj.isoformat()


# Configuraciones

# Carpeta donde están los gpxs de las actividades
folder_path = "Strava_downloaded_2//activities"
# Numpy array con las columnas especificadas
columns  = ['Latitude', 'Longitude', 'Elevation', 'PK', 'Time', 'Route Name', 'Distance (km)']
np_array = np.empty((0, len(columns)), dtype=object)

start_time = time.time()


# BUCLE

# Iteramos cada fichero gpx
for filename in os.listdir(folder_path):
    print("Filename:", filename)
    # filename = "4780191154.gpx" (prueba)
    file_path = os.path.join(folder_path, filename)
    prev_coords = None # Se usa, para calcular la distancia acumulada

    # Abrimos el fichero gpx con todos los puntos de la actividad
    gpx_data = read_gpx_file(file_path)

    dist = 0  # Contador de distancia (metros)
    dist_limit = 2.5  # A los 2.5 metros, guarda el punto (Luego cada 5)
    pk = filename[:-4]  # Guardamos la Activity_ID

    for track in gpx_data.tracks:
        route_name = track.name
        print(f"Track name: {track.name}")

        # Para cada punto de la actividad
        for ind, point in enumerate(track.segments[0].points):
            current_coords = (point.latitude, point.longitude)  # Se guardan las coordenadas

            if prev_coords is not None:
                dist += distance(prev_coords, current_coords)  # Se va sumando la distancia

            # Cada 5 metros, guardamos el punto en el array
            if dist > dist_limit:
                data_row = [current_coords[0], current_coords[1], point.elevation, pk, point.time.astimezone(pytz.timezone('Europe/Madrid')), route_name, dist/1000]
                np_array = np.append(np_array, [data_row], axis=0)
                # Va a volver a guardar el punto tras 5 metros
                dist_limit += 5

            prev_coords = current_coords

    # Vamos mostrando el tiempo y el número de puntos que llevamos iterados
    end_time = time.time()
    execution_time = end_time - start_time
    print(ind, execution_time)
    print("\n")



# Convierte el np_array en una lista de diccionarios
rank = [dict(zip(columns, row)) for row in np_array]

# Convierte la lista de diccionarios en un objeto con estructura json
json_data = {str(idx): data for idx, data in enumerate(rank)}

# Serializa el objeto con estructura json (para las fechas)
json_data_str = json.dumps(json_data, default=serialize_date)

# Lo guarda en un fichero .json
with open("gpx_prova.json", 'w') as json_file:
    json_file.write(json_data_str)
