import streamlit as st
from PIL import Image, UnidentifiedImageError
from utils import calculate_option_payment
from typing import List, Dict, Tuple, Any

LOGO_PATH = "drivepath_logo.png"
LOGO_WIDTH = 300
# Default sorting option shown in the sidebar. Must match one of the keys used
# in utils.sort_quote_options so sorting works without errors.
DEFAULT_SORT_BY = "Lowest Payment"


def render_header(
    model_year: str,
    make: str,
    model: str,
    trim: str,
    msrp: float,
    vin: str
) -> None:
    """Display the header with vehicle info and logo."""
    col1, col2 = st.columns([1, 3])
    with col1:
        try:
            logo = Image.open(LOGO_PATH)
            st.image(logo, width=LOGO_WIDTH)
        except (FileNotFoundError, UnidentifiedImageError):
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


def render_trade_down_section() -> Tuple[float, float]:
    """Render trade value and money down input section."""
    trade_value = st.number_input("Trade Value ($)", min_value=0.0, key="trade_value")
    money_down = st.number_input("Money Down ($)", min_value=0.0, key="default_money_down")
    return trade_value, money_down


def render_filters_section(quote_options: List[Dict[str, Any]]) -> Tuple[List[int], List[int]]:
    """Render filters for lease terms and mileages."""
    terms = sorted({opt["term"] for opt in quote_options})
    mileages = sorted({opt["mileage"] for opt in quote_options})
    term_filter = st.multiselect(
        "Select Lease Terms",
        options=terms,
        default=terms,
        key="term_filter",
    )
    mileage_filter = st.multiselect(
        "Select Mileages",
        options=mileages,
        default=mileages,
        key="mileage_filter",
    )
    return term_filter, mileage_filter


def render_right_sidebar(quote_options: List[Dict[str, Any]]) -> Tuple[float, float, str, List[int], List[int]]:
    """Render sidebar with trade value, filters, and summary."""
    st.header("Financial Settings")
    with st.expander("Trade & Down Payment", expanded=True):
        trade_value, money_down = render_trade_down_section()
    with st.expander("Filters"):
        term_filter, mileage_filter = render_filters_section(quote_options)
    sort_by = DEFAULT_SORT_BY  # This could be made user-configurable in the future
    return trade_value, money_down, sort_by, term_filter, mileage_filter


def render_quote_card(
    option: Dict[str, Any],
    option_key: str,
    trade_value: float,
    money_down: float,
    tax_rate: float
) -> None:
    """Display a single quote card."""
    if "selected_quotes" not in st.session_state:
        st.session_state.selected_quotes = set()
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
        min_value=0.0
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
