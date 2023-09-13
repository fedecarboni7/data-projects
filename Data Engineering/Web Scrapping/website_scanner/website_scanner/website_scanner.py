from website_scanner.website_scanner.scrapers.scraper import Scraper

class WebSiteScanner():

    def __init__(self, controller: Scraper):

        self.controller = controller
    
    def scanWebsite(self, url : str) :
        '''
            single scan
        '''
        return self.controller.get_raw_HTML()

