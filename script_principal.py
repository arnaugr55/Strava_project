# Librerías a importar
from geopy.geocoders import Nominatim
import gpxpy
import pandas as pd
import os
import re
import pytz
from geopy.distance import geodesic
import time
from datetime import datetime

def distance(coord1, coord2):
    '''
    :param coord1: Latitud y Longitud de la 1a coordenada
    :param coord2: Latitud y Longitud de la 2a coordenada
    :return: Distancia en metros de las 2 coordenadas
    '''
    return geodesic(coord1, coord2).meters

def get_municipality(latitude, longitude):
    '''
    Se llama a Nominatim() para encontrar la población de una coordenada
    latitude: Latitud de la coordenada
    longitude: Longitud de la coordenada
    '''
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.reverse((latitude, longitude), language='en')

    # Extract municipality from address
    components = location.raw.get('address', {})
    municipality = components.get('city', '') or components.get('town', '') or components.get('village', '')
    return municipality

def read_gpx_file(file_path):
    '''
    :param file_path: Dirección del fichero
    :return: Objeto gpxpy.gpx
    '''
    with open(file_path, 'r', encoding='utf-8') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    return gpx

def is_coordinate_in_gpx(target_latitude, target_longitude, possible_peaks):
    '''
    Obtiene un documento gpx con las montañas mas importantes de la península
    Si es la primera vez (de la ruta) que está función es llamada, devolverá las posibles montañas que, por proximidad, se podrían hacerse en la ruta (possible_peaks)
    Si no, busca si la latitud y longitud actuales están suficientemente cerca de unos de las montañas guardados en possible_peaks. Si es así, devuelve la montaña
    :param target_latitude: Latitud actual
    :param target_longitude: Longitud actual
    :param possible_peaks: Lista de possibles montañas en la ruta. Para cada posible montaña guarda la lat,long,nombre y altitud
    '''
    gpx_file_path = 'Mountains//Mendikat_1.gpx'
    zone_tolerance = 0.2  # Umbral de proximidad para guardar una montaña en possible_peaks
    peak_tolerance = 0.001  # Umbral de proximidad para considerar un montaña de possible_peaks como subida

    # Si es la primera vez
    if len(possible_peaks) == 0:
        # Abrimos el fichero gpx con todas las montañas
        gpx_data = read_gpx_file(gpx_file_path)
        for track in gpx_data.waypoints:
            # Calculamos la distancia respecto al punto actual
            latitude_diff = abs(track.latitude - target_latitude)
            longitude_diff = abs(track.longitude - target_longitude)
            # Si la proximidad es < zone_tolerance, se guarda la montaña en possible_peaks
            if latitude_diff < zone_tolerance and longitude_diff < zone_tolerance:
                match = re.search(r'\d', track.name)
                possible_peaks.append([track.latitude, track.longitude, track.name[:match.start()-1], track.name[match.start():]])
    # Si NO es la primera vez
    else:
        for lista in possible_peaks:
            # Campos guardados de la montaña
            mt_latitude = lista[0]
            mt_longitude = lista[1]
            mountain = lista[2]
            elevation = lista[3]

            # Calculamos la proximidad
            latitude_diff = abs(mt_latitude - target_latitude)
            longitude_diff = abs(mt_longitude - target_longitude)

            # Si la proximidad es < peak_tolerance, se devuelve la montaña como subida
            if latitude_diff < peak_tolerance and longitude_diff < peak_tolerance:
                return mountain, elevation, possible_peaks  # Coordinates are within tolerance of the target

    return False, False, possible_peaks



def calculate_acc_elevation(segment, entered_point):
    '''
    Va sumando el desnivel acumulado desde el inicio hasta el punto entrado
    :param segment: Ruta
    :param entered_point: Punto de la ruta donde está la montaña
    :return: Desnivel acumulado
    '''
    desnivel_acumulado = 0
    elevacion_anterior = None

    # Itera punto a punto
    for point in segment.points:
        # Cuando se llega al punto entrado, devuelve el desnivel
        if point == entered_point:
            return round(desnivel_acumulado,2)

        # Para cada punto, calcula la elevación y la va sumando
        elevacion_actual = point.elevation
        if elevacion_anterior is not None:
            desnivel_acumulado += max(0, elevacion_actual - elevacion_anterior)
        elevacion_anterior = elevacion_actual



# Configuraciones

# Carpeta donde están los gpxs de las actividades
folder_path = 'Strava_downloaded_2//activities'
# Fichero activites.csv
dataset = pd.read_csv('Strava_downloaded_2//activities.csv')
# Para evitar errores, el código se ejecuta en tramos. Tenemos que definir si es la primera ejecución o no
first_exeuction = False

if first_exeuction:
    # Se crean los dataframes
    mountains_df = pd.DataFrame()
    pobl_df = dataset['Activity ID'].to_frame()
    # dataset['Activity Date'] = pd.to_datetime(dataset['Activity Date']).dt.tz_localize('UTC').dt.tz_convert(pytz.timezone('Europe/Madrid'))
else:
    # Se leen los dataframes guardados
    dataset['Activity Date'] = pd.to_datetime(dataset['Activity Date']).dt.tz_localize('UTC').dt.tz_convert(pytz.timezone('Europe/Madrid'))
    mountains_df = pd.read_csv('mountains.csv')
    pobl_df = pd.read_csv('poblacions.csv')


start_time = time.time()

# Vamos a procesar de la actividad 'begin', hasta la 'end' (se recomineda de 20 en 20 actividades)
begin = 0
end = 20
# Iteramos todos los ficheros de la carpeta de GPXs
# PARA CADA RUTA...
for ind,filename in enumerate(os.listdir(folder_path)[begin:end]):
    # Abrimos el fichero gpx con todos los puntos de la actividad
    file_path = os.path.join(folder_path, filename)

    gpx_data = read_gpx_file(file_path)

    file_date = int(gpx_data.time.strftime("%Y%m%d"))  # se usa para ir actualizando los datos
    if file_date > 20240121:
        if os.path.isfile(file_path):
            print("\n", "Filename:", filename)

        # Encontramos el registro del activities.csv al que hace referencia el gpx
        row = dataset.loc[dataset['Activity ID'] == int(filename[:-4])]

        dist = 0  # Contador de distancia (metros)
        dist_limit = 50  # A los 50 metros, busca el municipio. (Luego cada 100)
        poblacion_counts = {}  # Guarda en un diccionario las poblaciones obtenidas
        prev_coords = None  # Se usa para calcular la distancia acumulada

        mountains = {}  # Inicializamos un diccionario vacío, donde pondremos las montañas de la ruta
        possible_peaks = []  # Lista que contendrá los posibles montañas a subir en aquella ruta
        count_mountain = 0  # Incializamos un contador, que controla cada cuando se llama a is_coordinate_in_gpx
        for track in gpx_data.tracks:
            print(f"Track name: {track.name}")

            prev_coords = None
            for segment in track.segments:
                # Para cada punto de la actividad
                for point in segment.points:
                    current_coords = (point.latitude, point.longitude)  # Se guardan las coordenadas

                    if prev_coords is not None:
                        dist += distance(prev_coords, current_coords)  # Se va sumando la distancia

                        count_mountain += 1
                        if count_mountain == 100:
                            # Cada 100 puntos, llamamos a is_coordinate_in_gpx()
                            mountain, mts, possible_peaks = is_coordinate_in_gpx(point.latitude, point.longitude, possible_peaks)

                            # En caso de que hayamos obtenido una montaña
                            if mountain:
                                if mountain not in mountains:
                                    print("Mountain: ", mountain, mts)

                                    # Desnivel acumulado hasta la cima de la montaña
                                    acc_elevation = calculate_acc_elevation(segment, point)

                                    # Hora de llegada a la cima
                                    arrival = point.time.astimezone(pytz.timezone('Europe/Madrid'))

                                    # Tiempo transcurrido desde el incio hasta la cima
                                    begin = row['Activity Date']
                                    time_to_peak0 = arrival - begin
                                    hours = time_to_peak0.iloc[0].seconds // 3600
                                    minutes = (time_to_peak0.iloc[0].seconds % 3600) // 60
                                    seconds = time_to_peak0.iloc[0].seconds % 60
                                    time_to_peak = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                                    # Guardamos las características recogidas
                                    mountains[mountain] = {'Elevation': mts, "Latitude": point.latitude, "Longitude": point.longitude, "Acc_Elevation": acc_elevation, "Time": arrival, "RouteCode": filename[:-4], "Distance_to_peak": round(dist/1000,2), "Time_to_peak": time_to_peak}

                            count_mountain = 0

                        # Cada 100 metros llamamos a get_municipality()
                        if dist > dist_limit:
                            town = get_municipality(point.latitude, point.longitude)

                            # Guardamos el municipio obtenido en el diccionario
                            if town in poblacion_counts:
                                poblacion_counts[town] += 1
                            else:
                                poblacion_counts[town] = 1

                            # Va a volver a buscar el muncipio, tras 100 metros
                            dist_limit += 100

                    prev_coords = current_coords

                # En caso de que en la ruta/actividad hayamos subido a alguna montaña, la/las guardamos en el mountains_df
                if mountains:
                    for mt, info in mountains.items():
                        mountains_df = mountains_df.append({'Mountain': mt,
                                                    'Elevation': info['Elevation'],
                                                    'Latitude': info['Latitude'],
                                                    'Longitude': info['Longitude'],
                                                    'Acc_Elevation': info['Acc_Elevation'],
                                                    'Time': info['Time'],
                                                    'Distance_to_peak': info['Distance_to_peak'],
                                                    'Time_to_peak': info['Time_to_peak'],
                                                    'RouteCode': info['RouteCode']}, ignore_index=True)
                    # Exoportamos el mountains_df a csv
                    mountains_df.to_csv("mountains.csv")

                # Actualizamos el pobl_df con el poblacion_counts de esta ruta
                print(poblacion_counts)
                for pob,count in poblacion_counts.items():
                    if pob != '':
                        pobl_df.loc[pobl_df['Activity ID'] == int(filename[:-4]), pob] = round(count*0.1, 1)

# Exoportamos el pobl_df a csv
pobl_df.to_csv("poblacions.csv", chunksize=1000)

# Mostramos el tiempo de ejecución
end_time = time.time()
execution_time = end_time - start_time
print("Execution time (seconds): ", execution_time)
