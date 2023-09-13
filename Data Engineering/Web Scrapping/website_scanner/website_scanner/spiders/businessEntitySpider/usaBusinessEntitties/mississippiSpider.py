import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import mississippi_extract_owner, mississippi_find_active
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

STATE = "Mississippi"
BASE_URL = "https://corp.sos.ms.gov/corp/portal/c/page/corpBusinessIdSearch/portal.aspx"
EXACT_SEARCH_XPATH = '//*[@id="rbExact"]'
INPUT_XPATH = '//*[@id="businessNameTextBox"]'
ENTITIE_OPTIONS_XPATH = '//*[@id="businessSearchResultsDiv"]/table/tbody/tr[{}]/td[6]/a'


class MississippiSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.proxy = proxy


class MississippiSpider:
    def __init__(self, config: MississippiSpiderConfig) -> None:
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
            time.sleep(1)
            tr_num = mississippi_find_active(self.scraper.get_raw_HTML())
            self.scraper.driver.find_element(By.XPATH, ENTITIE_OPTIONS_XPATH.format(tr_num)).click()
            time.sleep(1)
            return mississippi_extract_owner(self.scraper.get_raw_HTML())
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
        asc = MississippiSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = MississippiSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("Mississippi run_spider error")
        print(e)
        raise e
