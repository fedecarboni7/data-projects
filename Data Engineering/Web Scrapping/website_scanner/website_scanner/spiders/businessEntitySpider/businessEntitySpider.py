import site
import time
import threading
import asyncio
import csv
import re
import pandas as pd

from os import listdir
from os.path import isfile, join
from concurrent.futures import ThreadPoolExecutor

from io import TextIOWrapper

from ...posProcessors.posProcessors import createCSVForUsersInfoBySearch, add_business_owners
from ...utils.utils import proxySwitcher, orderBusinessEntityFile, createFile
from ...services.mysql import get_proxies

from .usaBusinessEntitties import alabamaSpider, arkansasSpider, californiaSpider, coloradoSpider, floridaSpider, \
    texasSpider, newYorkSpider, connecticutSpider, illinoisSpider, northCarolinaSpider, michiganSpider, delawareSpider, hawaiiSpider, \
    idahoSpider, iowaSpider, kentuckySpider, ohioSpider, kansasSpider, indianaSpider, louisianaSpider, maineSpider, massachusettsSpider, \
    mississippiSpider, montanaSpider


NAME = 'businessEntity_spider'

STATES = [
    alabamaSpider.STATE,
    arkansasSpider.STATE,
    californiaSpider.STATE,
    coloradoSpider.STATE,
    connecticutSpider.STATE,
    floridaSpider.STATE,
    texasSpider.STATE,
    #illinoisSpider.STATE,
    newYorkSpider.STATE,
    northCarolinaSpider.STATE,
    michiganSpider.STATE,
    delawareSpider.STATE,
    hawaiiSpider.STATE,
    idahoSpider.STATE,
    iowaSpider.STATE,
    #ohioSpider.STATE,
    indianaSpider.STATE,
    kansasSpider.STATE,
    kentuckySpider.STATE,
    louisianaSpider.STATE,
    maineSpider.STATE,
    mississippiSpider.STATE,
    massachusettsSpider.STATE,
    montanaSpider.STATE
]

def dispatcher(franchise: str, state: str, selenium_url: str, proxy, twocaptcha_key: str,
               accuracy: str, output_path: str, log_file: TextIOWrapper):

    data = {
        'company': franchise,
        'seleniumUrl': selenium_url,
        'proxy': proxy,
        'logFile': log_file,
        'twocaptchaKey' : twocaptcha_key,
        'accuracy' : accuracy
    }

    try:
        results = list()

        if state.strip() == alabamaSpider.STATE:
            results = alabamaSpider.run_spider(data)
        if state.strip() == arkansasSpider.STATE:
            results = arkansasSpider.run_spider(data)
        if state.strip() == californiaSpider.STATE:
            results = californiaSpider.run_spider(data)
        if state.strip() == coloradoSpider.STATE:
            results = coloradoSpider.run_spider(data)
        if state.strip() == connecticutSpider.STATE:
            results = connecticutSpider.run_spider(data)
        if state.strip() == floridaSpider.STATE:
            results = floridaSpider.run_spider(data)
        if state.strip() == texasSpider.STATE:
            results = texasSpider.run_spider(data)
        #if state.strip() == illinoisSpider.STATE:
        #    results = illinoisSpider.run_spider(data)
        if state.strip() == newYorkSpider.STATE:
            results = newYorkSpider.run_spider(data)
        if state.strip() == northCarolinaSpider.STATE:
            results = northCarolinaSpider.run_spider(data)
        if state.strip() == michiganSpider.STATE:
            results = michiganSpider.run_spider(data)
        if state.strip() == delawareSpider.STATE:
            results = delawareSpider.run_spider(data)
        if state.strip() == hawaiiSpider.STATE:
            results = hawaiiSpider.run_spider(data)
        if state.strip() == idahoSpider.STATE:
            results = idahoSpider.run_spider(data)
        if state.strip() == indianaSpider.STATE:
            results = indianaSpider.run_spider(data)
        if state.strip() == iowaSpider.STATE:
            results = iowaSpider.run_spider(data)
        if state.strip() == kansasSpider.STATE:
            results = kansasSpider.run_spider(data)
        if state.strip() == kentuckySpider.STATE:
            results = kentuckySpider.run_spider(data)
        if state.strip() == louisianaSpider.STATE:
            results = louisianaSpider.run_spider(data)
        #if state.strip() == ohioSpider.STATE:
        #    results = ohioSpider.run_spider(data)
        if state.strip() == maineSpider.STATE:
            results = maineSpider.run_spider(data)
        if state.strip() == mississippiSpider.STATE:
            results = mississippiSpider.run_spider(data)
        if state.strip() == massachusettsSpider.STATE:
            results = massachusettsSpider.run_spider(data)
        if state.strip() == montanaSpider.STATE:
            results = montanaSpider.run_spider(data)

        output_file = f'{output_path}/{state}.csv'

        if not results:
            add_business_owners(state.strip(), franchise, ["NOT FOUND"+"//"+"NOT FOUND"], output_file)
        else :
            
            add_business_owners(state.strip(), franchise, results, output_file)

    except Exception as e:
        raise e

def dispatch_by_list(
    sites, proxies, selenium_url, twocaptchaKey, accuracy, 
    threads, output_path, logFile
    ):
    ps = proxySwitcher(proxies)
    df = pd.read_csv(sites)
    siteList = orderBusinessEntityFile(df.values.tolist())

    _, state = siteList[0]

    if state in STATES:
        output_file = f'{output_path}/{state}.csv'
        add_business_owners('state', 'franchise', ['franchise_found'+'//'+'result'], output_file, True)

    tpool = ThreadPoolExecutor(max_workers=threads)

    for franchise, state in siteList:
        f = tpool.submit(dispatcher, franchise, state, selenium_url, next(ps),
                          twocaptchaKey, accuracy, output_path, logFile)


def run_spider(env: dict, context: dict):

    try:
        selenium_url = env['selenium_url']
        in_folder = env['input_folder_path']
        out_folder = env['output_folder_path']
        threads = env['threads']
        twocaptchaKey = env['twocaptcha_key']
        accuracy = env['accuracy']

        proxies = get_proxies()

        files = [f for f in listdir(in_folder) if isfile(join(in_folder, f))]

        for file in files:
            file_route = f"{in_folder}/{file}"
            dispatch_by_list(
                file_route, proxies, selenium_url, 
                twocaptchaKey, accuracy, threads, out_folder,
                context['logFile']
            )


    except Exception as e:
        print('runSpider error')
        raise e
