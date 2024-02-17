import logging

import requests

from db_config import db_config
from utils import (
    process_page, fetch_property_urls, fetch_property_details, add_geocode_data, insert_property_details,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def scrape_site2(base_url):
    headers = {
        "User-Agent": "Mozilla/5.0 ..."
    }

    current_page = 0

    while True:
        page_url = f"{base_url}index{current_page}.html" if current_page > 0 else base_url
        property_urls = fetch_property_urls(page_url, headers)

        if not property_urls:
            break

        for url in property_urls:
            property_details = fetch_property_details(url, headers)
            if property_details:
                property_details = add_geocode_data(property_details)
                insert_property_details(db_config, property_details)

        current_page += 1


def scrape_site1(base_url):
    index_increment = 24
    current_index = 0
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    while True:
        page_url = f"{base_url}&index={current_index}"
        process_page(page_url, headers, db_config)

        response = requests.get(page_url, headers=headers)
        if "There are no more properties to show" in response.text:
            break
        current_index += index_increment

# Main scraping logic
def main():
    site1_base_url_uk = "https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=POSTCODE%5E840076&radius=10.0"
    site2_base_url_bg = "https://www.bulgarianproperties.com/Sofia_imoti/properties_in_bulgaria/"
    scrape_site2(site2_base_url_bg)
    scrape_site1(site1_base_url_uk)

    print('Finished Scraping')


if __name__ == "__main__":
    main()
