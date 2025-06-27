import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    """Load lease programs, vehicle inventory, and county tax rates."""
    lease_programs = pd.read_csv("All_Lease_Programs_Database.csv", encoding="utf-8-sig")
    lease_programs.columns = lease_programs.columns.str.strip()

    vehicle_data = pd.read_excel("Locator_Detail_Updated.xlsx")
    vehicle_data.columns = vehicle_data.columns.str.strip()

    county_tax_rates = pd.read_csv("County_Tax_Rates.csv")
    county_tax_rates.columns = county_tax_rates.columns.str.strip()

    return lease_programs, vehicle_data, county_tax_rates
