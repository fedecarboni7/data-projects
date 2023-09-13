import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import indiana_extract_owner, indiana_extract_data_site_key, indiana_find_active
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig
from ....services.captchaService import solve_recaptcha

STATE = "Indiana"
BASE_URL = "https://bsd.sos.in.gov/publicbusinesssearch"
INPUT_XPATH = '//*[@id="txtBusinessName"]'
EXACT_MATCH_XPATH = '//*[@id="rdExactMatch"]'
ENTITIE_OPTIONS_XPATH = '/html/body/div[2]/table/tbody/tr[3]/td/div/table[1]/tbody/tr[{}]/td[1]/a'


class IndianaSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, twocaptcha_key: str, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.twocaptcha_key = twocaptcha_key
        self.proxy = proxy


class IndianaSpider:
    def __init__(self, config: IndianaSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy=config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.twocaptcha_key = config.twocaptcha_key
        self.proxy = config.proxy

    def get_franchise_agents(self) -> "list[str]":

        try:
            self.scraper.set_site(BASE_URL)
            siteKey = indiana_extract_data_site_key(self.scraper.get_raw_HTML())
            res = solve_recaptcha(siteKey, BASE_URL, self.twocaptcha_key)
            self.scraper.driver.execute_script("document.getElementById('g-recaptcha-response').innerHTML = " + "'" + res['code'] + "'")
            self.scraper.driver.find_element(By.XPATH, EXACT_MATCH_XPATH).click()
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company + Keys.RETURN)
            tr_num = indiana_find_active(self.scraper.get_raw_HTML())
            self.scraper.driver.find_element(By.XPATH, ENTITIE_OPTIONS_XPATH.format(tr_num)).click()
            return indiana_extract_owner(self.scraper.get_raw_HTML())
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
        asc = IndianaSpiderConfig(seleniumUrl, company, logFile, twocaptchaKey, proxy)
        _as = IndianaSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("Indiana run_spider error")
        print(e)
        raise e
