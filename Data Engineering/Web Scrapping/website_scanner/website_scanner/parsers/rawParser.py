def rawParser(text: str, pattern) -> str :
    '''
        looks for text no mater where it is
    '''
    name = 'TextFinder'

    custom_settings = {
        'LOG_ENABLED':False
    }
    
    def start_requests(self):
        #yield scrapy.Request(self.url)
        pass

    def parse(self, response):

        data = response.xpath('//script[@id = "hs-script-loader"]').extract()
        return {'data': data}