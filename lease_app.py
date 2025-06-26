import streamlit as st
import pandas as pd
from lease_calculations import calculate_ccr_full, calculate_payment_from_ccr
from PIL import Image
from datetime import datetime
import json

# Custom CSS to adjust layout
st.markdown("""
<style>
    header { display: none; }
    .main-content { padding: 0; margin-top: 0; font-family: 'Helvetica', Arial, sans-serif; }
    .quote-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        height: 100%;
    }
    .selected-quote {
        border: 2px solid #4CAF50;
        background-color: #f0fff0;
        box-shadow: 0 4px 8px rgba(76, 175, 80, 0.2);
    }
    .payment-highlight {
        font-size: 24px;
        font-weight: 700;
        color: #2E8B57;
        margin: 5px 0;
    }
    .term-mileage {
        font-size: 18px;
        font-weight: 600;
        color: #1e3a8a;
        margin: 5px 0;
    }
    .caption-text { font-size: 12px; color: #666; margin: 0; }
    .print-section {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .header-info {
        background: linear-gradient(90deg, #1e3a8a, #1e40af);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .sidebar .stExpander, .sidebar .stTextInput, .sidebar .stSelectbox, .sidebar .stNumberInput, .sidebar .stCheckbox {
        margin-bottom: 10px;
    }
    @media print { .no-print { display: none !important; } }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Lease Quote Tool", layout="wide", initial_sidebar_state="expanded")

# Load data
@st.cache_data
def load_data():
    lease_programs = pd.read_csv("All_Lease_Programs_Database.csv", encoding="utf-8-sig")
    lease_programs.columns = lease_programs.columns.str.strip()
    vehicle_data = pd.read_excel("Locator_Detail_Updated.xlsx")
    vehicle_data.columns = vehicle_data.columns.str.strip()
    return lease_programs, vehicle_data

try:
    lease_programs, vehicle_data = load_data()
except FileNotFoundError:
    st.error("⚠️ Required files not found.")
    st.stop()

# Sidebar inputs
with st.sidebar:
    st.header("Vehicle & Customer Info")
    vin_input = st.text_input("Enter VIN")
    selected_tier = st.selectbox("Credit Tier", [f"Tier {i}" for i in range(1, 9)])
    selected_county = st.selectbox("County", ["Adams", "Franklin", "Marion"])
    trade_value = st.number_input("Trade-in Value", min_value=0.0, value=0.0, step=100.0)
    default_money_down = st.number_input("Customer Cash Down", min_value=0.0, value=0.0, step=100.0)
    apply_markup = st.checkbox("Apply Money Factor Markup (+0.0004)", value=False)

if not vin_input:
    st.title("Lease Quote Tool")
    st.info("Enter a VIN in the sidebar to begin")
    st.stop()

vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
if vin_data.empty:
    st.error("VIN not found in inventory")
    st.stop()

vehicle = vin_data.iloc[0]
model_number = vehicle["ModelNumber"]
msrp = float(vehicle["MSRP"])
tier_num = int(selected_tier.split(" ")[1])
tax_rate = 0.0725

lease_matches = lease_programs[lease_programs["ModelNumber"] == model_number]
if lease_matches.empty:
    st.error("No lease programs found for this vehicle")
    st.stop()

# Build quote options
mileage_options = [10000, 12000, 15000]
lease_terms = sorted(lease_matches["Term"].dropna().unique())
quote_options = []
for term in lease_terms:
    term_group = lease_matches[lease_matches["Term"] == term]
    for mileage in mileage_options:
        row = term_group.iloc[0]
        base_residual = float(row["Residual"])
        adjusted_residual = base_residual + 0.01 if mileage == 10000 else base_residual - 0.02 if mileage == 15000 else base_residual
        residual_value = round(msrp * adjusted_residual, 2)
        mf_col = f"Tier {tier_num}"
        money_factor = float(row[mf_col])
        if apply_markup:
            money_factor += 0.0004
        available_lease_cash = float(row.get("LeaseCash", 0.0))
        quote_options.append({
            'term': int(term),
            'mileage': mileage,
            'residual_value': residual_value,
            'money_factor': money_factor,
            'available_lease_cash': available_lease_cash,
            'selling_price': float(msrp),
            'lease_cash_used': 0.0,
            'index': len(quote_options)
        })

st.session_state.quote_options = quote_options

# Calculate payments
filtered_options = quote_options
filtered_options.sort(key=lambda x: calculate_payment_from_ccr(
    S=x['selling_price'],
    CCR=0,
    RES=x['residual_value'],
    W=x['term'],
    F=x['money_factor'],
    τ=tax_rate,
    M=962.50,
    Q=0.0
)['Monthly Payment (MP)'])

# Show layout
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.subheader(f"Available Lease Options ({len(filtered_options)} options)")
with st.container():
    columns = st.columns(3, gap="small")
    for i, option in enumerate(filtered_options):
        with columns[i % 3]:
            option_key = f"{option['term']}_{option['mileage']}_{option['index']}"
            card_class = "quote-card"
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<p class="term-mileage">{option["term"]} Months | {option["mileage"]:,} mi/yr</p>', unsafe_allow_html=True)
            selling_price = st.number_input("Selling Price ($)", min_value=0.0, value=option["selling_price"], key=f"sp_{option_key}", step=100.0, format="%.2f")
            lease_cash_used = st.number_input(f"Lease Cash Used (Max: ${option['available_lease_cash']:.2f})", min_value=0.0, max_value=option['available_lease_cash'], value=option['lease_cash_used'], key=f"lc_{option_key}", step=50.0, format="%.2f")
            monthly_data = calculate_payment_from_ccr(
                S=selling_price,
                CCR=lease_cash_used + default_money_down + trade_value,
                RES=option['residual_value'],
                W=option['term'],
                F=option['money_factor'],
                τ=tax_rate,
                M=962.50,
                Q=0.0
            )
            st.markdown(f'<div class="payment-highlight">${monthly_data["Monthly Payment (MP)"]:.2f}/mo</div>', unsafe_allow_html=True)
            st.caption(f"Base: ${monthly_data['Base Payment (BP)']:.2f} + Tax: ${monthly_data['Tax']:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
