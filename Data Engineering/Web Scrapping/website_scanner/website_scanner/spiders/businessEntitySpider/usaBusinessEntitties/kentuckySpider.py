import pandas as pd
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from typing import Iterator
from io import TextIOWrapper
from ....utils.utils import execute_js_click

from ....parsers.businessEntityParser import kentucky_extract_owner_urls, kentucky_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = 'https://web.sos.ky.gov/ftsearch/'
ONLY_ACTIVE_OPTION = '//*[@id="ctl00_ContentPlaceHolder1_FTUC_cbActiveonly"]'
INPUT_XPATH = '//*[@id="ctl00_ContentPlaceHolder1_FTUC_tName"]'
STATE = 'Kentucky'

class KentuckySpiderConfig:
    def __init__(self, selenium_url: str, company: str, log_file, twocaptcha_key: str, proxy: str = '') -> None:
        self.selenium_url = selenium_url
        self.company     = company
        self.log_file     = log_file
        self.twocaptcha_key = twocaptcha_key
        self.proxy       = proxy


class KentuckySpider:

    def __init__(self, config: KentuckySpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.selenium_url, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.log_file
        self.twocaptcha_key = config.twocaptcha_key
        self.proxy   = config.proxy

    def get_franchise_agents(self) -> list[str]:

        try:
            self.scraper.set_site(BASE_URL)
            time.sleep(2)
            
            self.scraper.driver.execute_script(execute_js_click(ONLY_ACTIVE_OPTION))
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company+Keys.RETURN)
            time.sleep(2)

            results = list()

            urls = kentucky_extract_owner_urls(self.scraper.get_raw_HTML())

            for url in urls:

                self.scraper.set_site(url)
                time.sleep(2)
                results.append(kentucky_extract_owner(self.scraper.get_raw_HTML()))
                
            return results

        except NoSuchElementException:
            return []
        except Exception as e:
            print(e)
            print('get_franchise_agents')
            raise e

def standard(spider: KentuckySpider) -> list[str]:
    resp = spider.get_franchise_agents()
    return  resp

def with_accuracy(spider: KentuckySpider) -> list[str]:
    pass

def run_spider(env: dict) -> list[str]:

    try:
        seleniumUrl = env['seleniumUrl']
        proxy       = env['proxy']
        company     = env['company']
        logFile     = env['logFile']
        twocaptchaKey = env['twocaptchaKey']
        accuracy = env['accuracy']

        asc = KentuckySpiderConfig(seleniumUrl, company, logFile, twocaptchaKey, proxy)
        _as = KentuckySpider(asc)

        resp = list()
        if accuracy:
            resp = with_accuracy(_as)
        else :
            resp = standard(_as)

        _as.scraper.close_session()
        return resp
    except Exception as e:
        print('Kentucky run_spider error')
        #_as.scraper.closeSession()
        raise e
