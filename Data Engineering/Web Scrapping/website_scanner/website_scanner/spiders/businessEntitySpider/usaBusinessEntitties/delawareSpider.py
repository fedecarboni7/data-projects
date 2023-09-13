import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import delaware_extract_owner, delaware_extract_data_site_key, delaware_check_recaptcha
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig
from ....services.captchaService import solve_recaptcha

STATE = "Delaware"
BASE_URL = "https://icis.corp.delaware.gov/Ecorp/EntitySearch/NameSearch.aspx"
INPUT_XPATH = '//*[@id="ctl00_ContentPlaceHolder1_frmEntityName"]'
SEARCH_BUTTON_XPATH = '//*[@id="ctl00_ContentPlaceHolder1_btnSubmit"]'
FIRST_OPTION_XPATH = '//*[@id="ctl00_ContentPlaceHolder1_rptSearchResults_ctl00_lnkbtnEntityName"]'
SUBMIT_RECAPTCHA_XPATH = '/html/body/table/tbody/tr/td/div/table/tbody/tr[2]/td/table[3]/tbody/tr[3]/td/form/input'


class DelawareSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, twocaptcha_key: str, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.twocaptcha_key = twocaptcha_key
        self.proxy = proxy


class DelawareSpider:
    def __init__(self, config: DelawareSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy=config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.twocaptcha_key = config.twocaptcha_key
        self.proxy = config.proxy

    def get_franchise_agents(self) -> "list[str]":

        try:
            self.scraper.set_site(BASE_URL)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company)
            self.scraper.driver.find_element(By.XPATH, SEARCH_BUTTON_XPATH).click()
            if delaware_check_recaptcha(self.scraper.get_raw_HTML()):
                siteKey = delaware_extract_data_site_key(self.scraper.get_raw_HTML())
                res = solve_recaptcha(siteKey, BASE_URL, self.twocaptcha_key)
                self.scraper.driver.execute_script("document.getElementById('g-recaptcha-response').innerHTML = " + "'" + res['code'] + "'")
                self.scraper.driver.execute_script("function getElementByXpath(path){return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;} getElementByXpath('" + SUBMIT_RECAPTCHA_XPATH + "').click();")
                self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company)
                self.scraper.driver.find_element(By.XPATH, SEARCH_BUTTON_XPATH).click()
            time.sleep(2)
            self.scraper.driver.find_element(By.XPATH, FIRST_OPTION_XPATH).click()
            return delaware_extract_owner(self.scraper.get_raw_HTML())
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
        twocaptchaKey = env['twocaptchaKey']
        asc = DelawareSpiderConfig(seleniumUrl, company, logFile, twocaptchaKey, proxy)
        _as = DelawareSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("Delaware run_spider error")
        print(e)
        raise e
