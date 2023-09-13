import pandas as pd
import os

folder_path = '' # Ruta de la carpeta que contiene los archivos CSV

file_list = os.listdir(folder_path)

files = []
for file_name in file_list:
    file_path = os.path.join(folder_path, file_name)
    files.append(file_path)

# Leer cada archivo CSV en un DataFrame y almacenarlos en una lista
dfs = [pd.read_csv(file) for file in files]

# Concatenar los DataFrames en uno solo
merged_df = pd.concat(dfs, ignore_index=True)

# Agregar una columna 'id' que represente el índice del DataFrame
merged_df['#'] = merged_df.index

merged_df.to_csv('merged.csv', index=False)

# Seleccionar solo las columnas requeridas
selected_columns = [
    '#', 'fdd_name', 'owner_name', 'email', 'phone', 'website',
    'state', 'city', 'address', 'zipcode', 'additional_information',
    'franchise_id', 'franchise_name', 'title', 'company_name', 'linkedin_profile'
]

# Crear un nuevo DataFrame con las columnas seleccionadas
final_df = merged_df[selected_columns]

# Guardar el DataFrame combinado en un nuevo archivo CSV
final_df.to_csv('merged_result.csv', index=False)