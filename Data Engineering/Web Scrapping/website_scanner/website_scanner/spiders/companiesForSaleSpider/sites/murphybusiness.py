import time
import hashlib, json
import re

from requests.exceptions import Timeout
from io import TextIOWrapper
from selenium.common.exceptions import NoSuchElementException

from ....scrapers.playwrightScraper import PlaywrightScraper, PlaywrightScraperConfig
from ....parsers.companiesForSaleParser import check_length, get_next_index, get_clean_links_murphy
from ....utils.utils import proxySwitcher, STATUS
from ....services.mysql import notify_process

SPIDER_NAME = 'murphybusiness'
AFFECTED_TABLE = 'companies_for_sale_murphy'

SEARCHING_BASE = 'https://murphybusiness.com/business-brokerage/view-our-listings/'

ITEMS_PER_PAGE_XPATH = '//*[@id="per_page"]'
MAX_INDEX_XPATH = '/html/body/div[2]/section[4]/div/div[1]/div[1]/div[2]/ul/li[1]'
NEXT_PAGE_XPATH = '//*[@id="list_div"]/div[1]/div[1]/ul/li[{}]/a'
CATEGORY_BUTTONS_XPATH = '//*[@id="filter-form-cell"]/div/div[2]/div/div[2]/div[2]/div/span/div/div/button[{}]'

ACCOUNT_RECEIVABLE_XPATH      = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[1]/ul/li[1]/span'
ACCOUNT_RECEIVABLE_INCL_XPATH = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[1]/ul/li[2]/span'

INVENTORY_XPATH      = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[2]/ul/li[1]/span'
INVENTORY_INCL_XPATH = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[2]/ul/li[2]/span'

LIABILITIES_XPATH      = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[2]/ul/li[3]/span'
LIABILITIES_INCL_XPATH = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[2]/ul/li[2]/span'

REAL_ESTATE_XPATH      = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[1]/ul/li[3]/span'
REAL_ESTATE_INCL_XPATH = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[1]/ul/li[4]/span'

FF_AND_E_XPATH      = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[3]/ul/li[1]/span'
FF_AND_E_INCL_XPATH = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[3]/ul/li[2]/span'

OTHER_XPATH      = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[3]/ul/li[3]/span'
OTHER_INCL_XPATH = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[3]/ul/li[4]/span'

LEASEHOLD_XPATH      = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[4]/ul/li[1]/span'
LEASEHOLD_INCL_XPATH = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[4]/ul/li[2]/span'

TOTAL_ASSETS_XPATH      = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[4]/ul/li[3]/span'
TOTAL_ASSETS_INCL_XPATH = '/html/body/div[3]/div/div/div[2]/div[2]/div[4]/ul/li[4]/ul/li[4]/span'


class MurphyBusinessSpiderConfig:
    def __init__(self, logFile, proxy: str = '') -> None:
        self.logFile     = logFile
        self.proxy       = proxy

class MurphyBusinessSpider:

    def __init__(self, murphyBusinessSpiderConfig: MurphyBusinessSpiderConfig) -> None:
        try :

            self.TABLE_NAME = AFFECTED_TABLE

            proxy = murphyBusinessSpiderConfig.proxy
            logFile = murphyBusinessSpiderConfig.logFile

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
            (`asking_price`, `down_payment`, `total_sales`, `listing_number`, `title`,\
            `description`, `discretionary_earnings`, `state`,\
            `category`, `relocatable`, \
            `account_rec`, `account_rec_incl`, \
            `real_estate`, `real_estate_incl`, \
            `inventory`, `inventory_incl`, \
            `ff_and_e`, `ff_and_e_incl`, \
            `liabilities`, `liabilities_incl`, \
            `other`, `other_incl`, \
            `leasehold`, `leasehold_incl`, \
            `total_assets`, `total_assets_incl`, \
            `checksum`, `on_sale`) \
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, \
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, True)'


        UPDATE_ONSALE_QUERY = f'UPDATE {self.TABLE_NAME} SET on_sale=True WHERE id=%s'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(SELECT_QUERY, [obj['listing_number']])
        row = cursor.fetchone()
        checksum = hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()

        if row == None:
            cursor.execute(INSERT_QUERY,
                [obj['price'], obj['down_payment'], obj['total_sales'], obj['listing_number'],
                obj['title'], obj['description'], obj['discretionary_earnings'],
                obj['state'], obj['category'], obj['relocatable'],
                obj['account_rec'], obj['account_rec_incl'],
                obj['real_estate'], obj['real_estate_incl'],
                obj['inventory'], obj['inventory_incl'],
                obj['ff_and_e'], obj['ff_and_e_incl'],
                obj['liabilities'], obj['liabilities_incl'],
                obj['other'], obj['other_incl'],
                obj['leasehold'], obj['leasehold_incl'],
                obj['total_assets'], obj['total_assets_incl'],
                checksum]
            )

            
            self.scraper.conn.commit()

            cursor.close()
            return

        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = dict(zip(column_names, row))

        if data['checksum'] != checksum :
        
            cursor.execute(INSERT_QUERY,
                [obj['price'], obj['down_payment'], obj['total_sales'], obj['listing_number'],
                obj['title'], obj['description'], obj['discretionary_earnings'],
                obj['state'], obj['category'], obj['relocatable'],
                obj['account_rec'], obj['account_rec_incl'],
                obj['real_estate'], obj['real_estate_incl'],
                obj['inventory'], obj['inventory_incl'],
                obj['ff_and_e'], obj['ff_and_e_incl'],
                obj['liabilities'], obj['liabilities_incl'],
                obj['other'], obj['other_incl'],
                obj['leasehold'], obj['leasehold_incl'],
                obj['total_assets'], obj['total_assets_incl'],
                checksum]
            )

        else :
            cursor.execute(UPDATE_ONSALE_QUERY, [data['id']])

        self.scraper.conn.commit()
        cursor.close()
    
    def set_site(self) -> None:
        self.scraper.set_site(SEARCHING_BASE)
        time.sleep(3)
        self.scraper.page.locator('xpath='+ITEMS_PER_PAGE_XPATH).select_option('30')
        time.sleep(3)

    def setNextPage(self) -> None:
        index = get_next_index(self.scraper.page.content())
        
        if index == -1:
            return True
        
        self.scraper.page.locator('xpath='+NEXT_PAGE_XPATH.format(index)).click()
        time.sleep(2)
    
    def get_paginated_items(self) -> list:
        
        try :
            return get_clean_links_murphy(self.scraper.page.content())

        except Exception as e :
            print(e)
            self.logFile['logFile'].write(self.scraper.page.content())
            print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')

    def collect_data(self, obj: str):
        try:
            url = obj['link']
            print(url)
            self.scraper.set_site(url)
            time.sleep(2)

            account_rec = self.scraper.page.locator('xpath='+ACCOUNT_RECEIVABLE_XPATH).inner_text()
            account_rec_incl = self.scraper.page.locator('xpath='+ACCOUNT_RECEIVABLE_INCL_XPATH).inner_text()
            real_estate = self.scraper.page.locator('xpath='+REAL_ESTATE_XPATH).inner_text()
            real_estate_incl = self.scraper.page.locator('xpath='+REAL_ESTATE_INCL_XPATH).inner_text()
            inventory = self.scraper.page.locator('xpath='+INVENTORY_XPATH).inner_text()
            inventory_incl = self.scraper.page.locator('xpath='+INVENTORY_INCL_XPATH).inner_text()
            ff_and_e = self.scraper.page.locator('xpath='+FF_AND_E_XPATH).inner_text()
            ff_and_e_incl = self.scraper.page.locator('xpath='+FF_AND_E_INCL_XPATH).inner_text()
            liabilities = self.scraper.page.locator('xpath='+LIABILITIES_XPATH).inner_text()
            liabilities_incl = self.scraper.page.locator('xpath='+LIABILITIES_INCL_XPATH).inner_text()
            other = self.scraper.page.locator('xpath='+OTHER_XPATH).inner_text()
            other_incl = self.scraper.page.locator('xpath='+OTHER_INCL_XPATH).inner_text()
            leasehold = self.scraper.page.locator('xpath='+LEASEHOLD_XPATH).inner_text()
            leasehold_incl = self.scraper.page.locator('xpath='+LEASEHOLD_INCL_XPATH).inner_text()
            total_assets = self.scraper.page.locator('xpath='+TOTAL_ASSETS_XPATH).inner_text()
            total_assets_incl = self.scraper.page.locator('xpath='+TOTAL_ASSETS_INCL_XPATH).inner_text()

            account_rec = account_rec.strip().replace(',', '')
            account_rec = account_rec.replace('$', '')
            account_rec = float(account_rec)

            real_estate = real_estate.strip().replace(',', '')
            real_estate = real_estate.replace('$', '')
            real_estate = float(real_estate)

            inventory = inventory.strip().replace(',', '')
            inventory = inventory.replace('$', '')
            inventory = float(inventory)

            ff_and_e = ff_and_e.strip().replace(',', '')
            ff_and_e = ff_and_e.replace('$', '')
            ff_and_e = float(ff_and_e)

            liabilities = liabilities.strip().replace(',', '')
            liabilities = liabilities.replace('$', '')
            liabilities = float(liabilities)

            other = other.strip().replace(',', '')
            other = other.replace('$', '')
            other = float(other)

            leasehold = leasehold.strip().replace(',', '')
            leasehold = leasehold.replace('$', '')
            leasehold = float(leasehold)

            total_assets = total_assets.strip().replace(',', '')
            total_assets = total_assets.replace('$', '')
            total_assets = float(total_assets)

            asking_price = obj['price'].strip().replace(',', '')
            asking_price = asking_price.replace('$', '')
            asking_price = float(asking_price)

            down_payment = obj['down_payment'].strip().replace(',', '')
            down_payment = down_payment.replace('$', '')
            down_payment = float(down_payment)

            discretionary_earnings = obj['discretionary_earnings'].strip().replace(',', '')
            discretionary_earnings = discretionary_earnings.replace('$', '')
            discretionary_earnings = float(discretionary_earnings)

            total_sales = obj['total_sales'].strip().replace(',', '')
            total_sales = total_sales.replace('$', '')
            total_sales = float(total_sales)

            d = {
                'title' : obj['title'],
                'state' : obj['state'],
                'listing_number' : obj['listing_id'],
                'category' : obj['category'],
                'description' : obj['description'],
                'status' : obj['status'],
                'price' : asking_price,
                'relocatable' : obj['relocatable'],
                'down_payment' : down_payment,
                'discretionary_earnings' : discretionary_earnings,
                'total_sales' : total_sales,
                'description' : obj['description'],
                'account_rec' : account_rec,
                'account_rec_incl' : account_rec_incl,
                'real_estate' : real_estate,
                'real_estate_incl' : real_estate_incl,
                'inventory' : inventory,
                'inventory_incl' : inventory_incl,
                'ff_and_e' : ff_and_e,
                'ff_and_e_incl' : ff_and_e_incl,
                'liabilities' : liabilities,
                'liabilities_incl' : liabilities_incl,
                'other' : other,
                'other_incl' : other_incl,
                'leasehold' : leasehold,
                'leasehold_incl' : leasehold_incl,
                'total_assets' : total_assets,
                'total_assets_incl' : total_assets_incl,
            }

            self.update_business(d)

        except NoSuchElementException:
            return []
        except Exception as e:
            print(e)
            print('url invalida')

def get_paginated_links(murphyBusinessSpider: MurphyBusinessSpider) -> "list[str]":

    try :
        murphyBusinessSpider.set_on_sale()
        urls = list()
        murphyBusinessSpider.set_site()

        while True:
            try:

                urls.extend(murphyBusinessSpider.get_paginated_items())

                out = murphyBusinessSpider.setNextPage()

                if out == True:
                    break

                time.sleep(2)
            except Exception as e:
                print(e)
                
        return urls

    except Exception as e :
        print('error paginating')
        raise e

def collect_data(obj: str, proxy: str, logFile: TextIOWrapper):

    try: 
        bsc = MurphyBusinessSpiderConfig(logFile, proxy)
        bs = MurphyBusinessSpider(bsc)

        bs.collect_data(obj)

        bs.scraper.close_session()
    except Timeout:
        print('timeout in site: '+ obj['link'])

def run_spider(env: dict, logFile: TextIOWrapper) -> None:
    try :
        from ..companiesForSaleSpider import NAME

        proxies = []

        if 'proxies' in env:
            proxies.extend(env['proxies'])
        
        ps = proxySwitcher(proxies)
        
        bsc = MurphyBusinessSpiderConfig(logFile, next(ps))
        bs = MurphyBusinessSpider(bsc)
        business_urls = get_paginated_links(bs)

        bs.scraper.close_session()


        for b in business_urls:
            try :
                
                collect_data(b, next(ps), logFile)

            except Exception as e:
                print('mangp')
                print(e)

        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['SUCCESS'], '')

    except Exception as e:
        print('BizbuysellSpider - runSpider')
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['ERROR'], str(e))
        print(e)
        raise e
