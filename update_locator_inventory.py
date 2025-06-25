import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

SITEMAP_URL = "https://www.mathewshyundai.com/sitemap.xml"
OUTPUT_FILE = "Locator_Detail_Updated.xlsx"

# Fetch sitemap
sitemap_response = requests.get(SITEMAP_URL)
soup = BeautifulSoup(sitemap_response.content, "xml")
urls = [loc.get_text() for loc in soup.find_all("loc") if "/new/" in loc.get_text() and "/Hyundai/" in loc.get_text()]

vehicle_data = []

for url in urls:
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")

        # VIN
        vin_tag = soup.select_one("li.vin")
        vin = vin_tag.get_text(strip=True).replace("VIN:", "").strip() if vin_tag else ""

        # Stock #
        stock_tag = soup.select_one("li.stockNumber")
        stock = stock_tag.get_text(strip=True).replace("Stock:", "").strip() if stock_tag else ""

        # Title: year, make, model, trim
        title_tag = soup.select_one("h1.page-title")
        if not title_tag:
            continue
        title_parts = title_tag.get_text(strip=True).split()
        year, make, model = title_parts[:3]
        trim = " ".join(title_parts[3:]) if len(title_parts) > 3 else ""

        # MSRP
        msrp_tag = soup.select_one("div.pricing span.value")
        if msrp_tag:
            msrp_text = msrp_tag.get_text(strip=True).replace("$", "").replace(",", "")
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
        print(f"Error at {url}: {e}")

# Save to Excel
if vehicle_data:
    df = pd.DataFrame(vehicle_data)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Saved {len(df)} vehicles to {OUTPUT_FILE}")
else:
    print("No vehicles found.")
