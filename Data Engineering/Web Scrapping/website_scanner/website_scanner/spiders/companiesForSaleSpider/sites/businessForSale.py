import time
import hashlib, json
import re

from requests.exceptions import Timeout 
from io import TextIOWrapper
from selenium.common.exceptions import NoSuchElementException

from ....scrapers.playwrightScraper import PlaywrightScraper, PlaywrightScraperConfig
from ....parsers.companiesForSaleParser import get_max_index, get_clean_links_business_for_sale, check_length, get_clean_amounts_bfs
from ....utils.utils import proxySwitcher, STATUS
from ....services.mysql import notify_process

SPIDER_NAME = 'businesses_for_sales'
AFFECTED_TABLE = 'companies_for_sale_bfs'

SEARCHING_URL = 'https://us.businessesforsale.com/us/search/franchise-resale-businesses-for-sale?PageSize=100'
SEARCHING_URL_BY_PAGE = 'https://us.businessesforsale.com/us/search/franchise-resale-businesses-for-sale-{}?PageSize=100'

LISTING_NUMBER_XPATH = '//*[@id="listing-id"]'
TITLE_XPATH = '//*[@id="title-address"]/div[1]/h1'
LOCATION_XPATH = '//*[@id="address"]'
ASKING_PRICE_XPATH = '//*[@id="main-listing-content"]/div[1]/dl[1]/dd/span'
SALES_REVENUE_XPATH = '//*[@id="revenue"]/dd/strong'
CASH_FLOW_XPATH = '//*[@id="profit"]/dd/strong'
PROPERTY_INFORMATION_XPATH = '//*[@id="property-information"]'
BUSINESS_OPERATION_XPATH = '//*[@id="business-operation"]'
OTHER_INFORMATION_XPATH = '//*[@id="other-information"]'
FRANCHISE_INFORMATION_XPATH = '//*[@id="franchise-terms"]'
DESCRIPTION_XPATH = '//*[@id="main-listing-content"]/div[2]/div[1]/div[2]'
LISTED_BY_XPATH = '//*[@id="container"]/div[2]/div[4]/div[2]/div[2]/div[2]/h4'

class BusinessesForSaleSpiderConfig:
    def __init__(self, logFile, proxy: str = '') -> None:
        self.logFile     = logFile
        self.proxy       = proxy

class BusinessesForSaleSpider:

    def __init__(self, companiesForSaleSpiderConfig: BusinessesForSaleSpiderConfig) -> None:
        try :

            self.TABLE_NAME = AFFECTED_TABLE

            proxy = companiesForSaleSpiderConfig.proxy
            logFile = companiesForSaleSpiderConfig.logFile

            rsc = PlaywrightScraperConfig(proxy=proxy)
            self.scraper = PlaywrightScraper(rsc)
            self.scraper.page.set_default_timeout(timeout = 30000)
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
            (`listing number`, `County`, `State`, `Country`, `Asking price`, `Asking price min`, `Asking price max`,\
             `Sales revenue`, `Sales revenue min`, `Sales revenue max`, `Cash flow`, `Cash flow min`, `Cash flow max`,\
             `Franchise opportunity`, `Real state`, `Reason for selling`, `Number of employees`, `Year established`,\
             `Support & Training`, `Owner financing`, `Financing available`, `Furniture / Fixtures value`,\
             `Inventory / Stock value`, `Title`, `Is a Franchise`, `Relocatable`, `Home based`, `Lease terms`,\
             `Leasehold rent`, `Living accommodation`, `Location`, `Premises details`, `Size in square feet`,\
             `Planning consent`, `Trading hours`, `Franchise terms`, `Distressed`, `description`, `company`, `checksum`, `on_sale`) \
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,\
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, True)'

        UPDATE_ONSALE_QUERY = f'UPDATE {self.TABLE_NAME} SET on_sale=True WHERE id=%s'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(SELECT_QUERY, [obj['listing_number']])
        row = cursor.fetchone()
        checksum = hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()

        if row == None:
            cursor.execute(INSERT_QUERY,
                            [ obj['listing_number'], obj['county'], obj['state'], obj['country'], obj['asking_price'],
                              obj['asking_price_min'], obj['asking_price_max'], obj['sales_revenue'], obj['sales_revenue_min'],
                              obj['sales_revenue_max'], obj['cash_flow_range'], obj['cash_flow_min'], obj['cash_flow_max'],
                              obj['franchise_opportunity'], obj['real_state'], obj['reason_for_selling'],
                              obj['number_of_employees'], obj['year_established'], obj['support_training'],
                              obj['owner_financing'], obj['financing_available'], obj['furniture_fixtures_value'],
                              obj['inventory_stock_value'], obj['title'], obj['franchise'], obj['relocatable'], obj['home_based'],
                              obj['lease_terms'], obj['leasehold_rent'], obj['living_accommodation'], obj['location'],
                              obj['premises_details'], obj['size_in_square_feet'], obj['planning_consent'], obj['trading_hours'],
                              obj['franchise_terms'], obj['distressed'], obj['description'], obj['company'], checksum])
            self.scraper.conn.commit()

            cursor.close()
            return

        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = dict(zip(column_names, row))

        if data['checksum'] != checksum :
        
            cursor.execute(INSERT_QUERY,
                            [ obj['listing_number'], obj['county'], obj['state'], obj['country'], obj['asking_price'],
                              obj['asking_price_min'], obj['asking_price_max'], obj['sales_revenue'], obj['sales_revenue_min'],
                              obj['sales_revenue_max'], obj['cash_flow_range'], obj['cash_flow_min'], obj['cash_flow_max'],
                              obj['franchise_opportunity'], obj['real_state'], obj['reason_for_selling'],
                              obj['number_of_employees'], obj['year_established'], obj['support_training'],
                              obj['owner_financing'], obj['financing_available'], obj['furniture_fixtures_value'],
                              obj['inventory_stock_value'], obj['title'], obj['franchise'], obj['relocatable'], obj['home_based'],
                              obj['lease_terms'], obj['leasehold_rent'], obj['living_accommodation'], obj['location'],
                              obj['premises_details'], obj['size_in_square_feet'], obj['planning_consent'], obj['trading_hours'],
                              obj['franchise_terms'], obj['distressed'], obj['description'], obj['company'], checksum])
        else :
            cursor.execute(UPDATE_ONSALE_QUERY, [data['id']])

        self.scraper.conn.commit()
        cursor.close()

    def set_site(self) -> None:
        self.scraper.set_site(SEARCHING_URL)
        time.sleep(2)

    def get_max_page(self, index) -> int:
        try :
            result = self.scraper.page.locator('div.pagination')
            time.sleep(2)

            if index > 1 :
                try:
                    end = result.locator('li.disabled')
                    r= end.inner_html().strip()
                    if r :
                        return -1
                except :
                    print('timeout')
            
            res = get_max_index(result.inner_html())
            return int(res)
        except :
            print('timeout')

    def get_paginated_items(self, index) -> "tuple[str]":

        if index == 1:
            URL = SEARCHING_URL
        else:
            URL = SEARCHING_URL_BY_PAGE.format(str(index))

        self.scraper.set_site(URL)
        time.sleep(2)
        return get_clean_links_business_for_sale(self.scraper.page.content())
        
    def collect_data(self, url: str):
        try:
            self.scraper.set_site(url)
            time.sleep(2)

            listing_number = check_length(self.scraper.page.locator('xpath='+LISTING_NUMBER_XPATH).all_inner_texts())
            location = check_length(self.scraper.page.locator('xpath='+LOCATION_XPATH).all_inner_texts()).split(',')
            asking_price = get_clean_amounts_bfs(check_length(self.scraper.page.locator('xpath='+ASKING_PRICE_XPATH).all_inner_texts()))
            sales_revenue = get_clean_amounts_bfs(check_length(self.scraper.page.locator('xpath='+SALES_REVENUE_XPATH).all_inner_texts()))
            cash_flow = get_clean_amounts_bfs(check_length(self.scraper.page.locator('xpath='+CASH_FLOW_XPATH).all_inner_texts()))
            title = check_length(self.scraper.page.locator('xpath='+TITLE_XPATH).all_inner_texts())
            description = check_length(self.scraper.page.locator('xpath='+DESCRIPTION_XPATH).all_inner_texts())
            company = check_length(self.scraper.page.locator('xpath='+LISTED_BY_XPATH).all_inner_texts())

            print("#######")
            print(company)
            print("#######")

            franchise = 'Yes' if 'franchise' in title.lower() else 'No'

            d = {
                "listing_number" : listing_number,
                "county" : location[-3] if len(location) >= 3 else '',
                "state" : location[-2] if len(location) >= 2 else '',
                "country" : location[-1],
                "asking_price": asking_price[0],
                "asking_price_min": asking_price[1],
                "asking_price_max": asking_price[2],
                "sales_revenue" : sales_revenue[0],
                "sales_revenue_min" : sales_revenue[1],
                "sales_revenue_max" : sales_revenue[2],
                "cash_flow_range" : cash_flow[0],
                "cash_flow_min" : cash_flow[1],
                "cash_flow_max" : cash_flow[2],
                "title" : title,
                "franchise": franchise,
                "description" : description,
                "company" : company,
                "franchise_opportunity" : '',
                "real_state" : '',
                "reason_for_selling" : '',
                "number_of_employees" : '',
                "year_established" : '',
                "support_training" : '',
                "owner_financing" : '',
                "financing_available" : '',
                "furniture_fixtures_value" : '',
                "inventory_stock_value" : '',
                "relocatable" : '',
                "home_based" : '',
                "lease_terms" : '',
                "leasehold_rent" : '',
                "living_accommodation" : '',
                "location" : '',
                "premises_details" : '',
                "size_in_square_feet" : '',
                "planning_consent" : '',
                "trading_hours" : '',
                "franchise_terms" : '',
                "distressed" : ''
            }

            field_name_map = {
                "Reasons for selling:": "reason_for_selling",
                "Employees:": "number_of_employees",
                "Years established:": "year_established",
                "Support & training:": "support_training",
                "Owner financing:": "owner_financing",
                "Financing available:": "financing_available",
                "Furniture / Fixtures value:": "furniture_fixtures_value",
                "Inventory / Stock value:": "inventory_stock_value",
                "Relocatable:": "relocatable",
                "Home based:": "home_based",
                "Lease Terms:": "lease_terms",
                "Leasehold Rent:": "leasehold_rent",
                "Living Accommodation:" : "living_accommodation",
                "Location:" : "location",
                "Premises Details:" : "premises_details",
                "Size in square feet:" : "size_in_square_feet",
                "Planning Consent:" : "planning_consent",
                "Trading hours:" : "trading_hours",
                "Real Estate:" : "real_state",
                "Franchise terms:" : "franchise_terms",
                "Distressed:" : "distressed",
                "Franchise opportunity:" : "franchise_opportunity"
            }

            for xpath in (BUSINESS_OPERATION_XPATH, OTHER_INFORMATION_XPATH, PROPERTY_INFORMATION_XPATH, FRANCHISE_INFORMATION_XPATH):
                for i in range(1, 10):
                    field_name = check_length(self.scraper.page.locator(f'xpath={xpath}/dl[{i}]/dt').all_inner_texts())
                    field_value = check_length(self.scraper.page.locator(f'xpath={xpath}/dl[{i}]/dd/p').all_inner_texts())
                    if field_value == '': field_value = check_length(self.scraper.page.locator(f'xpath={xpath}/dl[{i}]/dd').all_inner_texts())
                    if field_value != '' and field_name in field_name_map:
                        if field_name in ("Furniture / Fixtures value:", "Inventory / Stock value:", "Size in square feet:", "Years established:"):
                            clean_value = re.search(r'(\d+)', field_value.replace(',', ''))
                            if clean_value:
                                if field_name == "Years established:" and len(clean_value.group(1)) < 4:
                                    d[field_name_map[field_name]] = time.localtime().tm_year - int(clean_value.group(1))
                                else:
                                    d[field_name_map[field_name]] = int(clean_value.group(1))
                            continue
                        d[field_name_map[field_name]] = field_value
            
            self.update_business(d)

        except NoSuchElementException:
            return []
        except Timeout:
            self.logFile.write('timeout in site: '+ url)


def get_paginated_items(companiesForSaleSpider: BusinessesForSaleSpider) -> "list[str]":

    try :
        companiesForSaleSpider.set_on_sale()
        urls = list()
        init = 1
        companiesForSaleSpider.set_site()
        max = companiesForSaleSpider.get_max_page(init)
        while True:
            
            for i in range(init, max+1) :
                print(i)
                urls.extend(companiesForSaleSpider.get_paginated_items(i))

            init = max + 1
        
            max = companiesForSaleSpider.get_max_page(init)

            if max == -1 :
                break

        return urls

    except Exception as e :
        print('')
        raise e

def collect_data(url: str, proxy: str, logFile: TextIOWrapper):

    try: 
        cfssc = BusinessesForSaleSpiderConfig(logFile, proxy)
        cfss = BusinessesForSaleSpider(cfssc)

        cfss.collect_data(url)

        cfss.scraper.close_session()
    except Timeout:
        print('timeout in site: '+ url)

def run_spider(env: dict, logFile: TextIOWrapper) -> None:
    #if not validate_schemas(env):
    #    print("invalid env configuration in boolean spider")
    #    return

    try :
        from ..companiesForSaleSpider import NAME

        proxies = []

        if 'proxies' in env:
            proxies.extend(env['proxies'])
        
        ps = proxySwitcher(proxies)
        
        cfssc = BusinessesForSaleSpiderConfig(logFile, next(ps))
        cfss = BusinessesForSaleSpider(cfssc)

        business_urls = get_paginated_items(cfss)
        print('pasa')
        cfss.scraper.close_session()

        for business_url in business_urls:
            print(business_url)
            collect_data(business_url, next(ps), logFile)

        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['SUCCESS'], '')

    except Exception as e:
        print('BusinessesForSaleSpider - runSpider')
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['ERROR'], str(e))
        print(e)
        raise e
