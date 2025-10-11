import logging
import mimetypes
import os
import pathlib
import re
import shutil
import signal
from io import TextIOWrapper

import camelot
import csv
import fitz
import pandas as pd
import numpy as np
import services.mysql_service as conn
import yaml
from pypdf import PdfReader
from services.mysql_service import DatabasePool
from yaml.loader import SafeLoader


class PageFilter(logging.Filter):
    def filter(self, record):
        return "Processing page-" not in record.getMessage()

logger = logging.getLogger("my_logger") # configurar el logger
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("main_franchisees_contacts.log") # crear el manejador de archivo
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(message)s') # definir el formateador personalizado
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler() # crear el manejador de consola
console_handler.setLevel(logging.INFO)

page_filter = PageFilter() # agregar el filtro a los dos manejadores
file_handler.addFilter(page_filter)
console_handler.addFilter(page_filter)

logger.addHandler(file_handler) # agregar los manejadores al logger
logger.addHandler(console_handler)

DATABASE_NAME = 'dev_franchisees_contacts'
DI_FDDS = 'di_fdds'

SELECT_FDD_NAME_QUERY = f"SELECT * FROM {DATABASE_NAME} WHERE fdd_name = %s"
SELECT_CONTACT_INFO_QUERY = f"SELECT has_contacts, scrape_contacts FROM {DI_FDDS} WHERE filename = %s"
SELECT_FRANCHISE_ID_QUERY = f"SELECT franchise_id FROM {DI_FDDS} WHERE filename = %s"

def df_to_db(df: pd.DataFrame, conn):
    INSERT_QUERY = f"INSERT INTO {DATABASE_NAME} (fdd_name, phone, email, owner_name, website, state, city, address, zipcode, additional_information, franchise_id, franchise_name, title, method, regex) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    
    UPDATE_QUERY = f"UPDATE {DATABASE_NAME} SET email = %s, owner_name = %s, website = %s, state = %s, city = %s, address = %s, zipcode = %s, additional_information = %s, franchise_id = %s, franchise_name = %s, title = %s, method = %s, regex = %s \
                    WHERE fdd_name = %s AND phone = %s"
    
    SELECT_PHONE_QUERY = f"SELECT * FROM {DATABASE_NAME} WHERE fdd_name = %s and phone = %s and phone != ''"

    df = df.fillna(value='')
    df = df.reindex(columns=['fdd_name', 'phone', 'email', 'owner_name', 'website', 'state', 'city', 'address', 'zipcode', 'additional_information', 'franchise_id', 'franchise_name', 'title', 'method', 'regex'])

    values_to_insert = []
    values_to_update = []

    check_fdd_in_db = False

    for index, row in df.iterrows():
        fdd_name = row['fdd_name']
        owner_name = row['owner_name']
        email = row['email']
        phone = row['phone']
        website = row['website']
        state = row['state']
        city = row['city']
        address = row['address']
        zipcode = row['zipcode']
        additional_information = row['additional_information']
        franchise_id = row['franchise_id']
        franchise_name = row['franchise_name']
        title = row['title']
        method = row['method']
        regex = row['regex']

        values = (fdd_name, phone, email, owner_name, website, state, city, address, zipcode, additional_information, franchise_id, franchise_name, title, method, regex)
        cursor = conn.cursor(buffered=True)
        
        if not check_fdd_in_db:
            check_fdd_in_db = True
            cursor.execute(SELECT_FDD_NAME_QUERY, values[:1])
            fdd_in_db = cursor.fetchone()
            if not fdd_in_db:
                values_to_insert = [tuple(row) for row in df.values.tolist()]
                break
        
        cursor.execute(SELECT_PHONE_QUERY, values[:2])
        row = cursor.fetchone()

        if row:
            values_to_update.append(values[2:] + values[:2])
        else:
            values_to_insert.append(values)

    if values_to_insert:
        cursor.executemany(INSERT_QUERY, values_to_insert)

    if values_to_update:
        cursor.executemany(UPDATE_QUERY, values_to_update)

    cursor.close()
    conn.commit()

def merge_and_rename_columns(df: pd.DataFrame, column_regex, new_name: str):
    column_regex = re.compile(column_regex, flags=re.IGNORECASE)
    cols = df.filter(regex=column_regex).columns
    
    if len(cols) > 1:
        df[new_name] = df[cols].apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1)
        df.drop(cols, axis=1, inplace=True)
    elif len(cols) == 1:
        df.rename(columns={cols[0]: new_name}, inplace=True)

def clean_df_result(df: pd.DataFrame) -> "tuple[pd.DataFrame, bool]":
    df.columns = df.iloc[0]
    df.drop(0, inplace=True)

    """ comentado porque no es necesario al usar camelot con el metodo de flavor común
    empty_cols = []
    empty_headers = []
    for i, col in enumerate(df.columns):
        if col == 'regex_key':
            continue
        if col == '':
            empty_headers.append(i)
        elif df.iloc[0, i] == '':
            empty_cols.append(col)

    if len(empty_cols) > 0 and len(empty_cols) == len(empty_headers):
        index_names = dict()
        for i in range(0, len(empty_cols)):
            empty_col = empty_cols[i]
            empty_header = empty_headers[i]
            index_names[empty_header] = empty_col
            df.rename(columns={empty_col: 'empty_col'}, inplace=True)
        new_columns_names = df.columns.values
        for key, value in index_names.items():
            new_columns_names[key] = value
        df.columns = new_columns_names
        df.drop(columns='empty_col', inplace=True)

    df_result = pd.DataFrame(columns=['fdd_name', 'method', 'regex', 'owner_name', 'email', 'phone', 'website', 'state', 'city', 'address',
                                      'zipcode', 'additional_information', 'franchise_id', 'franchise_name', 'title', 'CompanyName', 'linkedin_profile'])

    column_fdd_name_regex = r'fdd_name'
    column_method_regex = r'method'
    column_regex_regex = r'regex'
    column_name_regex = r'^(?!franchise|business|fdd|location|entity|territory|office|company|legal|branch|address)\
                            name|owner|proprietor|first|last|personnel|contact'
    column_phone_regex = r'.*phone.*|tel|.*number.*'
    column_email_regex = r'.*email.*|e-mail|e mail'
    column_website_regex = r'.*website.*'
    column_address_regex = r'.*address.*|.*street.*'
    column_city_regex = r'.*city.*'
    column_state_regex = r'^(?!city|store).*state.*|^(?!city|store|start)st'
    column_zip_regex = r'.*zip.*|postal'
    column_company_name_regex = r'^(?!number).*franchise.*|.*business.*|.*entity.*|.*company.*|.*legal.*|licensee|office'
    column_franchise_name_regex = r'.*title.*|location'
    column_additional_info_regex = r'.*additional information.*|.*other.*|.*note.*|.*#.*|rest\. no\.|franchise id|id'

    regex_list = [(column_fdd_name_regex, 'fdd_name'), (column_method_regex, 'method'), (column_regex_regex, 'regex'), (column_name_regex, 'owner_name'),
                  (column_email_regex, 'email'), (column_phone_regex, 'phone'), (column_website_regex, 'website'), (column_state_regex, 'state'),
                  (column_city_regex, 'city'), (column_address_regex, 'address'), (column_zip_regex, 'zipcode'),
                  (column_additional_info_regex, 'additional_information'), (column_company_name_regex, 'company_name'), (column_franchise_name_regex, '')]
    
    merge_and_rename_columns(df, column_name_regex, 'owner_name')
    merge_and_rename_columns(df, column_email_regex, 'emails')
    merge_and_rename_columns(df, column_address_regex, 'address')

    for i, col in enumerate(df.columns):
        col = str(col)
        for regex, col_name in regex_list:
            if re.search(regex, col, flags=re.IGNORECASE):
                df_result[col_name] = df.iloc[:,i]
                break

    cols_not_matched = 0
    for cols in df_result.columns:
        if df_result[cols].isna().all():
            cols_not_matched += 1

    return df_result, cols_not_matched > 8
    """
    return df, True

def export_dataframe(df: pd.DataFrame, data: dict):
    df_result, error = clean_df_result(df)
    fdd_name = data['fdd_name']
    config = data['config']
    dev_mode = data['config']['dev_mode']

    cursor = data['conn'].cursor(buffered=True)
    cursor.execute(SELECT_FRANCHISE_ID_QUERY, (fdd_name,))
    franchise_id = cursor.fetchone()
    cursor.close()

    if not franchise_id: franchise_id = ''
    franchise_id_repeated = np.repeat(franchise_id, df_result.shape[0])
    df_result['franchise_id'] = franchise_id_repeated
    """
    if error:
        df.to_csv(config['results_error_output_path'] + '/' + fdd_name[:-4] + '.csv', index=False, header=True)
        logger.debug(f"Exported with errors to: {config['results_error_output_path']}/{fdd_name[:-4]}.csv")
    """
    if dev_mode:
        df_result.to_csv(config['results_output_path'] + '/' + fdd_name[:-4] + '.csv', index=False, header=True)
        logger.debug(f"Exported to: {config['results_output_path']}/{fdd_name[:-4]}.csv")
    else:
        df_to_db(df_result, data['conn'])
        logger.debug(f"{fdd_name} exported to DB")

def clean_tables_camelot(tables) -> pd.DataFrame:
    '''Clean the dataframe from the tables'''
    tables_df = pd.DataFrame()

    for table in tables:
        tables_df = pd.concat([tables_df, table.df])

    """
    i = 0
    while sum(tables_df.iloc[i].values != '') < tables_df.columns.size - 1:
        i += 1
        if i == tables_df.index.size - 1: return tables_df.reset_index(drop=True)

    tables_df = tables_df.iloc[i:]
    """
    tables_df = tables_df.reset_index(drop=True)

    return tables_df

def create_df_regex(contact_info: str, regex_fields: str) -> pd.DataFrame:
    '''Create the dataframe from the contact info'''
    df = pd.DataFrame()

    for match in re.finditer(regex_fields, contact_info, flags=re.MULTILINE | re.IGNORECASE):
        df = pd.concat([df, pd.DataFrame(match.groupdict(), index=[0])], ignore_index=True)

    df = pd.concat([df.columns.to_frame().T, df])

    df.columns = [i for i in range(df.columns.size)]

    df.reset_index(drop=True, inplace=True)

    if 'email' not in regex_fields:
        df = df.replace('@', '', regex=True)

    return df

def create_df_result(input, method: str, fdd_name: str, regex_key: str) -> pd.DataFrame:
    '''Create a dataframe with the columns that we need'''
    df_result = pd.DataFrame()

    if method == 'camelot':
        df_result = clean_tables_camelot(input)
    elif method == 'regex':
        df_result = create_df_regex(input, REGEX_DICT[regex_key])
            
    if df_result.empty:
        df_result = input
    
    if type(df_result) == pd.DataFrame:
        df_result.insert(0, 'regex', 'regex')
        df_result.loc[1:, 'regex'] = regex_key
        df_result.insert(0, 'method', 'method')
        df_result.loc[1:, 'method'] = method
        df_result.insert(0, 'fdd_name', 'fdd_name')
        df_result.loc[1:, 'fdd_name'] = fdd_name
    
    return df_result

def timeout_handler(signum, frame):
    raise TimeoutError("Catastrophic Backtracking suspected!")

def validate_info_regex(data: dict) -> "tuple[bool, int, str]":
    i = data['i']
    validation = False
    regex_results = {}
    page_max = data['reader'].page_count
    for j in (i, i+1, i+2):
        if j >= page_max: break
        text = data['reader'].get_page_text(j)
        if len(text.replace(' ','')) > 100 and not re.search(r'state\s+administrator|item\s+19|\$|direct\s+franchise\s+agreement', text, flags=re.IGNORECASE):
            text = text.replace('\n', '@')
            for regex_key, regex_value in REGEX_DICT.items():
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(1)
                try:
                    match = re.search(regex_value, text, flags=re.IGNORECASE)
                    signal.alarm(0)
                except TimeoutError:
                    logger.debug(f"Possible Catastrophic Backtracking detected: {regex_key}")
                    continue
                if match:
                    matches = len(re.findall(regex_value, text, flags=re.IGNORECASE))
                    regex_results[regex_key] = match.groupdict()
                    regex_results[regex_key]['matches'] = matches
                    validation = True
            if validation and len(regex_results) > 1: # se selecciona el diccionario con mayor cantidad de matches y en segundo lugar, con mas keys
                largest_dictionary_key = max(regex_results, key=lambda d: (regex_results[d]['matches'], len(regex_results[d])))
                #for key, value in regex_results.items():
                #    print(key, value)
                #largest_dictionary_key = input('Select the regex key: ')
                return validation, j, largest_dictionary_key
            elif validation:
                return validation, j, next(iter(regex_results))
    return validation, i+1, 'regex false'

def extract_info_regex(data: dict, j: int, regex_key: str) -> str:
    regex = str(REGEX_DICT[regex_key])
    search_regex = regex[regex.find('(?P<phone>'):]
    if regex.find('(?P<phone>') == -1: search_regex = regex
    contact_info = ''
    while j < data['reader'].page_count:
        text = data['reader'].get_page_text(j).replace('\n', '@')
        if not re.search(search_regex, text, flags=re.IGNORECASE):
            break
        contact_info += text
        j += 1
    print(contact_info)
    return contact_info

def validate_tables_camelot(data: dict) -> "tuple[bool, int, str]":
    validation = False
    i = data['i']
    page_max = data['reader'].page_count
    for j in (i+1, i+2, i+3):
        if j > page_max: break
        text = data['reader'].get_page_text(j-1)
        if not re.search(r'state\s+administrator|item\s+19|\$', text, flags=re.IGNORECASE):
            tables = camelot.read_pdf(data['pdf'], pages=str(j), strip_text='\n')
            if tables.n > 0:
                #try: comentado porque no es necesario al usar camelot con el metodo de flavor común
                #    tables = camelot.read_pdf(data['pdf'], flavor='stream', pages=str(j), strip_text='\n')
                #except:
                #    continue
                if len(tables[0].df.columns) >= 3:
                    validation = True
                    return validation, j, ''
    #return True, i+1, ''
    return validation, i+1, 'camelot false'

def extract_tables_camelot(data: dict, j: int, regex_key: str):
    #page_num_range = input('Enter the page numbers range: ')
    page_num_range = ''
    if page_num_range == '':
        while j <= data['reader'].page_count:
            try:
                tables = camelot.read_pdf(data['pdf'], pages=str(j), strip_text='\n')
            except:
                j += 1
                continue
            if tables.n == 0: break
            page_num_range += f"{j},"
            j += 1
            #print('pages:', page_num_range)
    else: page_num_range += ','
    # se debe usar un solo metodo de extracción, stream o lattice, no ambos
    #tables = camelot.read_pdf(data['pdf'], flavor='stream', pages=page_num_range[:-1], strip_text='\n')
    tables = camelot.read_pdf(data['pdf'], flavor='lattice', pages=page_num_range[:-1], strip_text='\n')
    #print(tables[0].df)
    if tables.n > 0:
        return tables
    else:
        return ''

EXTRACTION_METHODS = {
    'camelot': {'name': 'camelot', 'extraction': extract_tables_camelot, 'validation': validate_tables_camelot}
    ,'regex': {'name': 'regex', 'extraction': extract_info_regex, 'validation': validate_info_regex}
}

REGEX_DICT = {
    'special_regex': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?) *@(?P<owner_name>[^@]+) +@ *(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'special_regex_2': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+|[^\d]+) +(?P<zipcode>\d{5}(?:-\d{4})?) @ *(?P<phone>\d{3}-\d{3}-\d{4})?'
    ,'special_regex_3': r'(?P<franchise_name>[^@]+): (?P<address>[^:]+), (?P<city>[^,]+),? (?P<state>\w+),?\.? ?@? (?P<zipcode>\d{5}(?:-\d{4})?) @? ?(?:–|-) @? *(?P<phone>\d{3}-?@? ?\d{3}-?@? ?\d{4})'
    ,'special_regex_4': r'(?P<title>[^@]+)@(?P<address>[^@]+(?:@suite \w+ )?)@(?P<city>[^@]+), +(?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?) @(?:phone|cell): +(?P<phone>\d{3}(?:-|\.)\d{3}(?:-|\.)\d{4}) *(?P<other>[^@]+)@(?P<owner_name>[^@]+) @(?P<other2>cell[^@]+@)?(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})? ?;?,? ?(?P<email_2>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})?'
    ,'special_regex_5': r'(?P<phone>\(?\d{3}\)?-? ?\d{3}-? ?\d{4})? @(?P<owner_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?)'
    ,'special_regex_6': r'(?P<title>[^@]+) @(?P<franchise_name>[^)]*) @(?P<address>[^@]+) @(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{4,5}(?:-\d{4})?) +@(?P<phone>\(?\d{3}\)? ?-?\d{3}-*\d{4})[^l]+l: +(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ,'special_regex_7': r'(?P<other>[^@]+)@(?P<owner_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?) @Phone – (?P<phone>\(?\d{3}\)?-? ?\d{3}-\d{4})'
    ,'special_regex_8': r'(?P<owner_name>[^@]+)[@ ]+(?P<address>[^@]+)[@ ]+(?P<city>[^@]+), (?P<state>\w+),? +(?P<zipcode>\d{5}(?:-\d{4})?)[ @]+(?P<phone>\(?\d{3}[\) -\.]+\d{3}[ -\.]\d{3,4})?'
    ,'special_regex_9': r'(?P<franchise_name>[^@]+)[@ ]+(?P<address>[^@]+)[@ ]+(?P<city>[^@]+), (?P<state>\w+),? +(?P<zipcode>\d{5}(?:-\d{4})?)[ @]+Phone: *(?P<phone>\(?\d{3}[\) -\.]+\d{3}[ -–\.]\d{3,4}) +@(?P<website>[^@]+)'
    ,'special_regex_10': r'\d+\.(?P<franchise_name>[^\.\d@]+)@(?P<address>[\w \d\.#,@/-]+)[ @]+(?P<city>[^@]+),? (?P<state>\w+),? +(?P<zipcode>\d{5}(?:-\d{4})?) +@(?P<owner_name>[^@]+) *@ ?(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}) *@ *(?:\(T\))? ?(?P<phone>\(?\d{3}\)?[ -]+\d{3}[- ]+\d{4})?'
    ,'special_regex_11': r'(?P<owner_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+),(?P<state>[^,\d]+)(?P<zipcode>\d{5}(?:-\d{4})?)? @(?:T: *)?(?P<phone>\(?\d{3}[\) -]+\d{3}[-]\d{4})'
    ,'special_regex_12': r'(?P<franchise_name>[^@]+)[@ ]+(?P<name>[^@]+)@ @(?P<phone>\(?\d{3}\)?[ -]+\d{3}-*\d{4})'
    ,'special_regex_13': r'(?P<name2>[^@]+)@(?P<name>[^@]+) @(?P<franchise_name>[^\)*]+) @(?P<address>[^@]+) @(?P<city>[a-zA-Z ]+) @(?P<state>[a-zA-Z]+) @(?P<zipcode>\d{5}(?:-\d{4})?) @(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'special_regex_14': r'(?P<address>[^@]+)@(?P<other>[^@]+)@(?P<city>[^@]+), +(?P<state>\w+),? +(?P<zipcode>\d{5}(?:-\d{4})?)?[ @]+Telephone: @?(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?@?\d{4})[ @]+Owners?: (?P<name>[^:@]+)'
    ,'special_regex_15': r'(?P<other>[^@]+)@(?P<id>[^@]+)@(?P<franchise>[^@]+)?@?(?P<city>[^@]+),? (?P<state>\w+) +@?(?P<zipcode>\d{5}(?:-\d{4})?)[* ]*@Bakery:?;? (?P<phone>\(?\d{3} ?\)?[ -]*\d{3}[- ]+\d{4})'
    ,'special_regex_16': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?)[ @]+contact:(?P<owner_name>[^:@]+)@?phone: @?(?P<phone>\(?\d{3}[\) -\.]+\d{3}[ -\.]\d{3,4})'
    ,'special_regex_17': r'(?P<owner_name>[^@]{2,})@(?P<address>[^@]+)[@ ]+(?P<address2>[^@]+)?@(?P<city>[^@]+),? (?P<state>\w+)[, -]+(?P<zipcode>\d{5}(?:-\d{4})?)[ @]+(?P<phone>\(?\d{3}[\) -\.]+\d{3}[ -\.]\d{3,4})?'
    ,'special_regex_18': r'(?P<owner_name>[^@]+)@(?P<franchise_name>[^@]+)@(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}) +@(?P<city>[^@]+),? (?P<state>\w+)[, -]+(?P<zipcode>\d{5}(?:-\d{4})?)?[ @]+(?P<phone>\(?\d{3}[\) -\.]+\d{3}[ -\.]\d{3,4})?'
    ,'special_regex_19': r'(?:(?P<address>[^@]+)|(?P<address2>[^@]+)@(?P<city>[^@]+),(?P<state>[^,\d]+)(?P<zipcode>\d{5}(?:-\d{4})?|\w{3} \w{3}))[@ ]+Owners:[@ ]+(?P<owner_name>[^@]+)[@ ]+Phone:[@ ]+(?P<phone>\(?\d{3}[\) -\.]+\d{3}[ -\.]\d{3,4})(?:[@ ]+(?P<city2>[^@]+),(?P<state2>[^,\d]+)(?P<zipcode2>\d{5}(?:-\d{4})?|\w{3} \w{3}))?'
    ,'table_columns': r'(?P<name>[^@]+)(?:@ @|@?\*@ @  @)(?P<address>[^@]+)@ @@(?P<city>[^@]+), (?P<state>\w{2}) (?P<zipcode>\d{5}(?:-\d{4})?)@ @ ?(?P<phone>\(\d{3}\) \d{3}@-@\d{4})'
    ,'table_columns_2': r'(?P<name>[^@]+) @ @(?P<address>[^@]+) @(?P<city>[^@]+), (?P<state>\w{2}) (?P<zipcode>\d{5}(?:-\d{4})?)(?: @ @ @ @)(?P<phone>\d{3}-\d{3}-\d{4})'
    ,'table_columns_3': r'(?P<name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+)@(?P<state>\w{2})@(?P<zipcode>\d{5}(?:-\d{4})?)@(?P<phone>\(\d{3}\) \d{3}-\d{4})'
    ,'table_columns_4': r'(?P<franchise_name>[^@]+) @\((?P<name>[^(]+)\)\* @(?P<address>[^@]+), @(?P<state>\w{2}) (?P<zipcode>\d{5}(?:-\d{4})?) @(?P<phone>\d{3}-\d{3}-\d{4})'
    ,'table_columns_5': r'(?P<name>[^@]+)@(?P<address>[^@]+) (?P<city>\w+) ?@?(?P<state>\w{2}) ?@?(?P<zipcode>\d{5}(?:-\d{4})?)@(?P<phone>\(?\d{3}\)? ?-?\d{3}-? ?\d{4})'
    ,'table_columns_6': r'(?P<city>[^@]+)@(?P<state>\w{2})@(?P<name>[^@]+)@(?P<address>[^@]+)@(?P<zipcode>\d{5}(?:-\d{4})?)@(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'table_columns_7': r'(?P<franchise_name>[^@]+) @(?P<name>[^@]+) @(?P<address>[^@]+) @(?P<city>[a-zA-Z ]+) @(?P<state>[a-zA-Z]+) @(?P<zipcode>\d{5}(?:-\d{4})?) @(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'table_columns_8': r'(?P<city>[\w ]*)@(?P<name>[^@]+)@(?P<address>[^@]+)@(?P<phone>\(?\d{3}\)? ?-?\d{3}-*\d{4})'
    ,'table_columns_9': r'(?P<owner_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+)@(?P<state>\w{2}) *@(?P<zipcode>\d{5}(?:-\d{4})?)[-_ ]*@?(?P<phone>\(?\d{3}\)?[ -]+\d{3}[- ]+\d{4})'
    ,'table_columns_10': r'(?P<franchise_name>[^@]+) @(?P<address>[^@]+) @(?P<city>[^@]+) @(?P<state>[^@]+)[@ ]+(?P<zipcode>\d{5}(?:-\d{4}|‐\d{4})?)[ @]+(?P<phone>\(?\d{3}\)? ?-?\d{3}-*\d{4})'
    ,'table_columns_11': r'(?P<franchise_name>[^@]+)@(?P<state>[^@]+)@(?P<city>[^@]+)@(?P<address>[^@]+)@(?P<phone>\(?\d{3}\)? ?-?\d{3}-*\d{4})'
    ,'table_columns_12': r'(?P<franchise_name2>[^@]+)@(?P<franchise_name>[^@]+)@(?P<owner_name>[^@]+)@(?P<city>[^@]+)@(?P<phone>\(?\d{3}[\) -]+\d{3}[-]\d{4}) @(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ,'table_columns_13': r'(?P<name>[^@]+)@(?P<phone>\(?\d{3}\)? ?-?\.?\d{3}-?\.?\d{4,5}) @(?P<address>[^@]+)[@ ]+(?P<city>[^@]+), (?P<state>\w+)\.? *(?P<zipcode>\d{5}(?:-\d{4})?)'
    ,'table_columns_14': r'(?P<owner_name>[^@]+)[@ ]+(?P<address>[^@]+)[@ ]+(?P<city>[^@]+), (?P<state>\w+),? +(?P<zipcode>\d{5}(?:-\d{4})?)[ @]+(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ,'table_columns_15': r'(?P<owner_name>[^@]+)@(?P<phone>\(?\d{3}\)?[- ]\d{3}[- ]\d{4}) @(?P<title>[^@]+)@(?P<city>[^@]+)@(?P<state>\w+) @(?P<address>[^@]+)[@ ](?P<zipcode>\d{5}(?:-\d{4})?)'
    ,'table_columns_16': r'(?P<owner_name>[^@]+)@(?P<franchise_name>[^@]+)@(?P<address>[^@]+) ?@?(?P<other>[^@]+)? @(?P<city>[a-zA-Z ]+) @(?P<state>[a-zA-Z]+) @(?P<zipcode>\d{5}(?:-\d{4})?) @(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'table_columns_17': r'(?P<state>[^@]+)@(?P<city>[^@]+)@(?P<other>[^@]+)@(?P<owner_name>[^@]+)@(?P<address>[^@]+)[^\d]+(?P<phone>\(?\d{3}\)?[ -@]+\d{3}[ -@]+\d{4})'
    ,'table_columns_18': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+),(?P<state>[^,]+)(?P<zipcode>\d{5}(?:-\d{4})?)[^\d]+(?P<phone>\d?-?\(?\d{3}\)?[ -@]+\d{3}[ -@]+\d{4})@(?P<CompanyName>[^@]+)'
    ,'blocks': r'(?: @ @ | @  |@ @|@ @ )(?P<franchise_name>.*?) @ (?P<address>[^@]+) @ (?P<city>[^@]+), (?P<state>\w+) (?P<zipcode>\d+) (?:@ |@)(?P<phone>\(\d{3}\) \d{3}-\d{4})'
    ,'blocks_2': r'(?P<franchise_name>[^@]+)\s+@(?P<name>[^@]+)\s+@(?P<address>[^@]+)\s+@(?P<city>[^@]+),\s+(?P<state>\w{2})\s+(?P<zipcode>\d{5}(?:-\d{4})?)\s+@phone:\s+(?P<phone>\d{3}-\d{3}-\d{4})\s+@email:\s+(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ,'blocks_3': r'(\d )?(?P<franchise_name>(?(1)[^@]+|(?:[^@]+@[^@]+))) @(?P<address>[^@]+) @(?P<city>[^@]+), (?P<state>\w{2}) (?P<zipcode>\d{5}(?:-\d{4})?)\s+@ ?(?P<phone>\d{3}\.\d{3}\.\d{4})'
    ,'blocks_4': r'(?P<franchise_name>[^@]+)\s+@(?P<title>[^@]+)\s+@(?P<address>[^@]+)\s+@(?P<city>[^@]+),\s+(?P<state>[^,]+)\s+(?P<zipcode>\d{5}(?:-\d{4})?)\s+@(?P<phone>\d{3}\.\d{3}\.\d{4})'
    ,'blocks_5': r'(?P<name>[^@]*) @(?P<address>[^@]*)@? +@ +(?P<city>[^@]+), +(?P<state>\w{2}) +(?P<zipcode>\d{5}(?:-\d{4})?) +(?P<phone>\(?\d{3}\)? +?\d{3}-?\d{4})'
    ,'blocks_6': r'(?P<name>[^@]+)(?: @)?(?P<franchise_name>[^@]+)? @(?P<title>[^@]+) @(?P<phone>\(?\d{3}\)?-? ?\d{3}-? ?\d{4}) @ ?(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ,'blocks_7': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w{2}) +(?P<zipcode>\d{5}(?:-\d{4})?)@(?P<phone>\(?\d{3}\)? ?-?\d{3}-\d{4})[^@]*@(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})?'
    ,'blocks_8': r'(?P<name>[^@]+) @(?P<franchise_name>[^@]+) @(?P<other>[^@]+) @(?P<address>[^@]+), (?P<city>[^,]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?) @(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?P<email2>, [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})? *@ *(?P<phone>\(?\d{3}\)? ?-?\d{3}-? ?\d{4})'
    ,'blocks_9': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?)'
    ,'blocks_9_1': r'(?P<owner_name>[^@]+)@(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?) *@(?P<phone>\(?\d{3}\)?[ -]+\d{3}[- ]+\d{4})'
    ,'blocks_9_2': r'(?P<owner_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?) *@(?P<phone>\(?\d{3}\)?[ -]+\d{3}[- ]+\d{4})'
    ,'blocks_9_3': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?) @(?P<owner_name>[^@(]+) *(?P<phone>\(?\d{3}\)?[ -]+\d{3}[- ]+\d{4})?'
    ,'blocks_9_4': r'(?P<owner_name>[^@]+)@(?P<address>[^@]+), (?P<city>[^,]+), +(?P<state>[^,\d]+) *(?P<zipcode>\d{5}(?:-\d{4})?)? ?@?(?P<phone>\(?\d{3}\)?[– -]+\d{3}-?\d{4})'
    ,'blocks_9_5': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?)@P: ?(?P<phone>\(?\d{3}\)?[ -\.]+\d{3}[- \.]+\d{4})[^:]*@E: (?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ,'blocks_10': r'(?P<franchise_name>[^@]+)[@ ]+(?P<name>[^@]+)[@ ]+(?P<address>[^@]+)[@ ]+(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?)[@ ]+T?:? (?P<phone>\(?\d{3}\)? ?-?\.?\d{3}-?\.?\d{4})'
    ,'blocks_11': r'(?P<franchise_name>[^@]+)\((?P<name>[^(]+)\)(?P<other>\@[^@]+)?@(?P<address>\d+[^@]+)@(?P<city>[^@]+),(?P<state>[^,]+)(?P<zipcode>\d{5}(?:-\d{4})?)@(?P<phone>\(?\d{3}\)? ?-?\d{3}-? ?\d{4})'
    ,'blocks_12': r'(?P<franchise_name>[^@]+)[@ ]+(?P<address>[^@]+)[@ ]+(?P<city>[^@]+), (?P<state>\w{2}) (?P<zipcode>\d{5}(?:-\d{4})?) @[a-zA-Z]+: (?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'blocks_13': r'(?P<franchise_name>[^@]+)@(?P<owner_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+),? (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?)[ @]+(?P<phone>\(?\d{3}\)?.\d{3,4}.\d{4})'
    ,'blocks_14': r'(?P<address>[\w \d@\.,#]+)@(?P<city>[^@]+),? (?P<state>\w{2}),? +(?P<zipcode>\d{5}(?:-\d{4})?) @(?P<owner_name>[^@]+)@?(?P<franchise_name>[^@\d]+)?[@ ]+(?P<phone>\(?\d{3}\)? ?-?\d{3}-*\d{4})?[ @]+(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})?[ @]*(?P<email2>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})?'
    ,'blocks_15': r'(?P<other>[^@]+)@(?P<id>[^@]+)@(?P<franchise>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?) *@(?P<phone>\d{3}-\d{3}-\d{4})?'
    ,'blocks_16': r'(?P<name>[^@]+)[ @]+(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4}) @(?P<other>[^@]+)[@ ]+(?P<address>[^@]+)[@ ]+(?P<city>[^,]+), (?P<state>\w+),? +(?P<zipcode>\d{5}(?:-\d{4})?) @(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ,'blocks_17': r'(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?)? ?@Phone: (?P<phone>\(?\d{3}\)?-? ?\d{3}-? ?\d{4}) @Contact: (?P<owner_name>[^@]+)'
    ,'blocks_18': r'(?P<CompanyName>[^@]+)@(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?) @(?P<phone>[^@(]+)'
    ,'blocks_19': r'(?P<CompanyName>[^@]+)@(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+),(?P<state>[^,]+)(?P<zipcode>\d{5}(?:-\d{4})?) ?@(?P<phone>\(?\d{3}\)? ?-?\d{3}-*\d{4})?'
    ,'columns': r'(?P<name>[^@]*)@(?P<address>[^@]*), (?P<city>[^,]+), (?P<state>\w{2}) (?P<zipcode>\d{5}(?:-\d{4})?)@(?P<phone>\d{3}-\d{3}-\d{4})'
    ,'columns_2': r'(?P<title>[^@]+)@(?P<franchise_name>[^@]+)@(?P<name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+)@(?P<state>\w{2})@(?P<zipcode>\d{5}(?:-\d{4})?) (?P<country>[^\d]+)@(?P<phone>\d{3}-?\d{3}-\d{4})'
    ,'columns_3': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+)@(?P<state>[^@]+)@(?P<zipcode>\d{5}(?:-\d{4})?)@(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'columns_4': r'(?P<franchise_name>[^@]+)@?(?P<store>\d+)@(?P<address>[^@]+)@?(?P<address_2>[^@]+)?@(?P<city>[^@]+)@(?P<state>\w{2})@(?P<zipcode>\d{5}(?:-?‐?\d{4})?)@? ?(?P<phone>\(?\d{3}\)?\s*-?/?\d{3}-?‐?\d{4})@(?P<country>[^@]+)'
    ,'columns_5': r'(?P<state>\w{2}) {3}(?P<name>\w+,? [^ ]* [^ ]* [^ ]* [^ ]* [^ ]*) +(?P<address>\w+ \w* ?\w* ?\w*) {2,}(?P<city>\w+ ?\w* ?\w*) +(?P<zipcode>\d{5}(?:-\d{4})?) {2,}(?P<phone>\d{3} \d{3}-\d{4})'
    ,'columns_6': r'(?P<state>[^@]+)@(?P<city>[^@]+)@(?P<id>\d+) (?P<title>[^@]+)@(?P<address>[^@]+)@(?P<zipcode>\d{5}(?:-\d{4})?)@(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})@(?P<franchise_name>[^@]+)'
    ,'columns_7': r'(?P<id>\w+)@? ?(?P<franchise_name>[^@\d]+)@(?P<address>[^@]+)@(?P<city>[^@]+)@(?P<state>\w{2})@(?P<zipcode>\d{5}(?:-\d{4})?)'
    ,'columns_8': r'(?P<other>[^@]+)@? ?(?P<franchise_name>[^@\d]+)@(?P<address>[^@]+)@(?P<city>[^@]+)@(?P<state>\w{2})@(?P<zipcode>\d{5}(?:-\d{4})?)@(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?‐?\d{4})'
    ,'columns_9': r'(?P<franchise_name>[^@\d]+)[ @]+(?P<address>[^@]+)@(?P<city>[^@]+)@ ?(?P<state>\w{2}) ?@?(?P<zipcode>\d{5}(?:-\d{4})?)@(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?‐?\d{4}) ?@?(?P<owner_name>[^@]+)?'
    ,'paragraphs': r'(?P<franchise_name>[^@]*) @(?P<address>[^@]*) @(?P<city>[^@]*), (?P<state>[^@]*)\s(?P<zipcode>\d{5}(?:-\d{4})?)\s*@(?P<phone>\d{3}- ?\d{3}-\d{4})\s*@(?P<email>\w+@\w+\.\w+)\s*@(?P<email_2>\w+@\w+\.\w+)?\s*@?(?P<email_3>\w+@\w+\.\w+)?'
    ,'paragraphs_2': r'(@ @)?(?P<franchise_name>(?(1)[^@]+|(?:[^@]+@[^@]+))) @(?P<address>[^@]+), (?P<city>[^,]+)\s+@(?P<phone>\(?\d{3}\)?\d{3}-\d{4})'
    ,'paragraphs_3': r'(?P<name>[^@]+),? (?P<franchise_name>\([^(]+\)) @?(?P<address>[^)]+), (?P<city>[^,]+), (?P<state>\w+),? +(?P<zipcode>\d{5}(?:-\d{4})?),? *@?(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'paragraphs_4': r'(?P<name>[^@]+), (?P<address>[^,]+), (?P<city>[^,]+), (?P<state>\w+),? +(?P<zipcode>\d{5}(?:-\d{4})?),? *@[\w ]+: (?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'paragraphs_5': r'(?P<name>[^@]+) @(?P<franchise_name>[^@:\d]+) @?(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4}) @(?P<other>[^@]+)[@ ]+(?P<address>[^@]+)[@ ]+(?P<city>[^,]+), (?P<state>\w+),? +(?P<zipcode>\d{5}(?:-\d{4})?)'
    ,'paragraphs_6': r'(?P<id>[^@]+)[@ ]+(?P<name>[^@]+)[@ ]+(?P<address>[^@]+)[@ ]+(?P<other>[^@]+)[@ ]+\w+[@ ]+(?P<city>[^@,]+), (?P<state>\w{2}) (?P<zipcode>\d{5}(?:-\d{4})?)[@ ]+(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'paragraphs_7': r'(?P<owner_name>[^:]+)@(?P<address>[^@]+), (?P<city>[^,]+), +(?P<state>\w{2}),? *(?P<zipcode>\d{5}(?:-\d{4})?),? ?@?(?P<phone>\(?\d{3}\)?[– -]+\d{3}-?\d{4})'
    ,'table_blocks': r'(?P<franchise_name>[^@]*) @(?P<address>[^@]*) @?(?P<city>[^,@]*), (?P<state>\w{2}),? +(?P<zipcode>\d{5}(?:-\d{4})?)(?: @| @ )(?:phone: |ph: )?(?P<phone>\(?\d{3}(?:\) | |-|/|)\d{3}(?:-|\.)\d{4})'
    ,'table_blocks_2': r'@?(?P<franchise_name>[^@]*)? @?(?P<address>[^@]*) @(?P<city>[^@]*),? @?(?P<state>\w{2}|\w+) +@?(?P<zipcode>\d{5}(?:-\d{4})?) @(?P<phone>\(?\d{3}\)? ?-?\d{3}-\d{4})'
    ,'table_blocks_3': r'(?P<city>[^@]+) (?P<state>\w{2}|\w+) @(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4}) @\w+: (?P<name>[^:@]+) '
    ,'table_blocks_4': r'(?P<title>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+) +(?P<zipcode>\d{5}(?:-\d{4})?)@phone: (?P<phone>\(?\d{3}\)? ?-?\d{3}-? ?\d{4})'
    ,'table_blocks_5': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+)@(?P<city>[^@]+), (?P<state>\w+|[^\d]+) +(?P<zipcode>\d{5}(?:-\d{4})?)[ @]+(?P<owner_name>[^@]+)?[ @]*(?P<phone>\(?\d{3}\)?[- ]\d{3}[ -]\d{4})'
    ,'lines': r'(?P<franchise_name>[^@]+), (?P<address>[^,]+)   (?P<city>[^,]+),\s+(?P<state>\w{2})\s+(?P<zipcode>\d{5}(?:-\d{4})?)?\s+(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'lines_2': r'(?P<name>[^@]+)[ @]+(?P<city>[^@]+), +(?P<state>\w{2}) +@(?P<franchise_name>[^@]+)[ @]+(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'lines_3': r'(?P<address>[^@]+) (?P<city>\w+) (?P<state>\w{2}) (?P<zipcode>\d{5}(?:-\d{4})?) (?P<name>[^\d]+) (?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'lines_4': r'(?P<id>\d+), (?P<name>[^,]+(?:,[^,]+)?), (?P<address>[^,]+(?:,[^,]+)?), (?P<city>[^,]+), (?P<state>\w{2}), (?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'lines_5': r'(?P<city>[^:@]+): (?P<name>[^:\d]+) (?P<address>\d+[\d\w ,\.#’]+),? (?P<state>\w+)\.?,? @?(?P<zipcode>\d{5}(?:-\d{4})?), ?@?(?P<phone>\(?\d{3}\)?\s*-?\d{3}-?\d{4})'
    ,'lines_6': r'(?P<franchise_name>[^@]+)@(?P<address>[^@]+), (?P<state>\w{2}) (?P<zipcode>\d{4,5}(?:-\d{4})?),? (?P<phone>\(?\d{3,4}\)?\s*-?\d{3}-?\d{4})'
    ,'table_without_lines_1': r'@(?P<franchise>[ a-zA-Z@]*) @(?P<name>[a-zA-Z]*,[@ a-zA-Z]*) @(?P<address>\d*[@\- a-zA-Z\.]*) @ ?(?P<city>\w*) @(?P<state>\w*) @(?P<zip>\d*) @(?P<phone>\(?\d*\)? \d*-@?\d*)'
    ,'table_without_lines_2': r'@(?P<franchise>[./ a-zA-Z@]*) *@(?P<name>\w*) *@(?P<address>\d*[@\- a-zA-Z\.]*) *@(?P<city>[\w ]*) *@(?P<state>[\w ]*) *@(?P<zip>\d*) (?P<phone>\(?\d*\)?-? ?\d*-@?\d*)'
    ,'table_without_lines_3': r'(?P<franchise>[&\w ]*) *@(?P<address>\d*[#@\- a-zA-Z\.,]*[\d\w]+) *@(?P<city>[\w ]*) *@(?P<state>\w*) @(?P<zip>\d*) *@(?P<country>\w*) *@(?P<phone>\(?\d*\)? \d*-@?\d*) @(?P<email>[.\w]+@\w+\.\w+)'
}

def extract_data(method, data) -> "tuple[str, bool]":
    valid_method = False
    try:
        if method:
            validate_function = EXTRACTION_METHODS[method]['validation']
            valid_method, extraction_page, regex_key = validate_function(data)
            if valid_method:
                extract_function = EXTRACTION_METHODS[method]['extraction']
                extracted_data = extract_function(data, extraction_page, regex_key)
                df = create_df_result(extracted_data, method, data['fdd_name'], regex_key)
                export_dataframe(df, data)
        else:
            for method, value in EXTRACTION_METHODS.items():
                validate_function = value['validation']
                valid_method, extraction_page, regex_key = validate_function(data)
                if valid_method:
                    extract_function = value['extraction']
                    extracted_data = extract_function(data, extraction_page, regex_key)
                    df = create_df_result(extracted_data, method, data['fdd_name'], regex_key)
                    export_dataframe(df, data)
                    break
                else:
                    method = ''
        return method, valid_method
    except Exception as e:
        logger.debug(f"Exception in extract_data: {e}")
        return 'exceptions', True
 
EXHIBIT_LETTERS = {
    '0': r'(?:exhibit|attachment|appendix)\s+((?:\[?\"?)\w+(?:\"?]?)).*(?:franchisees|franchised|franchise\s+directory)'
    ,'1': r'(?:exhibit|attachment|appendix)\s+((?:\[?\"?)\w+(?:\"?]?))\s+.*\s*.*(?:franchisees|franchised|franchise\s+directory)(?!\s+territory)'
    ,'2': r'(?:exhibits?|attachments?|appendi(?:x|ces)?)\s+((?:\[?\"?)\w+(?:\"?]?))\.?\s+(?:list\s+of).*(?:franchisees|franchised)'
    ,'3': r'(?:exhibits?|attachments?|appendi(?:x|ces)?)\s+.*\s+((?:\[?\"?)\w+(?:\"?]?))\.?.*(?:franchisees|franchised|franchise\s+directory)'
    ,'4': r'((?:\[?\"?)\w+(?:\"?]?))\.?:?-?\d?\s+(?:list\s+of).*(?:franchisees|franchised|franchise\s+owners|franchise\s+operators|outlets)'
    ,'5': r'^(?!item|obligation)((?:\[?\"?)\w+(?:\"?]?)).*(?:franchisees|franchised|franchise\s+directory)'
    ,'6': r'((?:\[?\"?)\w+(?:\"?]?))\.?:?-?\d?\s+(?:list\s+of) (?!state|agent)'
}

LIST_UNDER_ITEM_20 = r'the\s+following\s+(?:is|are|tables).+(?:address|franchise).+(?:\d{4}|year|system):|current\s+outlet\s+information|contact\s+information\s+for\s+franchisees|franchisee\s+locations\s+as\s+of.+(?:\d{4}|year)'

def extract_exhibit(text: str) -> str:
    exhibit_regex = ''
    exhibit = re.search(r"(?:exhibits?|attachments?|appendi(?:x|ces)?)\s+((?:\[?\"?)\w+(?:\"?]?))", text.replace('“', '').replace('”', '').replace('‘', '').replace('’', '').replace("'", ''))
    if exhibit:
        exhibit_regex = exhibit.group(1)
    return exhibit_regex

def get_exhibit_regex(text: str, i: int, reader, result: dict) -> dict:
    exhibit_regex = ''
    search_another = True
    if re.search(r'how\s+much\s+(?:can|will)\s+i\s+earn', text):
        match = re.search(r'how\s+much\s+w(?!.+earn)', text)
        if match:
            limit_max = text.find(match.group())
            exhibit_regex = extract_exhibit(text[:limit_max])
            if exhibit_regex: search_another = False
    if search_another:
        limit_min_match = re.search(r'what(?:’s|\'s|\s+is)\s+it\s+like\s+to\s+be', text)
        limit_max_match = re.search(r'what\s+else\s+should\s+i\s+know', text)
        if limit_min_match and limit_max_match:
            limit_min = text.find(limit_min_match.group())
            limit_max = text.find(limit_max_match.group())
            exhibit_regex = extract_exhibit(text[limit_min:limit_max])
            if exhibit_regex: search_another = False
    if exhibit_regex: result['how_to_table'] = exhibit_regex
    if search_another:
        match = re.search(r'(How\s+to\s+Use\s+This\s+Franchise\s+Disclosure\s+Document)|(What\s+You\s+Need\s+To\s+Know)', text, re.IGNORECASE)
        if not match and re.search(r'table\s+of\s+contents(?!\s+of\s+operations\s+manual)', text):
            exhibit_regex = []
            for j in (i, i+1):
                text = str(reader.get_page_text(j)).lower().replace('“', '').replace('”', '').replace('‘', '').replace('’', '').replace("'", '')
                if re.search(r'to\s+simplify|for\s+ease\s+of\s+reference', text): continue
                for exhibit_letter in EXHIBIT_LETTERS:
                    exhibit = re.findall(EXHIBIT_LETTERS[exhibit_letter], text)
                    if exhibit: exhibit_regex += exhibit
                if exhibit_regex:
                    result['contents_table'] = sorted(exhibit_regex, key=lambda x: (len(x), x)) # sort by length and alphabet
                    break
                if j == i+1: result['contents_table'] = 'NA'
        if i >= 20 and not result['contents_table']: result['contents_table'] = 'NA' 
    return result

def check_if_exists_in_db(conn, fdd_name: str) -> bool:
    skip = False
    cursor = conn.cursor(buffered=True)
    cursor.execute(SELECT_CONTACT_INFO_QUERY, [fdd_name])
    row = cursor.fetchone()
    cursor.close()
    if row:
        has_contact_info = row[0]
        scrape_contact_info = row[1]
        if has_contact_info == 'Yes' and scrape_contact_info == 'Yes' or has_contact_info == 'No' and scrape_contact_info == 'No':
            skip = True
    return skip

def check_encrypted(file, filename):
    reader = PdfReader(filename)
    if reader.is_encrypted:
            command = (
                "cp "
                + filename
                + " temp.pdf; qpdf --password='' --decrypt temp.pdf "
                + filename
                + "; rm temp.pdf"
            )
            os.system(command)
            reader = fitz.open(file)
    else:
        reader = fitz.open(file)
    return reader

def is_pdf(pdf_path) :
	tipo_mime = mimetypes.guess_type(pdf_path)[0]
	return tipo_mime == 'application/pdf'

def check_db_connection(config) -> None :
    try:
        test = conn.DatabasePool()
        test.setConfig(config)
        pool = test.get_pool(1)
        _conn = pool.get_connection()

        if not _conn.is_connected():
            raise ValueError('Invalid credentials or vpn off')

        _conn.close()

    except Exception as e:
        logger.debug('Error trying to connect to the database')
        raise e

def get_pdfs_files(folder_path) :

	file_list = os.listdir(folder_path)

	files = []
	for file_name in file_list:
		file_path = os.path.join(folder_path, file_name)
		files.append(file_path)
	
	return files

def get_pdfs_from_csv(folder_path, csv_path):
    pdf_names = []

    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            pdf_names.append(row[1])

    files = []
    for pdf_name in pdf_names:
        file_path = os.path.join(folder_path, pdf_name)
        if os.path.exists(file_path):
            files.append(file_path)

    return files

def get_config_file() -> dict:
    try:
        with open('./config.yaml') as f:
            return yaml.load(f, Loader=SafeLoader)
    except Exception as e:
        raise e

def main():
    logs = {
        'camelot': 0,
        'regex': 0,
        'already in db': 0,
        'franchisees not found': 0,
        'invalid methods': 0,
        'exceptions': 0
    }

    config = get_config_file()

    pdfs = get_pdfs_files(config['fdd_input_path'])
    #pdfs = get_pdfs_from_csv(config['fdd_input_path'], config['csv_input_path'])

    check_db_connection(config['mysqldb'])
    obj = DatabasePool()
    conn = obj.get_single_connection()

    for pdf in pdfs:
        if is_pdf(pdf):
            try:
                with open(pdf, 'rb') as file:
                    fdd_name = pathlib.Path(pdf).name
                    logger.debug(f"Processing: {fdd_name}")
                    print(f"Processing: {fdd_name}")
                    #reader = check_encrypted(file, pdf)
                    reader = fitz.open(file)
                    #method = input("Enter the method to use: ")
                    method = ''
                    manual_page = input("Enter the page number where the list of franchisees is located: ")
                    manual_page = -1 if manual_page == '' else int(manual_page) - 1
                    #skip = check_if_exists_in_db(conn, fdd_name)
                    #if skip and config['skip_fdd_in_db']:
                    #    logger.debug(f"{fdd_name} already in database")
                    #    logs['already in db'] += 1
                    #    continue
                    exhibit_result = {'how_to_table': '', 'contents_table': '', 'exhibit_regex': ''}
                    list_of_franchisees = False
                    i_exhibit = 0
                    for i, page in enumerate(reader.pages()):
                        if manual_page != -1 and i != manual_page: continue
                        text = str(page.get_text()).lower()
                        if not exhibit_result['exhibit_regex']:
                            exhibit_result = get_exhibit_regex(text, i, reader, exhibit_result)
                            exhibit = ''
                            if exhibit_result['contents_table'] and exhibit_result['contents_table'] != 'NA':
                                if not exhibit_result['how_to_table']: exhibit = exhibit_result['contents_table'][0]
                                elif exhibit_result['how_to_table'] in exhibit_result['contents_table']: exhibit = exhibit_result['how_to_table']
                                elif len(exhibit_result['contents_table'][0]) - 1 > len(exhibit_result['how_to_table']): exhibit = exhibit_result['how_to_table']
                                else: exhibit = exhibit_result['contents_table'][0]
                            elif exhibit_result['how_to_table'] and exhibit_result['contents_table'] == 'NA':
                                exhibit = exhibit_result['how_to_table']
                            if exhibit:
                                exhibit_result['exhibit_regex'] = f'(?:exhibit|attachment|appendix)[ ]*\"?{str(exhibit)}\"?'
                                i_exhibit = i
                            if i >= 20 and not exhibit: exhibit_result['exhibit_regex'] = LIST_UNDER_ITEM_20
                        if i == int(manual_page) or exhibit_result['exhibit_regex'] and i > i_exhibit + 1 and re.search(exhibit_result['exhibit_regex'], text.replace('\n', '').replace('”', '"').replace('“', '"').replace('‘', '"').replace('’', '"').replace("'", '"')) and not re.search(r'state\s+administrator|item\s+19|\$|(purchase|franchise)\s+agreement|business\s+experience', text):
                        #if exhibit_result['exhibit_regex'] and i > i_exhibit + 1 and re.search(exhibit_result['exhibit_regex'], text.replace('\n', '').replace('”', '"').replace('“', '"').replace('‘', '"').replace('’', '"').replace("'", '"')) and not re.search(r'state\s+administrator|item\s+19|\$|(purchase|franchise)\s+agreement|business\s+experience', text):
                            if re.search(r'total|provision', text) and exhibit_result['exhibit_regex'] != LIST_UNDER_ITEM_20: continue
                            list_of_franchisees = True
                            data = {'pdf': pdf, 'i': i, 'fdd_name': fdd_name, 'config': config, 'reader': reader, 'conn': conn}
                            result, data_extracted = extract_data(method, data)
                            method = result
                            if method and data_extracted:
                                logs[method] += 1
                                os.rename(pdf, os.path.join(config['fdd_output_path'], fdd_name))
                                break
                        if i >= reader.page_count - 1 and list_of_franchisees:
                            logger.debug(f"{fdd_name}: invalid methods")
                            logs['invalid methods'] += 1
                            os.rename(pdf, os.path.join(config['fdd_errors_path'], fdd_name))
                            break
                        if i >= reader.page_count - 1 and not list_of_franchisees:
                            logger.debug(f"{fdd_name}: list of franchisees not found")
                            logs['franchisees not found'] += 1
                            os.rename(pdf, os.path.join(config['fdd_errors_path'], fdd_name))
                            break
            except Exception as e:
                logger.debug(f"Exception in main: {e}")
                logs['exceptions'] += 1
    conn.close()
    logger.debug(f"Logs: {logs}")

if __name__ == '__main__':
	main()
