import json
import logging
import os
import re

import mysql.connector
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def geocode_address(address):
    """
    Retrieves the latitude and longitude for a given address using the Google Geocoding API.

    This function sends a request to the Google Geocoding API using the provided address.
    It then parses the API response to extract the geographical coordinates (latitude and longitude).
    If the response is successful and contains the coordinates, they are returned. If the
    API call fails or no coordinates are found, the function returns None for both latitude and longitude.

    :param address: The address for which to obtain geocode data
    :return: A tuple of (latitude, longitude) if successful, otherwise (None, None)
    """
    GOOGLE_API_KEY = os.getenv("google_key", "None")

    params = {"address": address, "key": GOOGLE_API_KEY}

    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json", params=params
    )

    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK":
            latitude = data["results"][0]["geometry"]["location"]["lat"]
            longitude = data["results"][0]["geometry"]["location"]["lng"]
            return latitude, longitude
    return None, None


def make_soup(url, headers):
    """
    Makes a GET request to the provided URL and returns a BeautifulSoup object.
    :param url: URL to fetch
    :param headers: Headers to use for the request
    :return: BeautifulSoup object
    """
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return None


# Function to extract details from a property's detail page
def extract_property_details(detail_url, headers):
    """
    Extracts property details from a given detail page URL.
    :param detail_url: URL of the property's detail page
    :param headers: Headers to use for the request
    :return: Dictionary containing property details
    """
    soup = make_soup(detail_url, headers)
    if not soup:
        return None

    # Extracting various details
    title = soup.find("h1").text.strip() if soup.find("h1") else "Title Not Found"
    price = (
        soup.find("div", class_="_1gfnqJ3Vtd1z40MlC0MzXu").text.strip()
        if soup.find("div", class_="_1gfnqJ3Vtd1z40MlC0MzXu")
        else "Price Not Found"
    )
    address = (
        soup.find("h1", itemprop="streetAddress").text.strip()
        if soup.find("h1", itemprop="streetAddress")
        else "Address Not Found"
    )

    # Extracting key features
    features = soup.find_all("li", class_="lIhZ24u1NHMa5Y6gDH90A")
    key_features = [feature.text.strip() for feature in features]

    # Extracting property description
    description = (
        soup.find(
            "div", class_="STw8udCxUaBUMfOOZu0iL _3nPVwR0HZYQah5tkVJHFh5"
        ).text.strip()
        if soup.find("div", class_="STw8udCxUaBUMfOOZu0iL _3nPVwR0HZYQah5tkVJHFh5")
        else "Description Not Found"
    )

    # Extracting images
    image_tags = soup.find_all("img")
    image_urls = [img["src"] for img in image_tags if "src" in img.attrs]

    data_payload = {
        "title": title,
        "price": price,
        "address": address,
        "key_features": key_features,
        "description": description,
        "images": image_urls,
    }

    return data_payload


def post_process_the_image_urls(property_details):
    """
    Processes and filters the image URLs in the property details.

    This function iterates through each image URL in the property details. It checks for specific
    substrings that indicate an image is not a property picture (such as logos or icons) and filters them out.
    The function then updates the property details with a cleaned list of image URLs.

    :param property_details: Dictionary containing details of a property, including image URLs
    :return: Updated property details with a filtered list of image URLs
    """
    image_urls = property_details["images"]
    corrected_images = []
    for image_url in image_urls:
        image = image_url.split("/")[-1]
        sub_strings = ["_bp_pd_h.jpg", "branch_logo_", "_bp_mpu"]
        if any(sub_string in image for sub_string in sub_strings):
            logging.info(f"Logo detected: {image_url}")
            continue
        else:
            logging.info(f"image... {image_url}")
            corrected_images.append(image_url)
    property_details["right_image_url"] = json.dumps(corrected_images)
    return property_details


def post_process_the_price(property_details):
    """
    Processes the price field in the property details to extract and separate
    the monthly and weekly prices.

    This function uses regular expressions to find patterns in the price field
    and extracts the monthly and weekly price. It updates the property details
    with these extracted prices.

    :param property_details: Dictionary containing details of a property
    :return: Updated property details with separated price per month and week
    """
    pattern = r"[1-9]\d{0,2}(?:,\d{3})*"
    amount = []
    price_amount = property_details["price"].split("£")
    matches = []
    for price in price_amount:
        matches = re.findall(pattern, price)
        amount.extend(matches)
    if matches:
        property_details["price_per_month"] = amount[0]
        property_details["price_per_week"] = amount[1]
    return property_details


def add_geocode_data(property_details):
    """
    Adds geocode data (latitude and longitude) to the property details.

    This function uses the 'geocode_address' function to obtain geocode
    information for the address in the property details. It updates the
    property details with latitude and longitude if available.

    :param property_details: Dictionary containing details of a property
    :return: Updated property details with geocode data
    """
    latitude, longitude = geocode_address(property_details["address"])
    if latitude is not None and longitude is not None:
        property_details["latitude"] = latitude
        property_details["longitude"] = longitude
    else:
        logging.warning(f"Could not geocode address: {property_details['address']}")
    return property_details


def insert_property_details(db_config, property_details):
    """
    Inserts property details into the database.
    :param db_config: Database configuration
    :param property_details: Dictionary containing property details
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Convert list to JSON string for storage
        key_features_json = json.dumps(property_details["key_features"])
        images_json = json.dumps(property_details["images"])

        insert_query = """
        INSERT INTO properties2 (title, price, address, key_features, description, images, price_per_month, price_per_week,
        right_image_url, latitude, longitude
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            property_details["title"],
            property_details["price"],
            property_details["address"],
            key_features_json,
            property_details["description"],
            images_json,
            property_details["price_per_month"],
            property_details["price_per_week"],
            property_details["right_image_url"],
            property_details["latitude"],
            property_details["longitude"],
        )

        cursor.execute(insert_query, values)
        conn.commit()
    except mysql.connector.Error as error:
        print(f"Failed to insert record into MySQL table: {error}")
    finally:
        cursor.close()
        conn.close()
