from bs4 import BeautifulSoup
from lxml import html, etree
import re

def extract_contact_information(page : str) -> dict:
    CONTACT_INFO_1_XPATH = '/html/body/div[5]/div[3]/div[1]/div/div/div/div/div/div/div/article/div/div/div[1]/ul[2]'
    CONTACT_INFO_2_XPATH = '//*[@id="item-header-content"]/div[2]/ul'
    
    tree = html.fromstring(page)
    items_1 = tree.xpath(CONTACT_INFO_1_XPATH)
    items_2 = tree.xpath(CONTACT_INFO_2_XPATH)
    
    li_num = 1
    fields = {}

    if len(items_1) > 0:
        for li in items_1[0].findall('li'):
            field = str(li[0].text)
            if field not in fields:
                fields[field] = CONTACT_INFO_1_XPATH + f'/li[{li_num}]'
            li_num += 1
    elif len(items_2) > 0:
        fields["Person:"] = '//*[@id="item-header-content"]/div[1]/h1'
        for li in items_2[0].findall('li'):
            field = str(li[0].text)
            fields[field] = CONTACT_INFO_2_XPATH + f'/li[{li_num}]'
            li_num += 1
    return fields