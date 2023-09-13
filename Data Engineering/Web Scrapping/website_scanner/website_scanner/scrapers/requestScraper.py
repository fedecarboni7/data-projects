from .scraper import Scraper
import requests
import random
import time
class RequestScraperConfig():
    def __init__(self, proxies: list[str] = []) -> None:
        self.proxies = proxies

class RequestScraper(Scraper):

    def __init__(self, config: RequestScraperConfig):
        super().__post_init__()
        self.proxies = config.proxies
        self.current_proxy = 0
        self.proxies_count = len(self.proxies)

    def set_site(self, site: str, switch_proxy: bool = False, set_waiting_seconds: int = -1) -> None:
        '''
        specifies the site we want to scrape.
        '''
        # if user didn't define a waiting time we set one ramdonly
        if set_waiting_seconds == -1:
            random_waiting_seconds = [1,2,3]
            waiting_seconds = random.choice(random_waiting_seconds)
            time.sleep(waiting_seconds)
        else :
            time.sleep(set_waiting_seconds)

        # if no proxies then just make the request without proxy
        if self.proxies_count > 0 :
            if switch_proxy :
                self.switchCurrentProxy()
            proxy = self.proxies[self.current_proxy]
            proxies = {
                'http': proxy
            }
            self.response = requests.get(site, proxies=proxies)

        else : 
            self.response = requests.get(site)

    def switchCurrentProxy(self):
        current_proxy = self.current_proxy + 1
        if current_proxy > self.proxies_count:
            current_proxy = 0
        self.current_proxy = current_proxy

    def get_raw_HTML(self) -> str :

        if self.response.status_code in range(200,300):
            return self.response.text
        else :
            pass