import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Constants
SITEMAP_URL = "https://www.mathewshyundai.com/sitemap.xml"
OUTPUT_FILE = "Locator_Detail_Updated.xlsx"

# Step 1: Parse sitemap
sitemap_response = requests.get(SITEMAP_URL)
sitemap_soup = BeautifulSoup(sitemap_response.content, "xml")
urls = [
    loc.get_text()
    for loc in sitemap_soup.find_all("loc")
    if "/new/" in loc.get_text() and "/Hyundai/" in loc.get_text()
]

# Step 2: Extract data from each vehicle page
vehicle_data = []

for url in urls:
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        # Title: 2025 Hyundai Elantra SEL
        title_el = soup.select_one("h1.page-title")
        if not title_el:
            continue
        title_parts = title_el.get_text(strip=True).split()
        year, make, model = title_parts[:3]
        trim = " ".join(title_parts[3:]) if len(title_parts) > 3 else ""

        # VIN and Stock
        vin_el = soup.select_one("li.vin")
        vin = vin_el.get_text(strip=True).replace("VIN:", "").strip() if vin_el else ""

        stock_el = soup.select_one("li.stockNumber")
        stock = stock_el.get_text(strip=True).replace("Stock:", "").strip() if stock_el else ""

        # MSRP
        msrp_el = soup.select_one("div.pricing span.value")
        if msrp_el:
            msrp_text = msrp_el.get_text(strip=True).replace("$", "").replace(",", "")
            msrp = float(msrp_text)
        else:
            msrp = None

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
        print(f"❌ Error parsing {url}: {e}")

# Step 3: Export
if vehicle_data:
    df = pd.DataFrame(vehicle_data)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Saved {len(df)} vehicles to {OUTPUT_FILE}")
else:
    print("❌ No vehicle data found.")
