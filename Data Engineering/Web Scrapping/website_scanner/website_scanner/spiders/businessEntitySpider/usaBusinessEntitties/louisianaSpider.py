import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import louisiana_extract_owner, louisiana_extract_data_site_key
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig
from ....services.captchaService import solve_recaptcha

STATE = "Louisiana"
BASE_URL = "https://coraweb.sos.la.gov/CommercialSearch/CommercialSearch.aspx"
INPUT_XPATH = '//*[@id="ctl00_cphContent_txtEntityName"]'
SEARCH_RESULTS_XPATH = '//*[@id="ctl00_cphContent_btnBackToSearchResults"]'


class LouisianaSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, twocaptcha_key: str, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.twocaptcha_key = twocaptcha_key
        self.proxy = proxy


class LouisianaSpider:
    def __init__(self, config: LouisianaSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.twocaptcha_key = config.twocaptcha_key
        self.proxy = config.proxy

    def get_franchise_agents(self) -> "list[str]":

        try:
            self.scraper.set_site(BASE_URL)
            siteKey = louisiana_extract_data_site_key(self.scraper.get_raw_HTML())
            res = solve_recaptcha(siteKey, BASE_URL, self.twocaptcha_key)
            self.scraper.driver.execute_script("document.getElementById('g-recaptcha-response').innerHTML = " + "'" + res['code'] + "'")
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company + Keys.RETURN)
            try:
                owners = louisiana_extract_owner(self.scraper.get_raw_HTML())
                if owners[0] == "Inactive":
                    owners.clear()
                return owners
            except:
                for i in range(2, 7):
                    OPTION_XPATH = f'//*[@id="ctl00_cphContent_grdSearchResults_EntityNameOrCharterNumber_ctl0{i}_btnViewDetails"]'
                    try:
                        self.scraper.driver.find_element(By.XPATH, OPTION_XPATH).click()
                        owners = louisiana_extract_owner(self.scraper.get_raw_HTML())
                        if owners[0] == "Inactive":
                            self.scraper.driver.find_element(By.XPATH, SEARCH_RESULTS_XPATH).click()
                            time.sleep(0.5)
                            continue
                        return owners
                    except:
                        return []
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
        asc = LouisianaSpiderConfig(seleniumUrl, company, logFile, twocaptchaKey, proxy)
        _as = LouisianaSpider(asc)
        resp = _as.get_franchise_agents()
        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("Louisiana run_spider error")
        print(e)
        raise e
