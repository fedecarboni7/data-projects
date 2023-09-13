import mysql.connector
from playwright.sync_api import sync_playwright
from .scraper import Scraper
from ..services.mysql import DatabasePool

class PlaywrightScraperConfig():
    def __init__(self, user_agent: str = '', proxy: str = '') -> None:
        self.proxy = proxy
        self.user_agent = user_agent


class PlaywrightScraper(Scraper):

    def __init__(self, config: PlaywrightScraperConfig) -> None:
        super().__post_init__()

        obj = DatabasePool()
        self.conn = obj.get_single_connection()
    
        self.pw = sync_playwright().start()

        self.set_browser_options(config.proxy, config.user_agent)

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
        self.page.goto(site)

    def set_browser_options(self, proxy = '', user_agent = '') -> None:

        options = {}

        if proxy != '' :
            options['proxy'] = {'server': proxy, 'timeout': 60000 }
        
        self.browser = self.pw.chromium.launch(**options)

        user_agent= ''
        if user_agent != '' :
            context =  self.browser.new_context(user_agent=user_agent)
        else :
            user_agent = self.get_new_user_agent()
            context =  self.browser.new_context(user_agent=user_agent)

        self.page = context.new_page()

    def get_raw_HTML(self) -> str:
        return self.page.content()

    def get_new_pw_context(self, proxy):
        
        user_agent = self.get_new_user_agent()
        context = self.browser.new_context(user_agent=user_agent, proxy={'server': proxy})
        return context.new_page()

    def close_session(self) :
        self.browser.close()
        self.pw.stop()
        self.conn.close()