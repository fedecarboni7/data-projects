from pypdf import PdfReader
import os
import glob
import shutil
import re
from regexfile import regex
from configparser import ConfigParser


def define_file_name(filepath):
    '''Esta función devuelve el nombre del archivo sin extensión'''
    file_name = filepath.split('\\')[-1].split('.')[0]
    return file_name


def find_regex(filepath, regex_list):
    '''Esta función devuelve los valores que coinciden con el regex'''
    values = []
    pages_with_error = ''
    page_number = 0
    regex_found = False

    try:
        pdf = PdfReader(filepath)
    except Exception as e:
        return f'Could not process PDF,Error Description:,{str(e)}'

    while (not values or regex_found) and page_number < len(pdf.pages):
        page = pdf.pages[page_number]

        try:  # Intenta obtener el texto de la página
            page_text = page.extract_text().replace('\n', '')
        except Exception as e: # Si no se puede obtener el texto, se saltea la página
            pages_with_error += f" {page_number}"
            if page_number == len(pdf.pages) - 1:
                return f'Could not process page(s):{pages_with_error},Error Description:,{str(e)}'
            page_number += 1
            continue

        for regex in regex_list:
            regex_found = re.findall(regex, page_text)
            if regex_found:
                if type(regex_found[0]) == tuple: # Convierto la lista de tuplas a lista de strings
                    regex_found = [item for t in regex_found for item in t]
                for i in range(len(regex_found)):
                    regex_found[i] = int(regex_found[i].replace(',', ''))
                values += regex_found

        page_number += 1

    return sorted(values)


def format_values(values):
    '''Esta función devuelve los valores formateados'''
    surface_min = values[0]
    surface_max = values[-1]
    surface_mid = (int(surface_min) + int(surface_max)) / 2
    values = f"{surface_min} sq. ft.,{surface_max} sq. ft.,{surface_mid} sq. ft."
    return values


def main():
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    config = ConfigParser()
    config.read(os.path.join(__location__,'config.ini'))

    fdd_src_path = config['paths']['fdd_folder_src']
    fdd_dst_path = config['paths']['fdd_folder_dst']
    fdd_na_path = config['paths']['fdd_folder_na']
    fdd_error_path = config['paths']['fdd_folder_error']
    output_path = config['paths']['output_path']
    output_file_name = config['files']['output_file']

    columns_names = f"{config['columns names']['first_column']}, {config['columns names']['second_column']}, {config['columns names']['third_column']}, {config['columns names']['fourth_column']}"

    with open(f"{output_path}\\{output_file_name}", "a") as output_file:
        output_file.write(f"{columns_names}\n")

        # Busca todos los archivos pdf en la carpeta source
        for filepath in glob.glob(os.path.join(fdd_src_path, '*.pdf')):
            filename = define_file_name(filepath)

            regex_list = regex()
            values = find_regex(filepath, regex_list)

            if type(values) == str:
                output_file.write(f"{filename},{values}\n")
                shutil.move(filepath, fdd_error_path + "\\" + filename + ".pdf")
            elif values:
                values = format_values(values)
                output_file.write(f"{filename},{values}\n")
                shutil.move(filepath, fdd_dst_path + "\\" + filename + ".pdf")
            else:
                output_file.write(f"{filename},N/A,N/A,N/A\n")
                shutil.move(filepath, fdd_na_path + "\\" + filename + ".pdf")


main()
