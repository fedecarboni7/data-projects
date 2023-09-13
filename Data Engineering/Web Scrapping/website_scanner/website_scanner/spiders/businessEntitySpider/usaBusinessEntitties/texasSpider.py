import pandas as pd
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from typing import Iterator
from io import TextIOWrapper

from ....parsers.businessEntityParser import texas_extract_data_site_key, texas_get_number_of_options, \
    texas_extract_owner, texas_get_option_status
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig
from ....services.captchaService import solve_recaptcha

BASE_URL = 'https://mycpa.cpa.state.tx.us/coa/Index.html'
INPUT_XPATH = '//*[@id="entityName"]'
CAPTCHA_CLICK_FIELD_XPATH = '//*[@id="recaptcha-anchor"]/div[1]'
OPTION_BUTTON_XPATH = '/html/body/div/div[3]/form/div[1]/div[1]/div[2]/div[1]/div/div/table/tbody/tr[{index}]/td[1]/span/button'
CLOSE_MODAL_WHEN_ERROR = '//*[@id="errorModal"]/div/div/div/div[2]/div/button'
CLOSE_MODAL = '//*[@id="modal-footer"]/button'
STATE = 'Texas'


class TexasSpiderConfig:
    def __init__(self, selenium_url: str, company: str, log_file, twocaptcha_key: str, proxy: str = '') -> None:
        self.selenium_url = selenium_url
        self.company     = company
        self.log_file     = log_file
        self.twocaptcha_key = twocaptcha_key
        self.proxy       = proxy


class TexasSpider:

    def __init__(self, config: TexasSpiderConfig) -> None:
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
            siteKey = texas_extract_data_site_key(self.scraper.get_raw_HTML())
            res = solve_recaptcha(siteKey, BASE_URL, self.twocaptcha_key)
            self.scraper.driver.execute_script(
                "document.getElementById('g-recaptcha-response').innerHTML = " + "'" + res['code'] + "'")
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(Keys.RETURN)
            time.sleep(2)
            num_options = texas_get_number_of_options(self.scraper.get_raw_HTML())

            results = list()
            
            for index in range(1,num_options+1):
                self.scraper.driver.find_element(By.XPATH, OPTION_BUTTON_XPATH.format(index=index)).click()
                time.sleep(0.5)

                page = self.scraper.get_raw_HTML()

                if not texas_get_option_status(page) :
                    self.scraper.driver.find_element(By.XPATH, CLOSE_MODAL_WHEN_ERROR).click()
                    time.sleep(0.5)
                    continue
                
                owner = texas_extract_owner(page)

                if owner is not None:
                    results.append(owner)

                self.scraper.driver.find_element(By.XPATH, CLOSE_MODAL).click()
                time.sleep(0.5)

            return results
        except NoSuchElementException:
            return []
        except Exception as e:
            print(e)
            print('get_franchise_agents')
            raise e

def standard(spider: TexasSpider) -> list[str]:
    resp = spider.get_franchise_agents()
    return  resp

def with_accuracy(spider: TexasSpider) -> list[str]:
    pass

def run_spider(env: dict) -> list[str]:

    try:
        seleniumUrl = env['seleniumUrl']
        proxy       = env['proxy']
        company     = env['company']
        logFile     = env['logFile']
        twocaptchaKey = env['twocaptchaKey']
        accuracy = env['accuracy']

        asc = TexasSpiderConfig(seleniumUrl, company, logFile, twocaptchaKey, proxy)
        _as = TexasSpider(asc)

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
