from io import TextIOWrapper
from typing import Dict, List, Union

# Parsing Imports
from bs4 import BeautifulSoup
import requests
import json
import time
from os import _exit
from os.path import exists
from tqdm.auto import tqdm
from re import match

import firebase_admin
from firebase_admin import credentials, firestore

from zillow_requests import zequests


cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Type Aliases to make Type Hints more helpful
URL = str
OpenFile = TextIOWrapper

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, sdch, br",
    "accept-language": "en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4",
    "cache-control": "max-age=0",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
    "referer": "https://www.google.com/",
}

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Parser:
    def __init__(self, data_source: Union[URL, None] = None) -> None:
        if isinstance(data_source, URL):
            response = requests.get(data_source, headers=headers).content

            self.soup = BeautifulSoup(response, "html.parser") if data_source else None

        self.urls: Dict[str, List[URL]] = {}
        self.listings: List[Dict] = []

        if exists('./parse_cache.json'):
            with open('parse_cache.json') as cache:
                self.parse_cache = json.load(cache)
        else:
            self.parse_cache: Dict[str, int] = {}



    def getListings(self, city: str, state: str, count: int) -> List[Dict]:
        listings = []
        count = int(count / 40)
        count += 1 if count == 0 else 0

        urls = self.parseSearchPage(city, state, [x for x in range(count)])
        url = 0

        while len(listings) < count:
            listings.append(urls[url])
            url += 1

        return listings

    def parseSearchPage(
        self, city_or_zip: str, state: str, pages: List[int] = []
    ) -> List[URL]:
        region = f"{city_or_zip},-{state}"
        search_url = f"https://www.zillow.com/{region}/"
        self.urls[region] = []
        if not pages:
            page = 1
            while (resp := requests.get(f"{search_url}{page}_p/")).status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                # Get data from all listings
                all_listings = soup.find(
                    "script",
                    attrs={"data-zrr-shared-data-key": "mobileSearchPageStore"},
                ).string
                # Remove comment symbols
                all_listings = all_listings.replace("<!--", "")
                all_listings = all_listings.replace("-->", "")
                # Load in JSON format
                all_listings = json.loads(all_listings)["cat1"]["searchResults"][
                    "listResults"
                ]

                for listing in all_listings:
                    self.urls[region].append(listing["detailUrl"])

                page += 1
                # Sleep to prevent sending too many requests
                time.sleep(2)
        else:
            for page in pages:
                resp = requests.get(f"{search_url}{page}_p/", headers=headers)
                if resp.status_code == 400:
                    break
                soup = BeautifulSoup(resp.content, "html.parser")
                # Get data from all listings
                all_listings = soup.find(
                    "script",
                    attrs={"data-zrr-shared-data-key": "mobileSearchPageStore"},
                ).string
                # Remove comment symbols
                all_listings = all_listings.replace("<!--", "")
                all_listings = all_listings.replace("-->", "")
                # Load in JSON format
                all_listings = json.loads(all_listings)["cat1"]["searchResults"][
                    "listResults"
                ]

                for listing in all_listings:
                    self.urls[region].append(listing["detailUrl"])

                # Sleep to prevent sending too many requests
                time.sleep(2)

        return self.urls[region]

    def parseIndividalListing(self, url: URL) -> Dict:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.content, "html.parser")

        data = json.loads(
            soup.find(
                "script", type="application/json", id="hdpApolloPreloadedData"
            ).string
        )
        data = json.loads(data["apiCache"])
        data = data[list(data.keys())[1]]

        listing_data = data["property"]
        self.listings.append(listing_data)

        return listing_data

    def parseListings(self, urls: List[URL]) -> List[Dict]:
        for url in urls:
            self.parseIndividalListing(url)["streetAddress"]
            time.sleep(1)
        return self.listings

    def getListingDataSP(
        self, c_or_z: str, st: str, pages: List[int] = [], rent: bool = False
    ) -> List[Dict]:
        """Gathers the listing data from a search page"""
        region = f"{c_or_z},-{st}"
        search_url = f"https://www.zillow.com/{region}/"
        if rent: search_url += 'rent/'
        these_listings = []
        start = self.parse_cache[region] if region in self.parse_cache else 1
        pages = [i for i in range(start, 26)] if not pages else pages
        all_addresses = set()
        all_listings = []

        for page in pages:
            try:
                resp = zequests(f"{search_url}{page}_p/", headers=headers)
                soup = BeautifulSoup(resp.content, "html.parser")
                if listings := soup.find(
                    "script",
                    attrs={"data-zrr-shared-data-key": "mobileSearchPageStore"},
                ):
                    listings = listings.string.replace("<!--", "").replace(
                        "-->", ""
                    )
                    listings = json.loads(listings)["cat1"]["searchResults"][
                        "listResults"
                    ]
                    if not listings: break
                    # If page redirected back to valid page break
                    if listings[0]['addressStreet'] in all_addresses: break
                    all_addresses.add(listings[0]['addressStreet'])
                    all_listings += listings


                time.sleep(1)
            except (ValueError):
                print(f'Capatcha encountered at {page} on {region}')
                self.parse_cache[region] = page
                with open('parse_cache.json', 'w') as cache:
                    cache.write(json.dumps(self.parse_cache))
                    _exit(1)

        for listing in tqdm(all_listings, desc=f'{c_or_z}'):
            if listing['addressStreet'] not in all_addresses:
                self.saveListing(listing)
                all_addresses.add(listing['addressStreet'])
                these_listings.append(listing)

        is_zipcode = match(r'.*(\d{5}(\-\d{4})?)$', c_or_z)
        if is_zipcode:
            db.collection('zipcodes').document(c_or_z).update({'Scraped': True})

        self.parse_cache[region] = -1

        return these_listings

    def getZipCodes(self, start: str, amount: int = 50) -> List[str]:
        try:
            db_ref = db.collection('zipcodes').document(start)
            return [z.to_dict() for z in db.collection('zipcodes').start_at(db_ref.get()).limit(amount+1).get() if not z.to_dict()['Scraped']]
        except:
            print(bcolors.FAIL + f'Zipcode for {start} not in DB' + bcolors.ENDC)
            _exit(1)

    def saveListing(self, listing: Dict) -> bool:
        db.collection('listings').document(listing['zpid']).set(listing)
        return True


# Example of how to use class
if __name__ == "__main__":

    # Initialize Class
    parser = Parser()

    starting_zip = input(bcolors.OKBLUE + 'Starting ZipCode: ' + bcolors.ENDC)
    count = input(bcolors.OKBLUE + 'Amount of ZipCodes to Parse: ' + bcolors.ENDC)

    zip_codes = parser.getZipCodes(starting_zip, int(count))
    next_to_do = zip_codes[-1]
    zip_codes = zip_codes[:-1]
    total_saved = 0

    for zip_code in zip_codes:
        z = zip_code['Zipcode']
        st = zip_code['State']
        results = parser.getListingDataSP(z, st)
        total_saved += len(results)
    print(bcolors.OKGREEN + f'Saved {total_saved} listings from {len(zip_codes)} zipcodes to 🔥 Firestore' + bcolors.ENDC)
    print(bcolors.WARNING + 'Next zipcode to read: ' + bcolors.BOLD + next_to_do["Zipcode"] + bcolors.ENDC)
    # Loads First page of Search Results for Knoxville, TN
    # parser.getListingDataSP("37916", "TN")

    # Store list of data from houses

    # Urls are organized by Region
    # for listings in parser.urls.values():
    #     # Get data on the 3rd listing in the Region
    #     data = parser.parseListings(listings[:4])

    # # Prints some data about the first house
    # for home in data:
    #     print(f"House at {home['streetAddress']} was built in {home['yearBuilt']}" +
    #           f" and it was last sold for ${home['lastSoldPrice']}.")
