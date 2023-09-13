import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import massachusetts_extract_owner_urls, massachusetts_extract_owner
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

STATE = "Massachusetts"
BASE_URL = "https://corp.sec.state.ma.us/CorpWeb/CorpSearch/"
SEARCHING_PATH = 'CorpSearch.aspx'
INPUT_XPATH = '//*[@id="MainContent_txtEntityName"]'

class MassachusettsSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.proxy = proxy


class MassachusettsSpider:
    def __init__(self, config: MassachusettsSpiderConfig) -> None:
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
            time.sleep(3) # less than 3 causes errors

            urls = massachusetts_extract_owner_urls(self.scraper.get_raw_HTML())

            results = list()

            for url in urls:
                
                self.scraper.set_site(BASE_URL+url)
                time.sleep(3)
                results.append(massachusetts_extract_owner(self.scraper.get_raw_HTML()))

            return results
        except NoSuchElementException:
            print("NoSuchElementException")
            
            return []
        except Exception as e:
            print("getUserInfo")
            print(e)
            raise e

def standard(spider: MassachusettsSpider) -> list[str]:
    resp = spider.get_franchise_agents()
    return  resp

def with_accuracy(spider: MassachusettsSpider) -> list[str]:
    pass

def run_spider(env: dict) -> "list[str]":

    try:
        seleniumUrl = env["seleniumUrl"]
        proxy = env["proxy"]
        company = env["company"]
        logFile = env["logFile"]
        accuracy = env['accuracy']

        asc = MassachusettsSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = MassachusettsSpider(asc)

        resp = list()
        if accuracy:
            resp = with_accuracy(_as)
        else :
            resp = standard(_as)

        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("Massachusetts run_spider error")
        print(e)
        raise e
