import streamlit as st
import pandas as pd
from utils import sort_quote_options, calculate_option_payment
from data_loader import load_data
from layout_sections import (
    render_header,
    render_right_sidebar,
    render_quote_card,
    render_vin_scanner_button,
    render_customer_quote_page,
)
from utils import sort_quote_options
from style import BASE_CSS
from pdf_utils import generate_quote_pdf

def main() -> None:
    st.set_page_config(page_title="Lease Quote Tool", layout="wide", initial_sidebar_state="auto")
    st.markdown(BASE_CSS, unsafe_allow_html=True)

    if 'selected_quotes' not in st.session_state:
        st.session_state.selected_quotes = set()
    if 'quote_options' not in st.session_state:
        st.session_state.quote_options = []
    if 'page' not in st.session_state:
        st.session_state.page = 'quote'
    if 'selected_down_payment' not in st.session_state:
        st.session_state.selected_down_payment = 0.0
    if 'apply_markup' not in st.session_state:
        st.session_state.apply_markup = True

    with st.spinner("Loading data..."):
        try:
            lease_programs, vehicle_data, county_tax_rates = load_data()
        except FileNotFoundError:
            st.error("⚠️ Data files not found. Please ensure required files are present.")
            st.stop()

    # Left Sidebar
    with st.sidebar:
        st.header("Vehicle & Customer Info")
        with st.expander("Customer Information", expanded=True):
            customer_name = st.text_input(
                "Customer Name",
                key="customer_name",
                help="Enter full name for quotes",
            )
            st.text_input(
                "Phone Number",
                key="phone_number",
                help="For follow-up contact",
            )
            st.text_input(
                "Email Address",
                key="email",
                help="To send quotes",
            )

        with st.expander("Lease Parameters", expanded=True):
            # Updated VIN scanner with camera input
            vin_photo = st.camera_input("Scan VIN (or upload)", help="Use camera for quick VIN capture")
            if vin_photo:
                vin = extract_vin_from_image(vin_photo)
                if vin:
                    st.success(f"✅ VIN Detected: {vin}")
                    st.session_state.vin_input = vin
            vin_input = st.text_input(
                "Enter VIN:",
                value=st.session_state.get("vin_input", ""),
                key="vin_input",
                help="17-character VIN; scan above or type manually.",
            )
            if vin_input and len(vin_input) != 17:
                st.warning("⚠️ VIN should be 17 characters.")
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

            selected_tier = st.selectbox("Credit Tier:", [f"Tier {i}" for i in range(1, 9)], help="Higher tiers may get better rates")
            counties = sorted(county_tax_rates["County"].tolist())
            selected_county = st.selectbox("County:", counties, index=counties.index("Marion"), help="For accurate tax calculation")
            tax_rate = county_tax_rates[county_tax_rates["County"] == selected_county]["Tax Rate"].iloc[0] / 100.0
            st.session_state.tax_rate = tax_rate

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
    st.session_state.msrp = msrp
    st.session_state.vin = vin_input

    lease_matches = lease_programs[lease_programs["ModelNumber"] == model_number]
    if lease_matches.empty:
        st.error("❌ No lease program found for this model number.")
        st.stop()

    lease_info = lease_matches.iloc[0]
    model_year = lease_info.get("Year", "N/A")
    make = lease_info.get("Make", "Hyundai")
    model = lease_info.get("Model")
    trim = lease_info.get("Trim")

    if pd.isna(model):
        model = vehicle.get("Model", "N/A")
    if pd.isna(trim):
        trim = vehicle.get("Trim", "N/A")
    st.session_state.model_year = model_year
    st.session_state.make = make
    st.session_state.model = model
    st.session_state.trim = trim

    # Build quote options (with spinner)
    with st.spinner("Generating quote options..."):
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
                    'residual_pct': adjusted_residual * 100,  # New: For display
                    'money_factor': money_factor + (0.0004 if st.session_state.get('apply_markup') else 0),
                    'available_lease_cash': available_lease_cash,
                    'selling_price': float(msrp),
                    'lease_cash_used': 0.0,
                    'index': len(quote_options)
                })

    st.session_state.quote_options = quote_options

    if st.session_state.page == 'print':
        selected = [
            opt for opt in st.session_state.quote_options
            if f"{opt['term']}_{opt['mileage']}_{opt['index']}" in st.session_state.selected_quotes
        ]
        render_customer_quote_page(
            selected[:4],
            st.session_state.get('tax_rate', 0.0),
            st.session_state.get('selected_down_payment',
                                st.session_state.get('default_money_down', 0.0)),
        )
        vehicle_info = {
            "year": st.session_state.get("model_year", "N/A"),
            "make": st.session_state.get("make", "N/A"),
            "model": st.session_state.get("model", "N/A"),
            "trim": st.session_state.get("trim", "N/A"),
            "msrp": st.session_state.get("msrp", 0.0),
            "vin": st.session_state.get("vin", "N/A"),
        }
        pdf_buffer = generate_quote_pdf(
            selected,
            tax_rate,
            st.session_state.selected_down_payment,
            customer_name,
            vehicle_info,
        )
        st.download_button(
            "Download Quote PDF",
            pdf_buffer,
            "lease_quote.pdf",
            "application/pdf",
            key="export_pdf_button",
        )
        return

    # Layout columns
    main_col, right_col = st.columns([2.5, 1], gap="large")

    with right_col:
        (
            trade_value,
            default_money_down,
            sort_by,
            term_filter,
            mileage_filter,
            create_quote_clicked,
            apply_markup,
        ) = render_right_sidebar(quote_options)
        st.session_state.apply_markup = apply_markup
        if create_quote_clicked:
            st.session_state.selected_down_payment = default_money_down
            st.session_state.page = 'print'

    with main_col:
        render_header(model_year, make, model, trim, msrp, vin_input)

        filtered_options = [opt for opt in quote_options if opt['term'] in term_filter and opt['mileage'] in mileage_filter]
        filtered_options = sort_quote_options(filtered_options, sort_by, trade_value, default_money_down, tax_rate)

        # Highlight lowest payment
        if filtered_options:
            min_payment = min(opt['payment'] for opt in [calculate_option_payment(
                o['selling_price'], o['lease_cash_used'], o['residual_value'],
                o['money_factor'], o['term'], trade_value, default_money_down, tax_rate
            ) for o in filtered_options])
            for opt in filtered_options:
                payment_data = calculate_option_payment(
                    opt['selling_price'], opt['lease_cash_used'], opt['residual_value'],
                    opt['money_factor'], opt['term'], trade_value, default_money_down, tax_rate
                )
                opt['is_lowest'] = payment_data['payment'] == min_payment

        st.subheader(f"Available Lease Options ({len(filtered_options)} options)")
        cols = st.columns(3 if st.session_state.get('screen_width', 1024) > 1023 else 2 if st.session_state.get('screen_width', 1024) > 767 else 1)
        for i, option in enumerate(filtered_options):
            with cols[i % len(cols)]:
                option_key = f"{option['term']}_{option['mileage']}_{option['index']}"
                render_quote_card(option, option_key, trade_value, default_money_down, tax_rate)

    st.markdown(
        '<style>.st-emotion-cache-13ejsyy { background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; }</style>',
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()
