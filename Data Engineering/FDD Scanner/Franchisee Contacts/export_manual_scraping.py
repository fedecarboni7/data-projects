import pandas as pd
from sqlalchemy import create_engine
import os
import mysql.connector

def get_csvs_files(folder_path) :

	file_list = os.listdir(folder_path)

	files = []
	for file_name in file_list:
		file_path = os.path.join(folder_path, file_name)
		files.append(file_path)
	
	return files

# Conectarse a MySQL
cnx = mysql.connector.connect(user='fcarboni', password='fcarboni1234', host='sql.prod.platform.vettedbiz.com', database='data_integration')
cursor = cnx.cursor()

# Conectar a la base de datos
engine = create_engine('mysql+mysqlconnector://fcarboni:fcarboni1234@sql.prod.platform.vettedbiz.com:3306/data_integration')

csvs = get_csvs_files('./test/results_to_check')

# Obtener el valor máximo de la columna 'id' en la tabla 'dev_franchisees_contacts_copy'
#select_max_id_query = "SELECT MAX(id) FROM dev_franchisees_contacts_copy_1"
#cursor.execute(select_max_id_query)
#id_result = cursor.fetchone()
#max_id = id_result[0] + 1  # Obtener el valor máximo
max_id = 0

for csv in csvs:
    try:
        df = pd.read_csv(csv)
    except Exception as e:
        print(e)
        print(csv)
        continue

    df = df.fillna(value='')
    fdd_name = df['fdd_name'][0]  # Obtener el nombre del archivo

    # Chequear si el archivo ya fue exportado a la base de datos
    #select_fdd_name_query = "SELECT COUNT(*) FROM dev_franchisees_contacts_clean_data_1 WHERE fdd_name = %s"
    #values = (fdd_name,)
    #cursor.execute(select_fdd_name_query, values)
    #fdd_uploaded = cursor.fetchone()[0]

    #if fdd_uploaded > 0:
    #    print(fdd_name + ' already exported to database')
    #    continue

    # Asignar valores continuos a la columna 'id' en el dataframe
    df['id'] = range(max_id, max_id + len(df))
    try:
        df = df.reindex(columns=['id', 'fdd_name', 'phone', 'email', 'owner_name', 'website', 'state', 'city', 'address', 'zipcode', 'additional_information', 'franchise_id', 'franchise_name', 'title', 'method', 'regex'])
    except Exception as e:
        print(e)
        print(csv)
        continue

    max_id = max_id + len(df)  # Actualizar el valor máximo
    
    #df.to_sql('dev_franchisees_contacts_copy', engine, if_exists='append', index=False)
    df.to_sql('dev_franchisees_contacts_clean_data_1', engine, if_exists='append', index=False)

    has_contacts_value = 'Yes'  # Valor a asignar a la columna 'has_contacts'
    scrape_contacts_value = 'No'  # Valor a asignar a la columna 'scrape_contacts'

    # Construir y ejecutar la consulta para actualizar los valores
    update_di_fdds_query = "UPDATE di_fdds SET has_contacts = %s, scrape_contacts = %s WHERE filename = %s"
    values = (has_contacts_value, scrape_contacts_value, fdd_name)
    cursor.execute(update_di_fdds_query, values)

    # Mover el archivo a la carpeta 'exported_to_db'
    os.rename(csv, './test/exported_to_db/' + csv[24:])
    #print(fdd_name + ' exported to database')

# Confirmar los cambios y cerrar la conexión a MySQL
cnx.commit()
cursor.close()
cnx.close()
