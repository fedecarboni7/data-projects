import os
import random
import time

from io import TextIOWrapper
from typing import Iterator

STATUS = {
    'SUCCESS' : 'SUCCESS',
    'ERROR' : 'ERROR',
    'UNKNOW' : 'UNKNOW'
}

def createFile(fileName : str) -> TextIOWrapper:
    os.umask(0)
    os.makedirs(os.path.dirname(fileName), exist_ok=True, mode=0o777)
    return open(fileName, 'w')

def proxySwitcher(proxies: list[str]) -> Iterator[str]:

    current_proxy = 0
    proxies_amount = len(proxies)

    while proxies_amount>0:

        yield proxies[current_proxy]
        current_proxy = current_proxy + 1
        if current_proxy >= proxies_amount:
            current_proxy = 0

    while True : 
        yield ''

def orderBusinessEntityFile(file: list) -> list :
    '''
    This is important to maximize the effectiveness of proxies
    '''
    return sorted(file, key=lambda i: i[1])

def execute_linkedin_delay() -> None:

    time.sleep(random.randint(4, 8)*60)

def execute_js_click(element_xpath: str) -> str:
    return f"document.evaluate('{element_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()"

def get_absolute_path(relative):
    ruta_actual = os.path.abspath(os.curdir)
    ruta_absoluta = os.path.join(ruta_actual, relative)
    return ruta_absoluta

def set_fdd_name(new_name):
    ap = get_absolute_path('downloads/')
    fdds = os.listdir(ap)
    archivos_pdf_ordenados = sorted(fdds, key=lambda x: os.path.getmtime(ap+x))
    if len(archivos_pdf_ordenados) > 0 :
        last_fdd = archivos_pdf_ordenados[-1]
        os.rename(ap+last_fdd, ap + new_name + '.pdf')

