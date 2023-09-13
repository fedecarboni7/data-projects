import pandas as pd
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from typing import Iterator
from io import TextIOWrapper
from ....utils.utils import execute_js_click

from ....parsers.businessEntityParser import idaho_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

BASE_URL = 'https://sosbiz.idaho.gov/search/business'
INPUT_XPATH = '//*[@id="root"]/div/div[1]/div/main/div[1]/div/div[1]/input'
OPTIONS_DROPDOWN = '/html/body/div[2]/div/div[1]/div/main/div/div/div[2]/button'
ONLY_ACTIVE_OPTION = '//*[@id="label-ACTIVE_ONLY_YN"]'

STATE = 'Idaho'

class IdahoSpiderConfig:
    def __init__(self, selenium_url: str, company: str, log_file, twocaptcha_key: str, proxy: str = '') -> None:
        self.selenium_url = selenium_url
        self.company     = company
        self.log_file     = log_file
        self.twocaptcha_key = twocaptcha_key
        self.proxy       = proxy


class IdahoSpider:

    def __init__(self, config: IdahoSpiderConfig) -> None:
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
            self.scraper.driver.find_element(By.XPATH, OPTIONS_DROPDOWN).click()
            self.scraper.driver.execute_script(execute_js_click(ONLY_ACTIVE_OPTION))
            time.sleep(1)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company+Keys.RETURN)
            time.sleep(2)
            return idaho_extract_owner(self.scraper.get_raw_HTML())
        except NoSuchElementException as e:
            return []
        except Exception as e:
            print('get_franchise_agents')
            raise e

def standard(spider: IdahoSpider) -> list[str]:
    resp = spider.get_franchise_agents()
    return  resp

def with_accuracy(spider: IdahoSpider) -> list[str]:
    pass

def run_spider(env: dict) -> list[str]:

    try:
        seleniumUrl = env['seleniumUrl']
        proxy       = env['proxy']
        company     = env['company']
        logFile     = env['logFile']
        twocaptchaKey = env['twocaptchaKey']
        accuracy = env['accuracy']

        asc = IdahoSpiderConfig(seleniumUrl, company, logFile, twocaptchaKey, proxy)
        _as = IdahoSpider(asc)

        resp = list()
        if accuracy:
            resp = with_accuracy(_as)
        else :
            resp = standard(_as)

        _as.scraper.close_session()
        return resp
    except Exception as e:
        print('Idaho run_spider error')
        print(e)
        raise e
