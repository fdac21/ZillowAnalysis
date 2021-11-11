# Check if http request was denied

import requests

default_header = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, sdch, br',
    'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
    'referer': 'https://www.google.com/'
}

def zequests(url, headers=default_header):
    resp = requests.get(url, headers=headers)
    
    if 'data-zrr-shared-data-key' in resp.text:
        return resp
    else:
        raise ValueError("Captcha Encountered")
        

