import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ....parsers.businessEntityParser import illinois_extract_owner, illinois_detect_invalid_user_agent
from ....scrapers.seleniumScraper import SeleniumScraper, SeleniumScraperConfig

STATE = "Illinois"
BASE_URL = "https://apps.ilsos.gov/corporatellc/"
SUBMIT_BUTTON_XPATH = '//*[@id="subCon"]'
INPUT_XPATH = '//*[@id="SOS6299469"]'
FIRST_OPTION_XPATH = '/html/body/div/div[3]/table/tbody/tr[2]/td[3]/a'


class IllinoisSpiderConfig:
    def __init__(self, seleniumUrl: str, company: str, logFile, proxy: str = "") -> None:
        self.seleniumUrl = seleniumUrl
        self.company = company
        self.logFile = logFile
        self.proxy = proxy


class IllinoisSpider:
    def __init__(self, config: IllinoisSpiderConfig) -> None:
        ssc = SeleniumScraperConfig(config.seleniumUrl, proxy = config.proxy)
        self.scraper = SeleniumScraper(ssc)
        self.company = config.company
        self.logFile = config.logFile
        self.proxy = config.proxy

    def get_franchise_agents(self) -> list[str]:

        try:
            bad_user_agent_status = True

            while bad_user_agent_status:
                
                self.scraper.set_site(BASE_URL)
                time.sleep(4)

                if illinois_detect_invalid_user_agent(self.scraper.get_raw_HTML()) :
                    print('borro')
                    self.scraper.discard_user_agent()
                    self.scraper.restart_session()
                else :
                    print('se pudo con '+str(self.scraper.current_user_agent))
                    bad_user_agent_status = False
            

            #self.scraper.driver.find_element(By.XPATH, SUBMIT_BUTTON_XPATH).click()
            #self.scraper.driver.execute_script('document.getElementById("subCon").click()')
            #time.sleep(4)
            #self.scraper.driver.find_element(By.XPATH, INPUT_XPATH).send_keys(self.company + Keys.RETURN)
            #time.sleep(1)
            #self.scraper.driver.find_element(By.XPATH, FIRST_OPTION_XPATH).click()
            #time.sleep(1) 
            #print(self.scraper.get_raw_HTML())
            return []#illinois_extract_owner(self.scraper.getRawHTML())
        except NoSuchElementException:
            print("NoSuchElementException")
            
            return []
        except Exception as e:
            print("getUserInfo")
            print(e)
            raise e

def standard(spider: IllinoisSpider) -> list[str]:
    resp = spider.get_franchise_agents()
    return  resp

def with_accuracy(spider: IllinoisSpider) -> list[str]:
    pass

def run_spider(env: dict) -> "list[str]":

    try:
        seleniumUrl = env["seleniumUrl"]
        proxy = env["proxy"]
        company = env["company"]
        logFile = env["logFile"]
        accuracy = env['accuracy']

        asc = IllinoisSpiderConfig(seleniumUrl, company, logFile, proxy)
        _as = IllinoisSpider(asc)

        resp = list()
        if accuracy:
            resp = with_accuracy(_as)
        else :
            resp = standard(_as)

        _as.scraper.close_session()
        return resp
    except Exception as e:
        print("Illinois run_spider error")
        print(e)
        raise e
