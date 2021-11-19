# Zillow Project
This project is to retrieve data from Zillow and analyze trends in the housing market.

## Task List:
+ Get data for all remaining zip codes [Marc]
+ Get zip code data (maybe from the Census?) and append to Firestore db [Matt & Sehee]
+ Make visualizations from data [Vishal & Selena]
   + Heatmaps
+ (Maybe) transfer firebase data across accounts [Matt]


## Main Function Pseudocode

1. Get zip code from Firestore that has not yet been scraped (see 'firestore.py')
2. Get random user-agent for heading (headers.py)
3. Get first page of search results
4. If http request was not blocked by captcha:    
&nbsp;&nbsp;&nbsp;&nbsp;a. Get range of page results (for the for-loop below)      
   (Number of pages is the number of results/40, with a max of 25. parse_results.py, lines 32-35)   
&nbsp;&nbsp;&nbsp;&nbsp; b. For each page in search results (starting with page 2):   
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    i. If http request was not blocked: (ip_rotations.py, line 86)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1. Parse and clean response (clean_results.py)    
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2. For each listing in search results:    
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; a. Add to Firestore 'listings' collection (see 'firestore.py')   
5. Repeat from step 3 with rentals = True (append '/rentals' to URL)
6. Update zip code in Firestore with 'scraped' = True
7. Repeat from step 1







