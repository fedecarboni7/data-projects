import re
from lxml import html

def get_clean_links_bizmls(broke_urls : any) -> str:
    
    result = []
    max_elements = broke_urls.count()
    BASE_URL = "https://bizmls.com/cgi-bin/a-bus-d.asp?LIST_NUMBER="

    for index in range(0, max_elements):
        url = broke_urls.nth(index).get_attribute('onclick')
        start = url.find("LIST_NUMBER=")
        end = url.find("&gen_hp")
        listing_number = url[start+12:end]
        result.append(BASE_URL+listing_number+"&more_details=go")

    return result

def clean_listing_number(listing_number : any) -> str:
    
    parts = listing_number.split(' ')
    return parts[2]

def check_length(array) -> str:
    if len(array) > 0:
        return array[0]
    
    return ''

def clean_loans(loans : any) -> str:
    loans_check = check_length(loans)
    parts = loans_check.split(' ')
    return parts[0].replace(',', '')

def check_int(value : any) -> "int | str":
    try:
        value = int(value.replace(',',''))
        return value
    except:
        return ''

def check_availability(value : any) -> bool:
    if len(value) > 0 and value[0] == 'Listing Not Found or Unavailable':
        return False
    return True

def extract_indiv_values(text : str, field : str) -> str:
    match = re.search(f'{field}:\s*(\d+|Y|N)', text)
    if match :
        match = match.group(1)
        return match
    else:
        return None

def get_max_index(text: str):
    elements = html.fromstring(text).find('ul')

    li = elements.findall('li')[-2]
    if li.find('a') == None :
        return li.find('span').text.strip()
    
    return li.find('a').text.strip()

def get_clean_links_business_for_sale(text : any) -> str:
    
    TABLE_XPATH = '//*[@id="searchFilterForm"]/section/div/div[1]'
    tree = html.fromstring(text)
    table = tree.xpath(TABLE_XPATH)

    results = list()
    for div in table[0].findall('div')[1:-2]:
        if div.find('table') is not None :
            results.append(div.find('table').find('caption').find('h2').find('a').attrib['href'])

    return results

def get_clean_amounts_bfs(value : any) -> list:
    if not re.search(r'\d+',value):
        return ['','',''] # no numbers in string
    value = value.replace('$','').replace(',', '').replace('K', '000').replace('M', '000000') # clean up value
    values = re.findall(r'\d+',value)
    min_value = int(values[0])
    max_value = min_value
    if len(values) > 1:
        max_value = int(values[1])
    range = str(min_value) + ' - ' + str(max_value)
    return [range, min_value, max_value]

def get_max_index_bizquest(text: str):

    MAX_PAGINATION_INDEX_XPATH = '//*[@id="results"]/nav/ul/li[9]/a'
    tree = html.fromstring(text)
    e = tree.xpath(MAX_PAGINATION_INDEX_XPATH)
    return e[0].text.strip()

def get_clean_links_bizquest (text : any) -> str:
    
    TABLE_XPATH = '//*[@id="results"]'
    tree = html.fromstring(text)
    table = tree.xpath(TABLE_XPATH)
    results = list()
    for div in table[0].findall('div'):
        if div.find('a') is not None :
            results.append(div.find('a').attrib['href'])

    return results

def get_clean_amounts_bizquest(value : str) -> int:
    if not re.search(r'\d+',value):
        return None # no numbers in string
    value = value.replace('$','').replace(',', '').replace('K', '000').replace('M', '000000') # clean up value
    value = re.findall(r'\d+',value)
    return int(value[0])

def get_max_index_bizbuysell(text: str):

    MAX_PAGINATION_INDEX_XPATH = '//*[@id="pagination-breadcrumbs-block"]/app-pagination/div/pagination-template/ul/li[6]/a'
    tree = html.fromstring(text)
    e = tree.xpath(MAX_PAGINATION_INDEX_XPATH)
    return e[0].text.strip()

def get_clean_links_bizbuysell (text : any, urlBase: str) -> str:
    
    TABLE_XPATH = '//*[@id="search-results"]/app-bfs-listing-container/div'
    tree = html.fromstring(text)
    table = tree.xpath(TABLE_XPATH)
    results = list()
    for div in table[0].findall('app-listing-diamond'):
        results.append(urlBase+div.find('a').attrib['href'])

    return results

def get_clean_links_franchise_flippers(text : any) -> str:
    
    TABLE_XPATH = '//*[@id="listing-tables"]/div/div/table/tbody'
    tree = html.fromstring(text)
    table = tree.xpath(TABLE_XPATH)
    results = list()
    for tr in table[0].findall('tr'):
        
        tds = tr.findall('td')
        result = dict()
        result['url'] =tr.attrib['onclick'][4:-2]
        result['listing number'] = tr.attrib['id']
        result['title'] = tds[1].find('a').text.strip()
        result['category'] = tds[2].text.strip()
        result['price'] = tds[3].text.strip()
        result['county'] = ''
        result['state'] = ''
        
        if tds[5].text :
            result['county'] = tds[5].text.strip()
        
        if tds[6].text :
            result['state'] = tds[6].text.strip()

        results.append(result)
    
    return results

def get_data_franchise_flippers(text: any) -> str:
    TABLE_XPATH = '//*[@id="listings-details-top"]/div/div[5]'
    DESC_XPATH = '//*[@id="contents-listings"]/p'
    EMPLOYEES_XPATH = '//*[@id="contents-listings"]/div[2]/div[4]/div[1]/h5[3]'
    TRAINING_XPATH = '//*[@id="listings-details-top"]/div/div[7]/div/div[1]/p'

    tree = html.fromstring(text)
    table = tree.xpath(TABLE_XPATH)
    desc = tree.xpath(DESC_XPATH)
    employees = tree.xpath(EMPLOYEES_XPATH)
    training = tree.xpath(TRAINING_XPATH)

    results = dict()
    results['annual_gross_revenue'] = None
    results['value_of_inventory'] = None
    results['value_of_assets'] = None
    results['business_category'] = None
    results['business_operates_from'] = None
    results['years'] = None
    results['seasonal_business'] = None
    results['annual_net_profit'] = None
    results['description'] = None
    results['training'] = None
    results['employees'] = None

    if len(desc) > 0 :
        results['description'] = desc[0].text.strip()
    
    if len(training) > 0 :
        results['training'] = training[0].text.strip()
    
    if len(employees) > 0 :
        results['employees'] = employees[0].text.strip()

    if len(table) == 0 :
        return results
    
    for div in table[0].findall('div'):
        h4 = div.findall('h4')
        h5 = div.findall('h5')

        for tit, val in zip(h4, h5):
            if 'annual gross revenue' in tit.text.lower().strip() :
                results['annual_gross_revenue'] = val.text.strip()
            elif 'value of inventory' in tit.text.lower().strip() :
               results['value_of_inventory'] = val.text.strip()
            elif 'value of assets' in tit.text.lower().strip() :
               results['value_of_assets'] = val.text.strip()
            elif 'business category' in tit.text.lower().strip() :
               results['business_category'] = val.text.strip()
            elif 'business operates from' in tit.text.lower().strip() :
               results['business_operates_from'] = val.text.strip()
            elif 'year established' in tit.text.lower().strip() :
               results['years'] = val.text.strip()
            elif 'seasonal business' in tit.text.lower().strip() :
               results['seasonal_business'] = val.text.strip()
            elif 'annual net profit' in tit.text.lower().strip() :
               results['annual_net_profit'] = val.text.strip()

    return results

def get_max_index_wesellrestaurants(text: str):

    MAX_PAGINATION_INDEX_XPATH = '/html/body/section[2]/div/div/div[1]/div/div/div/div[2]/div[2]/div[2]/ul'
    tree = html.fromstring(text)
    e = tree.xpath(MAX_PAGINATION_INDEX_XPATH)
    return len(e[0].findall('li'))

def get_clean_links_wesellrestaurants(text : any) -> str:
    
    TABLE_XPATH = '/html/body/section[2]/div/div/div[1]/div/div/div/div[2]/div[1]'
    tree = html.fromstring(text)
    table = tree.xpath(TABLE_XPATH)
    results = list()
    for div in table[0].findall('div'):
        if 'id' in div.attrib :
            results.append(div.find('div').find('a').attrib['href'])

    return results

def get_max_index_national_franchise_sale(text: str):

    MAX_PAGINATION_INDEX_XPATH = '//*[@id="listings-table_paginate"]/ul'
    tree = html.fromstring(text)
    ul = tree.xpath(MAX_PAGINATION_INDEX_XPATH)
    max_index = ul[0].findall('li')[-2].find('a').text.strip()

    return max_index

def get_clean_links_national_franchise_sales(text: str) :

    TABLE_XPATH = '//*[@id="listings-table"]/tbody'
    tree = html.fromstring(text)
    table = tree.xpath(TABLE_XPATH)
    results = list()

    for tr in table[0].findall('tr'):
        result = dict()
        result['brand'] = tr.findall('td')[0].findall('a')[1].text.strip()
        result['sales'] = tr.findall('td')[1].text.strip()
        result['cash_flow'] = tr.findall('td')[2].text.strip()
        result['updated'] = tr.findall('td')[3].text.strip()
        result['status'] = tr.findall('td')[4].find('span').text.strip()
        result['additional_info'] = tr.findall('td')[5].find('span').text.strip()
        result['listing_number'] = tr.findall('td')[0].attrib['data-href'].split('/')[2].strip()
        
        results.append(result)

    return results

def get_links_wesellrestaurants(text: str):

    MAX_PAGINATION_INDEX_XPATH = '//*[@id="div_block-14-52357"]'
    tree = html.fromstring(text)
    table = tree.xpath(MAX_PAGINATION_INDEX_XPATH)

    result = []
    for div in table[0].findall('div')[3:]:
        for a in div.find('div').find('div').findall('a'):
            result.append(a.attrib['href'])

    return result

def check_franchisee_franchiseresale(text: str):
    FRANCHISEES_XPATH = '//*[@id="shortcode-190-52363"]'
    tree = html.fromstring(text)
    table = tree.xpath(FRANCHISEES_XPATH)
    
    urls = []
    for div in table[0].findall('div'):
        for div2 in div.findall('div'):
            urls.append(div2.findall('div')[1].findall('span')[3].find('a').attrib['href'])
    
    return urls

def get_clean_links_bizben(text : any) -> list:
    
    TABLE_XPATH = '/html/body/div[2]/section[4]/div/div[1]/div[2]'
    tree = html.fromstring(text)
    table = tree.xpath(TABLE_XPATH)

    results = []

    if 'no postings found searching on your criteria' in text.lower() :
        return results
    
    for div in table[0].findall('div'):
        if 'bannerWrapper' in div.attrib['class'] :
            continue
        results.append(div.find('div').find('div').find('div').find('a').attrib['href'])
    
    return results

def get_number_of_category_buttons(text : any) :

    TABLE_XPATH = '//*[@id="filter-form-cell"]/div/div[2]/div/div[2]/div[2]/div/span/div/div'
    tree = html.fromstring(text)
    table = tree.xpath(TABLE_XPATH)

    results = []
    industry = 'not found'

    if table is None :
        return results
    
    for i, button in enumerate(table[0].findall('button')) :

        if 'multiselect-all' in button.attrib['class'] :
            continue

        if 'multiselect-group-option-indented' not in button.attrib['class'] :
            industry = button.attrib['title']
        
        if 'multiselect-group-option-indented' in button.attrib['class'] :
            category = button.attrib['title']
            results.append({
                'industry': industry,
                'category' : category,
                'index' : i+1
            })
    
    return results

def get_next_index(text: str) -> int:
    NEXT_INDEX_XPATH = '//*[@id="list_div"]/div[1]/div[1]/ul'
    tree = html.fromstring(text)
    table = tree.xpath(NEXT_INDEX_XPATH)


    for i, li in enumerate(table[0].findall('li')):
        if 'class' in li.attrib :
            if 'active' in li.attrib['class'] :
                if i == len(table[0].findall('li'))-1 :
                    print('no more pages')
                    return -1
            print("current = "+li.find('a').text.strip())
            print("Next in page :")
            return i + 2


def get_clean_links_murphy(text: str) :
    BODY_XPATH = '//*[@id="list_div"]/div[1]'
    tree = html.fromstring(text)
    table = tree.xpath(BODY_XPATH)

    results = []

    print(len(table[0].findall('div')))
    for div in table[0].findall('div')[3:]:
    
        title                  = div.find('h2').find('a').text.strip()
        link                   = div.find('h2').find('a').attrib['href']
        status                 = div.findall('div')[1].findall('ul')[0].findall('li')[0].find('span').text.strip()
        relocatable            = div.findall('div')[1].findall('ul')[0].findall('li')[1].find('span').text.strip()
        state                  = div.findall('div')[1].findall('ul')[1].findall('li')[0].find('span').text.strip()
        price                  = div.findall('div')[1].findall('ul')[1].findall('li')[1].find('span').text.strip()
        listing_id             = div.findall('div')[1].findall('ul')[1].findall('li')[2].find('span').text.strip()
        down_payment           = div.findall('div')[1].findall('ul')[2].findall('li')[0].find('span').text.strip()
        discretionary_earnings = div.findall('div')[1].findall('ul')[2].findall('li')[1].find('span').text.strip()
        total_sales            = div.findall('div')[1].findall('ul')[2].findall('li')[2].find('span').text.strip()
        description = ''
        category = ''

        all_tags               = div.findall('div')[3].xpath('.//*')
    
        is_category = False

        for tag in all_tags:
            if tag.tag == 'strong' :
                if 'category' in tag.text.strip().lower() :
                    is_category = True
                else :
                    is_category = False
            
            if tag.tag == 'p':

                if tag.text is None :
                    continue

                if is_category :
                    category = tag.text.strip()
                else :
                    description = description + tag.text.strip()
                
        results.append({
            'title' : title,
            'link' : link,
            'status' : status,
            'relocatable' : relocatable,
            'state' : state,
            'price' : price,
            'listing_id' : listing_id,
            'down_payment' : down_payment,
            'discretionary_earnings' : discretionary_earnings,
            'total_sales' : total_sales,
            'description' : description,
            'category' : category
        })

    return results