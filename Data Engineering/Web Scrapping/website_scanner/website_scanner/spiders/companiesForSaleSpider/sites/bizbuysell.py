import time
import hashlib, json
import re

from requests.exceptions import Timeout
from io import TextIOWrapper
from selenium.common.exceptions import NoSuchElementException

from ....scrapers.playwrightScraper import PlaywrightScraper, PlaywrightScraperConfig
from ....parsers.companiesForSaleParser import get_max_index_bizbuysell, get_clean_links_bizbuysell, check_length, get_clean_amounts_bizquest
from ....utils.utils import proxySwitcher, STATUS
from ....services.mysql import notify_process

SPIDER_NAME = 'bizbuysell'
AFFECTED_TABLE = 'companies_for_sale_bizbuysell'

SEARCHING_BASE = 'https://www.bizbuysell.com'
SEARCHING_URL = '/businesses-for-sale/?q=az1mcmFuY2hpc2UmbHQ9MzAsNDAsODA%3D&utm_medium=email&_hsmi=2&_hsenc=p2ANqtz-9D2KhmtofkIj-RxKM9aCF-_ffZj017SG3D-MkVbxY84gEVFRh2n74tAtFqMDZQD41vIpx1jXSw4xZcLSsIiofDepFt2olXGMoikrenRNMtgwL376s&utm_content=2&utm_source=hs_email'
SEARCHING_URL_BY_PAGE = '/businesses-for-sale/{}/?q=az1mcmFuY2hpc2UmbHQ9MzAsNDAsODA%3D'

FINANCIALS_XPATH = '//*[@id="aspnetForm"]/div[2]/div[2]/div/div/div/div/div[3]/div[1]'
DETAILED_INFO_XPATH = '//*[@id="ctl00_ctl00_Content_ContentPlaceHolder1_wideProfile_listingDetails_dlDetailedInformation"]'
LISTING_NUMBER_XPATH = '//*[@id="premiumListingDetails"]/div[2]/p[1]/b'
TITLE_XPATH = '//*[@id="aspnetForm"]/div[2]/div[2]/div/div/div/div/div[1]/div/h1'
DESCRIPTION_XPATH = '//*[@id="aspnetForm"]/div[2]/div[2]/div/div/div/div/div[3]/div[1]/div[5]'
SELLER_AND_COMPANY_XPATH = '//*[@id="contactForm"]/div/div[2]/div[3]/h3'
AGENT_PHONE_XPATH = '//*[@id="lblViewTpnTelephone_2014459"]/a'
CATEGORY_XPATH = '//*[@id="others"]/a[1]'

class BizbuysellSpiderConfig:
    def __init__(self, logFile, proxy: str = '') -> None:
        self.logFile     = logFile
        self.proxy       = proxy

class BizbuysellSpider:

    def __init__(self, companiesForSaleSpiderConfig: BizbuysellSpiderConfig) -> None:
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
            (`Asking price`, `listing number`,`Cash Flow`,`Gross Revenue`,EBITDA,`FF&E`,Inventory,Rent,`Year Established`,Location,\
            `Inventory Included`,`Real Estate`,`Building SF`,`Lease Expiration`,`Number of Employees`,Franchise,Facilities,Competition,\
            Financing,`Support & Training`,`Home Based`,`Business Website`,`FF&E Included`,`Growth Expansion`,`Reason for Selling`,\
            Title,`Real Estate Value`, `company`, `seller`, `description`, `agent_phone`, `city`, `state`, `category`,`checksum`, `on_sale`) \
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, True)'

        UPDATE_ONSALE_QUERY = f'UPDATE {self.TABLE_NAME} SET on_sale=True WHERE id=%s'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(SELECT_QUERY, [obj['listing_number']])
        row = cursor.fetchone()
        checksum = hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()

        if row == None:
            cursor.execute(INSERT_QUERY,
                            [obj['asking_price'],obj['listing_number'],obj['cash_flow'],obj['gross_revenue'],obj['ebitda'],obj['ff_e'],
                             obj['inventory'],obj['rent'],obj['established'],obj['location'],obj['inventory_included'],obj['real_estate'],
                             obj['building_sf'],obj['lease_expiration'],obj['employees'],obj['franchise'],obj['facilities'],obj['competition'],
                             obj['financing'],obj['support_training'],obj['home_based'],obj['business_website'],obj['ff_e_included'],
                             obj['growth_expansion'],obj['reason_for_selling'],obj['title'],obj['real_estate_value'],
                             obj['company'], obj['seller'], obj['description'], obj['agent_phone'], obj['city'], obj['state'], obj['category'] ,checksum])
            self.scraper.conn.commit()

            cursor.close()
            return

        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = dict(zip(column_names, row))

        if data['checksum'] != checksum :
        
            cursor.execute(INSERT_QUERY,
                            [obj['asking_price'],obj['listing_number'],obj['cash_flow'],obj['gross_revenue'],obj['ebitda'],obj['ff_e'],
                             obj['inventory'],obj['rent'],obj['established'],obj['location'],obj['inventory_included'],obj['real_estate'],
                             obj['building_sf'],obj['lease_expiration'],obj['employees'],obj['franchise'],obj['facilities'],obj['competition'],
                             obj['financing'],obj['support_training'],obj['home_based'],obj['business_website'],obj['ff_e_included'],
                             obj['growth_expansion'],obj['reason_for_selling'],obj['title'],obj['real_estate_value'],
                             obj['company'], obj['seller'], obj['description'], obj['agent_phone'], obj['city'], obj['state'], obj['category'] ,checksum])
        else :
            cursor.execute(UPDATE_ONSALE_QUERY, [data['id']])

        self.scraper.conn.commit()
        cursor.close()
    
    def set_site(self) -> None:
        self.scraper.set_site(SEARCHING_BASE+SEARCHING_URL)
        time.sleep(3)

    def get_max_page(self) -> int:
        try :
            infinite_scroll = "window.scrollTo(0, document.body.scrollHeight)"
            self.scraper.page.evaluate(infinite_scroll)
            time.sleep(2)

            self.logFile['logFile'].write(self.scraper.page.content())
            res = get_max_index_bizbuysell(self.scraper.page.content())
            return res
        except Exception as e :
            print(e)
            print('timeout')

    def get_paginated_items(self, index) -> "tuple[str]":

        if index == 1:
            URL = SEARCHING_BASE+SEARCHING_URL
        else:
            URL = SEARCHING_BASE+SEARCHING_URL_BY_PAGE.format(str(index))

        self.scraper.set_site(URL)
        time.sleep(2)
        return get_clean_links_bizbuysell(self.scraper.page.content(), SEARCHING_BASE)
        
    def collect_data(self, url: str):
        try:
            self.scraper.set_site(url)
            time.sleep(2)

            listing_number = check_length(self.scraper.page.locator('xpath='+LISTING_NUMBER_XPATH).all_inner_texts())
            title = check_length(self.scraper.page.locator('xpath='+TITLE_XPATH).all_inner_texts())
            description = check_length(self.scraper.page.locator('xpath='+DESCRIPTION_XPATH).all_inner_texts())
            seller_and_company = check_length(self.scraper.page.locator('xpath='+SELLER_AND_COMPANY_XPATH).all_inner_texts())
            agent_phone = check_length(self.scraper.page.locator('xpath='+AGENT_PHONE_XPATH).all_inner_texts())
            category = check_length(self.scraper.page.locator('xpath='+CATEGORY_XPATH).all_inner_texts())
            category = category.replace('Businesses for Sale', '')

            a = seller_and_company.lower().replace('\n', ' ').split(':')
            sac = ''
            if len(a) > 1:
                seller = a[1]
                seller = seller.split('phone')
                sac = seller[0].strip()

            d = {
                "description": description,
                "seller": sac,
                "agent_phone": agent_phone,
                "company": sac,
                "category": category,
                "state": '',
                "city": '',
                "asking_price": '',
                "cash_flow": '',
                "gross_revenue": '',
                "ebitda": '',
                "ff_e": '',
                "inventory": '',
                "rent": '',
                "established": '',
                "location": '',
                "inventory_included": '',
                "real_estate": '',
                "building_sf": '',
                "lease_expiration": '',
                "employees": '',
                "franchise": '',
                "facilities": '',
                "competition": '',
                "financing": '',
                "support_training": '',
                "home_based": '',
                "business_website": '',
                "ff_e_included": '',
                "growth_expansion": '',
                "reason_for_selling": '',
                "listing_number": listing_number[4:],
                "title": title,
                "real_estate_value": ''
            }

            financials_field_map = {
                "Gross Revenue:": "gross_revenue",
                "EBITDA:": "ebitda",
                "FF&E:": "ff_e",
                "Inventory:": "inventory",
                "Rent:": "rent",
                "Established:": "established",
                "Real Estate:": "real_estate_value"
            }

            for i in range(2, 4):
                asking_price = check_length(self.scraper.page.locator(f'xpath={FINANCIALS_XPATH}/div[{i}]/div/div[1]/div[1]/p/b').all_inner_texts())
                cash_flow = check_length(self.scraper.page.locator(f'xpath={FINANCIALS_XPATH}/div[{i}]/div/div[1]/div[2]/p/b').all_inner_texts())
                if asking_price != '' or cash_flow != '':
                    d['asking_price'] = get_clean_amounts_bizquest(asking_price)
                    d['cash_flow'] = get_clean_amounts_bizquest(cash_flow)
                for j in range(1, 3):
                    for k in range(1, 4):
                        field_name = check_length(self.scraper.page.locator(f'xpath={FINANCIALS_XPATH}/div[{i}]/div/div[2]/div[{j}]/p[{k}]/span').all_inner_texts())
                        field_value = check_length(self.scraper.page.locator(f'xpath={FINANCIALS_XPATH}/div[{i}]/div/div[2]/div[{j}]/p[{k}]/b').all_inner_texts())
                        if field_name in financials_field_map and field_value != '':
                            d[financials_field_map[field_name]] = get_clean_amounts_bizquest(field_value)
                        elif field_value == '':
                            break
                        else:
                            print(f'Field name not found in map: {field_name}\nURL: {url}')

            detailed_info_field_map = {
                "Location:": "location",
                "Inventory:": "inventory_included",
                "Real Estate:": "real_estate",
                "Building SF:": "building_sf",
                "Lease Expiration:": "lease_expiration",
                "Employees:": "employees",
                "Franchise:": "franchise",
                "Facilities:": "facilities",
                "Competition:": "competition",
                "Financing:": "financing",
                "Support & Training:": "support_training",
                "Home-Based:": "home_based",
                "Business Website:": "business_website",
                "Furniture, Fixtures, & Equipment (FF&E):": "ff_e_included",
                "Growth & Expansion:": "growth_expansion",
                "Reason for Selling:": "reason_for_selling"
            }

            for i in range(1, len(detailed_info_field_map) + 1):
                field_name = check_length(self.scraper.page.locator(f'xpath={DETAILED_INFO_XPATH}/dt[{i}]/strong').all_inner_texts())
                field_value = check_length(self.scraper.page.locator(f'xpath={DETAILED_INFO_XPATH}/dd[{i}]').all_inner_texts())
                if field_name in detailed_info_field_map and field_value != '':
                    if field_name in ("Employees:", "Building SF:"):
                            clean_value = re.search(r'(\d+)', field_value.replace(',', ''))
                            if clean_value:
                                d[detailed_info_field_map[field_name]] = int(clean_value.group(1))
                    else:
                        d[detailed_info_field_map[field_name]] = field_value
                elif field_value == '':
                    break
                else:
                    print(f'Field name not found in map: {field_name}\n URL: {url}')

            if len(d['location'].split(',')) >= 1:
                d['city'] = d['location'].split(',')[0].strip()
                d['state'] = d['location'].split(',')[1].strip()        

            self.update_business(d)

        except NoSuchElementException:
            return []
        except Exception as e:
            print(e)
            print('url invalida')


def get_paginated_items(bizbuysellSpider: BizbuysellSpider) -> "list[str]":

    try :
        bizbuysellSpider.set_on_sale()
        urls = list()
        bizbuysellSpider.set_site()
        max = bizbuysellSpider.get_max_page()
        for i in range(1, int(max)+1) :
            urls.extend(bizbuysellSpider.get_paginated_items(i))
            
            #break #descomenta esto para que te  pagine todo, para desarrollar es mejor mantenerlo
        return urls

    except Exception as e :
        print('error paginating')
        raise e

def collect_data(url: str, proxy: str, logFile: TextIOWrapper):

    try: 
        bsc = BizbuysellSpiderConfig(logFile, proxy)
        bs = BizbuysellSpider(bsc)

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
        
        bsc = BizbuysellSpiderConfig(logFile, next(ps))
        bs = BizbuysellSpider(bsc)
        business_urls = get_paginated_items(bs)

        bs.scraper.close_session()
        
        index = 0
        for business_url in business_urls:
            try :
                print(index)
                collect_data(business_url, next(ps), logFile)
                index += 1
            except Exception as e:
                print(e)

        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['SUCCESS'], '')

    except Exception as e:
        print('BizbuysellSpider - runSpider')
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['ERROR'], str(e))
        print(e)
        raise e
