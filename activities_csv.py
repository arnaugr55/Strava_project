# Modifica el activities.csv obtenido en el script_principal, ajustando algunos campos

import pandas as pd
import pytz

def convert_speed(speed_mps):
    '''
    Convierte la veolcidad m/s -> kms/h
    '''
    return round(speed_mps*3.6,2)

# Funció per convertir les columnes numèriques a cadenes de text amb comes en lloc de punts decimals
def convert_numeric_to_string_with_comma(df):
    for col in df.select_dtypes(include=['number']).columns:
        df[col] = df[col].apply(lambda x: str(x).replace('.', ','))
    return df


folder = 'Strava_downloaded_3//activities//'


dataset = pd.read_csv('Strava_downloaded_3//activities.csv')

dataset['Activity Date'] = pd.to_datetime(dataset['Activity Date']).dt.tz_localize('UTC').dt.tz_convert(pytz.timezone('Europe/Madrid'))
dataset['Max Speed'] = (dataset['Max Speed'] * 3.6).round(3)
dataset['Average Speed'] = (dataset['Average Speed'] * 3.6).round(3)
dataset['Elevation Gain'] = (dataset['Elevation Gain']).round(2)
dataset['Activity Name'] = dataset['Activity Name'].str.replace('\n', ' ')
dataset = convert_numeric_to_string_with_comma(dataset)


dataset.to_csv("activites_final.csv", chunksize=1000)