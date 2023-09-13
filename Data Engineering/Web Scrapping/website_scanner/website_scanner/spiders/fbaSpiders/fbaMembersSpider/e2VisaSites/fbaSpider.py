import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from .....posProcessors.posProcessors import fba_members_add_result
from .....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = 'https://fbamembers.com/members/'

USERNAME_LOGIN_INPUT_XPATH = '//*[@id="user_login"]'
PASSWORD_LOGIN_INPUT_XPATH = '//*[@id="user_pass"]'

NOT_FOUND_MESSAGE_XPATH = '//*[@id="message"]/p'

class FBASpiderConfig:
    def __init__(self, seleniumUrl: str, username: str, password: str, logFile, proxy: str = '') -> None:
        self.seleniumUrl = seleniumUrl
        self.logFile     = logFile
        self.proxy       = proxy
        self.username    = username
        self.password    = password


class FBASpider:

    def __init__(self, config: FBASpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper  = SeleniumScraper(ssc)
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
        page_num = 1
        while True:
            try:
                self.scraper.set_site(BASE_URL + f"page/{page_num}/")
                time.sleep(1)
                
                if len(self.scraper.driver.find_elements(By.XPATH, NOT_FOUND_MESSAGE_XPATH)) > 0:
                    break

                i = 1
                member_name = self.scraper.driver.find_elements(By.XPATH, f'//*[@id="members-list"]/li[{i}]/div[2]/div[1]/a')
                while len(member_name) > 0:
                    fba_members_add_result(member_name[0].text, output_path)
                    i += 1
                    member_name = self.scraper.driver.find_elements(By.XPATH, f'//*[@id="members-list"]/li[{i}]/div[2]/div[1]/a')

            except Exception as e:
                self.logFile.write('FBASpider')
                self.logFile.write('\n')
                self.logFile.write(str(e))
                self.logFile.write('\n')
            
            page_num += 1

def run_spider(env: dict) -> None:

    try:
        seleniumUrl = env['seleniumUrl']
        proxy       = env['proxy']
        logFile     = env['logFile']
        username    = env['username']
        password    = env['password']
        output_path = env['output_path']

        asc = FBASpiderConfig(seleniumUrl, username, password, logFile, proxy)
        _as = FBASpider(asc)
        _as.login()
        _as.check(output_path)

        _as.scraper.close_session()
    except Exception as e:
        print('FBASpiderConfig run_spider error')
        print(e)
        #_as.scraper.closeSession()
        raise e
