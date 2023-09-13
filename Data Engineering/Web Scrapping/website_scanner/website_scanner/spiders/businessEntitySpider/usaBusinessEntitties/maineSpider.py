import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import maine_extract_owner_urls,maine_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

STATE = "Maine"
BASE_URL = "https://icrs.informe.org"
SEARCHING_PATH = '/nei-sos-icrs/ICRS?MainPage=x'
INPUT_XPATH = '/html/body/form/center/table/tbody/tr[3]/td/table/tbody/tr[4]/td/table/tbody/tr/td[2]/input'


class MaineSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.proxy = proxy


class MaineSpider:
    def __init__(self, config: MaineSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.proxy = config.proxy

    def get_franchise_agents(self) -> list[str]:

        try:
 
            self.scraper.set_site(BASE_URL+SEARCHING_PATH)
            time.sleep(2)
            self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company + Keys.RETURN)
            time.sleep(1)

            urls = maine_extract_owner_urls(self.scraper.get_raw_HTML())
            
            results = list()

            for url in urls:

                self.scraper.set_site(BASE_URL+url)
                time.sleep(2)
                results.append(maine_extract_owner(self.scraper.get_raw_HTML()))
                
            return results
        except NoSuchElementException:
            print("NoSuchElementException")
            
            return []
        except Exception as e:
            print("getUserInfo")
            print(e)
            raise e

def standard(spider: MaineSpider) -> list[str]:
    resp = spider.get_franchise_agents()
    return  resp

def with_accuracy(spider: MaineSpider) -> list[str]:
    pass

def run_spider(env: dict) -> "list[str]":

    try:
        seleniumUrl = env["seleniumUrl"]
        proxy = env["proxy"]
        company = env["company"]
        logFile = env["logFile"]
        accuracy = env['accuracy']

        asc = MaineSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = MaineSpider(asc)

        resp = list()
        if accuracy:
            resp = with_accuracy(_as)
        else :
            resp = standard(_as)

        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("Maine run_spider error")
        print(e)
        raise e
