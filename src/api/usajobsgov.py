import requests
import pandas as pd
import json
from datetime import datetime
from icecream import ic
import pprint

# /home/dantvli/Documents/gitrepos/dt-experiments/data/input/usajobs_gov.json
f_apikey = "../dt-experiments/data/input/usajobs_gov.json"

url_root_search = "https://data.usajobs.gov/api/search"

"""
Compile a search of paygrade, organisation and starting salary of 
“Data Analyst”, 
“Data Scientist” and 
“Data Engineer” jobs on the USA jobs platform. 
Make sure you understand how to build CodeList queries so you can look up metadata dimensions
like ‘PayGrade’, ‘JobCategoryCode’, or ‘SecurityClearanceRequired’.

‘PayGrade’                  >> 
‘JobCategoryCode’           >> https://data.usajobs.gov/api/Search?JobCategoryCode=6501
‘SecurityClearanceRequired’ >> https://data.usajobs.gov/api/Search?SecurityClearanceRequired=1
"""


def data_extraction(resp):
    contents = resp.text
    content = json.loads(contents)

    search_result_items = content["SearchResult"]["SearchResultItems"]
    return search_result_items


def validate_status(response):
    """may be should be part of call_api, which will be get_search_result() func
    TODO: response.raise_status()"""
    if response.status_code == 200:
        return True
    else:
        print("API Authentication failed")
        raise Exception("Get /tasks/ {}".format(response.status_code))


def call_api(filepath: str):
    with open(filepath, "r") as apifile:
        creds = json.load(apifile)

    url = "https://data.usajobs.gov/api/search?JobCategoryCode=2210"
    user = creds.get("user_agent")
    authkey = creds.get("authorization_key")
    host = "data.usajobs.gov"

    kwloc = {"Keyword": "detonation", "LocationName": ""}
    response = requests.get(
        url_root_search,
        headers={"Host": host, "User-Agent": user, "Authorization-Key": authkey},
        params=kwloc,
    )

    return response


def main():
    # Read API keys and assign variables
    resp = call_api(f_apikey)
    if validate_status(resp):
        ic(data_extraction(resp))


if __name__ == "__main__":
    main()
