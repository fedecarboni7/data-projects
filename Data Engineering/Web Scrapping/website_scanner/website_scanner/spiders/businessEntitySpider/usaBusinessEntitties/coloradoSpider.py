import pandas as pd
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from typing import Iterator
from io import TextIOWrapper

from ....parsers.businessEntityParser import colorado_extract_owner_pages, colorado_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = 'https://www.sos.state.co.us/biz/'
SEARCHING_PATH = 'BusinessEntityCriteriaExt.do'
STATE = 'Colorado'
INPUT_XPATH = '//*[@id="application"]/table/tbody/tr/td[2]/table/tbody/tr[3]/td/form/table[1]/tbody/tr[5]/td/table/tbody/tr/td/table/tbody/tr/td[2]/font/input'

class ColoradoSpiderConfig:
    def __init__(self, selenium_url: str, company: str, log_file, proxy: str = '') -> None:
        self.selenium_url = selenium_url
        self.company     = company
        self.log_file     = log_file
        self.proxy       = proxy


class ColoradoSpider:

    def __init__(self, config: ColoradoSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.selenium_url, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.log_file
        self.proxy   = config.proxy

    def get_franchise_agents(self) -> list[str]:

        try:
            self.scraper.set_site(BASE_URL+SEARCHING_PATH)
            time.sleep(2)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company)
            time.sleep(1)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(Keys.RETURN)
            time.sleep(2)
            pages = colorado_extract_owner_pages(self.scraper.get_raw_HTML())

            results = list()
            for page in pages :
                self.scraper.set_site(BASE_URL + page)
                time.sleep(2)
                owner = colorado_extract_owner(self.scraper.get_raw_HTML())

                if owner is not None :
                    results.append(owner)

            return results
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
        asc = ColoradoSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = ColoradoSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print('Colorado run_spider error')
        #_as.scraper.closeSession()
        raise e
