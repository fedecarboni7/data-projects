import time
import hashlib, json
import re

from requests.exceptions import Timeout
from io import TextIOWrapper
from selenium.common.exceptions import NoSuchElementException

from ....scrapers.playwrightScraper import PlaywrightScraper, PlaywrightScraperConfig
from ....parsers.companiesForSaleParser import get_clean_links_bizmls, clean_listing_number, check_length, clean_loans, check_int, extract_indiv_values
from ....utils.utils import proxySwitcher, STATUS
from ....services.mysql import notify_process

SPIDER_NAME = 'companies_for_sale'
AFFECTED_TABLE = 'companies_for_sale'

SEARCHING_URL = 'https://bizmls.com/cgi-bin/a-bus2.asp?state=Florida&process=search&lgassnc=BIZMLS&folder=BIZMLS'
SEARCH_BUTTON_XPATH = '/html/body/section/div/form/div[3]/input[1]'

INPUT_XPATH = '//*[@id="block-sos-content"]/div/div/div[1]/form/div[1]/input'
FIRST_OPTION_XPATH = '//*[@id="block-sos-content"]/div/div/div/table/tbody/tr[1]/td[1]/a'

CATEGORY_XPATH = '/html/body/section/div/table/tbody/tr/td/table[2]/tbody/tr[1]/td[3]/span'
IS_A_FRANCHISE_XPATH = '/html/body/section/div/table/tbody/tr/td/table[4]/tbody/tr[8]/td[3]/span'
LISTING_NUMBER_XPATH = '/html/body/section/div/table/tbody/tr/td/table[1]/tbody/tr/td[1]/span'
DETAIL_XPATH = '/html/body/section/div/table/tbody/tr/td/table[2]/tbody/tr[2]/td[3]/span'
COUNTY_XPATH = '/html/body/section/div/table/tbody/tr/td/table[2]/tbody/tr[3]/td[3]/span'
STATE_XPATH = '/html/body/section/div/table/tbody/tr/td/table[2]/tbody/tr[4]/td[3]/span'
SIC_XPATH = '/html/body/section/div/table/tbody/tr/td/table[2]/tbody/tr[1]/td[7]/span'
PRICE_XPATH = '/html/body/section/div/table/tbody/tr/td/table[2]/tbody/tr[2]/td[7]/span'
DOWN_XPATH = '/html/body/section/div/table/tbody/tr/td/table[2]/tbody/tr[3]/td[7]/span'
ADJ_NET_XPATH = '/html/body/section/div/table/tbody/tr/td/table[2]/tbody/tr[4]/td[7]/span'
SALES_XPATH = '/html/body/section/div/table/tbody/tr/td/table[2]/tbody/tr[5]/td[7]/span'
REASON_FOR_SALE_XPATH = '/html/body/section/div/table/tbody/tr/td/table[4]/tbody/tr[1]/td[3]/span'
GENERAL_LOCATION_XPATH = '/html/body/section/div/table/tbody/tr/td/table[4]/tbody/tr[2]/td[3]/span'
ORGANIZATION_TYPE_XPATH = '/html/body/section/div/table/tbody/tr/td/table[4]/tbody/'
NON_COMPETE_XPATH = '/html/body/section/div/table/tbody/tr/td/table[4]/tbody/tr[5]/td[3]/span'
OPERATING_DYS_HRS_XPATH = '/html/body/section/div/table/tbody/tr/td/table[4]/tbody/tr[6]/td[3]/span'
SKILLS_XPATH = '/html/body/section/div/table/tbody/tr/td/table[4]/tbody/tr[7]/td[3]/span'
BUSINESS_XPATH = '/html/body/section/div/table/tbody/tr/td/table[4]/tbody/tr[8]/td[3]/span'
CONTACT_NAME_XPATH = 'tbody/tr[1]/td[1]/span/b'
CONTACT_ROLE_XPATH = 'tbody/tr[2]/td[1]/span/b'
CONTACT_OFFICE_NAME_XPATH = 'tbody/tr[3]/td[1]/span/b'
CONTACT_STREET_XPATH = 'tbody/tr[4]/td[1]/span/b'
CONTACT_CITY_XPATH = 'tbody/tr[5]/td[1]/span/b'
CONTACT_COUNTRY_XPATH = 'tbody/tr[6]/td[1]/span/b'
CONTACT_OFFICE_XPATH = 'tbody/tr[1]/td[5]/span'
CONTACT_AGENT_DIRECT_XPATH = 'tbody/tr[2]/td[5]/span'
CONTACT_FAX_XPATH = 'tbody/tr[3]/td[5]/span'
CONTACT_CELL_XPATH = 'tbody/tr[4]/td[5]/span'
CONTACT_EMAIL_NAME_XPATH = 'tbody/tr[5]/td[5]/span/a'
CONTACT_HOME_PAGE_XPATH = 'tbody/tr[6]/td[5]/span/a'
LOAN_ASSUMABLE_AMT_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[1]/td[3]/span'
LOAN_ASSUMABLE_MOS_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[1]/td[4]/span'
LOAN_ASSUMABLE_RATE_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[1]/td[5]/span'
LOAN_ASSUMABLE_MO_PMT_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[1]/td[6]/span'
LOAN_SELLER_AMT_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[2]/td[3]/span'
LOAN_SELLER_MOS_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[2]/td[4]/span'
LOAN_SELLER_RATE_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[2]/td[5]/span'
LOAN_SELLER_MO_PMT_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[2]/td[6]/span'
LOAN_OTHER_AMT_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[3]/td[3]/span'
LOAN_OTHER_MOS_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[3]/td[4]/span'
LOAN_OTHER_RATE_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[3]/td[5]/span'
LOAN_OTHER_MO_PMT_XPATH = '/html/body/section/div/table/tbody/tr/td/table[7]/tbody/tr[3]/td[6]/span'
YEARS_CASH_FLOW_XPATH = '/html/body/section/div/table/tbody/tr/td/table[5]/tbody/tr[2]'
YEAR_CASH_FLOW_XPATH_1 = '/html/body/section/div/table/tbody/tr/td/table[5]/tbody/tr[2]/td[2]'
YEAR_CASH_FLOW_XPATH_2 = '/html/body/section/div/table/tbody/tr/td/table[5]/tbody/tr[2]/td[3]'
YEAR_CASH_FLOW_XPATH_3 = '/html/body/section/div/table/tbody/tr/td/table[5]/tbody/tr[2]/td[4]'
INVENTORY_XPATH = '/html/body/section/div/table/tbody/tr/td/table[6]/tbody/tr[2]/td[2]'
REAL_STATE_AMOUNT_XPATH = '/html/body/section/div/table/tbody/tr/td/table[6]/tbody/tr[1]/td[5]'
REAL_STATE_INCLUDED_XPATH = '/html/body/section/div/table/tbody/tr/td/table[6]/tbody/tr[1]/td[6]'

class BizmlsSpiderConfig:
    def __init__(self, logFile, proxy: str = '') -> None:
        self.logFile     = logFile
        self.proxy       = proxy

class BizmlsSpider:

    def __init__(self, companiesForSaleSpiderConfig: BizmlsSpiderConfig) -> None:
        try :
            self.TABLE_NAME = 'companies_for_sale'

            proxy = companiesForSaleSpiderConfig.proxy
            logFile = companiesForSaleSpiderConfig.logFile

            rsc = PlaywrightScraperConfig(proxy=proxy)
            self.scraper = PlaywrightScraper(rsc)
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
            (`Category`, `Listing Number`, `Detail`, `County`, `State`, `SIC`, `Price`, `Down`, `Adj. Net`, `Sales`,\
                `Reason for Selling`, `General Location`, `Organization Type`, `Non Compete`, `Operating dys/hrs`,\
                `Skills`, `Business`, `contact name`,`contact role`,`contact office name`,`contact street`,`contact city`,\
                `contact country`,`contact office`,`contact agent direct`,`contact fax`,`contact cell`,`contact email name`,\
                `contact home page`, `Loan/Assumable [Amt]`,`Loan/Assumable [Mos]`,`Loan/Assumable [Rate]`,`Loan/Assumable [Mo Pmt]`,\
                `Loan/Seller [Amt]`,`Loan/Seller [Mos]`,`Loan/Seller [Rate]`,`Loan/Seller [Mo Pmt]`,`Loan/Other [Amt]`,\
                `Loan/Other [Mos]`,`Loan/Other [Rate]`,`Loan/Other [Mo Pmt]`,`Cash Flow 2017`, `Cash Flow 2018`, `Cash Flow 2019`, \
                `Cash Flow 2020`, `Cash Flow 2021`, `Cash Flow 2022`, `Cash Flow 2023`, `Gross Revenue 2017`, `Gross Revenue 2018`, \
                `Gross Revenue 2019`, `Gross Revenue 2020`, `Gross Revenue 2021`, `Gross Revenue 2022`, `Gross Revenue 2023`, \
                `Cost of Goods 2017`, `Cost of Goods 2018`, `Cost of Goods 2019`, `Cost of Goods 2020`, `Cost of Goods 2021`, \
                `Cost of Goods 2022`, `Cost of Goods 2023`, `Gross Profit 2017`, `Gross Profit 2018`, `Gross Profit 2019`, \
                `Gross Profit 2020`, `Gross Profit 2021`, `Gross Profit 2022`, `Gross Profit 2023`, `Expenses 2017`, `Expenses 2018`, \
                `Expenses 2019`, `Expenses 2020`, `Expenses 2021`, `Expenses 2022`, `Expenses 2023`, `Net 2017`, `Net 2018`, `Net 2019`, \
                `Net 2020`, `Net 2021`, `Net 2022`, `Net 2023`, `Owner Salary 2017`, `Owner Salary 2018`, `Owner Salary 2019`, \
                `Owner Salary 2020`, `Owner Salary 2021`, `Owner Salary 2022`, `Owner Salary 2023`, `Benefits 2017`, `Benefits 2018`, \
                `Benefits 2019`, `Benefits 2020`, `Benefits 2021`, `Benefits 2022`, `Benefits 2023`, `Interest Expense 2017`, \
                `Interest Expense 2018`, `Interest Expense 2019`, `Interest Expense 2020`, `Interest Expense 2021`, `Interest Expense 2022`, \
                `Interest Expense 2023`, `Depreciation 2017`, `Depreciation 2018`, `Depreciation 2019`, `Depreciation 2020`, \
                `Depreciation 2021`, `Depreciation 2022`, `Depreciation 2023`, `Other 2017`, `Other 2018`, `Other 2019`, `Other 2020`, \
                `Other 2021`, `Other 2022`, `Other 2023`, `Owner Benefit 2017`, `Owner Benefit 2018`, `Owner Benefit 2019`, \
                `Owner Benefit 2020`, `Owner Benefit 2021`, `Owner Benefit 2022`, `Owner Benefit 2023`, \
                `Founding Year`, `Number of Employees`, `Weeks of Training`, `Hours Owner Works`, `Absentee Owner`, `Is Relocatable`, \
                `Is a Franchise`, `Seller Financing`, `Is Lender P/Q`, `Contact State`, `Contact Zip Code`, `Inventory Total`, \
                `Real Estate Included in Sale (Amount)`, `City`, `Real Estate (leased or owned)`, `Building Square Feet`, `Business Website`, \
                `Facebook`, `YouTube`, `Accounting or bookkeeping software`, `Earnings Source`, `is_a_franchise`, `checksum`, `on_sale`) \
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,\
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,\
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,\
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,\
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,\
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, True)'

        UPDATE_ONSALE_QUERY = f'UPDATE {self.TABLE_NAME} SET on_sale=True WHERE id=%s'

        cursor = self.scraper.conn.cursor(buffered=True)
        cursor.execute(SELECT_QUERY, [obj['listing_number']])
        row = cursor.fetchone()
        checksum = hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()

        if row == None:
            cursor.execute(INSERT_QUERY,
                            [obj['category'], obj['listing_number'], obj['detail'], obj['county'], obj['state'],
                             obj['sic'], obj['price'], obj['down'], obj['adj_net'], obj['sales'], obj['reason_for_selling'],
                             obj['general_location'], obj['organization_type'], obj['non_compete'], obj['operating_dys_hrs'],
                             obj['skills'], obj['business'], obj['contact_name'], obj['contact_role'],
                             obj['contact_office_name'], obj['contact_street'], obj['contact_city'], obj['contact_country'],
                             obj['contact_office'], obj['contact_agent_direct'], obj['contact_fax'], obj['contact_cell'],
                             obj['contact_email_name'], obj['contact_home_page'], obj['loan_assumable_amt'],
                             obj['loan_assumable_mos'], obj['loan_assumable_rate'], obj['loan_assumable_mo_pmt'],
                             obj['loan_seller_amt'], obj['loan_seller_mos'], obj['loan_seller_rate'], obj['loan_seller_mo_pmt'],
                             obj['loan_other_amt'], obj['loan_other_mos'], obj['loan_other_rate'], obj['loan_other_mo_pmt'],
                             obj['cash_flow_2017'], obj['cash_flow_2018'], obj['cash_flow_2019'], obj['cash_flow_2020'], obj['cash_flow_2021'],
                             obj['cash_flow_2022'], obj['cash_flow_2023'], obj['gross_revenue_2017'], obj['gross_revenue_2018'], obj['gross_revenue_2019'],
                             obj['gross_revenue_2020'], obj['gross_revenue_2021'], obj['gross_revenue_2022'], obj['gross_revenue_2023'], obj['cost_of_goods_2017'],
                             obj['cost_of_goods_2018'], obj['cost_of_goods_2019'], obj['cost_of_goods_2020'], obj['cost_of_goods_2021'],
                             obj['cost_of_goods_2022'], obj['cost_of_goods_2023'], obj['gross_profit_2017'], obj['gross_profit_2018'],
                             obj['gross_profit_2019'], obj['gross_profit_2020'], obj['gross_profit_2021'], obj['gross_profit_2022'], obj['gross_profit_2023'],
                             obj['expenses_2017'], obj['expenses_2018'], obj['expenses_2019'], obj['expenses_2020'], obj['expenses_2021'], obj['expenses_2022'],
                             obj['expenses_2023'], obj['net_2017'], obj['net_2018'], obj['net_2019'], obj['net_2020'], obj['net_2021'], obj['net_2022'],
                             obj['net_2023'], obj['owner_salary_2017'], obj['owner_salary_2018'], obj['owner_salary_2019'], obj['owner_salary_2020'],
                             obj['owner_salary_2021'], obj['owner_salary_2022'], obj['owner_salary_2023'], obj['benefits_2017'],
                             obj['benefits_2018'], obj['benefits_2019'], obj['benefits_2020'], obj['benefits_2021'], obj['benefits_2022'],
                             obj['benefits_2023'], obj['interest_expense_2017'], obj['interest_expense_2018'], obj['interest_expense_2019'],
                             obj['interest_expense_2020'], obj['interest_expense_2021'], obj['interest_expense_2022'], obj['interest_expense_2023'],
                             obj['depreciation_2017'], obj['depreciation_2018'], obj['depreciation_2019'], obj['depreciation_2020'],
                             obj['depreciation_2021'], obj['depreciation_2022'], obj['depreciation_2023'], obj['other_2017'], obj['other_2018'],
                             obj['other_2019'], obj['other_2020'], obj['other_2021'], obj['other_2022'], obj['other_2023'], obj['owner_benefit_2017'],
                             obj['owner_benefit_2018'], obj['owner_benefit_2019'], obj['owner_benefit_2020'], obj['owner_benefit_2021'],
                             obj['owner_benefit_2022'], obj['owner_benefit_2023'], obj['founding_year'], obj['number_of_employees'],
                             obj['weeks_of_training'], obj['hours_owner_works'], obj['absentee_owner'], obj['relocatable'], obj['franchise'],
                             obj['seller_financing'], obj['lender_pq'], obj['contact_state'], obj['contact_zip_code'], obj['inventory'],
                             obj['real_state_value'], obj['city'], obj['real_estate_leased_or_owned'], obj['building_square_feet'], obj['business_website'],
                             obj['facebook'], obj['youtube'], obj['accounting_or_bookkeeping_software'], obj['earnings_source'], obj['is_a_franchise'], checksum])
            self.scraper.conn.commit()

            cursor.close()
            return

        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = dict(zip(column_names, row))

        if data['checksum'] != checksum :
        
            cursor.execute(INSERT_QUERY,
                            [obj['category'], obj['listing_number'], obj['detail'], obj['county'], obj['state'],
                             obj['sic'], obj['price'], obj['down'], obj['adj_net'], obj['sales'], obj['reason_for_selling'],
                             obj['general_location'], obj['organization_type'], obj['non_compete'], obj['operating_dys_hrs'],
                             obj['skills'], obj['business'], obj['contact_name'], obj['contact_role'],
                             obj['contact_office_name'], obj['contact_street'], obj['contact_city'], obj['contact_country'],
                             obj['contact_office'], obj['contact_agent_direct'], obj['contact_fax'], obj['contact_cell'],
                             obj['contact_email_name'], obj['contact_home_page'], obj['loan_assumable_amt'],
                             obj['loan_assumable_mos'], obj['loan_assumable_rate'], obj['loan_assumable_mo_pmt'],
                             obj['loan_seller_amt'], obj['loan_seller_mos'], obj['loan_seller_rate'], obj['loan_seller_mo_pmt'],
                             obj['loan_other_amt'], obj['loan_other_mos'], obj['loan_other_rate'], obj['loan_other_mo_pmt'],
                             obj['cash_flow_2017'], obj['cash_flow_2018'], obj['cash_flow_2019'], obj['cash_flow_2020'], obj['cash_flow_2021'],
                             obj['cash_flow_2022'], obj['cash_flow_2023'], obj['gross_revenue_2017'], obj['gross_revenue_2018'], obj['gross_revenue_2019'],
                             obj['gross_revenue_2020'], obj['gross_revenue_2021'], obj['gross_revenue_2022'], obj['gross_revenue_2023'], obj['cost_of_goods_2017'],
                             obj['cost_of_goods_2018'], obj['cost_of_goods_2019'], obj['cost_of_goods_2020'], obj['cost_of_goods_2021'],
                             obj['cost_of_goods_2022'], obj['cost_of_goods_2023'], obj['gross_profit_2017'], obj['gross_profit_2018'],
                             obj['gross_profit_2019'], obj['gross_profit_2020'], obj['gross_profit_2021'], obj['gross_profit_2022'], obj['gross_profit_2023'],
                             obj['expenses_2017'], obj['expenses_2018'], obj['expenses_2019'], obj['expenses_2020'], obj['expenses_2021'], obj['expenses_2022'],
                             obj['expenses_2023'], obj['net_2017'], obj['net_2018'], obj['net_2019'], obj['net_2020'], obj['net_2021'], obj['net_2022'],
                             obj['net_2023'], obj['owner_salary_2017'], obj['owner_salary_2018'], obj['owner_salary_2019'], obj['owner_salary_2020'],
                             obj['owner_salary_2021'], obj['owner_salary_2022'], obj['owner_salary_2023'], obj['benefits_2017'],
                             obj['benefits_2018'], obj['benefits_2019'], obj['benefits_2020'], obj['benefits_2021'], obj['benefits_2022'],
                             obj['benefits_2023'], obj['interest_expense_2017'], obj['interest_expense_2018'], obj['interest_expense_2019'],
                             obj['interest_expense_2020'], obj['interest_expense_2021'], obj['interest_expense_2022'], obj['interest_expense_2023'],
                             obj['depreciation_2017'], obj['depreciation_2018'], obj['depreciation_2019'], obj['depreciation_2020'],
                             obj['depreciation_2021'], obj['depreciation_2022'], obj['depreciation_2023'], obj['other_2017'], obj['other_2018'],
                             obj['other_2019'], obj['other_2020'], obj['other_2021'], obj['other_2022'], obj['other_2023'], obj['owner_benefit_2017'],
                             obj['owner_benefit_2018'], obj['owner_benefit_2019'], obj['owner_benefit_2020'], obj['owner_benefit_2021'],
                             obj['owner_benefit_2022'], obj['owner_benefit_2023'], obj['founding_year'], obj['number_of_employees'],
                             obj['weeks_of_training'], obj['hours_owner_works'], obj['absentee_owner'], obj['relocatable'], obj['franchise'],
                             obj['seller_financing'], obj['lender_pq'], obj['contact_state'], obj['contact_zip_code'], obj['inventory'],
                             obj['real_state_value'], obj['city'], obj['real_estate_leased_or_owned'], obj['building_square_feet'], obj['business_website'],
                             obj['facebook'], obj['youtube'], obj['accounting_or_bookkeeping_software'], obj['earnings_source'], obj['is_a_franchise'], checksum])
        else :
            cursor.execute(UPDATE_ONSALE_QUERY, [data['id']])

        self.scraper.conn.commit()
        cursor.close()
    
    def set_paginated_items(self) -> None:

        self.scraper.set_site(SEARCHING_URL)
        time.sleep(2)
        self.scraper.page.locator('xpath='+SEARCH_BUTTON_XPATH).click()
        time.sleep(4)
        #self.scraper.page.locator('input[name="displayall"]').click()
        #time.sleep(20) # este valor puede variar en funcion de lo que dura cargando los 2000 y pico negocios

    def get_paginated_items(self) -> "tuple[str]":
        find_results = self.scraper.page.locator("a", has_text="Click for more details")
        result = get_clean_links_bizmls(find_results)
        return result

    def collect_data(self, url: str):
        try:
            self.scraper.set_site(url)
            time.sleep(3)

            category = check_length(self.scraper.page.locator('xpath='+CATEGORY_XPATH).all_inner_texts())
            listing_number = check_length(self.scraper.page.locator('xpath='+LISTING_NUMBER_XPATH).all_inner_texts())
            listing_number = clean_listing_number(listing_number)
            detail = check_length(self.scraper.page.locator('xpath='+DETAIL_XPATH).all_inner_texts())
            county = check_length(self.scraper.page.locator('xpath='+COUNTY_XPATH).all_inner_texts())
            state = check_length(self.scraper.page.locator('xpath='+STATE_XPATH).all_inner_texts())
            sic = check_length(self.scraper.page.locator('xpath='+SIC_XPATH).all_inner_texts())
            price = check_length(self.scraper.page.locator('xpath='+PRICE_XPATH).all_inner_texts())
            down = check_length(self.scraper.page.locator('xpath='+DOWN_XPATH).all_inner_texts())
            adj_net = check_length(self.scraper.page.locator('xpath='+ADJ_NET_XPATH).all_inner_texts())
            sales = check_length(self.scraper.page.locator('xpath='+SALES_XPATH).all_inner_texts())
            reason_for_selling = check_length(self.scraper.page.locator('xpath='+REASON_FOR_SALE_XPATH).all_inner_texts())
            general_location = check_length(self.scraper.page.locator('xpath='+GENERAL_LOCATION_XPATH).all_inner_texts())
            organization_type = check_length(self.scraper.page.locator('xpath='+ORGANIZATION_TYPE_XPATH+'tr[3]/td[3]/span').all_inner_texts())
            organization_type += "   |  " + check_length(self.scraper.page.locator('xpath='+ORGANIZATION_TYPE_XPATH+'tr[4]/td[3]/span').all_inner_texts())
            non_compete = check_length(self.scraper.page.locator('xpath='+NON_COMPETE_XPATH).all_inner_texts())
            operating_dys_hrs = check_length(self.scraper.page.locator('xpath='+OPERATING_DYS_HRS_XPATH).all_inner_texts())
            skills = check_length(self.scraper.page.locator('xpath='+SKILLS_XPATH).all_inner_texts())
            business = check_length(self.scraper.page.locator('xpath='+BUSINESS_XPATH).all_inner_texts())
            loan_assumable_amt = clean_loans(self.scraper.page.locator('xpath='+LOAN_ASSUMABLE_AMT_XPATH).all_inner_texts())
            loan_assumable_mos = clean_loans(self.scraper.page.locator('xpath='+LOAN_ASSUMABLE_MOS_XPATH).all_inner_texts())
            loan_assumable_rate = clean_loans(self.scraper.page.locator('xpath='+LOAN_ASSUMABLE_RATE_XPATH).all_inner_texts())
            loan_assumable_mo_pmt = clean_loans(self.scraper.page.locator('xpath='+LOAN_ASSUMABLE_MO_PMT_XPATH).all_inner_texts())
            loan_seller_amt = clean_loans(self.scraper.page.locator('xpath='+LOAN_SELLER_AMT_XPATH).all_inner_texts())
            loan_seller_mos = clean_loans(self.scraper.page.locator('xpath='+LOAN_SELLER_MOS_XPATH).all_inner_texts())
            loan_seller_rate = clean_loans(self.scraper.page.locator('xpath='+LOAN_SELLER_RATE_XPATH).all_inner_texts())
            loan_seller_mo_pmt = clean_loans(self.scraper.page.locator('xpath='+LOAN_SELLER_MO_PMT_XPATH).all_inner_texts())
            loan_other_amt = clean_loans(self.scraper.page.locator('xpath='+LOAN_OTHER_AMT_XPATH).all_inner_texts())
            loan_other_mos = clean_loans(self.scraper.page.locator('xpath='+LOAN_OTHER_MOS_XPATH).all_inner_texts())
            loan_other_rate = clean_loans(self.scraper.page.locator('xpath='+LOAN_OTHER_RATE_XPATH).all_inner_texts())
            loan_other_mo_pmt = clean_loans(self.scraper.page.locator('xpath='+LOAN_OTHER_MO_PMT_XPATH).all_inner_texts())
            is_a_franchise = check_length(self.scraper.page.locator('xpath='+IS_A_FRANCHISE_XPATH).all_inner_texts())
            if 'Is a Franchise: Y' in is_a_franchise:
                is_a_franchise = 'Y'
            else:
                is_a_franchise = 'N'
            years_cash_flow = self.scraper.page.locator('xpath='+YEARS_CASH_FLOW_XPATH).all_inner_texts()[0]
            year_cash_flow_1 = self.scraper.page.locator('xpath='+YEAR_CASH_FLOW_XPATH_1).all_inner_texts()[0]
            year_cash_flow_2 = self.scraper.page.locator('xpath='+YEAR_CASH_FLOW_XPATH_2).all_inner_texts()[0]
            year_cash_flow_3 = self.scraper.page.locator('xpath='+YEAR_CASH_FLOW_XPATH_3).all_inner_texts()[0]
            fy = extract_indiv_values(organization_type, "Years Established")
            if fy:
                founding_year = time.localtime().tm_year - int(fy)
            else :
                founding_year = None
            mgrs  = extract_indiv_values(organization_type, "Mgrs")
            emppt = extract_indiv_values(organization_type, "Emp PT")
            empft = extract_indiv_values(organization_type, "Emp FT")

            if mgrs :
                mgrs = int(mgrs)
            else :
                mgrs = 0
            if emppt :
                emppt = int(emppt)
            else :
                emppt = 0
            if empft :
                empft = int(empft)
            else :
                empft = 0
            number_of_employees = mgrs + empft + emppt
            weeks_of_training = extract_indiv_values(non_compete, "Weeks Training")

            hours_owner_works = extract_indiv_values(organization_type, "Hours Owner Works")
            if hours_owner_works:
                hours_owner_works = int(hours_owner_works)
            else :
                hours_owner_works = None

            if hours_owner_works is None:
                absentee_owner = None
            else :
                absentee_owner = "Yes" if hours_owner_works < 30 else "No"
            relocatable = extract_indiv_values(business, "Is Relocatable")
            relocatable = "Yes" if relocatable == "Y" else "No"
            franchise = extract_indiv_values(business, "Is a Franchise")
            franchise = "Yes" if franchise == "Y" else "No"
            seller_financing = "No" if price == down else "Yes"
            lender_pq = extract_indiv_values(business, "Is Lender P/Q")
            lender_pq = "Yes" if lender_pq == "Y" else "No"
            inventory = self.scraper.page.locator('xpath='+INVENTORY_XPATH).all_inner_texts()
            if inventory and len(inventory) >= 0:
                inventory = check_int(inventory[0])
            else:
                inventory = None

            real_state_included = check_length(self.scraper.page.locator('xpath='+REAL_STATE_INCLUDED_XPATH).all_inner_texts())

            real_state_value = self.scraper.page.locator('xpath='+REAL_STATE_AMOUNT_XPATH).all_inner_texts()
            if real_state_value and len(real_state_value) >= 0:
                real_state_value = check_int(real_state_value[0])
            else:
                real_state_value = None
            if real_state_included == "N*": real_state_value = ''
            contact_table_num = 8 if lender_pq == "No" else 11
            contact_name = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_NAME_XPATH).all_inner_texts())
            contact_role = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_ROLE_XPATH).all_inner_texts())
            contact_office_name = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_OFFICE_NAME_XPATH).all_inner_texts())
            contact_street = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_STREET_XPATH).all_inner_texts())
            contact_city = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_CITY_XPATH).all_inner_texts())
            contact_country = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_COUNTRY_XPATH).all_inner_texts())
            contact_office = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_OFFICE_XPATH).all_inner_texts())
            contact_agent_direct = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_AGENT_DIRECT_XPATH).all_inner_texts())
            contact_fax = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_FAX_XPATH).all_inner_texts())
            contact_cell = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_CELL_XPATH).all_inner_texts())
            contact_email_name = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_EMAIL_NAME_XPATH).all_inner_texts())
            contact_home_page = check_length(self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[{contact_table_num}]/'+CONTACT_HOME_PAGE_XPATH).all_inner_texts())
        
            address = re.match(r'(.*), (.*) (\d+)', contact_city)
            if address:
                contact_city = address.group(1).strip()
                contact_state = address.group(2).strip()
                contact_zip_code = address.group(3).strip()
            else:
                contact_city = ""
                contact_state = ""
                contact_zip_code = ""
            #time.sleep(2)

            print("###########################")
            print(is_a_franchise)
            print("###########################")

            d = {
                "category": category,
                "listing_number": listing_number,
                "detail": detail,
                "county": county,
                "state": state,
                "sic": int(sic),
                "price": int(price.replace(',','')),
                "down": int(down.replace(',','')),
                "adj_net": int(adj_net.replace(',','')),
                "sales": int(sales.replace(',','')),
                "reason_for_selling": reason_for_selling,
                "general_location": general_location,
                "organization_type": organization_type,
                "non_compete": non_compete,
                "operating_dys_hrs": operating_dys_hrs,
                "skills": skills,
                "business": business,
                "contact_name": contact_name,
                "contact_role": contact_role,
                "contact_office_name": contact_office_name,
                "contact_street": contact_street,
                "contact_city": contact_city,
                "contact_country": contact_country,
                "contact_office": contact_office,
                "contact_agent_direct": contact_agent_direct,
                "contact_fax": contact_fax,
                "contact_cell": contact_cell,
                "contact_email_name": contact_email_name,
                "contact_home_page": contact_home_page,
                "loan_assumable_amt": loan_assumable_amt,
                "loan_assumable_mos": loan_assumable_mos,
                "loan_assumable_rate": loan_assumable_rate,
                "loan_assumable_mo_pmt": loan_assumable_mo_pmt,
                "loan_seller_amt": loan_seller_amt,
                "loan_seller_mos": loan_seller_mos,
                "loan_seller_rate": loan_seller_rate,
                "loan_seller_mo_pmt": loan_seller_mo_pmt,
                "loan_other_amt": loan_other_amt,
                "loan_other_mos": loan_other_mos,
                "loan_other_rate": loan_other_rate,
                "loan_other_mo_pmt": loan_other_mo_pmt,
                "cash_flow_2017": '',
                "gross_revenue_2017": '',
                "cost_of_goods_2017": '',
                "gross_profit_2017": '',
                "expenses_2017": '',
                "net_2017": '',
                "owner_salary_2017": '',
                "benefits_2017": '',
                "interest_expense_2017": '',
                "depreciation_2017": '',
                "other_2017": '',
                "owner_benefit_2017": '',
                "cash_flow_2018": '',
                "gross_revenue_2018": '',
                "cost_of_goods_2018": '',
                "gross_profit_2018": '',
                "expenses_2018": '',
                "net_2018": '',
                "owner_salary_2018": '',
                "benefits_2018": '',
                "interest_expense_2018": '',
                "depreciation_2018": '',
                "other_2018": '',
                "owner_benefit_2018": '',
                "cash_flow_2019": '',
                "gross_revenue_2019": '',
                "cost_of_goods_2019": '',
                "gross_profit_2019": '',
                "expenses_2019": '',
                "net_2019": '',
                "owner_salary_2019": '',
                "benefits_2019": '',
                "interest_expense_2019": '',
                "depreciation_2019": '',
                "other_2019": '',
                "owner_benefit_2019": '',
                "cash_flow_2020": '',
                "gross_revenue_2020": '',
                "cost_of_goods_2020": '',
                "gross_profit_2020": '',
                "expenses_2020": '',
                "net_2020": '',
                "owner_salary_2020": '',
                "benefits_2020": '',
                "interest_expense_2020": '',
                "depreciation_2020": '',
                "other_2020": '',
                "owner_benefit_2020": '',
                "cash_flow_2021": '',
                "gross_revenue_2021": '',
                "cost_of_goods_2021": '',
                "gross_profit_2021": '',
                "expenses_2021": '',
                "net_2021": '',
                "owner_salary_2021": '',
                "benefits_2021": '',
                "interest_expense_2021": '',
                "depreciation_2021": '',
                "other_2021": '',
                "owner_benefit_2021": '',
                "cash_flow_2022": '',
                "gross_revenue_2022": '',
                "cost_of_goods_2022": '',
                "gross_profit_2022": '',
                "expenses_2022": '',
                "net_2022": '',
                "owner_salary_2022": '',
                "benefits_2022": '',
                "interest_expense_2022": '',
                "depreciation_2022": '',
                "other_2022": '',
                "owner_benefit_2022": '',
                "cash_flow_2023": '',
                "gross_revenue_2023": '',
                "cost_of_goods_2023": '',
                "gross_profit_2023": '',
                "expenses_2023": '',
                "net_2023": '',
                "owner_salary_2023": '',
                "benefits_2023": '',
                "interest_expense_2023": '',
                "depreciation_2023": '',
                "other_2023": '',
                "owner_benefit_2023": '',
                "founding_year": founding_year,
                "number_of_employees": number_of_employees,
                "weeks_of_training": weeks_of_training,
                "hours_owner_works": hours_owner_works,
                "absentee_owner": absentee_owner,
                "relocatable": relocatable,
                "franchise": franchise,
                "seller_financing": seller_financing,
                "lender_pq": lender_pq,
                "contact_state": contact_state,
                "contact_zip_code": contact_zip_code,
                "inventory": inventory,
                "real_state_value": real_state_value,
                "is_a_franchise": is_a_franchise,
                "city": 'N/A',
                "real_estate_leased_or_owned": 'N/A',
                "building_square_feet": 'N/A',
                "business_website": 'N/A',
                "facebook": 'N/A',
                "youtube": 'N/A',
                "accounting_or_bookkeeping_software": 'N/A',
                "earnings_source": 'N/A'
            }
            
            def get_data_source_table(i: int, d: dict, year: str):
                values = ['gross_revenue', 'cost_of_goods', 'gross_profit', 'expenses', 'net', 'owner_salary', 'benefits', 'interest_expense', 'depreciation', 'other', 'owner_benefit']
                
                for j, value in enumerate(values, start=3):
                    locator = f'/html/body/section/div/table/tbody/tr/td/table[5]/tbody/tr[{j}]/td[{i}]'
                    v = self.scraper.page.locator(f'xpath={locator}').all_inner_texts()[0]
                    d.update({f"{value}_{year}": check_int(v)})

                cash_flow = self.scraper.page.locator(f'xpath=/html/body/section/div/table/tbody/tr/td/table[5]/tbody/tr[2]/td[{i}]').all_inner_texts()[0]
                d.update({f"cash_flow_{year}": cash_flow})

            def check_year_and_get_data(year: str, d: dict, years_cash_flow, year_cash_flow_1, year_cash_flow_2, year_cash_flow_3):
                if year in years_cash_flow:
                    if year in year_cash_flow_1:
                        i = 2
                    elif year in year_cash_flow_2:
                        i = 3
                    elif year in year_cash_flow_3:
                        i = 4
                    get_data_source_table(i, d, year)

            for year in ['2017', '2018', '2019', '2020', '2021', '2022', '2023']:
                check_year_and_get_data(year, d, years_cash_flow, year_cash_flow_1, year_cash_flow_2, year_cash_flow_3)

            self.update_business(d)

        except NoSuchElementException:
            return []
        except Timeout:
            self.logFile.write('timeout in site: '+ url)


def get_paginated_items(companiesForSaleSpider: BizmlsSpider) -> "list[str]":

    try :
        companiesForSaleSpider.set_paginated_items()
        companiesForSaleSpider.set_on_sale()
        first_page = companiesForSaleSpider.get_paginated_items()
        return first_page

    except Exception as e :
        print('')
        raise e

def collect_data(url: str, proxy: str, logFile: TextIOWrapper):

    cfssc = BizmlsSpiderConfig(logFile, proxy)
    cfss = BizmlsSpider(cfssc)

    cfss.collect_data(url)

    cfss.scraper.close_session()


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
        
        cfssc = BizmlsSpiderConfig(logFile, next(ps))
        cfss = BizmlsSpider(cfssc)

        business_urls = get_paginated_items(cfss)

        cfss.scraper.close_session()

        for business_url in business_urls:
            print(business_url)
            collect_data(business_url, next(ps), logFile)

        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['SUCCESS'], '')

    except Exception as e:
        print('BizmlsSpider - runSpider')
        notify_process(NAME, SPIDER_NAME, AFFECTED_TABLE, STATUS['ERROR'], str(e))
        print(e)
        raise e
