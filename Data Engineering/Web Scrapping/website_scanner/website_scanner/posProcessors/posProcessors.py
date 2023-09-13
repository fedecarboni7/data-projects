from typing import Iterator
import csv
import pandas as pd
from ..utils import utils
from ..parsers.booleanParser import booleanParser

def createCSVForUsersInfoBySearch(e : tuple[str], env, create = False):

    if create:
        file = utils.createFile(env['output_file_path'])
        file.close()

    with open(env['output_file_path'], 'a') as f:
        file_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        file_writer.writerow(e)


def createCSVForUsersInfo(iterator: Iterator[tuple[str]], env):

    file = utils.createFile(env['output_file_path'])
    csv_writer = csv.writer(file)
    csv_writer.writerow(['user', 'info'])
    

    for site, info in iterator:

        res = [ site, info]
        csv_writer.writerow(res)
        
    file.close()

def create_csv_by_boolean_search(iterator: Iterator[tuple[str]], patterns, env):

    file = open(env['output_file_path'], 'w')
    csv_writer = csv.writer(file)
    
    utils.createFile(env['output_file_path'])
    setHeaders = False
    headers = ['site']
    
    for site, html in iterator:
        results = booleanParser(html, patterns)
        row = [site]

        for result in results:
            headers.append(result[0])
            row.append(result[1])

        if not setHeaders:
            csv_writer.writerow(headers)
            setHeaders = True
        
        csv_writer.writerow(row)
        
    file.close()

def add_business_owners(state: str, franchise: str, results: list, file_path: str,  create = False):
    if create :
        file = utils.createFile(file_path)
        file.close()
    
    with open(file_path, 'a') as f:
        file_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for result in results:
            info = result.split('//')
            if len(info) == 1:
               file_writer.writerow([state, franchise, "NOT IMPLEMENTED", info[0]])
            else :
                file_writer.writerow([state, franchise, info[0], info[1]])

def e2_visa_add_result(franchise: str, column: int, file_path: str, result_file: str = None,  create = False):
    if create :
        df = pd.read_csv(file_path)
        df['Eligible for E-2 Visa?'] = 'No'
        df['Works with Franchise Consultants/ Brokers?'] = 'No'
        df.to_csv(result_file, index=False)
        return
    
    df = pd.read_csv(result_file)

    if column == 1 :
        df.loc[df["franchise"]==franchise, 'Eligible for E-2 Visa?'] = 'Yes'
    if column == 2 :
        df.loc[df["franchise"]==franchise, 'Works with Franchise Consultants/ Brokers?'] = 'Yes'

    df.to_csv(result_file, index=False)

def fba_info_add_result(owner: str, contact: str, email: str, url: str, phone: str, address: str, member_type: str, franchise_name: str, file_path: str, result_file: str, create: bool):

    if create:
        df = pd.read_csv(file_path)
        df['Contact Name'] = ''
        df['Contact Email'] = ''
        df['Contact URL'] = ''
        df['Contact Phone'] = ''
        df['Contact Address'] = ''
        df['Member Type'] = ''
        df['Franchise Name'] = ''
        df.to_csv(result_file, index=False)
        return
    
    df = pd.read_csv(result_file)

    df.loc[df["owner"]==owner, 'Contact Name'] = contact
    df.loc[df["owner"]==owner, 'Contact Email'] = email
    df.loc[df["owner"]==owner, 'Contact URL'] = url
    df.loc[df["owner"]==owner, 'Contact Phone'] = phone
    df.loc[df["owner"]==owner, 'Contact Address'] = address
    df.loc[df["owner"]==owner, 'Member Type'] = member_type
    df.loc[df["owner"]==owner, 'Franchise Name'] = franchise_name

    df.to_csv(result_file, index=False)

def fba_members_add_result(member: str, result_file: str):

    with open(result_file, 'a', newline='') as output_file:
            writer = csv.writer(output_file)
            writer.writerow([member])

def fba_all_members_info_add_result(contact: str, email: str, url: str, phone: str, address: str, member_type: str, franchise_name: str, result_file: str):

    with open(result_file, 'a', newline='') as output_file:
                writer = csv.writer(output_file)
                writer.writerow([contact, email, url, phone, address, member_type, franchise_name])