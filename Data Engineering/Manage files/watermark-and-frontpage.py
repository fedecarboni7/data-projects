import os
import glob
import time
from pathlib import Path
from configparser import ConfigParser
from pypdf import PdfReader, PdfWriter, PageObject


def define_file_name(filepath: Path) -> str:
    '''This function returns the file name without the extension'''
    filename = filepath.split('/')[-1]

    return filename


def watermark(input_pdf: Path, watermark_page: PageObject) -> (PdfWriter | int):
    '''This funtion adds a watermark to every page of the input pdf'''
    return_code = int(0)
    pdf_writer = PdfWriter()
    try:
        pdf_reader = PdfReader(input_pdf)
    except:
        return_code = int(8)
        return pdf_writer, return_code
        
    page_number = 0
    
    for page in pdf_reader.pages:
        page_number += 1
        try:
            page.merge_page(watermark_page)
        except Exception as e:
            print(f'Could not process page {page_number}, Error Description: {str(e)}')
            return_code = int(4)
        pdf_writer.add_page(page)

    return pdf_writer, return_code


def front_page(pdf_writer: PdfWriter, frontpage_page: PageObject) -> PdfWriter:
    '''This function adds a front page to the input PdfWriter'''
    pdf_writer.insert_page(frontpage_page, 0)

    return pdf_writer


def main():
    __location__ = os.path.realpath(os.path.join(
        os.getcwd(), os.path.dirname(__file__)))
    config = ConfigParser()
    config.read(os.path.join(__location__ + '/files', 'config.ini'))

    fdd_src_path = config['folders']['fdd_folder_src']
    fdd_dst_path = config['folders']['fdd_folder_dst']
    watermark_path = config['files']['watermark_path']
    front_page_file = config['files']['front_page_file']

    watermark_page = PdfReader(watermark_path).pages[0]
    frontpage_page = PdfReader(front_page_file).pages[0]

    num_of_successful = 0
    num_of_warnings = 0
    num_of_errors = 0

    for filepath in glob.glob(os.path.join(fdd_src_path, '*.pdf')):
        filename = define_file_name(filepath)

        pdf_writer, return_code = watermark(filepath, watermark_page)

        if return_code == 8:
            print(f'Could not process {filename}')
            num_of_errors += 1
            continue
        else:
            pdf_writer = front_page(pdf_writer, frontpage_page)

            with open(f'{fdd_dst_path}/{filename}', 'wb') as pdf_output:
                pdf_writer.write(pdf_output)

            if return_code == 4:
                print(f'Could not process all pages of {filename}')
                num_of_warnings += 1
            else:
                print(f'{filename} was successfully watermarked and frontpaged')
                num_of_successful += 1
                
    print('\nTotal number of files processed: ' + str(num_of_successful + num_of_errors + num_of_warnings))
    print('Successfully processed: ' + str(num_of_successful) + ', with warnings: ' + str(num_of_warnings) + ', with errors: ' + str(num_of_errors))


start_time = time.time()

main()

print(f"Execution time: {time.time() - start_time} seconds")
