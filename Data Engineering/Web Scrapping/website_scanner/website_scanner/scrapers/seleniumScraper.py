import mysql.connector
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from .scraper import Scraper
from ..services.mysql import DatabasePool

class SeleniumScraperConfig():
    def __init__(self, url: str, user_agent: str = '', proxy: str = '') -> None:
        self.selenium_url = url
        self.proxy = proxy
        self.user_agent = user_agent


class SeleniumScraper(Scraper):

    def __init__(self, config: SeleniumScraperConfig) -> None:
        super().__post_init__()

        self.download_directory = 'downloads'

        obj = DatabasePool()
        self.conn = obj.get_single_connection()

        self.init_proxy = config.proxy
        self.init_selenium_url = config.selenium_url
        self.init_user_agent = config.user_agent

        self.driver = webdriver.Remote(
            command_executor=config.selenium_url,
            options=self.set_chrome_options(config.proxy, config.user_agent)
        )

        self.driver.maximize_window() 

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def discard_user_agent(self) -> None:
        cursor = self.conn.cursor(buffered=True)
        cursor.execute('INSERT INTO discarded_useragent SELECT * FROM active_useragent WHERE id=%s',[self.current_user_agent])
        cursor.execute('DELETE FROM active_useragent WHERE id=%s',[self.current_user_agent])
        self.conn.commit()
        cursor.close()

    def get_new_user_agent(self) -> str:

        cursor = self.conn.cursor(buffered=True)
        cursor.execute('SELECT user_agent, id FROM active_useragent ORDER BY RAND() LIMIT 1')
        desc = cursor.description
        column_names = [col[0] for col in desc]
        data = [dict(zip(column_names, row))
                for row in cursor.fetchall()]
        cursor.close()
        
        self.current_user_agent = data[0]['id']
        return data[0]['user_agent']
        
    def set_site(self, site: str) -> None:
        self.driver.get(site)

    def set_chrome_options(self, proxy = '', user_agent = '') -> Options:
        """Sets chrome options for Selenium.
        Chrome options for headless browser is enabled.
        """

        chrome_options = Options()
        if proxy != '' :
            chrome_options.add_argument(f'--proxy-server={proxy}')
            
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument('--start-fullscreen')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument("disable-infobars")
        chrome_options.add_argument("plugins.always_open_pdf_externally=False")
        
        #user_agent = 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36'
        
        if user_agent != '' :
            chrome_options.add_argument(f'user-agent={user_agent}')
        else :
            user_agent = self.get_new_user_agent()
            chrome_options.add_argument(f'user-agent={user_agent}')
        
        chrome_options.add_experimental_option('prefs', {
            "excludeSwitches": ["enable-automation"],
            "useAutomationExtension": False,
            "download.default_directory": '/'+self.download_directory,
            "download.prompt_for_download": False, #To auto download the file
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
        })

        return chrome_options

    def restart_session(self) -> None:

        if self.init_user_agent != '' :
            raise "you can't use restart session if you are using a custom user_agent"

        self.driver.quit()

        self.driver = webdriver.Remote(
            command_executor=self.init_selenium_url,
            options=self.set_chrome_options(self.init_proxy, '')
        )
        
        self.driver.maximize_window() 
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def get_raw_HTML(self) -> str:
        return self.driver.page_source

    def close_session(self) :
        self.driver.quit()
        self.conn.close()

        