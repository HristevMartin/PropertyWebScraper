Real Estate Data Scraper and Processor
Introduction
This project is a Python-based tool designed to scrape real estate listings from websites, process the data for usability, and store it in a MySQL database. It extracts various details like property title, price, address, key features, and images. Additionally, it performs post-processing tasks like price normalization, image URL filtering, and geocoding of addresses.
****
Features
Data Scraping: 
* Extracts data from real estate listing websites.
* Data Processing: Normalizes prices, filters image URLs, and geocodes addresses.
* Database Storage: Inserts processed data into a MySQL database.

****
Technologies Used
 * Python
 * BeautifulSoup for HTML parsing
 * MySQL Connector for database interaction
 * Requests for HTTP requests
 * Google Geocoding API for address geocoding

***

Installation and Setup

****

git clone [repository URL]

* pip install beautifulsoup4 mysql-connector-python requests

****
Usage

* Create a virtual environment:
```
python -m venv venv
```
* Activate the virtual environment:
```
venv\Scripts\activate
```
* Install the dependencies:
````
pip install -r requirements.txt
````


Run the script using Python:
* python estate_scraper.py


