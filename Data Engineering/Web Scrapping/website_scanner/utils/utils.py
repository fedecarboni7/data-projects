from datetime import datetime
from io import TextIOWrapper
from yaml.loader import SafeLoader

import yaml
import os

import website_scanner.services.mysql as conn

def get_config_file(logFile) -> dict:
    try:
        with open('config.yaml') as f:
            return yaml.load(f, Loader=SafeLoader)
    except:
        logFile.write(
            "there is no config.yaml file in the root \n")
        raise ("there is no config.yaml file in the root ")

def create_file(fileName : str) -> TextIOWrapper:
    os.umask(0)
    os.makedirs(os.path.dirname(fileName), exist_ok=True, mode=0o777)
    return open(fileName, 'w')

def get_files() -> tuple[TextIOWrapper, dict]:
    now = datetime.now()
    date = now.strftime("%Y-%m-%d_%H:%M:%S")

    # Let's first start by creating a log file
    logFileName = f'{os.getcwd()}/logs/{date}.log'
    logFile = create_file(logFileName)

    # then lets get our config.yaml file

    configFile = get_config_file(logFile)

    return logFile, configFile

def process_config_file() -> tuple[TextIOWrapper, dict]:
    
    logFile, configFile = get_files()
    
    return logFile, configFile

def launch_spider(spider, context) -> None:
    spider.run_spider(context['env'][spider.NAME], context['global'])

def check_db_connection(config) -> None :
    print(os.getcwd())
    try:
        test = conn.DatabasePool()
        test.setConfig(config)
        pool = test.get_pool(1)
        _conn = pool.get_connection()

        if not _conn.is_connected():
            raise ValueError('Invalid credentials or vpn off')

        _conn.close()

    except Exception as e:
        print('Error trying to connect to the database')
        raise e