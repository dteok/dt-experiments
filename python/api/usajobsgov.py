import requests
import pandas as pd
import json


with open('../data/input/api_keys/usajobs_gov.json', 'r') as apifile:
    creds = json.load(apifile)

url = 'https://data.usajobs.gov/api/search?JobCategoryCode=2210'
user = creds.get('user_agent')
authkey = creds.get('authorization_key')
host = 'data.usajobs.gov'
# print(f"user: {user}, authorization_key: {authorization_key}")

kwloc = {'Keyword': 'detonation', 'LocationName': ''}
response = requests.get('https://data.usajobs.gov/api/search', headers={
  "Host": host,
  "User-Agent": user,
  "Authorization-Key": authkey}, params=kwloc)

if response.status_code == 200:
  # print(response.url)
  print(response.content)
else:
  raise ApiError('Get /tasks/ {}'.format(response.status_code))

# print(content.get('SearchResult'))
# print(content['SearchResult']['SearchResultItems'])
# print(type(content))

'''
Compile a search of paygrade, organisation and starting salary of 
“Data Analyst”, 
“Data Scientist” and 
“Data Engineer” jobs on the USA jobs platform. 
Make sure you understand how to build CodeList queries so you can look up metadata dimensions
like ‘PayGrade’, ‘JobCategoryCode’, or ‘SecurityClearanceRequired’.

‘PayGrade’                  >> 
‘JobCategoryCode’           >> https://data.usajobs.gov/api/Search?JobCategoryCode=6501
‘SecurityClearanceRequired’ >> https://data.usajobs.gov/api/Search?SecurityClearanceRequired=1
'''

codelist = 'occupationalseries'
resp = requests.get(f"https://data.usajobs.gov/api/codelist/{codelist}")
