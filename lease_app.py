import streamlit as st
import pandas as pd
from lease_calculations import calculate_ccr_full, calculate_payment_from_ccr
from PIL import Image
from datetime import datetime
import json

# Custom CSS to remove the top white bar and adjust layout
st.markdown("""
<style>
    /* Hide the default Streamlit header/menu bar */
    header {
        display: none;
    }
    /* Remove top padding and ensure content starts at the top */
    .main-content {
        padding: 0;
        margin-top: 0;
        font-family: 'Helvetica', Arial, sans-serif;
    }
    .quote-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        height: 100%; /* Ensure consistent height */
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
    .caption-text {
        font-size: 12px;
        color: #666;
        margin: 0;
    }
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
    .sidebar .stExpander {
        margin-bottom: 10px;
    }
    .sidebar .stTextInput, .sidebar .stSelectbox, .sidebar .stNumberInput, .sidebar .stCheckbox {
        margin-bottom: 10px;
    }
    /* Three-column layout */
    .three-column .stContainer {
        display: flex;
        justify-content: space-between;
    }
    .three-column .stContainer > div {
        width: 32%;
    }
    /* Remove extra padding/margin from containers */
    .stContainer {
        padding: 0;
    }
    .element-container {
        margin: 0;
    }
    /* Right column content styling */
    .right-content {
        max-width: 100%;
        overflow: hidden;
    }
    /* Mobile adjustment */
    @media (max-width: 768px) {
        .three-column .stContainer {
            flex-direction: column;
        }
        .three-column .stContainer > div {
            width: 100%;
        }
    }
    @media print {
        .no-print { display: none !important; }
    }
</style>
""", unsafe_allow_html=True)

# Set page config to minimize header and padding
st.set_page_config(page_title="Lease Quote Tool", layout="wide", initial_sidebar_state="expanded")

# Initialize session state
if 'selected_quotes' not in st.session_state:
    st.session_state.selected_quotes = []
if 'quote_options' not in st.session_state:
    st.session_state.quote_options = []

# Load data with caching
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
    st.error("⚠️ Data files not found. Please ensure 'All_Lease_Programs_Database.csv', 'Locator_Detail_Updated.xlsx', and 'County_Tax_Rates.csv' are in the correct directory.")
    st.stop()

# Left sidebar with Vehicle & Customer Info
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
        
        selected_tier = st.selectbox("Credit Tier:", [f"Tier {i}" for i in range(1, 9)], help="Choose your credit tier for lease terms.")
        counties = sorted(county_tax_rates["County"].tolist())
        selected_county = st.selectbox("County:", counties, index=counties.index("Marion"), help="Select your county for tax calculations.")
        tax_rate = county_tax_rates[county_tax_rates["County"] == selected_county]["Tax Rate"].iloc[0] / 100.0

# Main layout with columns for right sidebar and main content
main_col, right_col = st.columns([3, 1], gap="large")

with right_col:
    with st.container():
        st.markdown('<div class="right-content">', unsafe_allow_html=True)
        st.subheader("Financial Settings")
        trade_value = st.number_input("Trade-in Value ($)", min_value=0.0, value=0.0, step=100.0, help="Value of your trade-in vehicle.")
        default_money_down = st.number_input("Customer Cash Down ($)", min_value=0.0, value=0.0, step=100.0, help="Initial cash payment toward the lease.")
        apply_markup = st.checkbox("Apply Money Factor Markup (+0.0004)", value=False, help="Add a small markup to the money factor if desired.")

        st.subheader("Filters & Sorting")
        sort_options = {
            "Lowest Payment": "payment",
            "Lowest Term": "term",
            "Lowest Mileage": "mileage",
            "Most Lease Cash Available": "available_lease_cash"
        }
        sort_by = st.selectbox("Sort by:", list(sort_options.keys()))
        term_filter = st.multiselect("Filter by Term:", sorted(list(set(opt['term'] for opt in st.session_state.quote_options))), default=sorted(list(set(opt['term'] for opt in st.session_state.quote_options))))
        mileage_filter = st.multiselect("Filter by Mileage:", sorted(list(set(opt['mileage'] for opt in st.session_state.quote_options))), default=sorted(list(set(opt['mileage'] for opt in st.session_state.quote_options))))
        st.markdown('</div>', unsafe_allow_html=True)

with main_col:
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    # Main content area
    if not vin_input:
        col1, col2 = st.columns([1, 2])
        with col1:
            try:
                logo = Image.open("drivepath_logo.png")
                st.image(logo, width=300)
            except:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #2c3e50, #34495e); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <h2 style="margin: 0; color: white;">DrivePath</h2>
                    <p style="margin: 5px 0 0 0; color: #bdc3c7;">Lease Quote Tool</p>
                </div>
                """, unsafe_allow_html=True)
        with col2:
            st.title("Lease Quote Generator")
            st.info("👈 Enter a VIN number in the sidebar to get started")
        st.markdown("""
        ### How to use this tool:
        1. **Enter vehicle VIN** in the sidebar
        2. **Set customer parameters** (tier, county, trade value, etc.)
        3. **Review and customize** lease options
        4. **Select up to 3 quotes** for the customer
        5. **Generate printable quote**
        """)
        st.stop()

    # Process VIN and generate options
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

    # Header with logo and vehicle info
    col1, col2 = st.columns([1, 3])
    with col1:
        try:
            logo = Image.open("drivepath_logo.png")
            st.image(logo, width=300)
        except:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #2c3e50, #34495e); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h2 style="margin: 0; color: white;">DrivePath</h2>
                <p style="margin: 5px 0 0 0; color: #bdc3c7;">Lease Quote Tool</p>
            </div>
            """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="header-info">
            <h2 style="margin: 0;">{model_year} {make} {model} {trim}</h2>
            <h3 style="margin: 10px 0 0 0;">MSRP: ${msrp:,.2f} | VIN: {vin_input}</h3>
        </div>
        """, unsafe_allow_html=True)

    # Generate quote options
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

    # Apply filters without pre-calculating payments
    filtered_options = [opt for opt in st.session_state.quote_options if opt['term'] in term_filter and opt['mileage'] in mileage_filter]

    if sort_by == "Most Lease Cash Available":
        filtered_options.sort(key=lambda x: x['available_lease_cash'], reverse=True)
    elif sort_by == "Lowest Payment":
        filtered_options.sort(key=lambda x: calculate_option_payment(x['selling_price'], x['lease_cash_used'], x['residual_value'], x['money_factor'], x['term'], trade_value, default_money_down, tax_rate)['payment'])
    else:
        filtered_options.sort(key=lambda x: x[sort_options[sort_by]])

    # Display quote options in three columns
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
            if st.button("Select" if not is_selected else "Remove", key=f"action_{option_key}", help="Add or remove this quote from selection", type="primary" if not is_selected else "secondary"):
                if is_selected:
                    st.session_state.selected_quotes.remove(option_key)
                else:
                    if len(st.session_state.selected_quotes) < 3:
                        st.session_state.selected_quotes.append(option_key)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Generate Quote Section
    if st.session_state.selected_quotes:
        st.divider()
        st.subheader("Generate Customer Quote")
        if st.button("Generate Printable Quote", type="primary"):
            st.markdown('<div class="print-section no-print">', unsafe_allow_html=True)
            st.markdown("### Quote Preview (Click Print button below to print)")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="print-section">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #1e3a8a; margin-bottom: 10px;">DrivePath</h1>
                    <h2 style="color: #2E8B57; margin: 0;">LEASE QUOTE</h2>
                </div>
                <hr>
                <h3>Vehicle Information</h3>
                <p><strong>{model_year} {make} {model} {trim}</strong></p>
                <p><strong>VIN:</strong> {vin_input} | <strong>MSRP:</strong> ${msrp:,.2f}</p>
                <h3>Customer Information</h3>
                <p><strong>Name:</strong> {customer_name or 'Not provided'}</p>
                <p><strong>Phone:</strong> {customer_phone or 'Not provided'}</p>
                <p><strong>Email:</strong> {customer_email or 'Not provided'}</p>
                <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y %I:%M %p EDT')}</p>
                <h3>Lease Options</h3>
            """, unsafe_allow_html=True)
            for i, selected_key in enumerate(st.session_state.selected_quotes, 1):
                term, mileage, index = selected_key.split('_')
                option = next(opt for opt in filtered_options if opt['index'] == int(index))
                new_selling_price = st.session_state.quote_options[option['index']].get('selling_price', option['selling_price'])
                new_lease_cash = st.session_state.quote_options[option['index']].get('lease_cash_used', option['lease_cash_used'])
                payment_data = calculate_option_payment(new_selling_price, new_lease_cash, option['residual_value'], option['money_factor'], option['term'], trade_value, default_money_down, tax_rate)
                st.markdown(f"""
                <div style="border: 1px solid #e0e0e0; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                    <h4>Option {i}: {option['term']} Months | {option['mileage']:,} miles/year</h4>
                    <p style="font-size: 20px; color: #2E8B57;"><strong>Monthly Payment: ${payment_data['payment']:.2f}</strong></p>
                    <p><strong>Selling Price:</strong> ${new_selling_price:,.2f}</p>
                    <p><strong>Lease Cash Applied:</strong> ${new_lease_cash:,.2f}</p>
                    <p><strong>Trade Value:</strong> ${trade_value:,.2f}</p>
                    <p><strong>Cash Down:</strong> ${default_money_down:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("""
                <hr>
                <p style="font-size: 12px; color: #666;">
                    * Quote valid for 3 days from date shown above<br>
                    * All payments subject to approved credit<br>
                    * Tax, title, and license fees additional<br>
                    * See dealer for complete details
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="no-print">', unsafe_allow_html=True)
            st.markdown("""
            <script>
            function printQuote() {
                window.print();
            }
            </script>
            <button onclick="printQuote()" style="background-color: #1e3a8a; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                Print Quote
            </button>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👆 Select up to 3 lease options above to generate a customer quote")

# Function to calculate payment (kept outside for scope)
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
