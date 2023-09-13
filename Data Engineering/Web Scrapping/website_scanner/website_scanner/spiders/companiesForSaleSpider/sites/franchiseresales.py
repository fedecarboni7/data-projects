import time
import hashlib, json

from requests.exceptions import Timeout
from io import TextIOWrapper
from selenium.common.exceptions import NoSuchElementException

from ....scrapers.playwrightScraper import PlaywrightScraper, PlaywrightScraperConfig
from ....parsers.companiesForSaleParser import get_links_wesellrestaurants, check_franchisee_franchiseresale, check_length
from ....utils.utils import proxySwitcher, STATUS
from ....services.mysql import notify_process

SPIDER_NAME = 'franchise_resales'
AFFECTED_TABLE1 = 'companies_for_sale_franchise_resales'
AFFECTED_TABLE2 = 'companies_for_sale_franchise_resales_franchisee'
AFFECTED_TABLE = AFFECTED_TABLE1+'|'+AFFECTED_TABLE2

SEARCHING_URL = 'https://www.franchiseresales.com/franchisors/'
TITLE_XPATH = '//*[@id="span-175-52363"]'
LOCATIONS_XPATH = '//*[@id="code_block-64-52363"]/div/blockquote/ul/li[2]'
INITIAL_INVESTMENT_XPATH = '//*[@id="code_block-64-52363"]/div/blockquote/ul/li[3]'
HEADQUARTERS_XPATH = '//*[@id="code_block-64-52363"]/div/blockquote/ul/li[4]'
CATEGORY_XPATH = '//*[@id="code_block-64-52363"]/div/blockquote/ul/li[5]'
FOUNDED_XPATH = '//*[@id="code_block-64-52363"]/div/blockquote/ul/li[1]'
DESCRIPTION_XPATH = '//*[@id="code_block-64-52363"]/div/blockquote/p[1]'

FRANCHISEE_TITLE_XPATH = '//*[@id="shortcode-9-52280"]'
FRANCHISEE_ASKING_PRICE_XPATH = '//*[@id="shortcode-19-52280"]'
FRANCHISEE_GROSS_SALES_XPATH = '//*[@id="shortcode-307-52379"]'
FRANCHISEE_CASH_FLOW_XPATH = '//*[@id="shortcode-313-52379"]'
FRANCHISEE_EMPLOYEES_XPATH = '//*[@id="shortcode-317-52379"]'
FRANCHISEE_FOUNDED_XPATH = '//*[@id="shortcode-322-52379"]'

class FranchiseResalesSpiderConfig:
    def __init__(self, logFile, proxy: str = '') -> None:
        self.logFile     = logFile
        self.proxy       = proxy

class FranchiseResalesSpider:

    def __init__(self, companiesForSaleSpiderConfig: FranchiseResalesSpiderConfig) -> None:
        try :

            self.TABLE_NAME_1 = AFFECTED_TABLE1
            self.TABLE_NAME_2 = AFFECTED_TABLE2

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

        SET_ON_SALE_TO_FALSE_QUERY = f'UPDATE {self.TABLE_NAME_1} SET `on_sale`=False'

        cursor.execute(SET_ON_SALE_TO_FALSE_QUERY)
        self.scraper.conn.commit()

        cursor.close()

    def remove_franchisee(self, parent_id) :
        REMOVE_FRANCHISEE_QUERY = f"delete from {self.TABLE_NAME_2} where fk_companies_for_sale_franchise_resales_id={str(parent_id)}"
        print(REMOVE_FRANCHISEE_QUERY)
        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(REMOVE_FRANCHISEE_QUERY)
        self.scraper.conn.commit()
        cursor.close()

    def update_business(self, obj) -> str:

        SELECT_QUERY = f'SELECT id, checksum \
            FROM {self.TABLE_NAME_1}\
            WHERE `title`=%s\
            ORDER BY `created_at` DESC\
            LIMIT 1'

        INSERT_QUERY = f'INSERT INTO {self.TABLE_NAME_1} \
            (`checksum`, `title`, `locations` , `initial_investment`, \
            `headquarters`, `category`, `founded`, `on_sale`) \
            values (%s, %s, %s, %s, %s, %s, %s, True)'

        UPDATE_ONSALE_QUERY = f'UPDATE {self.TABLE_NAME_1} SET on_sale=True WHERE id=%s'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(SELECT_QUERY, [obj['title']])
        row = cursor.fetchone()
        checksum = hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()
        parent_id = None

        if row == None:
            cursor.execute(INSERT_QUERY,
                            [checksum, obj['title'], obj['locations'], obj['initial_investment'], 
                             obj['headquarters'], obj['category'], obj['founded']])
            self.scraper.conn.commit()
            parent_id = cursor.lastrowid
            cursor.close()
            return parent_id

        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = dict(zip(column_names, row))

        if parent_id is None :
            parent_id = data['id']

        if data['checksum'] != checksum :
        
            cursor.execute(INSERT_QUERY,
                            [obj['title'], checksum])
        else :
            cursor.execute(UPDATE_ONSALE_QUERY, [data['id']])

        self.scraper.conn.commit()
        cursor.close()

        return parent_id
    
    def update_franchisee(self, obj, parent_id) -> str:

        INSERT_QUERY = f'INSERT INTO {self.TABLE_NAME_2} \
            (`title`,`asking_price`,`gross_sales`,`cash_flow`,`employees`,`founded`,`fk_companies_for_sale_franchise_resales_id`)\
            values (%s, %s, %s, %s, %s, %s, %s)'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(INSERT_QUERY, [obj['title'],obj['asking_price'],obj['gross_sales'],
                                      obj['cash_flow'],obj['employees'],obj['founded'], parent_id])

        self.scraper.conn.commit()
        cursor.close()
    
    def set_site(self) -> None:
        self.scraper.set_site(SEARCHING_URL)
        time.sleep(2)

    def get_links_page(self) -> int:
        try :
            res = get_links_wesellrestaurants(self.scraper.page.content())
            return res
        except Exception as e :
            print(e)
            print('timeout')

    def collect_data(self, url: str):
        try:
            self.scraper.set_site(url)
            time.sleep(2)
    
            title = check_length(self.scraper.page.locator('xpath='+TITLE_XPATH).all_inner_texts())

            locations = check_length(self.scraper.page.locator('xpath='+LOCATIONS_XPATH).all_inner_texts())
            if locations != '':
                locations = locations.split(':')[1].strip().replace('\n', '').replace(',', '')

            initial_investment = check_length(self.scraper.page.locator('xpath='+INITIAL_INVESTMENT_XPATH).all_inner_texts())
            if initial_investment != '':
                initial_investment = initial_investment.split(':')[1].strip().replace('\n', '').replace(',', '')

            headquarters = check_length(self.scraper.page.locator('xpath='+HEADQUARTERS_XPATH).all_inner_texts())
            if headquarters != '':
                headquarters = headquarters.split(':')[1].strip().replace('\n', '').replace(',', '')

            category = check_length(self.scraper.page.locator('xpath='+CATEGORY_XPATH).all_inner_texts())
            if category != '':
                category = category.split(':')[1].strip().replace('\n', '').replace(',', '')

            founded = check_length(self.scraper.page.locator('xpath='+FOUNDED_XPATH).all_inner_texts())
            if founded != '':
                founded = founded.split(':')[1].strip().replace('\n', '').replace(',', '')

            d = {
                "title": title,
                "locations": locations,
                "initial_investment": initial_investment,
                "headquarters": headquarters,
                "category": category,
                "founded": founded,
            }

            parent_id = self.update_business(d)

            results = check_franchisee_franchiseresale(self.scraper.page.content())

            self.remove_franchisee(parent_id)

            for result in results :
                self.collect_data_franchisee(result, parent_id)

        except NoSuchElementException:
            return []
        except Exception as e:
            print(e)
            print('url invalida')

    def collect_data_franchisee(self, url: str, parent_id: str):
        try:
            self.scraper.set_site(url)
            
            time.sleep(2)

            title = check_length(self.scraper.page.locator('xpath='+FRANCHISEE_TITLE_XPATH).all_inner_texts())
            asking_price = check_length(self.scraper.page.locator('xpath='+FRANCHISEE_ASKING_PRICE_XPATH).all_inner_texts())
            gross_sales = check_length(self.scraper.page.locator('xpath='+FRANCHISEE_GROSS_SALES_XPATH).all_inner_texts())
            cash_flow = check_length(self.scraper.page.locator('xpath='+FRANCHISEE_CASH_FLOW_XPATH).all_inner_texts())
            employees = check_length(self.scraper.page.locator('xpath='+FRANCHISEE_EMPLOYEES_XPATH).all_inner_texts())
            founded = check_length(self.scraper.page.locator('xpath='+FRANCHISEE_FOUNDED_XPATH).all_inner_texts())

            d = {
                "title": title,
                "asking_price": asking_price,
                "gross_sales": gross_sales,
                "cash_flow": cash_flow,
                "employees": employees,
                "founded": founded,
            }
            
            self.update_franchisee(d, parent_id)

        except NoSuchElementException:
            return []
        except Exception as e:
            print(e)
            print('url invalida')

def get_paginated_items(franchiseResalesSpider: FranchiseResalesSpider) -> "list[str]":

    try :
        franchiseResalesSpider.set_on_sale()
        urls = list()
        franchiseResalesSpider.set_site()
        urls = franchiseResalesSpider.get_links_page()
        return urls

    except Exception as e :
        print('')
        raise e

def collect_data(url: str, proxy: str, logFile: TextIOWrapper):

    try: 
        bsc = FranchiseResalesSpiderConfig(logFile, proxy)
        bs = FranchiseResalesSpider(bsc)

        bs.collect_data(url)

        bs.scraper.close_session()
    except Exception as e:
        print(e)
        print('timeout in site: '+ url)

def run_spider(env: dict, logFile: TextIOWrapper) -> None:
    try :
        from ..companiesForSaleSpider import NAME

        proxies = []

        if 'proxies' in env:
            proxies.extend(env['proxies'])
        
        ps = proxySwitcher(proxies)
        
        bsc = FranchiseResalesSpiderConfig(logFile, next(ps))
        bs = FranchiseResalesSpider(bsc)

        business_urls = get_paginated_items(bs)

        bs.scraper.close_session()
        
        for business_url in business_urls:
            collect_data(business_url, next(ps), logFile)
        
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['SUCCESS'], '')

    except Exception as e:
        print('FranchiseResalesSpider - runSpider')
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['ERROR'], str(e))
        print(e)
        raise e
