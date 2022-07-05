import argparse
import json
import logging
import os
from pathlib import Path
import requests
import pprint
import sys
from typing import List

# ---------- GLOBAL SETTINGS ----------
MAIN_PATH = Path(os.path.abspath(__file__)).parent.parent.parent
APIKEY_PATH = f"{MAIN_PATH}/data/input/usajobs_gov.json"
HOST = "data.usajobs.gov"
URL_BASE = "https://data.usajobs.gov/api/search"


def verify_apikey_exists():
    try:
        with open(APIKEY_PATH, "r") as ap:
            # print(ap.read())
            return print(f"API Key exists -- OK!")
    # except OSError as e:
    #     logging.error(f"API Key not found! Exit status: {e.errno}")
    except FileNotFoundError as efnf:
        logging.error(f"{efnf}")
        os._exit(1)


def set_api(apipath: str) -> List:
    with open(apipath, "r") as ap:
        credentials = json.load(ap)
    user = credentials.get("user_agent")
    authkey = credentials.get("authorization_key")
    host = HOST
    return [user, authkey, host]


def get_data(url: str, headers=dict(), params=dict()):
    resp = requests.get(url, headers, params)

    print(resp.raise_for_status())


def main():
    print("doing the main thing now!")
    user, authkey, host = set_api(APIKEY_PATH)
    headers = {"Host": host, "User-Agent": user, "Authorization-Key": authkey}
    search_params = {"Keyword": job_title, "LocationName": job_location}
    # print(f"search_params: {job_title} and {job_location}")
    get_data(URL_BASE, headers, search_params)


if __name__ == "__main__":
    verify_apikey_exists()

    parser = argparse.ArgumentParser("Search job title on USAJobs.gov.")
    parser.add_argument("-j", "--job_title", help="keyword search for job title")
    parser.add_argument(
        "-l", "--location", default="", help="the search location for the job"
    )
    args = parser.parse_args()
    if not args.job_title:
        print("Please provide Job Title.")
        sys.exit()

    job_title, job_location = [args.job_title, args.location]
    # job_location = job_location if job_location != "" else "everywhere"
    print(
        f"\nSearching USAJobs.gov for: {job_title.title()} in {job_location.title()}\n"
    )

    main()
