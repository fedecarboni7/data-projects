import pandas as pd
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from typing import Iterator
from io import TextIOWrapper

from ....parsers.businessEntityParser import iowa_extract_owner_urls, iowa_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = 'https://sos.iowa.gov/search/business/'
SEARCHING_PATH = 'search.aspx'
INPUT_XPATH = '//*[@id="txtName"]'
STATE = 'Iowa'

class IowaSpiderConfig:
    def __init__(self, selenium_url: str, company: str, log_file, twocaptcha_key: str, proxy: str = '') -> None:
        self.selenium_url = selenium_url
        self.company     = company
        self.log_file     = log_file
        self.twocaptcha_key = twocaptcha_key
        self.proxy       = proxy


class IowaSpider:

    def __init__(self, config: IowaSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.selenium_url, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.log_file
        self.twocaptcha_key = config.twocaptcha_key
        self.proxy   = config.proxy

    def get_franchise_agents(self) -> list[str]:

        try:
            self.scraper.set_site(BASE_URL + SEARCHING_PATH)
            time.sleep(2)
            
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company+Keys.RETURN)
            time.sleep(2)

            results = list()

            urls = iowa_extract_owner_urls(self.scraper.get_raw_HTML())

            for url in urls:

                self.scraper.set_site(BASE_URL+url)
                time.sleep(2)
                results.append(iowa_extract_owner(self.scraper.get_raw_HTML()))
                
            return results
        except NoSuchElementException:
            return []
        except Exception as e:
            print(e)
            print('get_franchise_agents')
            raise e

def standard(spider: IowaSpider) -> list[str]:
    resp = spider.get_franchise_agents()
    return  resp

def with_accuracy(spider: IowaSpider) -> list[str]:
    pass

def run_spider(env: dict) -> list[str]:

    try:
        seleniumUrl = env['seleniumUrl']
        proxy       = env['proxy']
        company     = env['company']
        logFile     = env['logFile']
        twocaptchaKey = env['twocaptchaKey']
        accuracy = env['accuracy']

        asc = IowaSpiderConfig(seleniumUrl, company, logFile, twocaptchaKey, proxy)
        _as = IowaSpider(asc)

        resp = list()
        if accuracy:
            resp = with_accuracy(_as)
        else :
            resp = standard(_as)

        _as.scraper.close_session()
        return resp
    except Exception as e:
        print('Texas run_spider error')
        #_as.scraper.closeSession()
        raise e
