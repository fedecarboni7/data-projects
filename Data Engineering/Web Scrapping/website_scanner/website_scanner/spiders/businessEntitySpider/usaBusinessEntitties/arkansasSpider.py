import pandas as pd
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from typing import Iterator
from io import TextIOWrapper

from ....parsers.businessEntityParser import arkansas_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = 'https://www.sos.arkansas.gov/corps/search_all.php'
STATE = 'Arkansas'
INPUT_XPATH = '//*[@id="mainContent"]/form/table/tbody/tr[4]/td[2]/font/input'
FIRST_OPTION_XPATH = '//*[@id="mainContent"]/table[3]/tbody/tr[2]/td[1]/font/div/a'

class ArkansasSpiderConfig:
    def __init__(self, selenium_url: str, company: str, log_file, proxy: str = '') -> None:
        self.selenium_url = selenium_url
        self.company     = company
        self.log_file     = log_file
        self.proxy       = proxy


class ArkansasSpider:

    def __init__(self, config: ArkansasSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.selenium_url, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.log_file
        self.proxy   = config.proxy

    def get_franchise_agents(self) -> list[str]:

        try:
            self.scraper.set_site(BASE_URL)
            time.sleep(2)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company)
            time.sleep(1)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(Keys.RETURN)
            time.sleep(2)
            self.scraper.driver.find_element(By.XPATH, FIRST_OPTION_XPATH).click()
            time.sleep(2)
            return arkansas_extract_owner(self.scraper.get_raw_HTML())
        except NoSuchElementException:
            return []
        except Exception as e:
            print('getUserInfo')
            raise e


def run_spider(env: dict) -> list[str]:

    try:
        seleniumUrl = env['seleniumUrl']
        proxy       = env['proxy']
        company     = env['company']
        logFile     = env['logFile']
        asc = ArkansasSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = ArkansasSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print('Arkansas run_spider error')
        #_as.scraper.closeSession()
        raise e
