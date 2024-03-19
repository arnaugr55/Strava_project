import pandas as pd

# Lee el csv de poblacions obtenido en script_principal.py
poblacions = pd.read_csv('poblacions.csv')


### PARTE 1: POBLACIONS2 ###

# Lee poblacions2.csv que contiene información de cada muncipio de Cataluña
poblacions2 = pd.read_csv('poblacions2.csv')
rank = {}

all_mun = list(poblacions2['Municipi'])

# Itera el dataset poblacions y va guardando en cada municipio la distancia TOTAL recorrida
for col in poblacions.columns:
    count = poblacions[col].sum()
    rank[col] = poblacions[col].sum()
    if col in all_mun:
        poblacions2.loc[poblacions2['Municipi'] == col, 'Count'] = round(count,2)
    else:
        # Si hay algún muncipio que no se encuentra en poblacions2, lo muestra
        # Si se trata de una entidad de población no independiente, tendremos que modificar el poblacions, para guardar sus datos en los de su población "padre"
        print(col, count)

# Muestra el diccionaro de menos a mas
sorted_dict = {k: v for k, v in sorted(rank.items(), key=lambda item: item[1], reverse=True)}
print(sorted_dict)

# Se guarda el dataset a su csv (ahora con las distancias totales)
poblacions2.to_csv("poblacions2.csv")




### PARTE 2: POBLACIONS2 ###

# Crea un 3er dataset poblacions3
poblacions3 = pd.DataFrame(columns=['Activity ID', 'Poblacion', 'Distance'])

# Guarda un registro con cada municipio de una actividad (junto con su distancia)
for index, row in poblacions.iterrows():
    for col, value in row.items():
        if col != 'Activity ID':
            if pd.notna(value):
                poblacions3 = poblacions3.append({'Activity ID': int(row['Activity ID']), 'Poblacion': col, 'Distance': value}, ignore_index=True)

# Se guarda el dataset a csv
poblacions3.to_csv("poblacions3.csv")