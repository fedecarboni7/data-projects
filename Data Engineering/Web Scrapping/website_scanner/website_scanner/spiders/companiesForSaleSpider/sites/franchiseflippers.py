import time
import hashlib, json
import re

from requests.exceptions import Timeout
from io import TextIOWrapper

from ....scrapers.playwrightScraper import PlaywrightScraper, PlaywrightScraperConfig
from ....parsers.companiesForSaleParser import get_clean_links_franchise_flippers , get_data_franchise_flippers
from ....utils.utils import proxySwitcher, STATUS
from ....services.mysql import notify_process

SPIDER_NAME = 'franchise_flippers'
AFFECTED_TABLE = 'companies_for_sale_franchise_flippers'

SEARCHING_BASE = 'https://franchiseflippers.com/buy-a-franchise/?cpage=14' # this value is harcoded for a reason 
SEARCHING_URL = '/businesses-for-sale/?q=az1mcmFuY2hpc2UmbHQ9MzAsNDAsODA%3D&utm_medium=email&_hsmi=2&_hsenc=p2ANqtz-9D2KhmtofkIj-RxKM9aCF-_ffZj017SG3D-MkVbxY84gEVFRh2n74tAtFqMDZQD41vIpx1jXSw4xZcLSsIiofDepFt2olXGMoikrenRNMtgwL376s&utm_content=2&utm_source=hs_email'
SEARCHING_URL_BY_PAGE = '/businesses-for-sale/{}/?q=az1mcmFuY2hpc2UmbHQ9MzAsNDAsODA%3D'

class FranchiseFlippersSpiderConfig:
    def __init__(self, logFile, proxy: str = '') -> None:
        self.logFile     = logFile
        self.proxy       = proxy

class FranchiseFlippersSpider:

    def __init__(self, companiesForSaleSpiderConfig: FranchiseFlippersSpiderConfig) -> None:
        try :

            self.TABLE_NAME = AFFECTED_TABLE

            proxy = companiesForSaleSpiderConfig.proxy
            logFile = companiesForSaleSpiderConfig.logFile

            rsc = PlaywrightScraperConfig(proxy=proxy)
            self.scraper = PlaywrightScraper(rsc)
            self.scraper.page.set_default_timeout(timeout = 0)
            self.logFile = logFile

        except Exception as e:
            print(e)
            print('BooleanSpider - init')
            raise e
    
    def set_on_sale(self) -> str:
        cursor = self.scraper.conn.cursor(buffered=True)

        SET_ON_SALE_TO_FALSE_QUERY = f'UPDATE {self.TABLE_NAME} SET `on_sale`=False'

        cursor.execute(SET_ON_SALE_TO_FALSE_QUERY)
        self.scraper.conn.commit()

        cursor.close()

    def update_business(self, obj) -> str:

        SELECT_QUERY = f'SELECT id, checksum \
            FROM {self.TABLE_NAME}\
            WHERE `Listing Number`=%s\
            ORDER BY `created_at` DESC\
            LIMIT 1'

        INSERT_QUERY = f'INSERT INTO {self.TABLE_NAME} \
            (`Asking price`, `listing number`, `checksum`, `on_sale`, \
            `title`, `category`, `county`, `state`, \
            `annual_gross_revenue`, `value_of_inventory`, `value_of_assets`, \
            `business_category`, `business_operates_from`, `years`, \
            `seasonal_business`, `annual_net_profit`, `employees`, `training`, `description`) \
            values (%s, %s, %s, True, %s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s, %s, %s, %s)'

        UPDATE_ONSALE_QUERY = f'UPDATE {self.TABLE_NAME} SET on_sale=True WHERE id=%s'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(SELECT_QUERY, [obj['listing_number']])
        row = cursor.fetchone()
        checksum = hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()

        if row == None:
            cursor.execute(INSERT_QUERY,
                            [obj['asking_price'], obj['listing_number'], checksum,
                            obj['title'],obj['category'],obj['county'],obj['state'],
                            obj['annual_gross_revenue'],obj['value_of_inventory'],obj['value_of_assets'],
                            obj['business_category'],obj['business_operates_from'],obj['years'],
                            obj['seasonal_business'], obj['annual_net_profit'], 
                            obj['employees'], obj['training'], obj['description']])
            self.scraper.conn.commit()

            cursor.close()
            return

        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = dict(zip(column_names, row))

        if data['checksum'] != checksum :
        
            cursor.execute(INSERT_QUERY,
                            [obj['asking_price'], obj['listing_number'], checksum,
                            obj['title'],obj['category'],obj['county'],obj['state'],
                            obj['annual_gross_revenue'],obj['value_of_inventory'],obj['value_of_assets'],
                            obj['business_category'],obj['business_operates_from'],obj['years'],
                            obj['seasonal_business'], obj['annual_net_profit'],
                            obj['employees'], obj['training'], obj['description']])
        else :
            cursor.execute(UPDATE_ONSALE_QUERY, [data['id']])

        self.scraper.conn.commit()
        cursor.close()
    
    def get_paginated_items(self) -> "tuple[str]":

        self.scraper.set_site(SEARCHING_BASE)
        time.sleep(5)
        return get_clean_links_franchise_flippers(self.scraper.page.content())
        
    def collect_data(self, obj: dict):
        try:
            self.scraper.set_site(obj['url'])
            time.sleep(2)

            asking_price = obj['price']
            listing_number = obj['listing number']
            title = obj['title']
            category = obj['category']
            county = obj['county']
            state = obj['state']

            results = get_data_franchise_flippers(self.scraper.page.content())  

            d = {
                "asking_price": int(asking_price[1:].replace(',', '')),
                "listing_number" : listing_number,
                "title" : title,
                "category" : category,
                "county" : county,
                "state" : state,
            }

            d.update(results)

            self.update_business(d)

        except Exception as e:
            print(e)
            print('url invalida')


def get_paginated_items(bizbuysellSpider: FranchiseFlippersSpider) -> "list[str]":

    try :
        bizbuysellSpider.set_on_sale()
        urls = list()
        urls.extend(bizbuysellSpider.get_paginated_items())
        return urls

    except Exception as e :
        print('')
        raise e

def collect_data(obj: dict, proxy: str, logFile: TextIOWrapper):

    try: 
        bsc = FranchiseFlippersSpiderConfig(logFile, proxy)
        bs = FranchiseFlippersSpider(bsc)

        bs.collect_data(obj)

        bs.scraper.close_session()
    except Timeout:
        print('timeout in site: '+ obj['title'])

def run_spider(env: dict, logFile: TextIOWrapper) -> None:
    try :
        from ..companiesForSaleSpider import NAME

        proxies = []

        if 'proxies' in env:
            proxies.extend(env['proxies'])
        
        ps = proxySwitcher(proxies)
        
        bsc = FranchiseFlippersSpiderConfig(logFile, next(ps))
        bs = FranchiseFlippersSpider(bsc)

        business_urls = get_paginated_items(bs)

        bs.scraper.close_session()

        for business_url in business_urls:
            try :
                collect_data(business_url, next(ps), logFile)
            except Exception as e:
                print(e)
        
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['SUCCESS'], '')

    except Exception as e:
        print('FranchiseFlippersSpider - runSpider')
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['ERROR'], str(e))
        print(e)
        raise e
