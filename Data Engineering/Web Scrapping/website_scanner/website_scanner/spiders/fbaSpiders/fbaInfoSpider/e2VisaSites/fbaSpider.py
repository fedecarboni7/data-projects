import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from .....parsers.e2VisaElegibilityParser import checkFBAExistence
from .....parsers.fbaInfoParser import extract_contact_information
from .....posProcessors.posProcessors import fba_info_add_result
from .....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = 'https://fbamembers.com/members/'

USERNAME_LOGIN_INPUT_XPATH = '//*[@id="user_login"]'
PASSWORD_LOGIN_INPUT_XPATH = '//*[@id="user_pass"]'
INPUT_XPATH = '//*[@id="members_search"]'
FIRST_OPTION = '//*[@id="members-list"]/li[1]/div[2]/div[1]/a'
MEMBER_TYPE_XPATH = '//*[@id="members-list"]/li[1]/div[2]/div[3]/span'
FRANCHISE_NAME_XPATH = '/html/body/div[5]/div[3]/div[1]/div/div/div/div/div/div/div[1]/article/header/h1'

class FBASpiderConfig:
    def __init__(self, seleniumUrl: str, companies: "list[str]", username: str, password: str, logFile, proxy: str = '') -> None:
        self.seleniumUrl = seleniumUrl
        self.companies   = companies
        self.logFile     = logFile
        self.proxy       = proxy
        self.username    = username
        self.password    = password


class FBASpider:

    def __init__(self, config: FBASpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper  = SeleniumScraper(ssc)
        self.companies = config.companies
        self.logFile  = config.logFile
        self.proxy    = config.proxy
        self.username = config.username
        self.password = config.password
    
    def login(self) -> None:
        self.scraper.set_site(BASE_URL)
        time.sleep(1)
        self.scraper.driver.find_element(By.XPATH, USERNAME_LOGIN_INPUT_XPATH).send_keys(self.username)
        self.scraper.driver.find_element(By.XPATH, PASSWORD_LOGIN_INPUT_XPATH).send_keys(self.password)
        self.scraper.driver.find_element(By.XPATH, PASSWORD_LOGIN_INPUT_XPATH).send_keys(Keys.RETURN)
        time.sleep(1)

    def check(self, output_path: str) -> None:
        for owner in self.companies :
            try:
                self.scraper.set_site(BASE_URL)
                time.sleep(1)
                self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).clear()
                self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(owner)
                self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(Keys.RETURN)
                time.sleep(1)
                if checkFBAExistence(self.scraper.get_raw_HTML()):
                    member_type = self.scraper.driver.find_element(By.XPATH, MEMBER_TYPE_XPATH).text
                    self.scraper.driver.find_element(By.XPATH, FIRST_OPTION).click()
                    time.sleep(1)
                    contact_person = ''
                    contact_email = ''
                    contact_url = ''
                    contact_phone = ''
                    contact_address = ''
                    franchise_name = ''

                    fields = extract_contact_information(self.scraper.get_raw_HTML())
                    for field in fields:
                        if field == 'Contact Person:':
                            contact_person = self.scraper.driver.find_element(By.XPATH, fields[field]).text.split('Contact Person: ')[1].strip()
                            franchise_name = self.scraper.driver.find_element(By.XPATH, FRANCHISE_NAME_XPATH).text
                        elif field == 'Person:':
                            contact_person = self.scraper.driver.find_element(By.XPATH, fields[field]).text.strip()
                        elif 'Email' in field:
                            contact_email = self.scraper.driver.find_element(By.XPATH, fields[field] + '/a').text.strip()
                        elif field == 'URL:':
                            contact_url = self.scraper.driver.find_element(By.XPATH, fields[field]).text.split('URL:')[1].strip()
                        elif field == 'Phone:':
                            contact_phone = self.scraper.driver.find_element(By.XPATH, fields[field]).text.split('Phone:')[1].strip()
                        elif field == 'Address:':
                            contact_address = self.scraper.driver.find_element(By.XPATH, fields[field]).text.split('Address:')[1].replace('\n', ' ').strip()

                    fba_info_add_result(owner, contact_person, contact_email, contact_url, contact_phone, contact_address, member_type, franchise_name, '', output_path, False)


            except Exception as e:
                self.logFile.write('FBASpider')
                self.logFile.write('\n')
                self.logFile.write(owner)
                self.logFile.write('\n')
                self.logFile.write(str(e))
                self.logFile.write('\n')
                continue


def run_spider(env: dict) -> None:

    try:
        seleniumUrl = env['seleniumUrl']
        proxy       = env['proxy']
        companies   = env['companies']
        logFile     = env['logFile']
        username    = env['username']
        password    = env['password']
        output_path = env['output_path']

        asc = FBASpiderConfig(seleniumUrl, companies, username, password, logFile, proxy)
        _as = FBASpider(asc)
        _as.login()
        _as.check(output_path)

        _as.scraper.close_session()
    except Exception as e:
        print('FBASpiderConfig run_spider error')
        print(e)
        #_as.scraper.closeSession()
        raise e
