from twocaptcha import TwoCaptcha
import requests

def solve_recaptcha(data_site_key: str, site: str, key: str) :
    solver = TwoCaptcha(key)
    result = solver.recaptcha(sitekey=data_site_key,
                              url=site)
    return result

def solve_google_recaptcha(data_site_key: str, site: str, key: str, proxy: str, data_s: str) :

    clean_proxy = proxy.replace('http://', '').replace('https://', '')

    p = {
        'uri': clean_proxy,
        'type': 'HTTP'
    }
    
    solver = TwoCaptcha(key)
    result = solver.recaptcha(sitekey=data_site_key,
                              url=site,
                              proxy=p,
                              datas=data_s)
    return result
