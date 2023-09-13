import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import connecticut_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = "https://service.ct.gov/business/s/onlinebusinesssearch?language=en_US"
STATE = "Connecticut"
INPUT_XPATH = '//*[@id="input-2"]'


class ConnecticutSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.proxy = proxy


class ConnecticutSpider:
    def __init__(self, config: ConnecticutSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.proxy = config.proxy

    def get_franchise_agents(self) -> "list[str]":

        try:
            self.scraper.set_site(BASE_URL)
            time.sleep(2)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company + Keys.RETURN)
            time.sleep(5)
            return connecticut_extract_owner(self.scraper.get_raw_HTML())
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
        asc = ConnecticutSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = ConnecticutSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("Connecticut run_spider error")
        raise e
