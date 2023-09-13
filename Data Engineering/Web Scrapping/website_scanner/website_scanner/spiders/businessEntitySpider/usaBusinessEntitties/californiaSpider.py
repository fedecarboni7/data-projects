import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import california_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = "https://bizfileonline.sos.ca.gov/search/business"
STATE = "California"
ADVANCED_BUTTON_XPATH = '//*[@id="root"]/div/div[1]/div/main/div/div[2]/div[2]/button/span'
STARTS_WITH_XPATH = '//*[@id="field-undefined"]/div[2]'
STATUS_OPTIONS_XPATH = '//*[@id="field-STATUS_ID"]/option[2]'
INPUT_XPATH = '//*[@id="root"]/div/div[1]/div/main/div[1]/div[2]/div[1]/input'


class CaliforniaSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.proxy = proxy


class CaliforniaSpider:
    def __init__(self, config: CaliforniaSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.proxy = config.proxy

    def get_franchise_agents(self) -> "list[str]":

        try:
            self.scraper.set_site(BASE_URL)
            time.sleep(2)
            self.scraper.driver.find_element(By.XPATH, ADVANCED_BUTTON_XPATH).click()
            time.sleep(0.5)
            self.scraper.driver.find_element(By.XPATH, STATUS_OPTIONS_XPATH).click()
            time.sleep(0.05)
            self.scraper.driver.find_element(By.XPATH, STARTS_WITH_XPATH).click()
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(Keys.RETURN)
            time.sleep(2)
            return california_extract_owner(self.scraper.get_raw_HTML())
        except NoSuchElementException:
            return []
        except Exception as e:
            print("getUserInfo")
            raise e


def run_spider(env: dict) -> "list[str]":

    try:
        seleniumUrl = env["seleniumUrl"]
        proxy = env["proxy"]
        company = env["company"]
        logFile = env["logFile"]
        asc = CaliforniaSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = CaliforniaSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("California run_spider error")
        raise e
