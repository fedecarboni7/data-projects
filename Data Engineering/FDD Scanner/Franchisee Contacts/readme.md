# Extract FDDs Franchisees Contacts
Programa: main_franchisees_contacts.py

## Descripción:
Este programa extrae los contactos de los franquiciados de la base de datos de FDDs.

## Requerimientos:
Ver archivo requirements.txt y dockerfile.

config.yaml debe estar en la misma carpeta que el programa, y debe tener la siguiente estructura:

```
# config.yaml
# Configuración de la base de datos
mysqldb:
  host: vp-rds-prod01.ckfqic02hnip.us-east-1.rds.amazonaws.com
  port: 3306
  user: user
  password: password
  database: data_integration

# Ruta de la carpeta donde se guardarán los archivos
fdd_input_path: './test/fdd_input'
fdd_output_path: './test/fdd_output'
fdd_error_output_path: './test/fdd_errors'
results_output_path: './test/results'
results_error_output_path: './test/results_errors'

# Modo de ejecución
dev_mode: True
skip_fdd_in_db: False
```

## Ejecución:
```
python main_franchisees_contacts.py
```

## Modos de ejecución:
Se determinan en el archivo de configuración config.yaml. Los cuales son:
- **dev_mode**: True/False. Si es True, los resultados se cargan en formato de csv en la carpeta results_output_path determinada en config.yaml. Si es False, los resultados se cargaran a la base de datos.
- **skip_fdd_in_db**: True/False. Si es True, se omitirá la extracción de los FDDs que ya se encuentran en la base de datos. Si es False, se extraerán todos los FDDs.

## Resultados:
Los resultados se cargan en la tabla **dev_franchisees_contacts** de la base de datos **data_integration**. Si *dev_mode* es True, los resultados se cargan en formato de csv en la carpeta *results_output_path* determinada en config.yaml. Los resultados que presenten errores se cargan en la carpeta *results_error_output_path* determinada en config.yaml.

## Logs:
Los logs se guardan con el nombre de *main_franchisees_contacts.log*. Cada vez que se procesa un fdd, se imprime en el log el nombre del archivo con la fecha y hora de procesamiento. Según como se haya procesado, se imprimirá alguno de estos mensajes:
- **'already in database'**: Si el fdd ya se encuentra en la base de datos (Solo en el modo *skip_fdd_in_db* en True).
- **'invalid methods'**: Si no se encuentra ningún método de extracción de los franquiciados valido.
- **'list of franchisees not found'**: Si no se encuentra la lista de franquiciados en el fdd.
- **'Exported with errors to: *fdd_error_output_path*'**: Si el fdd presenta errores y se exporta en formato csv.
- **'Exported to: *results_output_path*'**: Si el fdd se procesa correctamente y se exporta en formato csv (Solo en el modo *dev_mode* en True).
- **'exported to DB'**: Si el fdd se procesa correctamente y se carga en la base de datos (Solo en el modo *dev_mode* en False).

Por último se imprime un resumen de los resultados del procesamiento de los fdds de la siguiente manera:
```
Logs: {'camelot': 0, 'regex': 0, 'already in db': 0, 'franchisees not found': 0, 'invalid methods': 0, 'exceptions': 0}
```
