import sys, json, time, requests, os

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

with open(file_path, 'r') as f:
  file_rdln = f.readlines()
  
  try:
    articles = list(set([article.strip('\n').strip('.') for article in file_rdln]))
    if not articles:
      print('Input file is empty!')
      sys.exit()
  except Exception as err:
    print('Error while collecting data from input file')
    print(err)
    sys.exit()

grouped_articles = [articles[i:i + 10] for i in range(0, len(articles), 10)]

limit_reached = False
for index, articles_arr in enumerate(grouped_articles):
  time.sleep(2)
  
  #? debug
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

  print(payload)

  try:
    response = requests.request("POST", url, headers=headers, data=payload)
  except Exception as err:
    for art in articles_arr:
      with open('article_parse.csv', 'a') as articles_parse:
        articles_parse.write(f'{art};request error\n')
    continue
  finally:
    if response.status_code != 200:
      print('Request error') #? log error
      for art in articles_arr:
        with open('article_parse.csv', 'a') as articles_parse:
          articles_parse.write(f'{art};request error\n')
      continue
    elif response.status_code == 403:
      print('403 limit reached') #? log error
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
          print(error.get("Message")) #? log error
        articles_parse.write('\n')
    continue

  if 'SearchResults' not in json_res or 'Parts' not in json_res['SearchResults']:
    for art in articles_arr:
      with open('article_parse.csv', 'a') as articles_parse:
        articles_parse.write(f'{art};request error\n')
        print('SearchResult or Parts nof found') #? log error
    continue
  else:
    response_parts = [{part['ManufacturerPartNumber']: part['ProductDetailUrl']} for part in json_res['SearchResults']['Parts']]

  
  parts_keys = [list(part.keys())[0] for part in response_parts]

  not_defined_articles = remove_duplicates(parts_keys, articles_arr)[1]
  defined_articles = find_common_elements(parts_keys, articles_arr)

  try:
    for defined_article in defined_articles:
      with open('article_parse.csv', 'a') as articles_parse:
        articles_parse.write(f'{defined_article};{find_link_by_key(response_parts, defined_article)}\n')
  except Exception as err:
    with open('article_parse.csv', 'a') as articles_parse:
        articles_parse.write(f'{defined_article};writing error\n')
        print('writing error') #? log error
    continue
  
  try:
    for not_defined_article in not_defined_articles:
      with open('article_parse.csv', 'a') as articles_parse:
        articles_parse.write(f'{not_defined_article};Not found\n')
  except Exception as err:
    with open('article_parse.csv', 'a') as articles_parse:
        articles_parse.write(f'{defined_article};writing error\n')
        print('writing error') #? log error
    continue
  
  #? debug
  print(f'{index + 1} REQUEST IS COMPLETE. {len(not_defined_articles)} ARTICLES NOT FOUND OUT OF {len(articles_arr)}')
