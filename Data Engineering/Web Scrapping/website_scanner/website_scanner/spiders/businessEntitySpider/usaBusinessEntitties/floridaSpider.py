import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import florida_check_status, florida_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = 'http://search.sunbiz.org/Inquiry/CorporationSearch/ByName'
STATE = 'Florida'
INPUT_XPATH = '//*[@id="SearchTerm"]'
RETURN_TO_LIST_XPATH = '//*[@id="navigationBar"]/table/tbody/tr/td[1]/table/tbody/tr[1]/td/span[5]/a'


class FloridaSpiderConfig():
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = '') -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.proxy = proxy


class FloridaSpider():

    def __init__(self, config: FloridaSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.proxy = config.proxy

    def get_franchise_agents(self) -> "list[str]":

        try:
            self.scraper.set_site(BASE_URL)
            time.sleep(1)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company + Keys.RETURN)
            time.sleep(1)
            results = []
            active_entities = florida_check_status(self.scraper.get_raw_HTML())
            if active_entities is None:
                return results
            for i in active_entities:
                self.scraper.driver.find_element(By.XPATH, f'//*[@id="search-results"]/table/tbody/tr[{i}]/td[1]/a').click()
                time.sleep(1)
                results.append(florida_extract_owner(self.scraper.get_raw_HTML()))
                self.scraper.driver.find_element(By.XPATH, RETURN_TO_LIST_XPATH).click()
                time.sleep(1)
            return results
        except NoSuchElementException:
            return []
        except Exception as e:
            print('getUserInfo')
            raise e


def run_spider(env: dict) -> "list[str]":

    try:
        seleniumUrl = env['seleniumUrl']
        proxy = env['proxy']
        company = env['company']
        logFile = env['logFile']
        asc = FloridaSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = FloridaSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print('Florida run_spider error')
        raise e
