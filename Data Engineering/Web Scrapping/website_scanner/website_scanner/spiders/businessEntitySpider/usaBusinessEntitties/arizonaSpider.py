import pandas as pd
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from typing import Iterator
from io import TextIOWrapper

from website_scanner.parsers.businessEntityParser import ArizonaExtractOwner
from website_scanner.scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig


""" RESOURCES TO SCRAPE
RESOURCE_BASE = 'https://www.linkedin.com'
RESOURCE_RESET = '/in/test/'
RESOURCE_SEARCHING = '/search/results/people/?origin=GLOBAL_SEARCH_HEADER&keywords='
RESOURCE_CONTACT_INFO = '/overlay/contact-info/'
RESOURCE_LOGIN = '/login'
"""
BASE_URL = 'https://ecorp.azcc.gov/EntitySearch/Index'
STATE = 'Arizona'
INPUT_XPATH = '//*[@id="block-sos-content"]/div/div/div[1]/form/div[1]/input'
FIRST_OPTION_XPATH = '//*[@id="block-sos-content"]/div/div/div/table/tbody/tr[1]/td[1]/a'

class ArizonaSpiderConfig():
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = '') -> None:
        self.seleniumUrl = seleniumUrl
        self.company     = company
        self.logFile     = logFile
        self.proxy       = proxy


class ArizonaSpider():

    def __init__(self, config: ArizonaSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile     = config.logFile
        self.proxy   = config.proxy

    def saveHTML(self) -> str:

        try:
            self.scraper.setSite(BASE_URL)
            time.sleep(2)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company)
            time.sleep(1)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(Keys.RETURN)
            time.sleep(2)
            self.scraper.driver.find_element(By.XPATH, FIRST_OPTION_XPATH).click()
            time.sleep(2)
            return ArizonaExtractOwner(self.scraper.getRawHTML())
        except Exception as e:
            print('getUserInfo')
            raise e


def runSpider(env: dict) -> str:
    print(env)
    try:
        seleniumUrl = env['seleniumUrl']
        proxy       = env['proxy']
        company     = env['company']
        logFile     = env['logFile']
        asc = ArizonaSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = ArizonaSpider(asc)
        return _as.saveHTML()


        _as.scraper.closeSession()
    except Exception as e:
        print('runSpider error')
        #_as.scraper.closeSession()
        raise e