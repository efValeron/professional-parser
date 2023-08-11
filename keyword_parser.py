import math
import sys, json, time, requests, os, re
import tkinter as tk
from tkinter.filedialog import askopenfilename


def get_data(url, headers, data):
  try:
    response = requests.request("POST", url, headers=headers, data=data)
  except Exception as err:
    with open(selected_result_file, 'a', encoding='utf8') as kw_ps:
      kw_ps.write(f'error: {err}' + '\n')
    return None
  finally:
    if response.status_code != 200:
      print('Request error')  # ? log error
      with open(selected_result_file, 'a', encoding='utf8') as kw_ps:
        kw_ps.write('request error' + '\n')
      return None
    elif response.status_code == 403:
      print('403 limit reached')  # ? log error
      with open(selected_result_file, 'a', encoding='utf8') as kw_ps:
        kw_ps.write('limit reached' + '\n')
      return 'limit_reached'

  json_res = json.loads(response.text)

  if json_res['Errors']:
    with open(selected_result_file, 'a', encoding='utf8') as kw_ps:
      for error in json_res['Errors']:
        kw_ps.write(f'{error.get("Message")}')
        print(error.get("Message"))  # ? log error
      kw_ps.write('\n')
    return None

  if 'SearchResults' not in json_res or 'Parts' not in json_res['SearchResults']:
    print('SearchResult or Parts nof found')  # ? log error
    return None
  elif 'SearchResults' not in json_res or 'NumberOfResult' not in json_res['SearchResults']:
    print('NumberOfResult is not found')  # ? log error
    return None
  else:
    response_parts = json_res['SearchResults']['Parts']
    number_of_result = json_res['SearchResults']['NumberOfResult']
    return response_parts, number_of_result


def parse_and_write_parts(parts):
  for part in parts:
    price_break_quantity_1 = ''
    price_break_price_1 = ''
    price_break_currency_1 = ''

    if 'PriceBreaks' in part and len(part["PriceBreaks"]) != 0:
      pb = part['PriceBreaks'][0]

      price_break_quantity_1 = str(pb.get('Quantity'))

      price = pb.get('Price')
      price_break_price_1 = re.search(r"\d+,?\d+", price).group()

      price_break_currency_1 = pb.get('Currency')

    try:
      with open(selected_result_file, 'a', encoding='utf8') as kw_ps:
        try:
          kw_ps.write(';'.join([
            f"{part[value]}" if value in part else "" for value in values[:-3]
          ]) + f";{price_break_quantity_1};{price_break_price_1};{price_break_currency_1}\n")
        except UnicodeEncodeError as e:
          print(f"UnicodeEncodeError: {e}")
    except Exception as e:
        print(f"An error occurred while writing to the CSV file: {e}")


#? -- starting prompt -- ?#
tk.Tk().withdraw() # part of the import if you are not using other tkinter functions

selected_input_file = askopenfilename()
if not selected_input_file:
    print('Необходимо выбрать файл!')
    os.system('pause')
    sys.exit()

selected_result_file = 'keyword_parse_data_' + time.strftime("%Y%m%d-%H%M%S") + '.csv'
#? -- starting prompt -- ?#


keywords = []
url = "https://api.mouser.com/api/v2/search/keyword?apiKey=6d87d3c4-7eb2-46b3-8ebb-4783dac0cba1"
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}
values = ['Availability',
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
          'AlternatePackagings',
          'ProductDetailUrl',
          'Reeling',
          'ROHSStatus',
          'SuggestedReplacement',
          'MultiSimBlue',
          'AvailabilityInStock',
          'Quantity',
          'Price',
          'Currency']

with open(selected_result_file, 'a', encoding='utf8') as kw_ps:
  kw_ps.write(';'.join([value for value in values]) + '\n')

with open(selected_input_file, 'r') as f:
  file_rdln = f.readlines()

  try:
    keywords = [keyword.strip('\n') for keyword in file_rdln]
    if not keywords:
      print('Input file is empty!')
      sys.exit()
  except Exception as err:
    print('Error while collecting data from input file')
    print(err)
    sys.exit()

limit_reached = False
for index, keyword in enumerate(keywords):
  time.sleep(2)

  # ? debug
  print(f'PROCESSING {index + 1} REQUEST')

  if limit_reached:
    print('Limit reached')
    with open(selected_result_file, 'a', encoding='utf8') as kw_ps:
      kw_ps.write('limit reached' + '\n')
    continue

  payload = json.dumps({
    "SearchByKeywordRequest": {
      "keyword": keyword,
      "records": 0,
      "startingRecord": 0,
      "searchOptions": "1"
    }
  })

  data = get_data(url=url, headers=headers, data=payload)
  if data == None:
    break
  elif data == 'limit_reached':
    limit_reached = True
    break
  else:
    response_parts, number_of_result = data[0], data[1]

  parse_and_write_parts(response_parts)  # ?1111231

  for i in range(math.ceil(number_of_result / 50) - 1):
    starting_record = (i + 1) * 50 + 1

    payload = json.dumps({
      "SearchByKeywordRequest": {
        "keyword": keyword,
        "records": 0,
        "startingRecord": starting_record,
        "searchOptions": "1"
      }
    })

    data = get_data(url=url, headers=headers, data=payload)
    if data == None:
      break
    elif data == 'limit_reached':
      limit_reached = True
      break
    else:
      response_parts, number_of_result = data[0], data[1]

    parse_and_write_parts(response_parts)  # ?1111231

  # ? debug
  print(f'{index + 1} REQUEST IS COMPLETE.')

print('\nAll keywords parsed!')
os.system('pause')