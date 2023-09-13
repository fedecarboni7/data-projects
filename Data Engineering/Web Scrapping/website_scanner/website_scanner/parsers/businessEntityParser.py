from bs4 import BeautifulSoup
from lxml import html
import re
                   
def alabama_extract_owner(page : str) -> list[str]:

    OWNER_XPATH = '//*[@id="block-sos-content"]/div/div/div/table[2]/tbody[1]'

    tree = html.fromstring(page)
    found = False
    
    options = tree.xpath(OWNER_XPATH)
    for i in options[0].findall('tr'):
        data = i.findall('td')

        if len(data) < 2 :
            continue

        if data[0] is None or  data[1] is None:
            continue

        if data[0].text.strip() == 'Registered Agent Name':
            return [data[1].text.strip()]

    return []

def arkansas_extract_owner(page: str) -> list[str]:
    OWNER_XPATH = '//*[@id="mainContent"]/table[2]/tbody'
    tree = html.fromstring(page)
    found = False

    options = tree.xpath(OWNER_XPATH)
    for i in options[0].findall('tr'):
        data = i.findall('td')

        if len(data) < 2 :
            continue

        if data[0].find('font') is None or  data[1].find('font') is None:
            continue

        if data[0].find('font').text.strip() == 'Reg. Agent':
             return [data[1].find('font').text.strip()]
           
    return []

def california_extract_owner(page: str) -> "list[str]":
    OWNER_XPATH = '//*[@id="root"]/div/div[1]/div/main/div[2]/table/tbody'
    NO_RESULTS_XPATH = '//*[@id="root"]/div/div[1]/div/main/div[2]/svg'
    RESULTS_LIMIT = 5

    tree = html.fromstring(page)

    if tree.xpath(NO_RESULTS_XPATH):
        return []

    agent_names = list()
    options = tree.xpath(OWNER_XPATH)
    cant_results = 0
    for i in options[0].findall('tr'):
        data = i.findall('td')

        agent_name = data[5].findall('span')
        try:
            agent_names.append(agent_name[0].text.strip())
            cant_results += 1
            if cant_results == RESULTS_LIMIT:
                break
        except:
            continue

    return agent_names

def colorado_extract_owner_pages(page: str) -> list[str]:
    TABLE_XPATH = '//*[@id="box"]/table/tbody'
    tree = html.fromstring(page)
    options = tree.xpath(TABLE_XPATH)

    nonBreakSpace = u'\xa0'

    if len(options[0].findall('tr')) < 1 :
        return []

    headers = options[0].findall('tr')[0]

    index = 0
    id_index = 0
    status_index = 0
    found_status_col = False
    found_link_col = False

    for header in headers.findall('th') :
        if header.find('a') is None:
            index += 1
            continue

        if header.find('a').find('b').text == 'ID Number' :
            found_link_col = True
            id_index = index

        if header.find('a').find('b').text == 'Status' :
            found_status_col = True
            status_index = index

        index += 1

    if not found_status_col or not found_link_col : return []

    urls = list()

    for i in options[0].findall('tr')[1:]:
        status = i.findall('td')[status_index]
        if status.text.strip().replace(nonBreakSpace, ' ') == 'Good Standing' :
            link = i.findall('td')[id_index].find('a')
            urls.append(link.attrib['href'])

    return urls

def colorado_extract_owner(page: str) -> str|None:
    TABLE_XPATH = '//*[@id="application"]/table/tbody/tr/td[2]/table/tbody/tr[3]/td/form/table[1]/tbody/tr[1]/td/table/tbody/tr[7]/td/table/tbody'
    tree = html.fromstring(page)
    table = tree.xpath(TABLE_XPATH)

    header = table[0].findall('tr')[0].find('th')

    if header.text.strip() == 'Registered Agent' :
        for tr in table[0].findall('tr')[1:] :
            tds = tr.findall('td')

            if tds[0].text.strip() == 'Name':
                return tds[1].text.strip()

    return None

def connecticut_extract_owner(page: str) -> "list[str]":
    OWNER_XPATH = '//*[@id="ServiceCommunityTemplate"]/div[1]/div/div[2]/div/div/div/div/div/div/div/section/div/div[2]/div/div/div/c-brs_-business-search/div/div/div[2]/c-brs_business-detail-card'
    NO_RESULTS_XPATH = '//*[@id="ServiceCommunityTemplate"]/div[1]/div/div[2]/div/div/div/div/div/div/div/section/div/div[2]/div/div/div/c-brs_-business-search/div/div/div[2]/c-brs_no-data-card'
    RESULTS_LIMIT = 5

    tree = html.fromstring(page)

    if tree.xpath(NO_RESULTS_XPATH):
        return []

    cards = tree.xpath(OWNER_XPATH)
    principals_name = list()
    cant_results = 0

    for card in cards[0].findall('div'):
        status = card.findall('div')[0].findall('div')[0].findall('div')[1].findall('span')[0].findall('c-brs_badges')[0].findall('span')
        if status[0].text.strip() != 'ACTIVE':
            continue

        principal_name = card.findall('div')[1].findall('div')[0].findall('div')[0].findall('div')[0].findall('p')
        try:
            for name in principal_name:
                if name.text.strip() != 'View all':
                    principals_name.append(name.text.strip())
            cant_results += 1
            if cant_results == RESULTS_LIMIT:
                break
        except:
            continue

    return principals_name

def florida_extract_owner(page: str) -> "str|None":
    REGISTERED_AGENT_XPATH = '//*[@id="maincontent"]/div[2]/div[5]/span[2]'

    tree = html.fromstring(page)

    agent_name = tree.xpath(REGISTERED_AGENT_XPATH)
    
    if len(agent_name) == 0 : return None
    return agent_name[0].text.strip()

def florida_check_status(page:str) -> "list[int] | None":
    TABLE_XPATH = '//*[@id="search-results"]/table/tbody'
    RESULTS_LIMIT = 5

    tree = html.fromstring(page)
    options = tree.xpath(TABLE_XPATH)

    if not options:
        return None

    active_entities = []
    entity_number = 1

    for i in options[0].findall('tr'):
        data = i.findall('td')
        if data[2].text.strip() == 'Active':
            active_entities.append(entity_number)
        if entity_number == RESULTS_LIMIT:
            break
        entity_number += 1
    return active_entities

def texas_extract_data_site_key(page: str) -> str:
    DSK_XPATH = '//*[@id="rcaptcha"]'
    tree = html.fromstring(page)
    options = tree.xpath(DSK_XPATH)
    dsk = options[0].attrib['data-sitekey']
    return dsk

def texas_get_number_of_options(page: str) -> int:
    TABLE_XPATH = '/html/body/div/div[3]/form/div[1]/div[1]/div[2]/div[1]/div/div/table/tbody'
    tree = html.fromstring(page)
    options = tree.xpath(TABLE_XPATH)
    if len(options) > 0:
        return len(options[0].findall('tr'))
    return 0

def texas_get_option_status(page: str) -> bool:
    MODAL_XPATH = '//*[@id="editModal"]'
    tree = html.fromstring(page)
    modal = tree.xpath(MODAL_XPATH)
    if 'display: none;' in modal[0].attrib['style'] :
        return False

    return True

def texas_extract_owner(page: str) -> str|None:
    TABLE_XPATH = '//*[@id="trDetailsBody"]'
    tree = html.fromstring(page)
    table = tree.xpath(TABLE_XPATH)

    for tr in table[0].findall('tr'):
        data = tr.findall('td')

        if data[0].find('b') is None :
            continue

        if data[0].find('b').text.strip() == 'Registered Agent Name':
            return data[1].text.strip()

    return None

def illinois_detect_invalid_user_agent(page: str) -> bool:
    matching_texts = [
        'Sorry, the page you are looking for is not available.  Please email webmaster@ilsos.gov including the Reference ID and Client IP numbers below',
        "You don't have permission to access"
        ]

    for matching_text in matching_texts :
        if matching_text in page:
            return True
    
    return False

def illinois_extract_owner(page: str) -> "list[str]":
    TABLE_XPATH = '/html/body/div/div[3]'
    tree = html.fromstring(page)
    table = tree.xpath(TABLE_XPATH)

    for div in table[0].findall('div'):
        agent_div = div.findall('div')[0].findall('h3')[0].text.strip()
        if agent_div == 'Agent Information':
            agent_name = div.findall('div')[1].findall('div')[0].findall('div')[0].text.strip()
            return [agent_name]

    return []
    
def newyork_get_number_of_options(page: str) -> int:
    TABLE_XPATH = '//*[@id="app"]/div/main/div/div/div/div[2]/div/div[1]/div/div[2]/div/div[1]/table/tbody'
    tree = html.fromstring(page)
    options = tree.xpath(TABLE_XPATH)
    if len(options) > 0:
        return len(options[0].findall('tr'))
    return 0

def newyork_extract_owner(page: str) -> str|None:
    OWNER_XPATH = '//*[@id="app"]/div/main/div/div/div[2]/div[3]/div[4]/div/div[2]/div[1]/div/span[2]'
    NAME_XPATH = '//*[@id="app"]/div/main/div/div/div[2]/div[1]/div[2]/div/div/div/div/div/div[1]/span/span[2]'

    tree = html.fromstring(page)

    owner = tree.xpath(OWNER_XPATH)
    name = tree.xpath(NAME_XPATH)

    _owner = owner[0].text.strip()
    _name = name[0].text.strip()

    if not _owner and not _name:
        return None
    
    return "//".join([_name,_owner])

def north_carolina_extract_owner(page: str) -> "list[str]":
    OFFICERS_SECTION_XPATH = '//*[@id="filings-article"]/section/section[4]'
    INFORMATION_XPATH = '//*[@id="filings-article"]/section/section[2]/div'
    LEGAL_NAME_XPATH = '//*[@id="filings-article"]/section/section[1]/div/span[2]'

    tree = html.fromstring(page)
    
    legal_name = tree.xpath(LEGAL_NAME_XPATH)
    if len(legal_name) == 0 : return []
    legal_name = legal_name[0].text.strip()
    
    officers_section = tree.xpath(OFFICERS_SECTION_XPATH)
    owners = []    
    if len(officers_section) > 0:
        for p in officers_section[0].findall('p'):
            officer = p.findall('span')[1].find('a')
            officer_names = officer.text.strip()
            for name in officer.findall('span'):
                try:
                    officer_names += f' {name.text.strip()}'
                except:
                    continue
            owners.append(legal_name + '//' + officer_names)
    
    if not owners:
        owners = [legal_name + '//']
        information = tree.xpath(INFORMATION_XPATH)
        agent_name = information[0].findall('span')[-1].find('a')
        if agent_name is not None:
            owners[0] += agent_name.text.strip()

    return owners

def ArizonaExtractOwner(page : str) -> str:

    ARIZONA_OWNER_XPATH = '/html/body/div[1]/div/div[14]/div[2]'
    tree = html.fromstring(page)
    names = tree.xpath(ARIZONA_OWNER_XPATH)
    for name in names :
        print('===' + name.text+ '+++')
    return names

def michigan_extract_owner(page: str) -> "list[str]":
    ENTITIE_NAME_XPATH = '//*[@id="MainContent_lblEntityNameHeader"]'
    AGENT_XPATH = '//*[@id="MainContent_lblResidentAgentName"]'
    tree = html.fromstring(page)
    entitie = tree.xpath(ENTITIE_NAME_XPATH)[0].text.strip()
    agent = tree.xpath(AGENT_XPATH)
    if len(agent) > 0:
        agent = agent[0].text.strip()
        return [entitie + "//" + agent]
    return [entitie + "//"]

def delaware_extract_owner(page: str) -> "list[str]":
    ENTITIE_NAME_XPATH = '//*[@id="ctl00_ContentPlaceHolder1_lblEntityName"]'
    AGENT_XPATH = '//*[@id="ctl00_ContentPlaceHolder1_lblAgentName"]'
    tree = html.fromstring(page)
    entitie = tree.xpath(ENTITIE_NAME_XPATH)[0].text.strip()
    agent = tree.xpath(AGENT_XPATH)
    if len(agent) > 0:
        agent = agent[0].text.strip()
        return [entitie + "//" + agent]
    return [entitie + "//"]

def delaware_extract_data_site_key(page: str) -> str:
    DSK_XPATH = '//*[@id="hdr"]/table/tbody/tr[2]/td/table[3]/tbody/tr[3]/td/form/div'
    tree = html.fromstring(page)
    options = tree.xpath(DSK_XPATH)
    dsk = options[0].attrib['data-sitekey']
    return dsk

def delaware_check_recaptcha(page: str) -> bool:
    RECAPTCHA_XPATH = '//*[@id="hdr"]/table/tbody/tr[2]/td/table[3]/tbody/tr[3]/td'
    tree = html.fromstring(page)
    options = tree.xpath(RECAPTCHA_XPATH)
    if len(options) > 0:
        return True
    return False

def hawaii_extract_owner(page: str) -> "list[str]":
    ENTITIE_NAME_XPATH = '//*[@id="body-container"]/main/div[1]/div[1]/h1'
    TABLE_NAME_XPATH = '//*[@id="general"]/section[3]/h2'
    TABLE_XPATH = '//*[@id="officersTable"]/tbody'
    AGENT_XPATH = '//*[@id="general"]/section[1]/div[2]/div[2]/dl'

    tree = html.fromstring(page)
    entitie = tree.xpath(ENTITIE_NAME_XPATH)[0].text.strip()
    try:
        table_name = tree.xpath(TABLE_NAME_XPATH)[0].text.strip()
    except:
        table_name = []

    if table_name in ['Member/MGR', 'Officers']:
        owners_table = tree.xpath(TABLE_XPATH)
        if len(owners_table) > 0:
            owners = []
            for owner in owners_table[0].findall('tr'):
                owners.append(entitie + "//" + owner.findall('td')[0].text.strip())
            return owners
    
    agent_info = tree.xpath(AGENT_XPATH)
    if len(agent_info) > 0:
        agent_name_pos = 0
        for agent_field in agent_info[0].findall('dt'):
            if agent_field.text.strip() == 'AGENT NAME':
                agent_name = agent_info[0].findall('dd')[agent_name_pos].text.strip()
                return [entitie + "//" + agent_name]
            agent_name_pos += 1
    return [entitie + "//" + "NOT FOUND"]

def idaho_extract_owner(page: str) -> "list[str]":

    TABLE_XPATH = '//*[@id="root"]/div/div[1]/div/main/div[2]/table/tbody'
    RESULTS_LIMIT = 3

    tree = html.fromstring(page)
    options = tree.xpath(TABLE_XPATH)

    if not options:
        return None

    results = []

    count = 0
    for i in options[0].findall('tr'):

        if count == RESULTS_LIMIT:
            break

        data = i.findall('td')
        _owner = data[3].findall('span')[0].text.strip()
        _company_found = data[0].findall('div')[0].findall('span')[0].text.strip()
        results.append("//".join([_company_found,_owner]))
        count += 1
    
    return results

def indiana_extract_owner(page: str) -> "list[str]":
    ENTITIE_NAME_XPATH = '/html/body/table/tbody/tr[1]/td/div/table/tbody/tr[2]/td[2]/strong'
    GOVERNING_PERSON_TABLE = '//*[@id="grid_principalList"]/tbody'
    TABLE_BODY_XPATH = '/html/body/table/tbody'
    AGENT_XPATH = '/td/div/table/tbody/tr[3]/td[2]/strong'

    tree = html.fromstring(page)
    entitie = tree.xpath(ENTITIE_NAME_XPATH)[0].text.strip()
    table = tree.xpath(GOVERNING_PERSON_TABLE)
    if len(table) > 0:
        owners = []
        for i in table[0].findall('tr'):
            owner = i.findall('td')[1].text.strip()
            owners.append(entitie + "//" + owner)
        return owners
    
    table_body = tree.xpath(TABLE_BODY_XPATH)
    tr_num = 1
    for tr in table_body[0].findall('tr'):
        agent_table = tr.findall('td')[0].findall('div')[0].findall('table')[0].findall('tbody')[0].findall('tr')[0].findall('td')[0].text.strip()
        if agent_table == 'Registered Agent Information':
            agent_name_xpath = TABLE_BODY_XPATH + f'/tr[{tr_num}]' + AGENT_XPATH
            agent = tree.xpath(agent_name_xpath)
            try:
                return [entitie + "//" + agent[0].text.strip()]
            except:
                return [entitie + "//"]
        tr_num += 1

def indiana_extract_data_site_key(page: str) -> str:
    CAPTCHA_SCRIPT_XPATH = '//*[@id="Captchahide"]/div/script[2]'
    tree = html.fromstring(page)
    options = tree.xpath(CAPTCHA_SCRIPT_XPATH)
    dsk = re.search("'sitekey':.'(.*)',", options[0].text).group(1)
    return dsk

def indiana_find_active(page: str) -> int:
    TABLE_XPATH = '//*[@id="grid_businessList"]/tbody'

    tree = html.fromstring(page)
    table = tree.xpath(TABLE_XPATH)
    if table == []:
        return -1
    
    tr_num = 1
    for entitie in table[0].findall('tr'):
        status = entitie.findall('td')[6].text.strip()
        if status == 'Active':
            return tr_num
        tr_num += 1
    return -1
    
def iowa_extract_owner_urls(page: str) -> "list[str]":

    TABLE_XPATH = '/html/body/div/section/article/table/tbody'
    RESULTS_LIMIT = 3

    tree = html.fromstring(page)
    options = tree.xpath(TABLE_XPATH)

    if not options:
        return []

    results = []

    count = 0
    
    for i in options[0].findall('tr')[1:]:

        if count == RESULTS_LIMIT:
            break
        
        status = i.findall('td')[2].text.strip()
        
        if status != 'Active':
            continue

        url = i.findall('td')[0].find('a').attrib['href']

        results.append(url)
        count += 1
    
    return results

def iowa_extract_owner(page: str) -> "list[str]":

    OWNER_XPATH = '/html/body/div/section/article/table[3]/tbody/tr[2]/td'
    FRANCHISE_XPATH = '/html/body/div/section/article/table[1]/tbody/tr[2]/td[2]'

    tree = html.fromstring(page)
    owner = tree.xpath(OWNER_XPATH)
    company_found = tree.xpath(FRANCHISE_XPATH)

    _owner = owner[0].text.strip()
    _company_found = company_found[0].text.strip()
    
    return "//".join([_company_found,_owner])

def kansas_extract_owner(page: str) -> "list[str]":
    ENTITIE_NAME_XPATH = '/html/body/div[2]/table[2]/tbody/tr[2]/td[1]'
    AGENT_NAME_XPATH = '/html/body/div[2]/p[9]/text()'
    
    tree = html.fromstring(page)

    if not kansas_check_status(tree): return []

    entitie = tree.xpath(ENTITIE_NAME_XPATH)[0].text.strip()
    agent = tree.xpath(AGENT_NAME_XPATH)[0]
    return [entitie + "//" + agent]

def kansas_check_status(tree) -> bool:
    STATUS_XPATH = '/html/body/div[2]/p[7]'
    status = tree.xpath(STATUS_XPATH)[0].text.strip()
    if status == 'Current Status: ACTIVE AND IN GOOD STANDING':
        return True
    return False

def kentucky_extract_owner_urls(page: str) -> "list[str]":
    TABLE_XPATH = '//*[@id="ctl00_ContentPlaceHolder1_FTUC_pOrglist"]/table/tbody'
    RESULTS_LIMIT = 3

    tree = html.fromstring(page)
    options = tree.xpath(TABLE_XPATH)

    if not options:
        return []

    results = []

    count = 0
    
    for i in options[0].findall('tr')[1:]:
        
        if count == RESULTS_LIMIT:
            break

        url = i.findall('td')[0].find('a').attrib['href']

        results.append(url)
        count += 1
    
    return results

def kentucky_extract_owner(page: str) -> "list[str]":

    TABLE_XPATH = '//*[@id="ctl00_ContentPlaceHolder1_FTUC_pInfo"]/table/tbody'

    page.replace("<br>", "")
    tree = html.fromstring(page)
    options = tree.xpath(TABLE_XPATH)
    owner = ''
    company_found = ''

    for i in options[0].findall('tr'):
        data = i.findall('td')

        if data[1].text.strip() == 'Name':
            company_found = data[2].text.strip()
        
        if data[1].text.strip() == 'Registered Agent':
            owner = data[2].text_content().strip()

    return "//".join([company_found, owner])

def louisiana_extract_owner(page: str) -> "list[str]":
    ENTITIE_NAME_XPATH = '//*[@id="ctl00_cphContent_lblName"]'
    OFFICER_TABLE_XPATH = '//*[@id="ctl00_cphContent_pnlOfficers"]'
    AGENT_NAME_XPATH = '//*[@id="ctl00_cphContent_rptAgents_ctl00_lblAgentName"]'
    
    tree = html.fromstring(page)

    if not louisiana_check_status(tree): return ["Inactive"]

    entitie = tree.xpath(ENTITIE_NAME_XPATH)[0].text.strip()
    owners = []

    officer_table = tree.xpath(OFFICER_TABLE_XPATH)
    if len(officer_table) == 0:
        agent = tree.xpath(AGENT_NAME_XPATH)[0].text.strip()
        owners.append(entitie + "//" + agent)
        return owners

    for i in range(0, 5):
        OFFICER_NAME_XPATH = f'//*[@id="ctl00_cphContent_rptOfficers_ctl0{i}_lblOfficerName"]'
        try:
            officer = tree.xpath(OFFICER_NAME_XPATH)[0].text.strip()
            owners.append(entitie + "//" + officer)
        except:
            break
    return owners

def louisiana_extract_data_site_key(page: str) -> str:
    CAPTCHA_XPATH = '//*[@id="ctl00_cphContent_divCaptcha"]/div[2]/div'
    tree = html.fromstring(page)
    options = tree.xpath(CAPTCHA_XPATH)
    dsk = options[0].attrib['data-sitekey']
    return dsk

def louisiana_check_status(tree) -> bool:
    STATUS_XPATH = '//*[@id="ctl00_cphContent_lblStatus"]'
    status = tree.xpath(STATUS_XPATH)[0].text.strip()
    if status == 'Active':
        return True
    return False

def ohio_extract_owner(page:str) -> "list[str]":
    # First, we need to figure out how to trespass the bot detector
    return []

def maine_extract_owner_urls(page:str) -> "list[str]" :
    TABLE_XPATH = '/html/body/form/center/table/tbody/tr[3]/td/table[1]/tbody'
    RESULTS_LIMIT = 3

    tree = html.fromstring(page)
    options = tree.xpath(TABLE_XPATH)
    
    results = []

    count = 0
    
    for i in options[0].findall('tr')[5:]:
        
        if count == RESULTS_LIMIT:
            break

        url = i.findall('td')[3].find('font').find('a').attrib['href']
        results.append(url)
        count += 1
    
    return results

def maine_extract_owner(page:str) -> "list[str]" :

    OWNER_XPATH = '/html/body/center/table/tbody/tr[3]/td/table/tbody/tr[12]/td'
    FRANCHISE_XPATH = '/html/body/center/table/tbody/tr[3]/td/table/tbody/tr[5]/td[1]'

    tree = html.fromstring(page)
    owner = tree.xpath(OWNER_XPATH)
    company_found = tree.xpath(FRANCHISE_XPATH)

    _owner = owner[0].text_content().strip()
    _company_found = company_found[0].text_content().strip()
    
    return "//".join([_company_found,_owner])

def mississippi_extract_owner(page:str) -> "list[str]":
    ENTITIE_NAME_XPATH = '//*[@id="printDiv2"]/div[2]/table/tbody/tr[2]/td[1]'
    OFFICERS_TABLE_XPATH = '//*[@id="printDiv2"]/table[3]/tbody'
    AGENT_NAME_XPATH = '//*[@id="printDiv2"]/table[2]/tbody/tr[2]/td/a'

    tree = html.fromstring(page)
    
    entitie = tree.xpath(ENTITIE_NAME_XPATH)[0].text.strip()
    owners = []
    try:
        officer_table = tree.xpath(OFFICERS_TABLE_XPATH)
    except:
        agent = tree.xpath(AGENT_NAME_XPATH)[0].text.strip().replace(' ', '').replace('\n', '')
        owners.append(entitie + "//" + agent)
        return owners

    for tr in officer_table[0].findall('tr')[1:]:
        officer = tr.findall('td')[0].findall('a')[0].text.strip().replace(' ', '').replace('\n', '')
        owners.append(entitie + "//" + officer)
    return owners

def mississippi_find_active(page:str) -> bool:
    TABLE_XPATH = '//*[@id="businessSearchResultsDiv"]/table/tbody'
    tree = html.fromstring(page)
    table = tree.xpath(TABLE_XPATH)
    if len(table) == 0:
        return -1
    
    tr_num = 1
    for tr in table[0].findall('tr'):
        status = tr.findall('td')[3].text.strip()
        if status == 'Good Standing':
            return tr_num
        tr_num += 1
    return -1

def massachusetts_extract_owner_urls(page:str) -> "list[str]" :
    TABLE_XPATH = '//*[@id="MainContent_SearchControl_grdSearchResultsEntity"]/tbody'
    RESULTS_LIMIT = 3

    tree = html.fromstring(page)
    options = tree.xpath(TABLE_XPATH)
    
    results = []

    count = 0
    
    for i in options[0].findall('tr')[1:]:
        
        if count == RESULTS_LIMIT:
            break

        url = i.findall('th')[0].find('a').attrib['href']
        results.append(url)
        count += 1
    
    return results

def massachusetts_extract_owner(page:str) -> "list[str]" :

    OWNER_XPATH = '//*[@id="MainContent_lblResidentAgentName"]'
    FRANCHISE_XPATH = '//*[@id="MainContent_lblEntityName"]'

    tree = html.fromstring(page)
    owner = tree.xpath(OWNER_XPATH)
    company_found = tree.xpath(FRANCHISE_XPATH)

    _owner = owner[0].text_content().strip()
    _company_found = company_found[0].text_content().strip()
    
    return "//".join([_company_found,_owner])

def montana_extract_owner(page:str) -> "list[str]" :
    AGENT_NAME_XPATH = '//*[@id="root"]/div/div[1]/div/main/div[2]/table/tbody/tr/td[4]/span'
    ENTITIE_NAME_XPATH = '//*[@id="root"]/div/div[1]/div/main/div[2]/table/tbody/tr/td[1]/div/span[1]'
    NOT_RESULTS_XPATH = '//*[@id="root"]/div/div[1]/div/main/div[2]/p'

    tree = html.fromstring(page)
    not_results = tree.xpath(NOT_RESULTS_XPATH)
    if len(not_results) > 0:
        return []
    agent = tree.xpath(AGENT_NAME_XPATH)[0].text.strip()
    entitie = tree.xpath(ENTITIE_NAME_XPATH)[0].text.strip()
    return [entitie + "//" + agent]