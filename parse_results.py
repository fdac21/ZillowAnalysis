from bs4 import BeautifulSoup
import requests
import json
import pprint
import os
import collections

#Function to flatten a nested dictionary
def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        #new_key = parent_key + sep + k if parent_key else k #original
        new_key = k #this is better for this application
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

#***************************#
#    Search Results Page    #
#***************************#
"""
This is the page that includes all the homes that resulted from a city/zip code search.
These pages can give us some general details on many properties with a single crawl. (40 properties per page)
An example can be seen at https://www.zillow.com/knoxville-tn/
"""
file = open(os.path.join('ExampleResponses',
            "search-results-sample.html"), "r")
response = file.read()
file.close()
soup = BeautifulSoup(response, "html.parser")

# Get the number of listings
nListings = soup.find_all("div", class_="total-text")
print("There are", nListings[0].text, nListings[0].next_sibling,
      "and", nListings[1].text, nListings[1].next_sibling)

# Get data from all listings
all_listings = soup.find(
    'script', attrs={"data-zrr-shared-data-key": "mobileSearchPageStore"}).string
# Remove comment symbols
all_listings = all_listings.replace('<!--', '')
all_listings = all_listings.replace('-->', '')
# Load in JSON format
all_listings = json.loads(all_listings)

# Look at data:
# View entire response
pprint.pprint(all_listings)  # Too much output to see it all

# Narrow it down to just the results-related data
all_listings.keys()
all_listings['cat1'].keys()  # We want 'cat1' > 'searchResults' > 'listResults'
# This is the file 'search-results-sample-cleaned.txt'
pprint.pprint(all_listings['cat1']['searchResults']['listResults'])

# This is a list of json dictionaries, one entry for each home result on the page
type(all_listings['cat1']['searchResults']['listResults'])
len(all_listings['cat1']['searchResults']['listResults'])
all_listings = all_listings['cat1']['searchResults']['listResults']

#Flatten dictionary
all_listings[0] = flatten(all_listings[0], parent_key=False)

# There are 40 results per page. We'll need a way to detect the number of pages so we can cycle through them all.
# NEXT STEPS:
#Remove redundant variables from each home listing (beds, baths, zpid, etc.)
#Add more variables (datetime posted, listing by agent or owner, for sale or for rent, etc.)
    #We'll want to compare with a listing that's for sale by owner (these are for sale by agent by default)
    #Also compare with a rental listing

#***************************#
#  Individual Listing Page  #
#***************************#
"""
This is the page for only one single property.
It includes much more detail than the search results page, but these pages must be crawled one-by-one for each property.
Not only will it make the function slower, but also increase the risk of the crawler getting blocked by Zillow.
An example of this page can be found at https://www.zillow.com/homedetails/10301-Noras-Path-Ln-Knoxville-TN-37932/296376611_zpid/
"""
file = open(os.path.join('ExampleResponses',
            'individual-listing-sample.html'), 'r')
response = file.read()
file.close()
soup = BeautifulSoup(response, "html.parser")

# Get data from listing
data = json.loads(soup.find("script", type="application/json",
                  id="hdpApolloPreloadedData").string)
data = json.loads(data['apiCache'])
pprint.pprint(data)  # This is the file 'individual-list-sample-cleaned.txt'
list(data.keys())[0]


# Example attributes:
data['VariantQuery{"zpid":296376611,"altId":null}']['property'].keys()
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['yearBuilt']
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['lotSize']
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['homeType']
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['homeStatus']
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['isPreforeclosureAuction']
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['hoaFee']
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['isZillowOwned']
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['taxAssessedValue']
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['lotAreaValue']
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['lotAreaUnit']
# This Zestimate does not match what's on the website for some reason
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['zestimate']

# other attributes:
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['zpid']
data['VariantQuery{"zpid":296376611,"altId":null}']['property']['price']

# more attributes
data['ForSaleDoubleScrollFullRenderQuery{"zpid":296376611,"contactFormRenderParameter":{"zpid":296376611,"platform":"desktop","isDoubleScroll":true}}']['property'].keys()
attribute_key = data['ForSaleDoubleScrollFullRenderQuery{"zpid":296376611,"contactFormRenderParameter":{"zpid":296376611,"platform":"desktop","isDoubleScroll":true}}']['property']
attribute_key['isCurrentSignedInAgentResponsible']
attribute_key['bedrooms']
attribute_key['bathrooms']
attribute_key['description']
attribute_key['propertyTypeDimension']
attribute_key['foreclosurePriorSaleAmount']
attribute_key['foreclosureAmount']
attribute_key['foreclosingBank']
attribute_key['rentZestimate']
attribute_key['priceChangeDate']
attribute_key['mortgageRates']
attribute_key['propertyTaxRate']
attribute_key['isListedByOwner']
attribute_key['timeOnZillow']
attribute_key['parentRegion']

# NEXT STEPS:
# Make sure we have all the variables we could possibly want to collect
# Save all results from a single page and add to dataframe / database
