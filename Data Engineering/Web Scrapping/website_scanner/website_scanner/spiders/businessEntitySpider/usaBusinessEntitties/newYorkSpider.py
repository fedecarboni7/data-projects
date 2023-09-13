import pandas as pd
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select

from typing import Iterator
from io import TextIOWrapper

from ....parsers.businessEntityParser import texas_extract_data_site_key, texas_get_number_of_options, \
    texas_extract_owner, texas_get_option_status, newyork_get_number_of_options, newyork_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig
from ....services.captchaService import solve_recaptcha

BASE_URL = 'https://apps.dos.ny.gov/publicInquiry/'
INPUT_XPATH = '//*[@id="entityname"]'
CONTAINS_OPTIONS_XPATH = '//*[@id="Corporation"]'
CORP_OPTIONS_XPATH = '//*[@id="app"]/div/main/div/div/div/div[2]/form/div[1]/div/div[5]/div/ul/li[1]/label'
LLC_OPTIONS_XPATH = '//*[@id="app"]/div/main/div/div/div/div[2]/form/div[1]/div/div[5]/div/ul/li[2]/label'
OPTION_XPATH = '//*[@id="app"]/div/main/div/div/div/div[2]/div/div[1]/div/div[2]/div/div[1]/table/tbody/tr[{index}]'
RETURN_BUTTON = '//*[@id="app"]/div/main/div/div/div[2]/div[1]/div[1]/button[1]'
STATE = 'New York'


class NewYorkSpiderConfig:
    def __init__(self, selenium_url: str, company: str, log_file, twocaptcha_key: str, proxy: str = '') -> None:
        self.selenium_url = selenium_url
        self.company     = company
        self.log_file     = log_file
        self.twocaptcha_key = twocaptcha_key
        self.proxy       = proxy


class NewYorkSpider:

    def __init__(self, config: NewYorkSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.selenium_url, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.log_file
        self.twocaptcha_key = config.twocaptcha_key
        self.proxy   = config.proxy

    def get_franchise_agents(self) -> list[str]:

        try:
            self.scraper.set_site(BASE_URL)
            time.sleep(3)

            searchByStatus = self.scraper.driver.find_element(By.ID, 'nameType')
            select = Select(searchByStatus)
            select.select_by_value('1') # Active
            
            searchByPattern = self.scraper.driver.find_element(By.ID, 'searchFunctionality')
            select = Select(searchByPattern)
            select.select_by_value('2') # Contains

            self.scraper.driver.find_element(By.XPATH, LLC_OPTIONS_XPATH).click()

            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company)
            time.sleep(1)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(Keys.RETURN)
            time.sleep(2)

            num_options = newyork_get_number_of_options(self.scraper.get_raw_HTML())
            
            results = list()

            for index in range(1,num_options+1):
                self.scraper.driver.find_element(By.XPATH, OPTION_XPATH.format(index=index)).click()
                time.sleep(0.5)

                owner = newyork_extract_owner(self.scraper.get_raw_HTML())

                if owner is not None:
                    results.append(owner)

                self.scraper.driver.find_element(By.XPATH, RETURN_BUTTON).click()
                time.sleep(0.5)

            return results
        except NoSuchElementException:
            
            return []
        except Exception as e:
            print('get_franchise_agents')
            raise e

def standard(spider: NewYorkSpider) -> list[str]:
    resp = spider.get_franchise_agents()
    return  resp

def with_accuracy(spider: NewYorkSpider) -> list[str]:
    return []

def run_spider(env: dict) -> list[str]:

    try:
        seleniumUrl = env['seleniumUrl']
        proxy       = env['proxy']
        company     = env['company']
        logFile     = env['logFile']
        twocaptchaKey = env['twocaptchaKey']
        accuracy = env['accuracy']

        asc = NewYorkSpiderConfig(seleniumUrl, company, logFile, twocaptchaKey, proxy)
        _as = NewYorkSpider(asc)

        resp = list()
        if accuracy:
            resp = with_accuracy(_as)
        else :
            resp = standard(_as)

        _as.scraper.close_session()
        return resp
    except Exception as e:
        print('New York run_spider error')
        raise e
