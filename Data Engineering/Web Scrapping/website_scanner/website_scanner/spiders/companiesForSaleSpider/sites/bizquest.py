import time
import hashlib, json
import re

from requests.exceptions import Timeout
from io import TextIOWrapper
from selenium.common.exceptions import NoSuchElementException

from ....scrapers.playwrightScraper import PlaywrightScraper, PlaywrightScraperConfig
from ....parsers.companiesForSaleParser import get_max_index_bizquest, get_clean_links_bizquest, check_length, get_clean_amounts_bizquest, get_clean_amounts_bfs
from ....utils.utils import proxySwitcher, STATUS
from ....services.mysql import notify_process

SPIDER_NAME = 'bizquest'
AFFECTED_TABLE = 'companies_for_sale_bizquest'

SEARCHING_URL = 'https://www.bizquest.com/businesses-for-sale/?q=az1mcmFuY2hpc2Uma2g9MSZvc3M9ZnJhbmNoaXNl&utm_medium=email&_hsmi=2&_hsenc=p2ANqtz--TWnVngjpEcklj9-O46QlTvmzedBKMb0bCDqggj8oK32ICpCw4Dbw3B2GVVrhzDKle4sTlvinK_oCLKzrLRwZD7VR30UNiNuV1AD76pI11VY9nH4I&utm_content=2&utm_source=hs_email'
SEARCHING_URL_BY_PAGE = 'https://www.bizquest.com/businesses-for-sale/page-{}/?q=az1mcmFuY2hpc2Uma2g9MSZvc3M9ZnJhbmNoaXNl'

TITLE_XPATH = '/html/body/div[2]/div[2]/div[1]/h1'
ASKING_PRICE_XPATH = '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/b[2]'
GROSS_REVENUE_XPATH = '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/b[4]'
CASH_FLOW_XPATH = '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/b[6]'
EBITDA_XPATH = '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/b[8]'
INVENTORY_XPATH = '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/b[10]'
FF_E_XPATH = '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/b[12]'
REAL_ESTATE_XPATH = '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/b[14]'
MORE_INFORMATION_XPATH = '/html/body/div[2]/div[2]/div[1]'
TITLE_XPATH2 = '/html/body/div[2]/app-root/app-bfs-franchise-detail/div/div[1]/div[3]/div[2]/h1'
MIN_LIQUID_CAPITAL_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[1]/div[3]/div/div[1]/p'
MIN_FRANCHISE_FEE_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[1]/div[3]/div/div[2]/p'
TOTAL_UNITS_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[1]/div[3]/div/div[3]/p'
FRANCHISING_SINCE_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[3]/div[1]/p'
COMPANY_UNITS_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[3]/div[2]/p'
AVERAGE_UNIT_REVENUE_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[3]/div[3]/p'
MIN_FRANCHISE_FEE_XPATH2 = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[5]/div/div[1]/p'
ROYALTY_FEE_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[5]/div/div[2]/p'
AD_FUND_FEE_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[5]/div/div[3]/p'
INITIAL_INVESTMENT_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[8]/div[1]/p'
MIN_LIQUID_CAPITAL_XPATH2 = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[8]/div[2]/p'
NET_WORTH_REQUIRED_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[8]/div[3]/p'
BENEFITS_LIST_XPATH = '//*[@id="franchise-details-container"]/div[2]/div[1]/div[9]/div/ul'
DESCRIPTION_XPATH = '/html/body/div[2]/div[2]/div[1]/div[4]'
SELLER_AND_COMPANY_XPATH = '/html/body/div[2]/div[2]/div[2]/div[2]/b'
AGENT_PHONE_XPATH = '//*[@id="phone"]'
STATE_XPATH = '//*[@id="crumbs"]/li[2]/a/span'
CATEGORY_XPATH = '//*[@id="crumbs"]/li[4]/a/span'

class BizquestSpiderConfig:
    def __init__(self, logFile, proxy: str = '') -> None:
        self.logFile     = logFile
        self.proxy       = proxy

class BizquestSpider:

    def __init__(self, companiesForSaleSpiderConfig: BizquestSpiderConfig) -> None:
        try :

            self.TABLE_NAME = AFFECTED_TABLE

            proxy = companiesForSaleSpiderConfig.proxy
            logFile = companiesForSaleSpiderConfig.logFile

            rsc = PlaywrightScraperConfig(proxy=proxy)
            self.scraper = PlaywrightScraper(rsc)
            self.scraper.page.set_default_timeout(timeout = 100000)
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
            (`Listing Number`,Title,`Asking price`,`Gross revenue`,`Cash flow`,EBITDA,Inventory,`FF&E`,`Real Estate Value`,\
             Location,`Year Established`,`Number of Employees`,Franchise,`Real Estate`,`Building Sq. Ft.`,Facilities,Website,\
             `Growth & Expansion`,Rent,`Market Outlook/Competition`,`Reason For Selling`,`Training/Support`,`Seller Financing`,\
             `Ad Detail Views`,`Lease Expiration`,`Home Based`,`Relocatable`,`Min Liquid Capital`,`Min Franchise Fee`,`Total Units`,\
             `Franchising Since`,`Company Units`,`Average Unit Revenue`,`Royalty Fee`,`Ad Fund Fee`,`Initial Investment`,\
             `Initial Investment Min`,`Initial Investment Max`,`Net Worth Required`,`Financing Available`,Mobile,`Multi Units`,\
             `SBA Approved`,`company`, `description`,`agent_phone`,`seller`,`city`,`state`, `category`, `checksum`,`on_sale`) \
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,\
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, True)'

        UPDATE_ONSALE_QUERY = f'UPDATE {self.TABLE_NAME} SET on_sale=True WHERE id=%s'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(SELECT_QUERY, [obj['listing_number']])
        row = cursor.fetchone()
        checksum = hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()

        if row == None:
            cursor.execute(INSERT_QUERY,
                            [obj['listing_number'], obj['title'], obj['asking_price'], obj['gross_revenue'], obj['cash_flow'], obj['ebitda'],
                             obj['inventory'], obj['ff_e'], obj['real_estate_value'], obj['location'], obj['year_established'], obj['number_of_employees'],
                             obj['franchise'], obj['real_estate'], obj['building_sq_ft'], obj['facilities'], obj['website'], obj['growth_expansion'],
                             obj['rent'], obj['market_outlook_competition'], obj['reason_for_selling'], obj['training_support'], obj['seller_financing'],
                             obj['ad_detail_views'], obj['lease_expiration'], obj['home_based'], obj['relocatable'], obj['min_liquid_capital'],
                             obj['min_franchise_fee'], obj['total_units'], obj['franchising_since'], obj['company_units'], obj['average_unit_revenue'],
                             obj['royalty_fee'], obj['ad_fund_fee'], obj['initial_investment'], obj['initial_investment_min'], obj['initial_investment_max'],
                             obj['net_worth_required'], obj['financing_available'], obj['mobile'], obj['multi_units'], obj['sba_approved'], 
                             obj['company'],obj['description'],obj['agent_phone'], obj['seller'], obj['city'], obj['state'], obj['category'],checksum])
            self.scraper.conn.commit()

            cursor.close()
            return

        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = dict(zip(column_names, row))

        if data['checksum'] != checksum :
        
            cursor.execute(INSERT_QUERY,
                            [obj['listing_number'], obj['title'], obj['asking_price'], obj['gross_revenue'], obj['cash_flow'], obj['ebitda'],
                             obj['inventory'], obj['ff_e'], obj['real_estate_value'], obj['location'], obj['year_established'], obj['number_of_employees'],
                             obj['franchise'], obj['real_estate'], obj['building_sq_ft'], obj['facilities'], obj['website'], obj['growth_expansion'],
                             obj['rent'], obj['market_outlook_competition'], obj['reason_for_selling'], obj['training_support'], obj['seller_financing'],
                             obj['ad_detail_views'], obj['lease_expiration'], obj['home_based'], obj['relocatable'], obj['min_liquid_capital'],
                             obj['min_franchise_fee'], obj['total_units'], obj['franchising_since'], obj['company_units'], obj['average_unit_revenue'],
                             obj['royalty_fee'], obj['ad_fund_fee'], obj['initial_investment'], obj['initial_investment_min'], obj['initial_investment_max'],
                             obj['net_worth_required'], obj['financing_available'], obj['mobile'], obj['multi_units'], obj['sba_approved'], 
                             obj['company'],obj['description'],obj['agent_phone'], obj['seller'], obj['city'], obj['state'], obj['category'],checksum])
        else :
            cursor.execute(UPDATE_ONSALE_QUERY, [data['id']])

        self.scraper.conn.commit()
        cursor.close()
    
    def set_site(self) -> None:
        self.scraper.set_site(SEARCHING_URL)
        time.sleep(2)

    def get_max_page(self) -> int:
        try :
            res = get_max_index_bizquest(self.scraper.page.content())
            return res
        except Exception as e :
            print(e)
            print('timeout')

    def get_paginated_items(self, index) -> "tuple[str]":

        if index == 1:
            URL = SEARCHING_URL
        else:
            URL = SEARCHING_URL_BY_PAGE.format(str(index))

        self.scraper.set_site(URL)
        time.sleep(2)
        return get_clean_links_bizquest(self.scraper.page.content())
        
    def collect_data(self, url: str):
        try:
            if "?src=flbr&bfsid=0" in url: url = "https://www.bizquest.com" + url
            self.scraper.set_site(url)
            time.sleep(2)

            title = check_length(self.scraper.page.locator('xpath='+TITLE_XPATH).all_inner_texts())
            if not title: title = check_length(self.scraper.page.locator('xpath='+TITLE_XPATH2).all_inner_texts())
            asking_price = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+ASKING_PRICE_XPATH).all_inner_texts()))
            gross_revenue = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+GROSS_REVENUE_XPATH).all_inner_texts()))
            cash_flow = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+CASH_FLOW_XPATH).all_inner_texts()))
            ebitda = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+EBITDA_XPATH).all_inner_texts()))
            inventory = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+INVENTORY_XPATH).all_inner_texts()))
            ff_e = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+FF_E_XPATH).all_inner_texts()))
            real_estate_value = check_length(self.scraper.page.locator('xpath='+REAL_ESTATE_XPATH).all_inner_texts())
            min_liquid_capital = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+MIN_LIQUID_CAPITAL_XPATH).all_inner_texts()))
            if not min_liquid_capital: min_liquid_capital = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+MIN_LIQUID_CAPITAL_XPATH2).all_inner_texts()))
            min_franchise_fee = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+MIN_FRANCHISE_FEE_XPATH).all_inner_texts()))
            if not min_franchise_fee: min_franchise_fee = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+MIN_FRANCHISE_FEE_XPATH2).all_inner_texts()))
            total_units = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+TOTAL_UNITS_XPATH).all_inner_texts()))
            franchising_since = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+FRANCHISING_SINCE_XPATH).all_inner_texts()))
            company_units = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+COMPANY_UNITS_XPATH).all_inner_texts()))
            average_unit_revenue = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+AVERAGE_UNIT_REVENUE_XPATH).all_inner_texts()))
            royalty_fee = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+ROYALTY_FEE_XPATH).all_inner_texts()))
            ad_fund_fee = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+AD_FUND_FEE_XPATH).all_inner_texts()))
            initial_investment = get_clean_amounts_bfs(check_length(self.scraper.page.locator('xpath='+INITIAL_INVESTMENT_XPATH).all_inner_texts()))
            net_worth_required = get_clean_amounts_bizquest(check_length(self.scraper.page.locator('xpath='+NET_WORTH_REQUIRED_XPATH).all_inner_texts()))
            description = check_length(self.scraper.page.locator('xpath='+DESCRIPTION_XPATH).all_inner_texts())
            agent_phone = check_length(self.scraper.page.locator('xpath='+AGENT_PHONE_XPATH).all_inner_texts())
            agent_phone = agent_phone.strip()
            seller = check_length(self.scraper.page.locator('xpath='+SELLER_AND_COMPANY_XPATH).all_inner_texts())
            company = check_length(self.scraper.page.locator('xpath='+SELLER_AND_COMPANY_XPATH).all_inner_texts())
            state = check_length(self.scraper.page.locator('xpath='+STATE_XPATH).all_inner_texts())
            state = state.replace('Businesses for Sale', '').strip()

            category = check_length(self.scraper.page.locator('xpath='+CATEGORY_XPATH).all_inner_texts())
            category = category.replace(state, '').replace('Businesses for Sale', '').strip()

            d = {
                "title": title,
                "asking_price": asking_price,
                "gross_revenue": gross_revenue,
                "cash_flow": cash_flow,
                "ebitda": ebitda,
                "inventory": inventory,
                "ff_e": ff_e,
                "real_estate_value": real_estate_value,
                'description': description,
                'agent_phone': agent_phone,
                'seller': seller,
                'company': company,
                'category' : category,
                "city": '',
                "state": '',
                "location": '',
                "year_established": '',
                "number_of_employees": '',
                "franchise": '',
                "real_estate": '',
                "building_sq_ft": '',
                "facilities": '',
                "website": '',
                "growth_expansion": '',
                "rent": '',
                "market_outlook_competition": '',
                "reason_for_selling": '',
                "training_support": '',
                "seller_financing": '',
                "listing_number": '',
                "ad_detail_views": '',
                "lease_expiration": '',
                "home_based": '',
                "relocatable": '',
                "min_liquid_capital": min_liquid_capital,
                "min_franchise_fee": min_franchise_fee,
                "total_units": total_units,
                "franchising_since": franchising_since,
                "company_units": company_units,
                "average_unit_revenue": average_unit_revenue,
                "royalty_fee": royalty_fee,
                "ad_fund_fee": ad_fund_fee,
                "initial_investment": initial_investment[0],
                "initial_investment_min": initial_investment[1],
                "initial_investment_max": initial_investment[2],
                "net_worth_required": net_worth_required,
                "financing_available": '',
                "mobile": '',
                "multi_units": '',
                "sba_approved": ''
            }

            field_name_map = {
                "Location:": "location",
                "Year Established:": "year_established",
                "Number of Employees:": "number_of_employees",
                "Franchise:": "franchise",
                "Real Estate:": "real_estate",
                "Building Sq. Ft.:": "building_sq_ft",
                "Facilities:": "facilities",
                "Website:": "website",
                "Growth & Expansion:": "growth_expansion",
                "Rent:": "rent",
                "Market Outlook/Competition:": "market_outlook_competition",
                "Reason For Selling:": "reason_for_selling",
                "Training/Support:": "training_support",
                "Seller Financing:": "seller_financing",
                "ID:": "listing_number",
                "Ad Detail Views:": "ad_detail_views",
                "Lease Expiration:": "lease_expiration",
                "Home Based:": "home_based",
                "Relocatable:": "relocatable"
            }

            for j in range(1, 4):
                for i in range(1, len(field_name_map)):
                    field_name = check_length(self.scraper.page.locator(f'xpath={MORE_INFORMATION_XPATH}/dl[{j}]/dt[{i}]').all_inner_texts())
                    if "Market Outlook/" in field_name: field_name = "Market Outlook/Competition:" 
                    field_value = check_length(self.scraper.page.locator(f'xpath={MORE_INFORMATION_XPATH}/dl[{j}]/dd[{i}]').all_inner_texts())
                    if field_value != '' and field_name in field_name_map:
                        if field_name in ("Year Established:", "Number of Employees:", "Building Sq. Ft.:"):
                            clean_value = re.search(r'(\d+)', field_value.replace(',', ''))
                            if clean_value:
                                d[field_name_map[field_name]] = int(clean_value.group(1))
                                continue
                        else:
                            d[field_name_map[field_name]] = field_value
                    elif field_name == '':
                        break
                    else:
                        print(f'Field name not found in map: {field_name}\n URL: {url}')

            benefits_fields_map = {
                "Training and Support": "training_support",
                "Financing Available": "financing_available",
                "Mobile": "mobile",
                "Multi Units": "multi_units",
                "SBA Approved": "sba_approved"
            }

            for i in range(1, len(benefits_fields_map)+2):
                benefit_name = check_length(self.scraper.page.locator(f'xpath={BENEFITS_LIST_XPATH}/li[{i}]/span[2]').all_inner_texts())
                if benefit_name in benefits_fields_map:
                    d[benefits_fields_map[benefit_name]] = "Yes"
                elif field_name == '':
                    break
                else:
                    print(f'Field name not found in map: {field_name}\n URL: {url}')

            if len(d['location'].split(',')) >= 1:
                d['city'] = d['location'].split(',')[0].strip()
                d['state'] = d['location'].split(',')[1].strip()   

            self.update_business(d)

        except NoSuchElementException:
            print('error nosuchelement in url '+ url)
        except Exception as e:
            print(e)


def get_paginated_items(bizquestSpider: BizquestSpider) -> "list[str]":

    try :
        bizquestSpider.set_on_sale()
        urls = list()
        bizquestSpider.set_site()
        max = bizquestSpider.get_max_page()
        print(max)
        for i in range(1, int(max)+1) :

            urls.extend(bizquestSpider.get_paginated_items(i))
            #break comenta esto para que te pagine todo, para desarrollar es mejor mantenerlo descomentarlo
        print(len(urls))
        return urls

    except Exception as e :
        print('paginando')
        raise e

def collect_data(url: str, proxy: str, logFile: TextIOWrapper):

    try: 
        bsc = BizquestSpiderConfig(logFile, proxy)
        bs = BizquestSpider(bsc)

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
        
        bsc = BizquestSpiderConfig(logFile, next(ps))
        bs = BizquestSpider(bsc)

        business_objs = get_paginated_items(bs)

        bs.scraper.close_session()

        for business_objs in business_objs:
            collect_data(business_objs, next(ps), logFile)
        
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['SUCCESS'], '')

    except Exception as e:
        print('BizquestSpider - runSpider')
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['ERROR'], str(e))
        print(e)
        raise e
