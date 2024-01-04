import logging

import requests

from db_config import db_config
from utils import (
    make_soup,
    extract_property_details,
    post_process_the_price,
    post_process_the_image_urls,
    add_geocode_data,
    insert_property_details,
)

# Setting up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def process_page(url, headers, db_config):
    """
    Processes a single page of property listings.
    :param url: URL of the page to process
    :param headers: Headers to use for the request
    :param db_config: Database configuration
    """
    soup = make_soup(url, headers)
    if not soup:
        return

    # Extract the URLs for the detail pages
    detail_links = [
        a["href"]
        for a in soup.select("a.propertyCard-link")
        if "properties" in a["href"]
    ]

    for link in detail_links:
        detail_url = f"https://www.rightmove.co.uk{link}"
        property_details = extract_property_details(detail_url, headers=headers)

        if property_details:
            # Post-process the price and image URLs
            property_details = post_process_the_price(property_details)
            property_details = post_process_the_image_urls(property_details)
            property_details = add_geocode_data(property_details)
            insert_property_details(db_config, property_details)


# configuration headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}


# Main scraping logic
def main():
    base_url = "https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=POSTCODE%5E840076&radius=10.0"
    index_increment = 24
    current_index = 0

    while True:
        page_url = f"{base_url}&index={current_index}"
        process_page(page_url, headers, db_config)

        response = requests.get(page_url, headers=headers)
        if "There are no more properties to show" in response.text:
            break
        current_index += index_increment


if __name__ == "__main__":
    main()
