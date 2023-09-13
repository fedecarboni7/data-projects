import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import montana_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

STATE = "Montana"
BASE_URL = "https://biz.sosmt.gov/search/business"
ADVANCED_BUTTON_XPATH = '//*[@id="root"]/div/div[1]/div/main/div/div/div[2]/button'
STATUS_OPTIONS_XPATH = '//*[@id="field-STATUS_ID"]/option[2]'
INPUT_XPATH = '//*[@id="root"]/div/div[1]/div/main/div/div/div[1]/input'


class MontanaSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.proxy = proxy


class MontanaSpider:
    def __init__(self, config: MontanaSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.proxy = config.proxy

    def get_franchise_agents(self) -> "list[str]":

        try:
            self.scraper.set_site(BASE_URL)
            self.scraper.driver.find_element(By.XPATH, ADVANCED_BUTTON_XPATH).click()
            time.sleep(2)
            self.scraper.driver.find_element(By.XPATH, STATUS_OPTIONS_XPATH).click()
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company + Keys.RETURN)
            time.sleep(2)
            return montana_extract_owner(self.scraper.get_raw_HTML())
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
        asc = MontanaSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = MontanaSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("Montana run_spider error")
        raise e
