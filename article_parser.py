import json
import os
import re
import sys
import time
import requests
import tkinter as tk
from tkinter.filedialog import askopenfilename

def parse_and_write_parts(parts, all_requested_parts, not_found):
    requested_part_numbers = set(all_requested_parts)
    current_not_found = not_found
    
    try:
        with open(selected_result_file, 'a', encoding='utf8') as kw_ps:
            for requested_part_number in requested_part_numbers:
                found_part = next((part for part in parts if part["ManufacturerPartNumber"] == requested_part_number), None)
                    
                if found_part:
                    price_break_quantity_1 = ''
                    price_break_price_1 = ''
                    price_break_currency_1 = ''
                        
                    if 'PriceBreaks' in found_part and len(found_part["PriceBreaks"]) != 0:
                        pb = found_part['PriceBreaks'][0]
                        price_break_quantity_1 = str(pb.get('Quantity'))
                        price = pb.get('Price')
                        price_break_price_1 = re.search(r"\d+,?\d+", price).group()
                        price_break_currency_1 = pb.get('Currency')
                    try:
                        kw_ps.write(f"{requested_part_number};found;" + ';'.join([f"{found_part[value]}" if value in found_part else "" for value in values[2:-3]
                        ]) + f";{price_break_quantity_1};{price_break_price_1};{price_break_currency_1}\n")
                    except UnicodeEncodeError as e:
                        print(f"{requested_part_number} - UnicodeEncodeError: {e}")
                        current_not_found += 1
                        kw_ps.write(';'.join([requested_part_number, "UnicodeEncodeError"] + [""] * (len(values) - 2)) + '\n')
                else:
                    current_not_found += 1
                    kw_ps.write(';'.join([requested_part_number, "not found"] + [""] * (len(values) - 2)) + '\n')
        return current_not_found
    except Exception as e:
        print(f"An error occurred while writing to the CSV file: {e}")
        return None


#? -- starting prompt -- ?#
tk.Tk().withdraw() # part of the import if you are not using other tkinter functions

selected_input_file = askopenfilename()
if not selected_input_file:
    print('Необходимо выбрать файл!')
    os.system('pause')
    sys.exit()

selected_result_file = 'article_parse_data_' + time.strftime("%Y%m%d-%H%M%S") + '.csv'
#? -- starting prompt -- ?#


if os.stat(selected_input_file).st_size == 0:
    print('Файл данных пустой!')
    os.system('pause')
    sys.exit()

url = "https://api.mouser.com/api/v2/search/partnumber?apiKey=6d87d3c4-7eb2-46b3-8ebb-4783dac0cba1"
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
values = ['Article',
          'Status',   
          'Availability',
          'DataSheetUrl',
          'Description',
          'FactoryStock',
          'ImagePath',
          'Category',
          'LeadTime',
          'LifecycleStatus',
          'Manufacturer',
          'ManufacturerPartNumber',
          'Min',
          'Mult',
          'MouserPartNumber',
          'ProductDetailUrl',
          'Reeling',
          'ROHSStatus',
          'SuggestedReplacement',
          'MultiSimBlue',
          'AvailabilityInStock',
          'Quantity',
          'Price',
          'Currency']

with open(selected_input_file, 'r') as f:
    articles = list(set(line.strip('.\n') for line in f if line.strip('.\n')))

grouped_articles = [articles[i:i + 10] for i in range(0, len(articles), 10)]

with open(selected_result_file, 'a', encoding='utf8') as kw_ps:
    kw_ps.write(';'.join(values) + '\n')

limit_reached = False
for index, articles_arr in enumerate(grouped_articles):
    time.sleep(2)
    not_found = 0

    print(f'PROCESSING {index + 1} REQUEST')

    if limit_reached:
        print('Limit reached')
        for art in articles_arr:
            with open(selected_result_file, 'a', encoding='utf8') as articles_parse:
                articles_parse.write(f'{art};limit reached\n')
        continue

    payload = json.dumps({
        "SearchByPartRequest": {
          "mouserPartNumber": '|'.join([article for article in articles_arr])
        }
    })

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
    except Exception as err:
        for art in articles_arr:
            with open(selected_result_file, 'a', encoding='utf8') as articles_parse:
                articles_parse.write(f'{art};request error\n')
        continue
    finally:
        if response.status_code != 200:
            print('Request error')
            for art in articles_arr:
                with open(selected_result_file, 'a', encoding='utf8') as articles_parse:
                    articles_parse.write(f'{art};request error\n')
            continue
        elif response.status_code == 403:
            print('403 limit reached')
            for art in articles_arr:
                with open(selected_result_file, 'a', encoding='utf8') as articles_parse:
                    articles_parse.write(f'{art};limit reached\n')
            limit_reached = True
            continue

    json_res = json.loads(response.text)

    if json_res['Errors']:
        for art in articles_arr:
            with open(selected_result_file, 'a', encoding='utf8') as articles_parse:
                articles_parse.write(f'{art};')
                for error in json_res['Errors']:
                    articles_parse.write(f'{error.get("Message")}')
                    print(error.get("Message"))
                articles_parse.write('\n')
        continue

    if 'SearchResults' not in json_res or 'Parts' not in json_res['SearchResults']:
        for art in articles_arr:
            with open(selected_result_file, 'a', encoding='utf8') as articles_parse:
                articles_parse.write(f'{art};request error\n')
                print('SearchResult or Parts not found')
        continue

    response_parts = json_res['SearchResults']['Parts']

    if len(response_parts) < 1:
        for art in articles_arr:
            with open(selected_result_file, 'a', encoding='utf8') as articles_parse:
                not_found += 1
                kw_ps.write(';'.join([art, "not found"] + [""] * (len(values) - 2)) + '\n')
    else:
        res = parse_and_write_parts(response_parts, articles_arr, not_found)
        not_found += res if res != None else 0

    print(f'{index + 1} REQUEST IS COMPLETE. {not_found} ARTICLES NOT FOUND OUT OF {len(articles_arr)}')

print('\nAll articles parsed!')
os.system('pause')