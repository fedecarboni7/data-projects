import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....utils.utils import execute_js_click
from ....parsers.businessEntityParser import ohio_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

STATE = "Ohio"
BASE_URL = "https://businesssearch.ohiosos.gov/"
ACTIVE_STATUS_XPATH = '//*[@id="sos-radio-group-1"]/label[2]'
INPUT_XPATH = '//*[@id="bSearch"]'
SEARCH_BUTTON_XPATH = '//*[@id="BusinessNameDiv"]/div/div[3]/div[1]/input[1]'
SHOW_DETAILS_XPATH = '//*[@id="srch-table"]/tbody/tr[1]/td[10]/a'

op = '//*[@id="282791"]'


class OhioSpiderConfig:
    def __init__(self, selenium_url: str, company: str, log_file, twocaptcha_key: str, proxy: str = '') -> None:
        self.selenium_url = selenium_url
        self.company     = company
        self.log_file     = log_file
        self.twocaptcha_key = twocaptcha_key
        self.proxy       = proxy


class OhioSpider:
    def __init__(self, config: OhioSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.selenium_url, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.log_file
        self.twocaptcha_key = config.twocaptcha_key
        self.proxy   = config.proxy

    def get_franchise_agents(self) -> "list[str]":

        try:
            self.scraper.set_site(BASE_URL)
            time.sleep(20)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company)
            time.sleep(1)
            self.scraper.driver.execute_script(execute_js_click(ACTIVE_STATUS_XPATH))
            time.sleep(1)
            #self.scraper.driver.find_element(By.XPATH, SEARCH_BUTTON_XPATH).click()
            self.scraper.driver.execute_script(execute_js_click(SEARCH_BUTTON_XPATH))
            time.sleep(20)
            
            self.scraper.driver.execute_script(execute_js_click(op))
            time.sleep(5)
            print(self.scraper.get_raw_HTML())
            print("##########################################")
            #self.scraper.driver.find_element(By.XPATH, SHOW_DETAILS_XPATH).click()
            #time.sleep(1)
            return []#ohio_extract_owner(self.scraper.get_raw_HTML())
        except NoSuchElementException as e:
            print('boom')
            print(e)
            return []
        except Exception as e:
            print("getUserInfo")
            raise e


def standard(spider: OhioSpider) -> list[str]:
    resp = spider.get_franchise_agents()
    return  resp

def with_accuracy(spider: OhioSpider) -> list[str]:
    pass

def run_spider(env: dict) -> "list[str]":

    try:
        seleniumUrl = env["seleniumUrl"]
        proxy = env["proxy"]
        company = env["company"]
        logFile = env["logFile"]
        accuracy = env['accuracy']
        twocaptchaKey = env['twocaptchaKey']

        asc = OhioSpiderConfig(seleniumUrl, company, logFile, twocaptchaKey, proxy)
        _as = OhioSpider(asc)

        resp = list()
        if accuracy:
            resp = with_accuracy(_as)
        else :
            resp = standard(_as)
            
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print(e)
        print("Ohio run_spider error")
        raise e
