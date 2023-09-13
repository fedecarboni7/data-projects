import time
import hashlib, json

from requests.exceptions import Timeout
from io import TextIOWrapper
from selenium.common.exceptions import NoSuchElementException

from ....scrapers.playwrightScraper import PlaywrightScraper, PlaywrightScraperConfig
from ....parsers.companiesForSaleParser import get_max_index_wesellrestaurants, get_clean_links_wesellrestaurants, check_length
from ....utils.utils import proxySwitcher, STATUS
from ....services.mysql import notify_process

SPIDER_NAME = 'wesellrestaurants'
AFFECTED_TABLE = 'companies_for_sale_wesellrestaurants'

SEARCHING_URL = 'https://www.wesellrestaurants.com/restaurants-for-sale/Franchise-Resales-Guide?utm_medium=email&_hsmi=2&_hsenc=p2ANqtz-_hZeTQ8LG2hQ8_72d1DOMKeWs8-b5gxyU7hC4SiDzrhBmPLTWUWdCKm5q7sFg0cRtop2bRPuPBPfM19ErCUMOr0wlQ_XDxsz0Vi0qEMj4nU73573E&utm_content=2&utm_source=hs_email'
PAGINATION_BUTTON_XPATH = '/html/body/section[2]/div/div/div[1]/div/div/div/div[2]/div[2]/div[2]/ul/li[{}]'
ASKING_PRICE_XPATH = '/html/body/section[2]/div/div/div[1]/div/div[2]/div[3]/div/div/ul/li[2]'
LISTING_NUMBER_XPATH = '/html/body/section[2]/div/div/div[1]/div/div[2]/div[3]/div/div/ul/li[1]'
LOCATION_XPATH = '/html/body/section[2]/div/div/div[1]/div/div[2]/div[3]/div/div/ul/li[3]'
LEASE_TERM_XPATH = '//*[@id="p-info"]/div/p[1]'
MONTHY_RENT_XPATH = '//*[@id="p-info"]/div/p[2]'
INDOOR_SEATING_XPATH = '//*[@id="p-info"]/div/p[3]'
INSIDE_SQ_FT_XPATH = '//*[@id="p-info"]/div/p[4]'
HOOD_SYSTEM_XPATH = '//*[@id="p-info"]/div/p[5]'
HOUR_OPEN_XPATH = '//*[@id="Operations"]/div/p[1]'
PART_TIME_EMPLOYEES_XPATH = '//*[@id="Operations"]/div/p[2]'
FULL_TIME_EMPLOYEES_XPATH = '//*[@id="Operations"]/div/p[3]'
NET_SALES_XPATH = '//*[@id="finance"]/div/p[1]'
OWNER_BENEFIT_XPATH = '//*[@id="finance"]/div/p[2]'
TITLE_XPATH = '/html/body/section[2]/div/div/div[1]/div/div[2]/h2'
DESCRIPTION_XPATH = '/html/body/section[2]/div/div/div[1]/div/div[2]/div[1]/div'
SELLER_XPATH = '//*[@id="brokerEmailFrm"]/div[1]/div[1]/div[2]/div[1]'
AGENT_PHONE_XPATH = '//*[@id="ofcPhone"]'

class WesellrestaurantsSpiderConfig:
    def __init__(self, logFile, proxy: str = '') -> None:
        self.logFile     = logFile
        self.proxy       = proxy

class WesellrestaurantsSpider:

    def __init__(self, companiesForSaleSpiderConfig: WesellrestaurantsSpiderConfig) -> None:
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
            `location`, `lease term`, `monthly rent`, `indoor seating`, \
            `inside sq ft`, `hood system`, `hour open`, `part time emp`, \
            `full time emp`, `net sales`, `owner benefit`, `title`, `description`,\
            `seller`, `agent_phone`) \
            values (%s, %s, %s, True, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

        UPDATE_ONSALE_QUERY = f'UPDATE {self.TABLE_NAME} SET on_sale=True WHERE id=%s'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(SELECT_QUERY, [obj['listing_number']])
        row = cursor.fetchone()
        checksum = hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()

        if row == None:
            cursor.execute(INSERT_QUERY,
                            [obj['asking_price'], obj['listing_number'], checksum,
                             obj['location'], obj['lease_term'], obj['monthly_rent'], obj['indoor_seating'], 
                             obj['inside_sq_ft'], obj['hood_system'], obj['hour_open'], obj['part_time_emp'], 
                             obj['full_time_emp'], obj['net_sales'], obj['owner_benefit'], obj['title'], 
                             obj['description'], obj['seller'], obj['agent_phone']])
            
            self.scraper.conn.commit()

            cursor.close()
            return

        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = dict(zip(column_names, row))

        if data['checksum'] != checksum :
        
            cursor.execute(INSERT_QUERY,
                            [obj['asking_price'], obj['listing_number'], checksum,
                             obj['location'], obj['lease_term'], obj['monthly_rent'], obj['indoor_seating'], 
                             obj['inside_sq_ft'], obj['hood_system'], obj['hour_open'], obj['part_time_emp'], 
                             obj['full_time_emp'], obj['net_sales'], obj['owner_benefit'], obj['title'],
                             obj['description'], obj['seller'], obj['agent_phone']])
        else :
            cursor.execute(UPDATE_ONSALE_QUERY, [data['id']])

        self.scraper.conn.commit()
        cursor.close()
    
    def set_site(self) -> None:
        self.scraper.set_site(SEARCHING_URL)
        time.sleep(2)

    def get_max_page(self) -> int:
        try :
            res = get_max_index_wesellrestaurants(self.scraper.page.content())
            return res
        except Exception as e :
            print(e)
            print('timeout')

    def get_paginated_items(self, index) -> "tuple[str]":

        self.scraper.set_site(SEARCHING_URL)
        time.sleep(2)

        if index != 1:
            self.scraper.page.locator('xpath=/'+PAGINATION_BUTTON_XPATH.format(index)).click()
            time.sleep(2)

        return get_clean_links_wesellrestaurants(self.scraper.page.content())
        
    def collect_data(self, url: str):
        try:
            self.scraper.set_site(url)
            time.sleep(2)

            asking_price = check_length(self.scraper.page.locator('xpath='+ASKING_PRICE_XPATH).all_inner_texts())
            listing_number = check_length(self.scraper.page.locator('xpath='+LISTING_NUMBER_XPATH).all_inner_texts())
            location = check_length(self.scraper.page.locator('xpath='+LOCATION_XPATH).all_inner_texts())
            lease_term = check_length(self.scraper.page.locator('xpath='+LEASE_TERM_XPATH).all_inner_texts())
            monthly_rent = check_length(self.scraper.page.locator('xpath='+MONTHY_RENT_XPATH).all_inner_texts())
            indoor_seating = check_length(self.scraper.page.locator('xpath='+INDOOR_SEATING_XPATH).all_inner_texts())
            inside_sq_ft = check_length(self.scraper.page.locator('xpath='+INSIDE_SQ_FT_XPATH).all_inner_texts())
            hood_system = check_length(self.scraper.page.locator('xpath='+HOOD_SYSTEM_XPATH).all_inner_texts())
            hour_open = check_length(self.scraper.page.locator('xpath='+HOUR_OPEN_XPATH).all_inner_texts())
            part_time_emp = check_length(self.scraper.page.locator('xpath='+PART_TIME_EMPLOYEES_XPATH).all_inner_texts())
            full_time_emp = check_length(self.scraper.page.locator('xpath='+FULL_TIME_EMPLOYEES_XPATH).all_inner_texts())
            net_sales = check_length(self.scraper.page.locator('xpath='+NET_SALES_XPATH).all_inner_texts())
            owner_benefit = check_length(self.scraper.page.locator('xpath='+OWNER_BENEFIT_XPATH).all_inner_texts())
            description = check_length(self.scraper.page.locator('xpath='+DESCRIPTION_XPATH).all_inner_texts())
            title = check_length(self.scraper.page.locator('xpath='+TITLE_XPATH).all_inner_texts())
            seller = check_length(self.scraper.page.locator('xpath='+SELLER_XPATH).all_inner_texts())
            agent_phone = check_length(self.scraper.page.locator('xpath='+AGENT_PHONE_XPATH).all_inner_texts())

            if asking_price != '':
                asking_price = asking_price.split(':')[1].strip().replace('\n', '').replace(',', '')
            
            if listing_number != '':
                listing_number = listing_number.split(':')[1].strip().replace('\n', '').replace(',', '')

            if location != '':
                location = location.split(':')[1].strip().replace('\n', '').replace(',', '')
            
            if lease_term != '':
                lease_term = lease_term.split(':')[1].strip().replace('\n', '').replace(',', '')
            
            if monthly_rent != '':
                monthly_rent = monthly_rent.split(':')[1].strip().replace('\n', '').replace(',', '')
            
            if indoor_seating != '':
                indoor_seating = indoor_seating.split(':')[1].strip().replace('\n', '').replace(',', '')
            
            if inside_sq_ft != '':
                inside_sq_ft = inside_sq_ft.split(':')[1].strip().replace('\n', '').replace(',', '')
            
            if hood_system != '':
                hood_system = hood_system.split(':')[1].strip().replace('\n', '').replace(',', '')
            
            if hour_open != '':
                hour_open = hour_open.split(':')[1].strip().replace('\n', '').replace(',', '')

            if part_time_emp != '':
                part_time_emp = part_time_emp.split(':')[1].strip().replace('\n', '').replace(',', '')
            
            if full_time_emp != '':
                full_time_emp = full_time_emp.split(':')[1].strip().replace('\n', '').replace(',', '')
            
            if  net_sales != '':
                net_sales = net_sales.split(':')[1].strip().replace('\n', '').replace(',', '')
            
            if owner_benefit != '':
                owner_benefit = owner_benefit.split(':')[1].strip().replace('\n', '').replace(',', '')

            d = {
                "asking_price": int(asking_price[1:]),
                "listing_number" : int(listing_number),
                "location" : location,
                "lease_term" : lease_term,
                "monthly_rent" : monthly_rent,
                "indoor_seating" : indoor_seating,
                "inside_sq_ft" : inside_sq_ft,
                "hood_system" : hood_system,
                "hour_open" : hour_open,
                "part_time_emp" : part_time_emp,
                "full_time_emp" : full_time_emp,
                "net_sales" : net_sales,
                "owner_benefit" : owner_benefit,
                "title" : title,
                "description" : description,
                "seller" : seller,
                "agent_phone" : agent_phone
            }
            

            self.update_business(d)

        except NoSuchElementException:
            return []
        except Exception as e:
            print(e)
            print(listing_number)
            print('url invalida')

def get_paginated_items(wesellrestaurantsSpider: WesellrestaurantsSpider) -> "list[str]":

    try :
        wesellrestaurantsSpider.set_on_sale()
        urls = list()
        wesellrestaurantsSpider.set_site()
        max = wesellrestaurantsSpider.get_max_page()

        for i in range(1, 3):#int(max)+1) :
            urls.extend(wesellrestaurantsSpider.get_paginated_items(i))

        return urls

    except Exception as e :
        print('')
        raise e

def collect_data(url: str, proxy: str, logFile: TextIOWrapper):

    try: 
        bsc = WesellrestaurantsSpiderConfig(logFile, proxy)
        bs = WesellrestaurantsSpider(bsc)

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
        
        bsc = WesellrestaurantsSpiderConfig(logFile, next(ps))
        bs = WesellrestaurantsSpider(bsc)

        business_urls = get_paginated_items(bs)

        bs.scraper.close_session()

        for business_url in business_urls:
            collect_data(business_url, next(ps), logFile)

        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['SUCCESS'], '')

    except Exception as e:
        print('WesellrestaurantsSpider - runSpider')
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['ERROR'], str(e))
        print(e)
        raise e
