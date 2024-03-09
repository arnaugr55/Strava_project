# Modifica el activities.csv obtenido en el script_principal, ajustando algunos campos

import pandas as pd
import pytz

def convert_speed(speed_mps):
    '''
    Convierte la veolcidad m/s -> kms/h
    '''
    return round(speed_mps*3.6,2)

folder = 'Strava_downloaded_2//activities//'

dataset = pd.read_csv('Strava_downloaded_2//activities.csv')

dataset['Activity Date'] = pd.to_datetime(dataset['Activity Date']).dt.tz_localize('UTC').dt.tz_convert(pytz.timezone('Europe/Madrid'))
dataset['Max Speed'] = (dataset['Max Speed'] * 3.6).round(3)
dataset['Average Speed'] = (dataset['Average Speed'] * 3.6).round(3)
dataset['Elevation Gain'] = (dataset['Elevation Gain']).round(2)


dataset.to_csv("activites_final.csv", chunksize=1000)

