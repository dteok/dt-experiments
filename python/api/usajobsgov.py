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