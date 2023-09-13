# Website Scanner

Como el nombre lo indica, WS permite extraer data directamente de el HTML de los sitios web, no importa si tiene SSR el HTML que verias en tu navegador tambien es extraible por WS.

## Caracteristicas

1. Soporta Login en sitios web.
2. compatibilidad con Selenium y playwright para analizar sitios con SSR (mas headless browsers en camino).
3. Arañas preconfiguradas para extraer data de sitios  web populares.

## Instalacion

Existen dos formas de correr WS, la primera es directamente sobre su maquina y la segunda es levantarlo con docker.

### Directamente en el servidor

Para instalar el proyecto sin usar docker asegurate de tener las siguientes dependencias

* Python >3.10
* La ultima version de selenium
* La ultima version de playwright
* Una instancia de mysql

### Con Docker (Recomendado)

Para correr el proyecto usando docker asegurate de tenerlo correctamente configurado y con la version al dia mas 2Gb de espacio en disco duro libre.

[Como instalar docker en linux](https://docs.docker.com/engine/install/ubuntu/)

Una vez tengas docker instalado basta con moverte al root del proyecto y ejecutar los siquientes comandos

```
sudo docker compose build # Construimos el proyecto
sudo docker compose up -d
```

podemos ver que los contenedores estan corriendo con el comando :

```
sudo docker ps
```
![Contenedores](./docs/assets/contenedores.png?raw=true "containers")

ingresamos al contenedor con el comando :

```
sudo docker exec -it {container_id} bash
```

en este caso seria e882efcbea37

```
sudo docker exec -it e882efcbea37 bash
```
![Inside](./docs/assets/inside_container.png?raw=true "inside")
## Uso

El uso basico parte de el archivo de configuracion (config.yaml), archivo que siempre debe estar en el root del proyecto antes de correrlo.

El archivo consta de multiples configuraciones de las arañas disponibles, asi si necesitas usar una araña solo basta con 
definirla en el archivo de configuracion antes de ejecutarlo, y de necesitar mas, basta con solo definirla despues (actualmente la ejecucion de multiples arañas a la vez esta en pausa).

por ejemplo si necesitas solo determinar si un sitio web cumple con tener algun patron de palabras o numeros en particular
bastaria con simplemente definirlo de la siguiente manera.

```
boolean_spider:

  - input_file_path: ./testBoolean.csv
    output_file_path: ./result/results_boolean.csv
    regex: 
      - 'object and pass in our loaded YAM'
      - 'objecto|manzana'
      - 'obje..'
```

esta es la configuracion mas basica posible, un archivo de entrada con formato csv donde debe estar el listado de urls, un archivo de salida donde quieres los resultados y una o multiples expresiones regex.

Un archivo con dos arañas luciria de la siguiente forma

```
linkedin_spider:
  linkedin_login_username:
  linkedin_login_password:
  selenium_url: http://chrome:4444/wd/hub

  configs:
    - input_file_path: ./test.csv
      output_file_path: ./result/results.csv
      action: GET_CONTACT_INFO

    - input_file_path: ./test_by_search.csv
      output_file_path: ./result/results_searchs.csv
      max_number_of_matches: 3
      action: GET_CONTACT_INFO_BY_SEARCH


boolean_spider:

  - input_file_path: ./testBoolean.csv
    output_file_path: ./result/results_boolean.csv
    regex: 
      - 'object and pass in our loaded YAM'
      - 'objecto|manzana'
      - 'obje..'

```
## arañas disponibles

Cuando ejecutamos la busqueda de data lo hacemos a partir de arañas. Cada una no es mas que la logica que quieres aplicar a la busqueda. 

Para definir que tipo de scraping queremos aplicar basta con añadir la araña correspondiente al archivo de config.yaml.

Hay una excepcion en las arañas y es una que siempre debe ir, aunque actua mas como data para ciertas configuraciones que como una araña en si

```
mysqldb:
  host: host.com
  port: 3306
  user: user
  password: password
  database: database
```

sin importar que tipo de scraping quieras aplicar siempre es importante definir la base de datos a usar

### Boolean spider

input_file_path : la ubicacion del CSV de urls a escrapear, posee el siguiente formato :
```
ulr
https://www.url.com/in/a/
https://www.url2.com/in/b/
https://www.url3.com/in/c/
```

output_file_path : la ruta del CSV con la data obtenida
regex : un array de expresiones regulares para buscar de los sitios en input_file_path

ejm = 

```
boolean_spider:

  - input_file_path: ./testBoolean.csv
    output_file_path: ./result/results_boolean.csv
    regex: 
      - 'object and pass in our loaded YAM'
      - 'objecto|manzana'
      - 'obje..'
```
### Linkedin spider

Esta araña posee multiples funcionalidades, las cuales se determinan a travez del parametro action, la estructura es la siguiente :

```
linkedin_spider:
  linkedin_login_username: usuario@gmail.com
  linkedin_login_password: passw1234
  selenium_url: http://chrome:4444/wd/hub

  configs:
    - input_file_path: ./test.csv
      output_file_path: ./result/results.csv
      action: GET_CONTACT_INFO

    - input_file_path: ./test_by_search.csv
      output_file_path: ./result/results_searchs.csv
      max_number_of_matches: 3
      action: GET_CONTACT_INFO_BY_SEARCH
```
linkedin_login_username: tu usuario de linkedin
linkedin_login_password: tu contraseña de linkedin
selenium_url: la url de la instancia de selenium
input_file_path : la ubicacion del CSV de urls de linkedin a escrapear, mas adelante se especificara su estructura dependiendo de el action
output_file_path : la ruta del CSV con la data obtenida
action : el tipo de scrapeo en linkedin que quieres realizar

#### Actions

##### GET_CONTACT_INFO
se usa para a partir de una lista de urls de linkedin obtener la info de contacto
el campo input_file_path debe tener esta forma
```
ulr
https://www.linkedin.com/in/a/
https://www.linkedin.com/in/b/
https://www.linkedin.com/in/c/
```
##### GET_CONTACT_INFO_BY_SEARCH
se usa para a partir de una lista de nombres obtener resultados que coincidan con los nombres
```
pattern
jorge arroyo
hilmer vivas
araque simon
federico carboni
```
cuando se usa este action hay un atributo extra que es necesario pasar
max_number_of_matches: se usa para indicar cual es el maximo numero de resultados que quieres obtener por match
### business entity spider
### FDD gathering spider
twocaptcha_key : para tener esta key primero necesitas una cuenta en twocaptcha
```
fddGathering_spider:
  twocaptcha_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxx
  threads: 1
  selenium_url: http://chrome:4444/wd/hub
  input_file_path: ./tests/assets/franchise_names.csv
  fdd_path: ./downloads/
  proxies:
    - http://104.144.215.139:3128
    - http://107.172.97.37:3128
    - http://107.152.249.101:3128
    - http://107.152.248.26:3128
    - http://107.152.173.113:3128

```

el archivo de entrada tiene la siguiente forma
```
name
crunch
gym
test
```
### Companies for sale spider

para esta araña solo basta con los proxies
```
companiesForSale_spider:
  spider: bizbuysell #'franchiseresales' #'bizmls' 'businessesforsale' 'bizquest' 'bizbuysell' 'franchiseflippers' 'wesellrestaurants' 'nationalfranchisesales' 'franchiseresales'
```
### FBA Spiders

#### FBA get all members names

```
fba_members_spider:
  selenium_url: http://chrome:4444/wd/hub
  output_file_path: ./tests/assets/fba_members_results.csv
  threads: 1
  fba_credentials:
    username: fba_user
    password: fba_pwd
  proxies:
    - http://104.144.252.20:3128
    - http://107.172.97.37:3128
    - http://107.152.249.101:3128
    - http://107.152.248.26:3128
    - http://107.152.173.113:3128
```

#### FBA get all members info

```
fba_all_members_info_spider:
  selenium_url: http://chrome:4444/wd/hub
  output_file_path: ./tests/assets/fba_all_members_info_results.csv
  threads: 1
  fba_credentials:
    username: fba_user
    password: fba_pwd
  proxies:
    - http://104.144.252.20:3128
    - http://107.172.97.37:3128
    - http://107.152.249.101:3128
    - http://107.152.248.26:3128
    - http://107.152.173.113:3128
```

#### FBA get member info by name

```
fba_info_spider
  selenium_url: http://chrome:4444/wd/hub
  input_file_path: ./tests/assets/fba_owners_names.csv
  output_file_path: ./tests/assets/fba_owners_results.csv
  threads: 1
  fba_credentials:
    username: fba_user
    password: fba_pwd
  proxies:
    - http://104.144.252.20:3128
    - http://107.172.97.37:3128
    - http://107.152.249.101:3128
    - http://107.152.248.26:3128
    - http://107.152.173.113:3128
```

### Business Entity spider
### Fdd gathering spider

## Para desarrolladores

El proyecto hace uso de la libreria Website Scanner (del mismo nombre del proyecto). Hay tres conceptos basicos que entender para hacer uso de esta : Parser, Scraper, Spider.

Parser: un Parser es simplemente una funciona que toma una data extraida de una web y la procesa en el formato
o tipo de dato que sea necesaria.

Scraper: un Scraper actua como la pieza de codigo especifica que se encarga de interpretar el sitio web y 
devolver la informacion que detecta, tambien sirve para interactuar con cualquier elemento como un boton, un
desplegable o el html en general.

Spider: la araña o spider es el elemento del codigo que une todas las demas funcionalidades para producir un
tipo de scraping especifico, por lo tanto puede estar conformado de varios parsers y scrapers, aunque de este
ultimo, lo normal es solo usar uno por araña.

Otros conceptos importantes de aprender son el de postprocessor y service.

Posprocessor: en cualquier proceso de extraccion de datos hay que almacenarlos, aqui entra en juego los 
Posprocessors, basicamente encapsulan la logica de almacenamiento de los datos (db o archivos) aunque no son
indispensables, es posible crear tu propia solucion de almacenamiento local

Services: un Service es cualquier dependencia que requiera del uso de una peticion http/s para funcionar 
(en general cualquier servicio remoto, como una base de datos o 2captcha)
