#from website_scanner import cli, __app_name__
from utils.utils import process_config_file, check_db_connection
from utils.dispatcher import dispatcher

def main():
    try :

        logFile, env = process_config_file()
        context: map = {}
        context['global']: map = {}
        context['global']['logFile'] = logFile
        context['env'] = env

        check_db_connection(context['env']['mysqldb'])
        dispatcher(context)

        # cli.app(prog_name=__app_name__), testing pipeline 5

    except Exception as e:

        print('Main error')
        print(str(e))

if __name__ == "__main__":
    main()
