import pandas as pd

from ....posProcessors.posProcessors import fba_info_add_result
from ....utils.utils import proxySwitcher, STATUS
from .e2VisaSites.fbaSpider import run_spider as fba_runSpider
from ....services.mysql import get_proxies, notify_process

NAME = 'fba_info_spider'

def dispatch_by_list(creds, selenium_url, siteList, inFile, proxies, outFile, logFile):

    ps = proxySwitcher(proxies)

    fba_info_add_result('', '', '', '', '', '', '', '', inFile, outFile, True)
    config = {
        'proxy': next(ps),
        'companies' : siteList,
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
        inFile = env['input_file_path']
        outFile = env['output_file_path']
        threads = env['threads']

        creds = {
            'fba' : env['fba_credentials']
        }
        
        proxies = get_proxies()

        df = pd.read_csv(inFile)
        siteList = df.loc[:,"owner"].values.tolist()

        dispatch_by_list(
            creds, selenium_url, siteList, inFile, proxies, 
            outFile, context['logFile']
        )

        notify_process("FBA", NAME,'', STATUS['SUCCESS'], '')
        
    except Exception as e:
        print('runSpider error')
        notify_process("FBA", NAME, '', STATUS['ERROR'], str(e))
        raise e
