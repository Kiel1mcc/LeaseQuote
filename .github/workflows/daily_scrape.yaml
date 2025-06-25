import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
from urllib.parse import urljoin

# Constants
SITEMAP_URL = "https://www.mathewshyundai.com/sitemap.xml"
OUTPUT_FILE = "Locator_Detail_Updated.xlsx"

# Step 1: Fetch and parse the sitemap
sitemap_response = requests.get(SITEMAP_URL)
sitemap_soup = BeautifulSoup(sitemap_response.content, "xml")
urls = [loc.get_text() for loc in sitemap_soup.find_all("loc") if "/new/" in loc.get_text() and "/Hyundai/" in loc.get_text()]

# Step 2: Visit each vehicle page and extract details
vehicle_data = []

for url in urls:
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        overview = soup.find("div", class_="vdp-overview-container")
        if not overview:
            continue

        # Extract VIN and Stock Number from visible text
        vin_text = overview.find(text=lambda t: "VIN#" in t)
        stock_text = overview.find(text=lambda t: "Stock#" in t)
        vin = vin_text.split("VIN#")[-1].split()[0] if vin_text else ""
        stock = stock_text.split("Stock#")[-1].split()[0] if stock_text else ""

        # Extract vehicle title
        title_element = soup.find("h1", class_="page-title")
        if not title_element:
            continue
        title = title_element.get_text(strip=True)
        year, make, model, *trim_parts = title.split()
        trim = " ".join(trim_parts)

        # Extract MSRP
        msrp_element = soup.find(text=lambda t: "MSRP" in t)
        msrp_container = msrp_element.find_parent("div") if msrp_element else None
        msrp_value = msrp_container.find_next("div").get_text(strip=True) if msrp_container else ""
        msrp = float(msrp_value.replace("$", "").replace(",", "")) if msrp_value else None

        vehicle_data.append({
            "VIN": vin,
            "StockNumber": stock,
            "Year": year,
            "Make": make,
            "Model": model,
            "Trim": trim,
            "MSRP": msrp,
            "URL": url,
            "ScrapeDate": datetime.today().strftime("%Y-%m-%d")
        })
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")

# Step 3: Save to Excel
if vehicle_data:
    df = pd.DataFrame(vehicle_data)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Saved {len(df)} vehicles to {OUTPUT_FILE}")
else:
    print("No vehicle data found.")
