import json
import os
import re
import sys
import time

import requests


def remove_duplicates(arr1, arr2):
  common_values = set(arr1) & set(arr2)
  arr1 = [x for x in arr1 if x not in common_values]
  arr2 = [x for x in arr2 if x not in common_values]
  return arr1, arr2


def find_common_elements(arr1, arr2):
  common_values = set(arr1) & set(arr2)
  return list(common_values)


def find_link_by_key(data, key):
  for item in data:
    if key in item:
      return item[key]
  return None


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

    with open('article_parse.csv', 'a') as kw_ps:
      kw_ps.write(';'.join([
        f"{part[value]}" if value in part else "" for value in values[:-3]
      ]) + f";{price_break_quantity_1};{price_break_price_1};{price_break_currency_1}\n")


if len(sys.argv) < 2:
  print('Specify the path to the input file after main.exe\nThe program must be run from the command line!')
  os.system('pause')
  sys.exit()

file_path = sys.argv[1]

articles = []
url = "https://api.mouser.com/api/v2/search/partnumber?apiKey=6d87d3c4-7eb2-46b3-8ebb-4783dac0cba1"
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

with open(file_path, 'r') as f:
  file_rdln = f.readlines()

  try:
    articles = list(
      set([article.strip('\n').strip('.') for article in file_rdln if article.strip('\n').strip('.')]))
    if not articles:
      print('Input file is empty!')
      sys.exit()
  except Exception as err:
    print('Error while collecting data from input file')
    print(err)
    sys.exit()

grouped_articles = [articles[i:i + 10] for i in range(0, len(articles), 10)]

with open('article_parse.csv', 'a') as kw_ps:
  kw_ps.write(';'.join([value for value in values]) + '\n')

limit_reached = False
for index, articles_arr in enumerate(grouped_articles):
  time.sleep(2)

  # ? debug
  print(f'PROCESSING {index + 1} REQUEST')

  if limit_reached:
    print('Limit reached')
    for art in articles_arr:
      with open('article_parse.csv', 'a') as articles_parse:
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
      with open('article_parse.csv', 'a') as articles_parse:
        articles_parse.write(f'{art};request error\n')
    continue
  finally:
    if response.status_code != 200:
      print('Request error')  # ? log error
      for art in articles_arr:
        with open('article_parse.csv', 'a') as articles_parse:
          articles_parse.write(f'{art};request error\n')
      continue
    elif response.status_code == 403:
      print('403 limit reached')  # ? log error
      for art in articles_arr:
        with open('article_parse.csv', 'a') as articles_parse:
          articles_parse.write(f'{art};limit reached\n')
      limit_reached = True
      continue

  json_res = json.loads(response.text)

  if json_res['Errors']:
    for art in articles_arr:
      with open('article_parse.csv', 'a') as articles_parse:
        articles_parse.write(f'{art};')
        for error in json_res['Errors']:
          articles_parse.write(f'{error.get("Message")}')
          print(error.get("Message"))  # ? log error
        articles_parse.write('\n')
    continue

  if 'SearchResults' not in json_res or 'Parts' not in json_res['SearchResults']:
    for art in articles_arr:
      with open('article_parse.csv', 'a') as articles_parse:
        articles_parse.write(f'{art};request error\n')
        print('SearchResult or Parts nof found')  # ? log error
    continue
  else:
    for part in json_res['SearchResults']['Parts']:
      with open('article_parse.csv', 'a') as kw_ps:
        kw_ps.write(';'.join([f"{part[value]}" if value in part else "" for value in values]) + '\n')
      # print(part["Availability"] if "Availability" in part else "")

    # response_parts = [
    #   {part['MouserPartNumber']: part['ProductDetailUrl']}
    #   if part['MouserPartNumber'] in articles_arr
    #   else {part['ManufacturerPartNumber']: part['ProductDetailUrl']}
    #   for part in json_res['SearchResults']['Parts']
    #   if part['MouserPartNumber'] in articles_arr or part['ManufacturerPartNumber'] in articles_arr
    # ]

    response_parts = json_res['SearchResults']['Parts']

    print(response_parts[0]["PriceBreaks"])

    parse_and_write_parts(response_parts)

  # parts_keys = [list(part.keys())[0] for part in response_parts]

  # not_defined_articles = remove_duplicates(parts_keys, articles_arr)[1]
  # defined_articles = find_common_elements(parts_keys, articles_arr)

  # try:
  #   for defined_article in defined_articles:
  #     with open('article_parse.csv', 'a') as articles_parse:
  #       articles_parse.write(f'{defined_article};{find_link_by_key(response_parts, defined_article)}\n')
  # except Exception as err:
  #   with open('article_parse.csv', 'a') as articles_parse:
  #       articles_parse.write(f'{defined_article};writing error\n')
  #       print('writing error') #? log error
  #   continue

  # try:
  #   for not_defined_article in not_defined_articles:
  #     with open('article_parse.csv', 'a') as articles_parse:
  #       articles_parse.write(f'{not_defined_article};Not found\n')
  # except Exception as err:
  #   with open('article_parse.csv', 'a') as articles_parse:
  #       articles_parse.write(f'{defined_article};writing error\n')
  #       print('writing error') #? log error
  #   continue

  # ? debug
  # print(f'{index + 1} REQUEST IS COMPLETE. {len(not_defined_articles)} ARTICLES NOT FOUND OUT OF {len(articles_arr)}')
  print(f'{index + 1} REQUEST IS COMPLETE')