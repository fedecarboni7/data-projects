import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import north_carolina_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

STATE = "North Carolina"
BASE_URL = "https://www.sosnc.gov/search/index/corp"
EXACT_SEARCH_XPATH = '//*[@id="Words"]/option[2]'
INPUT_XPATH = '//*[@id="SearchCriteria"]'
FIRST_OPTION_XPATH = '/html/body/div[3]/main/article[1]/section[1]/div/table/tbody/tr[1]/td[1]/b/a'


class NorthCarolinaSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.proxy = proxy


class NorthCarolinaSpider:
    def __init__(self, config: NorthCarolinaSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.proxy = config.proxy

    def get_franchise_agents(self) -> "list[str]":

        try:
            self.scraper.set_site(BASE_URL)
            self.scraper.driver.find_element(By.XPATH, EXACT_SEARCH_XPATH).click()
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company + Keys.RETURN)
            time.sleep(0.6)
            self.scraper.driver.find_element(By.XPATH, FIRST_OPTION_XPATH).click()
            time.sleep(0.8)
            return north_carolina_extract_owner(self.scraper.get_raw_HTML())
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
        asc = NorthCarolinaSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = NorthCarolinaSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("North Carolina run_spider error")
        print(e)
        raise e
