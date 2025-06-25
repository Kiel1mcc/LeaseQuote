import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys

# Check if running in test mode
OUTPUT_FILE = "Locator_Detail_Test.xlsx" if "--temp" in sys.argv else "Locator_Detail_Updated.xlsx"

# Constants
URL = "https://www.mathewshyundai.com/new-inventory/index.htm"

# Start request
response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(response.text, "html.parser")

# Container to collect all scraped vehicle data
inventory_data = []

# Scrape each vehicle listing
for card in soup.select(".vehicle-card-info"):
    try:
        vin = card.select_one(".vin-number").get_text(strip=True).replace("VIN:", "")
        stock = card.select_one(".stock-number").get_text(strip=True).replace("Stock:", "")
        title = card.select_one(".title").get_text(strip=True)
        year, make, model, *trim_parts = title.split(" ")
        trim = " ".join(trim_parts)
        msrp_text = card.select_one(".pricing .price").get_text(strip=True)
        msrp = float(msrp_text.replace("$", "").replace(",", ""))

        inventory_data.append({
            "VIN": vin,
            "StockNumber": stock,
            "Year": year,
            "Make": make,
            "Model": model,
            "Trim": trim,
            "MSRP": msrp,
            "ScrapeDate": datetime.today().strftime("%Y-%m-%d")
        })
    except Exception as e:
        print("Skipped one vehicle due to error:", e)

# Convert to DataFrame and save
if inventory_data:
    df = pd.DataFrame(inventory_data)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Saved {len(df)} vehicles to {OUTPUT_FILE}")
else:
    print("No vehicles found.")
