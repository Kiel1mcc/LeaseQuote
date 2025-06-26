import streamlit as st
import pandas as pd
from lease_calculations import calculate_ccr_full, calculate_payment_from_ccr
from PIL import Image
from datetime import datetime
import json

st.set_page_config(page_title="Lease Quote Tool", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    header { display: none; }
    .main-content { padding: 0; margin-top: 0; font-family: 'Helvetica', Arial, sans-serif; }
    .quote-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 0 0 15px 0;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        height: 100%;
    }
    .selected-quote {
        border: 2px solid #4CAF50;
        background-color: #f0fff0;
        box-shadow: 0 4px 8px rgba(76, 175, 80, 0.2);
    }
    .payment-highlight { font-size: 24px; font-weight: 700; color: #2E8B57; margin: 5px 0; }
    .term-mileage { font-size: 18px; font-weight: 600; color: #1e3a8a; margin: 0 0 5px 0; }
    .caption-text { font-size: 12px; color: #666; margin: 0; }
</style>
""", unsafe_allow_html=True)

if 'selected_quotes' not in st.session_state:
    st.session_state.selected_quotes = []
if 'quote_options' not in st.session_state:
    st.session_state.quote_options = []

@st.cache_data
def load_data():
    lease_programs = pd.read_csv("All_Lease_Programs_Database.csv", encoding="utf-8-sig")
    lease_programs.columns = lease_programs.columns.str.strip()
    vehicle_data = pd.read_excel("Locator_Detail_Updated.xlsx")
    vehicle_data.columns = vehicle_data.columns.str.strip()
    counties = pd.read_csv("County_Tax_Rates.csv")['County'].dropna().unique().tolist()
    return lease_programs, vehicle_data, counties

try:
    lease_programs, vehicle_data, counties = load_data()
except FileNotFoundError:
    st.error("⚠️ Missing data files.")
    st.stop()

with st.sidebar:
    st.header("Vehicle & Customer Info")
    with st.expander("Customer Information", expanded=True):
        customer_name = st.text_input("Customer Name", "")
        customer_phone = st.text_input("Phone Number", "")
        customer_email = st.text_input("Email Address", "")

    vin_input = st.text_input("Enter VIN:", "")
    if vin_input:
        vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
        if not vin_data.empty:
            vehicle = vin_data.iloc[0]
            st.success("✅ Vehicle Found!")
            st.write(f"**Model:** {vehicle.get('ModelNumber', 'N/A')}")
            st.write(f"**MSRP:** ${vehicle.get('MSRP', 0):,.2f}")
        else:
            st.warning("❌ Vehicle not found in inventory")

    st.header("Lease Parameters")
    selected_tier = st.selectbox("Credit Tier:", [f"Tier {i}" for i in range(1, 9)])
    selected_county = st.selectbox("County:", sorted(counties))
    st.subheader("Financial Settings")
    trade_value = st.number_input("Trade-in Value ($)", min_value=0.0, value=0.0, step=100.0)
    default_money_down = st.number_input("Customer Cash Down ($)", min_value=0.0, value=0.0, step=100.0)
    apply_markup = st.checkbox("Apply Money Factor Markup (+0.0004)", value=False)

if not vin_input:
    st.title("Lease Quote Generator")
    st.info("👈 Enter a VIN in the sidebar to get started.")
    st.stop()

vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
if vin_data.empty:
    st.error("❌ VIN not found in inventory.")
    st.stop()

vehicle = vin_data.iloc[0]
model_number = vehicle["ModelNumber"]
msrp = float(vehicle["MSRP"])
lease_matches = lease_programs[lease_programs["ModelNumber"] == model_number]
if lease_matches.empty:
    st.error("❌ No lease program found for this model number.")
    st.stop()

model_year = lease_matches.iloc[0].get("Year", "N/A")
make = lease_matches.iloc[0].get("Make", "Hyundai")
model = lease_matches.iloc[0].get("Model", "N/A")
trim = lease_matches.iloc[0].get("Trim", "N/A")

st.markdown(f"""
<div class="header-info">
    <h2>{model_year} {make} {model} {trim}</h2>
    <h3>MSRP: ${msrp:,.2f} | VIN: {vin_input}</h3>
</div>
""", unsafe_allow_html=True)

tier_num = int(selected_tier.split(" ")[1])
tax_rate = 0.0725  # Placeholder
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
        lease_cash = float(row.get("LeaseCash", 0.0))
        quote_options.append({
            'term': int(term),
            'mileage': mileage,
            'residual_value': residual_value,
            'money_factor': money_factor,
            'available_lease_cash': lease_cash,
            'selling_price': msrp,
            'lease_cash_used': 0.0,
            'index': len(quote_options)
        })

st.session_state.quote_options = quote_options

st.subheader("Available Lease Options")
for i in range(0, len(quote_options), 3):
    row = st.columns(min(3, len(quote_options) - i), gap="small")
    for j in range(len(row)):
        option = quote_options[i + j]
        with row[j]:
            option_key = f"{option['term']}_{option['mileage']}_{option['index']}"
            is_selected = option_key in st.session_state.selected_quotes
            card_class = "selected-quote" if is_selected else "quote-card"
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<p class="term-mileage">{option["term"]} Months | {option["mileage"]:,} mi/yr</p>', unsafe_allow_html=True)
            new_sp = st.number_input("Selling Price ($)", value=option['selling_price'], key=f"sp_{option_key}", step=100.0)
            new_lc = st.number_input("Lease Cash Used", min_value=0.0, max_value=option['available_lease_cash'], value=option['lease_cash_used'], key=f"lc_{option_key}", step=100.0)
            result = calculate_payment_from_ccr(new_sp, new_lc, option['residual_value'], option['money_factor'], option['term'], trade_value, default_money_down, tax_rate)
            st.markdown(f"<details><summary><b style='color:#2E8B57;'>Debug Info</b></summary><pre style='font-size:11px'>{json.dumps(result, indent=2)}</pre></details>", unsafe_allow_html=True)
            st.markdown(f'<div class="payment-highlight">${result["Monthly Payment (MP)"]:.2f}/mo</div>', unsafe_allow_html=True)
            st.markdown(f'<p class="caption-text">Base: ${result["Base Payment (BP)"]:.2f} + Tax: ${result["Sales Tax (ST)"]:.2f}</p>', unsafe_allow_html=True)
            if st.button("Select" if not is_selected else "Remove", key=f"action_{option_key}"):
                if is_selected:
                    st.session_state.selected_quotes.remove(option_key)
                else:
                    if len(st.session_state.selected_quotes) < 3:
                        st.session_state.selected_quotes.append(option_key)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.selected_quotes:
    st.subheader("Generate Quote")
    if st.button("Generate Printable Quote"):
        st.write("// Final output generation coming soon")
