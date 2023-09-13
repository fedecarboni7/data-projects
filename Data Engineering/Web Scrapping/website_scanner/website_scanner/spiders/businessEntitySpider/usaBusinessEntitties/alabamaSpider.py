import mysql.connector
import pandas as pd
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from typing import Iterator
from io import TextIOWrapper

from ....parsers.businessEntityParser import alabama_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = 'https://arc-sos.state.al.us/CGI/CORPNAME.MBR/INPUT'
STATE = 'Alabama'
INPUT_XPATH = '//*[@id="block-sos-content"]/div/div/div[1]/form/div[1]/input'
FIRST_OPTION_XPATH = '//*[@id="block-sos-content"]/div/div/div/table/tbody/tr[1]/td[1]/a'
class AlabamaSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = '') -> None:
        self.seleniumUrl = seleniumUrl
        self.company     = company
        self.logFile     = logFile
        self.proxy       = proxy


class AlabamaSpider:

    def __init__(self, config: AlabamaSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
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
            return alabama_extract_owner(self.scraper.get_raw_HTML())
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

        asc = AlabamaSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = AlabamaSpider(asc)
        resp = _as.get_franchise_agents()

        _as.scraper.close_session()
        return resp
    except Exception as e:
        print('Alabama run_spider error')
        print(e)
        #_as.scraper.closeSession()
        raise e
