PROJECT SUMMARY - DESCRIPTION, FUNCTIONALITY, FEATURES, & ATTRIBUTES:
	1. Description:
		a. Project Directory Root Path -- "/home/mattb/MaricopaPropertySearch".
		b. Short Description -- Maricopa County Assessor Property Search Tool - Enhanced Edition Interactive GUI for searching property information, taxes, sales history, and recorded documents.
			i. Includes batch processing and export capabilities.
	2. Functionality:
		a. Production Optimizations:
			i. LRU caching on API calls reduces redundant requests
			ii. Session reuse for connection pooling
			iii. Non-blocking UI with threading
			iv. Retry logic with exponential backoff potential
			v. Clean separation of concerns (API/Model/View)
		b. Error Resilience:
			i. Graceful fallback to mock data
			ii. Try multiple API endpoints
			iii. User-friendly error messages
			iv. Validation of input formats
		c. Extensibility:
			i. Easy to add new data types (permits, valuations)
			ii. Modular API client can be reused
			iii. Clean data model structure for serialization
		d. Web Scraping - Pulls data directly from the Maricopa website
		e. CSV Import - Load bulk downloaded data files
		f. API Discovery Helper - Instructions to find real endpoints
		g. Multiple Data Sources - Choose between API, scraping, and CSV
		h. Enhanced UI - More options and better status feedback
	3. Features/Attributes:
		a. Property Search Results: When searching by address or apn the below information is what should initially be pulled for a property [Actual Example Data]:
			i. Assessor Parcel Number (APN): [118-22-001A]
			ii. Owner Name: [RISE LOFTS LLC]
			iii. Property Address: [550 E EARLL DR PHOENIX, AZ 85012]
			iv. Description: [RESIDENTIAL RENTAL]
			v. Legal Class: [4.2]
			vi. Property Use Code: [0366]
			vii. PU Description: [Multiple Family Residential]
			viii. Lot Size (sq ft.): [38,881]
			ix. Year Built (Construction Year): [1973]
			x. Website to cross-check the above for training: https://mcassessor.maricopa.gov/mcs/?q=11822001A&mod=pd#owner\
		b. Data Source Priority: The app tries data sources in this order:
			i. API endpoints
			ii. Web Scraping
			iii. Cached Data
		c. Data Source URLS:
			i. Maricopa County Assessor (Parcel/Address Search):
				1) https://mcassessor.maricopa.gov/
				2) https://mcassessor.maricopa.gov/mcs/?q=20053822&mod=pd#owner
				3) https://mcassessor.maricopa.gov/mcs/?q=20053822&mod=pd#valuation
				4) https://mcassessor.maricopa.gov/mcs/?q=20053822&mod=pd#addinfo
			ii. Maricopa County Treasurer (Property Tax Search):
				1) https://treasurer.maricopa.gov/Parcel/Summary.aspx
				2) https://treasurer.maricopa.gov/Parcel/Summary.aspx?List=All
				3) https://treasurer.maricopa.gov/Parcel/Activities.aspx
				4) https://treasurer.maricopa.gov/Parcel/Valuations.aspx
				5) https://treasurer.maricopa.gov/Parcel/DetailedTaxStatement.aspx
			iii. Maricopa County Recorder (Document Search):
				1) https://treasurer.maricopa.gov/Parcel/Summary.aspx
				2) https://treasurer.maricopa.gov/Parcel/Summary.aspx?List=All
				3) https://treasurer.maricopa.gov/Parcel/Activities.aspx
				4) https://treasurer.maricopa.gov/Parcel/Valuations.aspx
				5) https://recorder.maricopa.gov/recording/document-search.html#tab-research
				6) https://recorder.maricopa.gov/recording/document-search.html#tab-map-search
				7) https://recorder.maricopa.gov/recording/document-search.html#tab-doc-search
				8) https://recorder.maricopa.gov/recording/document-search.html
				9) https://recorder.maricopa.gov/recording/new-document-codes.html
				10) https://recorder.maricopa.gov/information/faqs.html
				11) https://recorder.maricopa.gov/
		d. Maricopa County Assessor - Property Search Documentation:
			i. By Parcel Number:
				i. To find any parcel, just type in the parcel (apn) number. Any format works. For instance, [book]-[map]-[parcel][split] will work with any characters (or no characters) in between the items.
				ii. 111-11-111-A
				iii. 11111111
				iv. 11111111a
			ii. By Owner Name:
				i. To search by owner name, you can simply type in the owner's name in full, do not abbreviate the first name.
			iii. By Address:
				i. To search by address, enter in an address in a standard "address" format. What we define as a standard format is [number] [street pre direction] [street name] [street type] [city], AZ [zip code]. You can omit city, state and zip code from queries. Please note street direction must be E, N, W, S, NE, NW, SE, SW and street type should be abbreviated; for example, ST, AVE, PL, LN. TIP! If you are having difficulties leave off the street type and simply search by number direction and street name.
					a) 123 E MAIN
					b) 123 E MAIN ST
					c) 123 E. MAIN ST PHOENIX
					d) 123 E MAIN 85001
			iv. By City of Zip Code:
				i. To search for parcels within a city or zip code, simply type in the city or zip code.
			v. URL:
				1) How Do I Search - Maricopa County Assessor's Office
		e. Maricopa County Assessor - API Documentation and Usage:
			i. Documentation URLs:
				1) https://mcassessor.maricopa.gov/file/home/MC-Assessor-API-Documentation.pdf
				2) https://github.com/request/request
				3) https://curl.se/libcurl/c/CURLOPT_HTTPHEADER.html
		f. API Usage Details:
			i. Custom Request Headers:
				1) When setting up the API request, it is required that a custom header be added to the request (documentation varies between languages and transports).
				2) This custom header includes:
					a) A header name of AUTHORIZATION with a value as the API token; and
					b) A header name of user-agent with a value of null.
				3) API Token – ca1a11a6-adc4-4e0c-a584-36cbb6eb35e5
			· Search Functions:
				i. Parameters:
					i. {query} – URL encoded query to search for.
				ii. Search Property:
					i. Description: Searches all data points available. Returns a structured JSON result set with Real Property, BPP, MH, Rentals, Subdivisions, and Content along with totals found.
						i. Path: /search/property/?q={query}
						ii. Example: https://mcassessor.maricopa.gov/search/property/?q={query}
					ii. Paging within Property Results: Results are returned at 25 results at a time. To access results after 25 simply add the page number. For example, if there are 250 results and you want to access results 201-225, then that would be page 9.
						i. Path: /search/property/?q={query}&page={number}
						ii. Example: https://mcassessor.maricopa.gov/search/property/?q={query}&page=9
				iii. Search Subdivisions:
					i. Description: Searches only subdivision names. Returns a structured JSON result set with a list of subdivision names and parcel counts.
						i. Path: /search/sub/?q={query}
						ii. Example: https://mcassessor.maricopa.gov/search/sub/?q={query}
				iv. Search Rentals:
					i. Description: Searches only rental registrations. Returns a structured JSON result set with only rental registrations.
						i. Path: /search/rental/?q={query}
						ii. Example: https://mcassessor.maricopa.gov/search/rental/?q={query}
					ii. Paging within Property Results: Results are returned at 25 results at a time. To access results after 25 simply add the page number. For example, if there are 250 results and you want to access results 201-225, then that would be page 9.
						i. Path: /search/ rentals /?q={query}&page={number}
						ii. Example: https://mcassessor.maricopa.gov/search/ rentals /?q={query}&page=9
			ii. Parcel Functions:
				i. Parameters:
					i. {apn} – APN (Assessor Parcel Number or APN for short) must formatted with (or without) spaces, dashes, or dots.
				ii. Parcel Details:
					i. Description: Returns a JSON object with all available parcel data. Works with parcel type(s): Residential, Commercial, Land, Agriculture
						i. Path: /parcel/{apn}
						ii. Example: https://mcassessor.maricopa.gov/parcel/{apn}
				iii. Property Information:
					i. Description: Returns a JSON object with information specific to the property. Works with parcel type(s): Residential, Commercial, Land, Agriculture
						i. Path: /parcel/{apn}/propertyinfo
						ii. Example: https://mcassessor.maricopa.gov/parcel/{apn}/propertyinfo
				iv. Property Address:
					i. Description: Returns a JSON object with address of the property. Works with parcel type(s): Residential, Commercial, Land, Agriculture
						i. Path: /parcel/{apn}/address
						ii. Example: https://mcassessor.maricopa.gov/parcel/{apn}/address
				v. Valuation Details:
					i. Description: Returns a JSON object with the past 5 years of valuation data from a parcel. Works with parcel type(s): Residential, Commercial, Land, Agriculture
						i. Path: /parcel/{apn}/valuations
						ii. Example: https://mcassessor.maricopa.gov/parcel/{apn}/valuations
				vi. Residential Details:
					i. Description: Returns a JSON object with all the available residential parcel data. Does not apply to commerical, land or agriculture parcels. Works with parcel type(s): Residential, Commercial, Land
						i. Path: /parcel/{apn}
						ii. Example: https://mcassessor.maricopa.gov/parcel/{apn}/residential-details
				vii. Owner Details:
					i. Description: Returns a JSON object with all available parcel data. Works with parcel type(s): Residential, Commercial, Land, Agriculture
						i. Path: /parcel/{apn}/owner-details
						ii. Example: https://mcassessor.maricopa.gov/parcel/{apn}/owner-details.
