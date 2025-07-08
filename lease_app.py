import streamlit.components.v1 as components
import streamlit as st
from data_loader import load_data
from layout_sections import render_header, render_right_sidebar, render_quote_card
from utils import sort_quote_options
from style import BASE_CSS


def main() -> None:
    st.set_page_config(page_title="Lease Quote Tool", layout="centered", initial_sidebar_state="auto")
    st.markdown(BASE_CSS, unsafe_allow_html=True)

    if 'selected_quotes' not in st.session_state:
        st.session_state.selected_quotes = []
    if 'quote_options' not in st.session_state:
        st.session_state.quote_options = []

    try:
        lease_programs, vehicle_data, county_tax_rates = load_data()
        st.write("Debug: Data loaded successfully")
    except FileNotFoundError:
        st.error("⚠️ Data files not found. Please ensure required files are present.")
        st.stop()

    # Left Sidebar
    with st.sidebar:
        st.header("Vehicle & Customer Info")
        with st.expander("Customer Information", expanded=True):
            st.text_input("Customer Name", "")
            st.text_input("Phone Number", "")
            st.text_input("Email Address", "")

        with st.expander("Lease Parameters", expanded=True):
            vin_input = st.text_input("Enter VIN:", "", help="Enter the Vehicle Identification Number to begin.")
            if vin_input:
                vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
                if not vin_data.empty:
                    vehicle = vin_data.iloc[0]
                    msrp_value = vehicle.get("MSRP", 0)
                    try:
                        msrp_display = float(str(msrp_value).replace("$", "").replace(",", ""))
                    except (TypeError, ValueError):
                        msrp_display = 0.0
                    st.success("✅ Vehicle Found!")
                    st.write(f"**Model:** {vehicle.get('ModelNumber', 'N/A')}")
                    st.write(f"**MSRP:** ${msrp_display:,.2f}")
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
    msrp_raw = vehicle.get("MSRP", 0)
    try:
        msrp = float(str(msrp_raw).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        msrp = 0.0

    lease_matches = lease_programs[lease_programs["ModelNumber"] == model_number]
    if lease_matches.empty:
        st.error("❌ No lease program found for this model number.")
        st.stop()

    lease_info = lease_matches.iloc[0]
    model_year = lease_info.get("Year", "N/A")
    make = lease_info.get("Make", "Hyundai")
    model = lease_info.get("Model", "N/A")
    trim = lease_info.get("Trim", "N/A")

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
            adjusted_residual = (
                base_residual + 0.01 if mileage == 10000 else
                base_residual - 0.02 if mileage == 15000 else
                base_residual
            )
            residual_value = round(msrp * adjusted_residual, 2)
            mf_col = f"Tier {tier_num}"
            money_factor = float(row[mf_col])
            available_lease_cash = float(row.get("LeaseCash", 0.0))
            quote_options.append({
                'term': int(term),
                'mileage': mileage,
                'residual_value': residual_value,
                'money_factor': money_factor + (0.0004 if st.session_state.get('apply_markup') else 0),
                'available_lease_cash': available_lease_cash,
                'selling_price': float(msrp),
                'lease_cash_used': 0.0,
                'index': len(quote_options)
            })

    st.session_state.quote_options = quote_options
    st.write("Debug: Quote options generated", len(quote_options))

    # Layout columns
    main_col, right_col = st.columns([2.5, 1], gap="large")

    with right_col:
        trade_value, default_money_down, sort_by, term_filter, mileage_filter = render_right_sidebar(quote_options)
        st.write("Debug: Right sidebar rendered")

    with main_col:
        render_header(model_year, make, model, trim, msrp, vin_input)
        st.write("Debug: Header rendered")

        filtered_options = [opt for opt in quote_options if opt['term'] in term_filter and opt['mileage'] in mileage_filter]
        filtered_options = sort_quote_options(filtered_options, sort_by, trade_value, default_money_down, tax_rate)
        st.write("Debug: Options filtered and sorted", len(filtered_options))

        st.subheader(f"Available Lease Options ({len(filtered_options)} options)")
        cols = st.columns(3, gap="small")  # Reduced gap to minimize white space
        for i, option in enumerate(filtered_options):
            with cols[i % 3]:
                option_key = f"{option['term']}_{option['mileage']}_{option['index']}"
                render_quote_card(option, option_key, trade_value, default_money_down, tax_rate)
        st.write("Debug: Quote cards rendered")

    st.markdown('<style>.st-emotion-cache-13ejsyy { background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; }</style>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
