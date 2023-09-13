from ....utils.utils import proxySwitcher, STATUS
from .e2VisaSites.fbaSpider import run_spider as fba_runSpider
from ....services.mysql import get_proxies, notify_process

NAME = 'fba_members_spider'

def dispatch_by_list(creds, selenium_url, proxies, outFile, logFile):

    ps = proxySwitcher(proxies)

    config = {
        'proxy': next(ps),
        'seleniumUrl': selenium_url,
        'logFile': logFile,
        'username' : creds['fba']['username'],
        'password' : creds ['fba']['password'],
        'output_path' : outFile
    }

    fba_runSpider(config)


def run_spider(env: dict, context: dict):

    try:
        selenium_url = env['selenium_url']
        outFile = env['output_file_path']
        threads = env['threads']

        creds = {
            'fba' : env['fba_credentials']
        }
        
        proxies = get_proxies()

        dispatch_by_list(
            creds, selenium_url, proxies, 
            outFile, context['logFile']
        )

        notify_process("FBA", NAME,'', STATUS['SUCCESS'], '')
    except Exception as e:
        print('runSpider error')
        notify_process("FBA", NAME, '', STATUS['ERROR'], str(e))
        raise e
