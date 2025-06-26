# Full updated lease_app.py with styled Filters & Sorting section using columns

import streamlit as st
import pandas as pd
from lease_calculations import calculate_ccr_full, calculate_payment_from_ccr
from PIL import Image
from datetime import datetime
import json

st.set_page_config(page_title="Lease Quote Tool", layout="wide", initial_sidebar_state="expanded")

# Add custom CSS for consistent styling
st.markdown("""
<style>
    .right-sidebar {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    
    .sidebar-section {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .sidebar-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #495057;
        margin-bottom: 0.75rem;
        border-bottom: 2px solid #007bff;
        padding-bottom: 0.5rem;
    }
    
    .quote-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    
    .quote-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .selected-quote {
        background: #e3f2fd;
        border: 2px solid #2196f3;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 4px 8px rgba(33,150,243,0.2);
    }
    
    .term-mileage {
        font-weight: 600;
        color: #1976d2;
        margin-bottom: 8px;
        font-size: 0.9rem;
    }
    
    .payment-highlight {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2e7d32;
        margin: 8px 0;
    }
    
    .caption-text {
        font-size: 0.8rem;
        color: #666;
        margin-bottom: 8px;
    }
    
    .main-content {
        padding-left: 1rem;
    }
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
    county_tax_rates = pd.read_csv("County_Tax_Rates.csv")
    county_tax_rates.columns = county_tax_rates.columns.str.strip()
    return lease_programs, vehicle_data, county_tax_rates

try:
    lease_programs, vehicle_data, county_tax_rates = load_data()
except FileNotFoundError:
    st.error("⚠️ Data files not found. Please ensure required files are present.")
    st.stop()

with st.sidebar:
    st.header("Vehicle & Customer Info")
    with st.expander("Customer Information", expanded=True):
        customer_name = st.text_input("Customer Name", "")
        customer_phone = st.text_input("Phone Number", "")
        customer_email = st.text_input("Email Address", "")

    with st.expander("Lease Parameters", expanded=True):
        vin_input = st.text_input("Enter VIN:", "", help="Enter the Vehicle Identification Number to begin.")
        if vin_input:
            vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
            if not vin_data.empty:
                vehicle = vin_data.iloc[0]
                st.success("✅ Vehicle Found!")
                st.write(f"**Model:** {vehicle.get('ModelNumber', 'N/A')}")
                st.write(f"**MSRP:** ${vehicle.get('MSRP', 0):,.2f}")
            else:
                st.warning("❌ Vehicle not found in inventory")

        selected_tier = st.selectbox("Credit Tier:", [f"Tier {i}" for i in range(1, 9)])
        counties = sorted(county_tax_rates["County"].tolist())
        selected_county = st.selectbox("County:", counties, index=counties.index("Marion"))
        tax_rate = county_tax_rates[county_tax_rates["County"] == selected_county]["Tax Rate"].iloc[0] / 100.0

if not vin_input:
    st.title("Lease Quote Generator")
    st.info("👈 Enter a VIN number in the sidebar to get started")
    st.stop()

vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
if vin_data.empty:
    st.error("❌ Vehicle not found in inventory. Please check the VIN number.")
    st.stop()

vehicle = vin_data.iloc[0]
model_number = vehicle["ModelNumber"]
msrp = float(vehicle["MSRP"])

lease_matches = lease_programs[lease_programs["ModelNumber"] == model_number]
if lease_matches.empty:
    st.error("❌ No lease program found for this model number.")
    st.stop()

lease_info = lease_matches.iloc[0]
model_year = lease_info.get("Year", "N/A")
make = lease_info.get("Make", "Hyundai")
model = lease_info.get("Model", "N/A")
trim = lease_info.get("Trim", "N/A")

col1, col2 = st.columns([1, 3])
with col1:
    try:
        logo = Image.open("drivepath_logo.png")
        st.image(logo, width=300)
    except:
        st.markdown("<h2>DrivePath</h2>", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div style='background:#1e3a8a;padding:20px;color:white;border-radius:10px'>
        <h2>{model_year} {make} {model} {trim}</h2>
        <h3>MSRP: ${msrp:,.2f} | VIN: {vin_input}</h3>
        </div>
    """, unsafe_allow_html=True)

# Build quote options
tier_num = int(selected_tier.split(" ")[1])
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
        available_lease_cash = float(row.get("LeaseCash", 0.0))
        quote_options.append({
            'term': int(term),
            'mileage': mileage,
            'residual_value': residual_value,
            'money_factor': money_factor + (0.0004 if 'apply_markup' in st.session_state and st.session_state['apply_markup'] else 0),
            'available_lease_cash': available_lease_cash,
            'selling_price': float(msrp),
            'lease_cash_used': 0.0,
            'index': len(quote_options)
        })

st.session_state.quote_options = quote_options

main_col, right_col = st.columns([3, 1], gap="large")

with right_col:
    st.markdown('<div class="right-sidebar">', unsafe_allow_html=True)
    
    # Vehicle & Customer Info Header
    st.markdown('<div class="sidebar-header">Vehicle & Customer Info</div>', unsafe_allow_html=True)
    
    # Financial Settings Section
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header">Financial Settings</div>', unsafe_allow_html=True)
    
    trade_value = st.number_input("Trade-in Value ($)", min_value=0.0, value=0.0, step=100.0)
    default_money_down = st.number_input("Customer Cash Down ($)", min_value=0.0, value=0.0, step=100.0)
    apply_markup = st.checkbox("Apply Money Factor Markup (+0.0004)", value=False)
    st.session_state['apply_markup'] = apply_markup
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Filters & Sorting Section
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header">Filters & Sorting</div>', unsafe_allow_html=True)
    
    sort_options = {
        "Lowest Payment": "payment",
        "Lowest Term": "term",
        "Lowest Mileage": "mileage",
        "Most Lease Cash Available": "available_lease_cash"
    }
    sort_by = st.selectbox("Sort by:", list(sort_options.keys()))
    term_filter = st.multiselect("Filter by Term:", sorted(list(set(opt['term'] for opt in quote_options))), default=sorted(list(set(opt['term'] for opt in quote_options))))
    mileage_filter = st.multiselect("Filter by Mileage:", sorted(list(set(opt['mileage'] for opt in quote_options))), default=sorted(list(set(opt['mileage'] for opt in quote_options))))
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def calculate_option_payment(selling_price, lease_cash_used, residual_value, money_factor, term, trade_val, cash_down, tax_rt):
    initial_B = lease_cash_used
    ccr_initial, _, debug_ccr_initial = calculate_ccr_full(
        SP=selling_price, B=initial_B, rebates=0.0, TV=0.0, K=0.0, M=962.50, Q=0.0,
        RES=residual_value, F=money_factor, W=term, τ=tax_rt
    )
    overflow = abs(debug_ccr_initial.get("Initial TopVal", 0.0)) if debug_ccr_initial.get("Initial TopVal", 0.0) < 0 else 0
    trade_used = min(trade_val, overflow)
    remaining_gap = overflow - trade_used
    cash_used = min(cash_down, remaining_gap)
    remaining_trade = trade_val - trade_used
    remaining_cash = cash_down - cash_used
    adjusted_SP = selling_price - remaining_trade
    total_B = initial_B + trade_used + cash_used + remaining_cash
    ccr, _, _ = calculate_ccr_full(
        SP=adjusted_SP, B=total_B, rebates=0.0, TV=0.0, K=0.0, M=962.50, Q=0.0,
        RES=residual_value, F=money_factor, W=term, τ=tax_rt
    )
    payment = calculate_payment_from_ccr(
        S=adjusted_SP, CCR=ccr, RES=residual_value, W=term,
        F=money_factor, τ=tax_rt, M=962.50, Q=0.0
    )
    return {
        'payment': payment['Monthly Payment (MP)'],
        'base_payment': payment['Base Payment (BP)'],
        'tax_payment': payment['Sales Tax (ST)'],
        'ccr': ccr,
        'trade_used': trade_used,
        'remaining_cash': remaining_cash
    }

with main_col:
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    filtered_options = [opt for opt in quote_options if opt['term'] in term_filter and opt['mileage'] in mileage_filter]

    if sort_by == "Most Lease Cash Available":
        filtered_options.sort(key=lambda x: x['available_lease_cash'], reverse=True)
    elif sort_by == "Lowest Payment":
        filtered_options.sort(key=lambda x: calculate_option_payment(x['selling_price'], x['lease_cash_used'], x['residual_value'], x['money_factor'], x['term'], trade_value, default_money_down, tax_rate)['payment'])
    else:
        filtered_options.sort(key=lambda x: x[sort_options[sort_by]])

    st.subheader(f"Available Lease Options ({len(filtered_options)} options)")
    cols = st.columns(3, gap="small")
    for i, option in enumerate(filtered_options):
        with cols[i % 3]:
            option_key = f"{option['term']}_{option['mileage']}_{option['index']}"
            is_selected = option_key in st.session_state.selected_quotes
            card_class = "selected-quote" if is_selected else "quote-card"

            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<p class="term-mileage">{option["term"]} Months | {option["mileage"]:,} mi/yr</p>', unsafe_allow_html=True)
            new_selling_price = st.number_input("Selling Price ($)", value=float(option['selling_price']), key=f"sp_{option_key}", step=100.0)
            new_lease_cash = st.number_input(f"Lease Cash Used (Max: ${option['available_lease_cash']:,.2f})", min_value=0.0, max_value=float(option['available_lease_cash']), value=float(option['lease_cash_used']), key=f"lc_{option_key}", step=100.0)
            payment_data = calculate_option_payment(new_selling_price, new_lease_cash, option['residual_value'], option['money_factor'], option['term'], trade_value, default_money_down, tax_rate)
            st.markdown(f'<div class="payment-highlight">${payment_data["payment"]:.2f}/mo</div>', unsafe_allow_html=True)
            st.markdown(f'<p class="caption-text">Base: ${payment_data["base_payment"]:.2f} + Tax: ${payment_data["tax_payment"]:.2f}</p>', unsafe_allow_html=True)
            if st.button("Select" if not is_selected else "Remove", key=f"action_{option_key}", type="primary" if not is_selected else "secondary"):
                if is_selected:
                    st.session_state.selected_quotes.remove(option_key)
                else:
                    if len(st.session_state.selected_quotes) < 3:
                        st.session_state.selected_quotes.append(option_key)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
