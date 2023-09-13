import time
import hashlib, json
import re

from requests.exceptions import Timeout
from io import TextIOWrapper
from selenium.common.exceptions import NoSuchElementException

from ....scrapers.playwrightScraper import PlaywrightScraper, PlaywrightScraperConfig
from ....parsers.companiesForSaleParser import get_clean_links_bizben, get_number_of_category_buttons, check_length, get_clean_amounts_bizquest
from ....utils.utils import proxySwitcher, STATUS
from ....services.mysql import notify_process

SPIDER_NAME = 'bizben'
AFFECTED_TABLE = 'companies_for_sale_bizben'

SEARCHING_BASE = 'https://www.bizben.com/todays-new-revised-business-for-sale.php'
SEARCHING_BASE_URL =  'https://www.bizben.com'
SEARCH_BUTTON_XPATH = '//*[@id="filter-form-cell"]/div/div[4]/div[1]/input'

MAX_INDEX_XPATH = '/html/body/div[2]/section[4]/div/div[1]/div[1]/div[2]/ul/li[1]'
NEXT_PAGE_XPATH = '/html/body/div[2]/section[4]/div/div[1]/div[1]/div[2]/ul/li[{}]/a'
CATEGORY_BUTTONS_XPATH = '//*[@id="filter-form-cell"]/div/div[2]/div/div[2]/div[2]/div/span/div/div/button[{}]'

LISTING_NUMBER_XPATH = '/html/body/div[2]/div/div[1]/ul[2]/li[2]/p/span'
TITLE_XPATH = '/html/body/div[2]/div/div[1]/h1/span[1]'
DESCRIPTION_XPATH = '/html/body/div[2]/section/div/div[1]/div/div[2]/div'
AGENT_XPATH = '/html/body/div[2]/section/div/div[1]/div/div[3]/ol/li[1]/span'
AGENT_PHONE_1_XPATH = '/html/body/div[2]/section/div/div[1]/div/div[3]/ol/li[3]/span[2]'
AGENT_PHONE_2_XPATH = '/html/body/div[2]/section/div/div[1]/div/div[3]/ol/li[2]/span[2]'
ASKING_PRICE_XPATH = '/html/body/div[2]/div/div[2]/div/p[1]'
AREA_XPATH = '/html/body/div[2]/section/div/div[1]/div/div[4]/ol[2]/li[1]/p/span'
CASH_FLOW_XPATH = '/html/body/div[2]/section/div/div[1]/div/div[4]/ol[1]/li[3]/p/span'
REVENUE_XPATH = '/html/body/div[2]/section/div/div[1]/div/div[4]/ol[1]/li[4]/p/span'
CITY_XPATH = '/html/body/div[2]/section/div/div[1]/div/div[4]/ol[2]/li[2]/p/span'

class BizbenSpiderConfig:
    def __init__(self, logFile, proxy: str = '') -> None:
        self.logFile     = logFile
        self.proxy       = proxy

class BizbenSpider:

    def __init__(self, BizbenSpiderConfig: BizbenSpiderConfig) -> None:
        try :

            self.TABLE_NAME = AFFECTED_TABLE

            proxy = BizbenSpiderConfig.proxy
            logFile = BizbenSpiderConfig.logFile

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
            WHERE `listing_number`=%s\
            ORDER BY `created_at` DESC\
            LIMIT 1'

        INSERT_QUERY = f'INSERT INTO {self.TABLE_NAME} \
            (`asking_price`, `revenue`, `listing_number`,`cash_flow`, `title` , area,\
            `description`, `agent`, `agent_phone_1`, `agent_phone_2`, `city`, `industry`,\
            `category`,`checksum`, `on_sale`) \
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, True)'

        UPDATE_ONSALE_QUERY = f'UPDATE {self.TABLE_NAME} SET on_sale=True WHERE id=%s'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(SELECT_QUERY, [obj['listing_number']])
        row = cursor.fetchone()
        checksum = hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()

        if row == None:
            cursor.execute(INSERT_QUERY,
                            [obj['asking_price'], obj['revenue'], obj['listing_number'],obj['cash_flow'],\
                            obj['title'], obj['area'], obj['description'], obj['agent'], obj['agent_phone_1'], obj['agent_phone_2'],\
                            obj['city'],  obj['industry'], obj['category'] ,checksum])
            self.scraper.conn.commit()

            cursor.close()
            return

        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = dict(zip(column_names, row))

        if data['checksum'] != checksum :
        
            cursor.execute(INSERT_QUERY,
                            [obj['asking_price'], obj['revenue'], obj['listing_number'],obj['cash_flow'],\
                            obj['title'], obj['area'],obj['description'], obj['agent'], obj['agent_phone_1'], obj['agent_phone_2'],\
                            obj['city'],  obj['industry'], obj['category'] ,checksum])
        else :
            cursor.execute(UPDATE_ONSALE_QUERY, [data['id']])

        self.scraper.conn.commit()
        cursor.close()
    
    def set_site(self) -> None:
        self.scraper.set_site(SEARCHING_BASE)
        time.sleep(3)

    def set_site_by_category(self, index) -> None:
        self.scraper.set_site(SEARCHING_BASE)
        time.sleep(2)
        self.scraper.page.evaluate("document.evaluate('"+CATEGORY_BUTTONS_XPATH.format(index)+"', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()")
        self.scraper.page.locator('xpath='+SEARCH_BUTTON_XPATH).click()
        time.sleep(2)

    def get_max_page(self) -> int:
        try :
            max_index = check_length(self.scraper.page.locator('xpath='+MAX_INDEX_XPATH).all_inner_texts())
            aux = max_index.split(' ')
            if len(aux) > 1:
                return int(aux[-1])
                           
        except Exception as e :
            print(e)
            print('timeout')

    def get_number_of_categories(self) -> int:
        return get_number_of_category_buttons(self.scraper.page.content())
    
    def get_paginated_items(self, index) -> "tuple[str]":
        
        try :
            xpath = NEXT_PAGE_XPATH.format(2)
            if index > 1:
                xpath = NEXT_PAGE_XPATH.format(3)

            results = get_clean_links_bizben(self.scraper.page.content())
            self.scraper.page.locator('xpath='+xpath).click()
            time.sleep(2)

            print(len(results))

            return results
        except Exception as e :
            print(e)
            self.logFile['logFile'].write(self.scraper.page.content())
            print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')

    def collect_data(self, url: str, category):
        try:
            self.scraper.set_site(SEARCHING_BASE_URL+url)
            time.sleep(2)

            print(category['industry'] + " - " +category['category'])
            

            listing_number = check_length(self.scraper.page.locator('xpath='+LISTING_NUMBER_XPATH).all_inner_texts())
            title = check_length(self.scraper.page.locator('xpath='+TITLE_XPATH).all_inner_texts())
            description = check_length(self.scraper.page.locator('xpath='+DESCRIPTION_XPATH).all_inner_texts())
            agent = check_length(self.scraper.page.locator('xpath='+AGENT_XPATH).all_inner_texts())
            agent_phone_1 = check_length(self.scraper.page.locator('xpath='+AGENT_PHONE_1_XPATH).all_inner_texts())
            agent_phone_1 = agent_phone_1.lower().replace('text', '')
            agent_phone_2 = check_length(self.scraper.page.locator('xpath='+AGENT_PHONE_2_XPATH).all_inner_texts())
            agent_phone_2 = agent_phone_2.lower().replace('cell', '')
            
            asking_price = check_length(self.scraper.page.locator('xpath='+ASKING_PRICE_XPATH).all_inner_texts())
            asking_price = asking_price.lower()
            if 'call' in asking_price or 'email' in asking_price or '/' in asking_price or 'n' in asking_price or 's' in asking_price:
                asking_price = None
            else :
                asking_price = asking_price.strip().replace(',', '')
                asking_price = asking_price.replace('$', '')
                asking_price = float(asking_price)
            
            area = check_length(self.scraper.page.locator('xpath='+AREA_XPATH).all_inner_texts())
            
            cash_flow = check_length(self.scraper.page.locator('xpath='+CASH_FLOW_XPATH).all_inner_texts())
            cash_flow = cash_flow.lower()
            if 'call' in cash_flow or 'email' in cash_flow or '/' in cash_flow or 'n' in cash_flow or 's' in cash_flow:
                cash_flow = None
            else :
                cash_flow = cash_flow.strip().replace(',', '')
                cash_flow = cash_flow.replace('$', '')  # Elimina el signo de dólar
                cash_flow = float(cash_flow)

            revenue = check_length(self.scraper.page.locator('xpath='+REVENUE_XPATH).all_inner_texts())
            revenue = revenue.lower()
            if 'call' in revenue or 'email' in revenue or '/' in revenue or 'n' in revenue or 's' in revenue:
                revenue = None
            else :
                revenue = revenue.strip().replace(',', '')
                revenue = revenue.replace('$', '')
                revenue = float(revenue)

            city = check_length(self.scraper.page.locator('xpath='+CITY_XPATH).all_inner_texts())

            
            d = {
                "description": description,
                "listing_number": listing_number,
                "title": title,
                "agent": agent,
                "agent_phone_2": agent_phone_2,
                "agent_phone_1": agent_phone_1,
                "asking_price": asking_price,
                "area": area,
                "cash_flow": cash_flow,
                "revenue": revenue,
                "city": city,
                "category": category['category'],
                "industry": category['industry'],
            }

            self.update_business(d)

        except NoSuchElementException:
            return []
        except Exception as e:
            print(e)
            print('url invalida')


def get_paginated_links_by_category(bizbenSpider: BizbenSpider) -> "list[str]":

    try :
        #bizbuysellSpider.set_on_sale()
        urls = list()
        bizbenSpider.set_site()
        categories = bizbenSpider.get_number_of_categories()

        for category in categories:
            print(str(category['index']) +" : " +category['category'])
            bizbenSpider.set_site_by_category(category['index'])
            max = bizbenSpider.get_max_page()
            for i in range(1, 2): #int(max)+1) :
                urls.append({
                    'category':category,
                    'urls':bizbenSpider.get_paginated_items(i)
                })
    
        return urls

    except Exception as e :
        print('error paginating')
        raise e

def collect_data(url: str, category, proxy: str, logFile: TextIOWrapper):

    try: 
        bsc = BizbenSpiderConfig(logFile, proxy)
        bs = BizbenSpider(bsc)

        bs.collect_data(url, category)

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
        
        bsc = BizbenSpiderConfig(logFile, next(ps))
        bs = BizbenSpider(bsc)
        business_urls = get_paginated_links_by_category(bs)

        bs.scraper.close_session()


        for business_url_subgroup in business_urls:
            try :
                for business_url in business_url_subgroup['urls']:
                    collect_data(business_url, business_url_subgroup['category'], next(ps), logFile)

            except Exception as e:
                print('mangp')
                print(e)

        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['SUCCESS'], '')

    except Exception as e:
        print('BizbuysellSpider - runSpider')
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['ERROR'], str(e))
        print(e)
        raise e
