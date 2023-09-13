import time
import hashlib, json

from requests.exceptions import Timeout
from io import TextIOWrapper
from selenium.common.exceptions import NoSuchElementException

from ....scrapers.playwrightScraper import PlaywrightScraper, PlaywrightScraperConfig
from ....parsers.companiesForSaleParser import get_max_index_national_franchise_sale, get_clean_links_national_franchise_sales
from ....utils.utils import proxySwitcher, STATUS
from ....services.mysql import notify_process


SPIDER_NAME = 'national_franchise_sales'
AFFECTED_TABLE = 'companies_for_sale_nfs'

SEARCHING_URL = 'https://www.nationalfranchisesales.com/listings?utm_medium=email&_hsmi=2&_hsenc=p2ANqtz-_Ju-2kwEam0MeNRcMn47rxUfW2Jv40SdVVO8SyXP9RfQkwmoWBikNXZ3Rm1b0oBOpeptKOYyIECNNPQ8d7qkzp3N8zlDkIm-53CuX4TFpitayKh2Y&utm_content=2&utm_source=hs_email'
PAGINATION_BUTTON_XPATH = '/html/body/g/div/div[2]/div/div[2]/div[2]/div[1]/div/div[3]/div[2]/div/ul/li[{}]/a'
                           
class NationalFranchiseSalesSpiderConfig:
    def __init__(self, logFile, proxy: str = '') -> None:
        self.logFile     = logFile
        self.proxy       = proxy

class NationalFranchiseSalesSpider:

    def __init__(self, nationalFranchiseSalesSpiderConfig: NationalFranchiseSalesSpiderConfig) -> None:
        try :

            self.TABLE_NAME = AFFECTED_TABLE

            proxy = nationalFranchiseSalesSpiderConfig.proxy
            logFile = nationalFranchiseSalesSpiderConfig.logFile

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

        print('upadte')
        SELECT_QUERY = f'SELECT id, checksum \
            FROM {self.TABLE_NAME}\
            WHERE `listing_number`=%s\
            ORDER BY `created_at` DESC\
            LIMIT 1'

        INSERT_QUERY = f'INSERT INTO {self.TABLE_NAME} \
            (`brand`, `sales`, `checksum`, `on_sale`, `updated`, \
            `status`, `additional_info`, `listing_number`, `cash_flow`) \
            values (%s, %s, %s, True, %s, %s, %s, %s, %s)'

        UPDATE_ONSALE_QUERY = f'UPDATE {self.TABLE_NAME} SET on_sale=True WHERE id=%s'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(SELECT_QUERY, [obj['listing_number']])
        row = cursor.fetchone()
        checksum = hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()

        if row == None:
            cursor.execute(INSERT_QUERY,
                            [obj['brand'], obj['sales'], checksum, obj['updated'],
                            obj['status'], obj['additional_info'], obj['listing_number'], obj['cash_flow']])
            self.scraper.conn.commit()

            cursor.close()
            return

        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = dict(zip(column_names, row))

        if data['checksum'] != checksum :
        
            cursor.execute(INSERT_QUERY,
                            [obj['brand'], obj['sales'], checksum, obj['updated'],
                            obj['status'], obj['additional_info'], obj['listing_number'], obj['cash_flow']])
        else :
            cursor.execute(UPDATE_ONSALE_QUERY, [data['id']])

        self.scraper.conn.commit()
        cursor.close()
    
    def set_site(self) -> None:
        self.scraper.set_site(SEARCHING_URL)
        time.sleep(2)

    def get_max_page(self) -> int:
        try :
            res = get_max_index_national_franchise_sale(self.scraper.page.content())
            return res
        except Exception as e :
            print(e)
            print('timeout')

    def get_paginated_items(self, index) -> "tuple[str]":

        self.scraper.set_site(SEARCHING_URL)
        time.sleep(5)

        if index != 2:
            self.scraper.page.locator('xpath=/'+PAGINATION_BUTTON_XPATH.format(index)).click()
            time.sleep(2)

        return get_clean_links_national_franchise_sales(self.scraper.page.content())
        
    def collect_data(self, data: dict):
        try:

            d = {
                'brand' : data['brand'],
                'sales' : data['sales'],
                'cash_flow' : data['cash_flow'],
                'updated' : data['updated'],
                'status' : data['status'],
                'additional_info' : data['additional_info'],
                'listing_number' : data['listing_number'],
            }
            
            self.update_business(d)

        except NoSuchElementException:
            return []
        except Exception as e:
            print(e)
            print('url invalida')


def get_paginated_items(nationalFranchiseSalesSpider: NationalFranchiseSalesSpider) -> "list[str]":

    try :
        nationalFranchiseSalesSpider.set_on_sale()
        results = list()
        nationalFranchiseSalesSpider.set_site()
        max = nationalFranchiseSalesSpider.get_max_page()
        for i in range(2, int(max)+2) :
            results.extend(nationalFranchiseSalesSpider.get_paginated_items(i))

        return results

    except Exception as e :
        print('')
        raise e

def collect_data(url: str, proxy: str, logFile: TextIOWrapper):

    try: 
        bsc = NationalFranchiseSalesSpiderConfig(logFile, proxy)
        bs = NationalFranchiseSalesSpider(bsc)

        bs.collect_data(url)

        bs.scraper.close_session()
    except Timeout:
        print('timeout in site: '+ url)

def run_spider(env: dict, logFile: TextIOWrapper) -> None:
    try :

        from ..companiesForSaleSpider import NAME

        proxies = []

        if 'proxies' in env:
            proxies.extend(env['proxies'])
        
        ps = proxySwitcher(proxies)
        
        bsc = NationalFranchiseSalesSpiderConfig(logFile, next(ps))
        bs = NationalFranchiseSalesSpider(bsc)

        business_urls = get_paginated_items(bs)

        bs.scraper.close_session()

        for business_url in business_urls:
            collect_data(business_url, next(ps), logFile)

        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['SUCCESS'], '')

    except Exception as e:
        print('NationalFranchiseSalesSpider - runSpider')
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['ERROR'], str(e))
        print(e)
        raise e
