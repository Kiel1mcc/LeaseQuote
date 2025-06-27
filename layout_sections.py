import streamlit as st
from PIL import Image
from utils import calculate_option_payment

def render_header(model_year: str, make: str, model: str, trim: str, msrp: float, vin: str) -> None:
    """Display the header with vehicle info and logo."""
    col1, col2 = st.columns([1, 3])
    with col1:
        try:
            logo = Image.open("drivepath_logo.png")
            st.image(logo, width=300)
        except Exception:
            st.markdown("<h2>DrivePath</h2>", unsafe_allow_html=True)
    with col2:
        st.markdown(
            f"""
            <div style='background:#1e3a8a;padding:20px;color:white;border-radius:10px'>
                <h2>{model_year} {make} {model} {trim}</h2>
                <h3>MSRP: ${msrp:,.2f} | VIN: {vin}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_right_sidebar(quote_options):
    """Render sidebar with trade value, filters, and summary."""
    st.header("Financial Settings")

    with st.expander("Trade & Down Payment", expanded=True):
        st.number_input("Trade Value ($)", min_value=0, key="trade_value")
        st.number_input("Money Down ($)", min_value=0, key="default_money_down")

    with st.expander("Filters"):
        st.multiselect(
            "Select Lease Terms",
            options=sorted({opt["term"] for opt in quote_options}),
            key="term_filter",
        )
        st.multiselect(
            "Select Mileages",
            options=sorted({opt["mileage"] for opt in quote_options}),
            key="mileage_filter",
        )

def render_quote_card(option, option_key, trade_value, default_money_down, tax_rate):
    """Display a single quote card."""
    is_selected = option_key in st.session_state.selected_quotes
    css_class = "selected-quote" if is_selected else "quote-card"

    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)

    st.markdown(
        f'<p class="term-mileage">{option["term"]} Months | {option["mileage"]:,} mi/yr</p>',
        unsafe_allow_html=True
    )

    new_selling_price = st.number_input(
        "Selling Price ($)",
        value=float(option['selling_price']),
        key=f"sp_{option_key}",
        step=100.0,
    )

    new_lease_cash = st.number_input(
        f"Lease Cash Used (Max: ${option['available_lease_cash']:.2f})",
        min_value=0.0,
        max_value=float(option['available_lease_cash']),
        value=float(option['lease_cash_used']),
        key=f"lc_{option_key}",
        step=100.0,
    )

    st.markdown("</div>", unsafe_allow_html=True)
