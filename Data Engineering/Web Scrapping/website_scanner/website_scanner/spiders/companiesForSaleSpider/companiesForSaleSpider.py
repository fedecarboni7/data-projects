from io import TextIOWrapper
from .sites import businessForSale, bizmls, bizquest, bizbuysell, franchiseflippers,\
    wesellrestaurants, nationalfranchisesales, franchiseresales, bizben, murphybusiness
from ...services.mysql import get_proxies

NAME = 'companiesForSale_spider'

def run_spider(env: dict, logFile: TextIOWrapper):

    env['proxies'] = get_proxies()

    spider = env['spider']

    if spider == "bizmls" :
        bizmls.run_spider(env, logFile)
    elif spider == "businessesforsale" :
        businessForSale.run_spider(env, logFile)
    elif spider == "bizquest" :
        bizquest.run_spider(env, logFile)
    elif spider == "bizbuysell" :
        bizbuysell.run_spider(env, logFile)
    elif spider == "franchiseflippers" :
        franchiseflippers.run_spider(env, logFile)
    elif spider == "wesellrestaurants" :
        wesellrestaurants.run_spider(env, logFile)
    elif spider == "nationalfranchisesales" :
        nationalfranchisesales.run_spider(env, logFile)
    elif spider == "franchiseresales" :
        franchiseresales.run_spider(env, logFile)
    elif spider == "bizben" :
        bizben.run_spider(env, logFile)
    elif spider == "murphybusiness" :
        murphybusiness.run_spider(env, logFile)
    else :
        print('invalid option in config.yaml')