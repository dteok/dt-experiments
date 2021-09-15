import requests
import pandas as pd
import json
from requests.auth import HTTPBasicAuth


with open('../data/input/api_keys/usajobs_gov.json', 'r') as apifile:
    creds = json.load(apifile)

url = 'https://data.usajobs.gov/api/search?JobCategoryCode=2210'
user = creds.get('user_agent')
authkey = creds.get('authorization_key')
# print(f"user: {user}, authorization_key: {authorization_key}")

# kwloc = {'Keyword': 'detonation', 'LocationName': ''}
# response = requests.get('https://data.usajobs.gov/api/search', auth=HTTPBasicAuth(user, authkey), params=kwloc)

response = requests.get(url,
  auth=(user, authkey)
)

print(response)
# print(response.url)
