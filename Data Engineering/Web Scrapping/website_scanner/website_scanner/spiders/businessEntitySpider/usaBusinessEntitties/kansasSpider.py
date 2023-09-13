import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import kansas_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

STATE = "Kansas"
BASE_URL = "https://www.kansas.gov/bess/"
BUSINESS_DATABASE_XPATH = '//*[@id="startSearchLink"]'
BUSINESS_NAME_SEARCH_XPATH = '//*[@id="byNameLink"]'
INPUT_XPATH = '//*[@id="searchFormForm:businessName"]'
FIRST_OPTION_XPATH = '//*[@id="resultsTable:0:searchFormForm:searchFormFormButton"]'


class KansasSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.proxy = proxy


class KansasSpider:
    def __init__(self, config: KansasSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.proxy = config.proxy

    def get_franchise_agents(self) -> "list[str]":

        try:
            self.scraper.set_site(BASE_URL)
            self.scraper.driver.find_element(By.XPATH, BUSINESS_DATABASE_XPATH).click()
            self.scraper.driver.find_element(By.XPATH, BUSINESS_NAME_SEARCH_XPATH).click()
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company + Keys.RETURN)
            self.scraper.driver.find_element(By.XPATH, FIRST_OPTION_XPATH).click()
            return kansas_extract_owner(self.scraper.get_raw_HTML())
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
        asc = KansasSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = KansasSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("Kansas run_spider error")
        print(e)
        raise e
