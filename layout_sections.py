import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, UnidentifiedImageError
from utils import calculate_option_payment
from typing import List, Dict, Tuple, Any

LOGO_PATH = "drivepath_logo.png"
LOGO_WIDTH = 300
DEFAULT_SORT_BY = "Lowest Payment"


def render_header(model_year: str, make: str, model: str, trim: str, msrp: float, vin: str) -> None:
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
    trade_value = st.number_input("Trade Value ($)", min_value=0.0, key="trade_value")
    money_down = st.number_input("Money Down ($)", min_value=0.0, key="default_money_down")
    return trade_value, money_down


def render_filters_section(quote_options: List[Dict[str, Any]]) -> Tuple[List[int], List[int]]:
    terms = sorted({opt["term"] for opt in quote_options})
    mileages = sorted({opt["mileage"] for opt in quote_options})
    term_filter = st.multiselect("Select Lease Terms", options=terms, default=terms, key="term_filter")
    mileage_filter = st.multiselect("Select Mileages", options=mileages, default=mileages, key="mileage_filter")
    return term_filter, mileage_filter


def render_right_sidebar(quote_options: List[Dict[str, Any]]) -> Tuple[float, float, str, List[int], List[int]]:
    st.markdown('<div class="right-sidebar">', unsafe_allow_html=True)
    st.header("Financial Settings")
    with st.expander("Trade & Down Payment", expanded=True):
        trade_value, money_down = render_trade_down_section()
    with st.expander("Filters"):
        term_filter, mileage_filter = render_filters_section(quote_options)
    st.markdown("</div>", unsafe_allow_html=True)
    sort_by = DEFAULT_SORT_BY
    return trade_value, money_down, sort_by, term_filter, mileage_filter


def render_quote_card(
    option: Dict[str, Any],
    option_key: str,
    trade_value: float,
    money_down: float,
    tax_rate: float,
) -> None:
    if "selected_quotes" not in st.session_state:
        st.session_state.selected_quotes = set()
    is_selected = option_key in st.session_state.selected_quotes
    css_class = "selected-quote" if is_selected else "quote-card"

    with st.container():
        st.markdown('<div class="quote-card-retainer">', unsafe_allow_html=True)
        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)

        st.markdown(f'<p class="term-mileage">{option["term"]} Months | {option["mileage"]:,} mi/yr</p>', unsafe_allow_html=True)

        new_selling_price = st.number_input(
            "Selling Price ($)",
            value=float(option["selling_price"]),
            key=f"sp_{option_key}",
            step=100.0,
            min_value=0.0,
        )

        new_lease_cash = st.number_input(
            f"Lease Cash Used (Max: ${option['available_lease_cash']:.2f})",
            min_value=0.0,
            max_value=float(option["available_lease_cash"]),
            value=float(option["lease_cash_used"]),
            key=f"lc_{option_key}",
            step=100.0,
        )

        try:
            payment_data = calculate_option_payment(
                selling_price=new_selling_price,
                lease_cash_used=new_lease_cash,
                residual_value=option["residual_value"],
                money_factor=option["money_factor"],
                term=option["term"],
                trade_val=trade_value,
                cash_down=money_down,
                tax_rt=tax_rate,
            )
            st.markdown(f'<div class="payment-highlight">${payment_data["payment"]:,.2f}/mo</div>', unsafe_allow_html=True)
        except Exception:
            st.markdown('<div class="payment-highlight">Monthly Payment: N/A</div>', unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)


# VIN SCANNER: Embedded camera scanner
if st.button("📷 Scan VIN"):
    components.iframe("vin_scanner.html", height=350, scrolling=False)
    st.markdown("_(Scan the barcode on the door or windshield label)_")
    st.markdown("""
    <script>
    window.addEventListener("message", (event) => {
        if (event.data.type === "vin") {
            const vin = event.data.data;
            const input = window.parent.document.querySelector('input[data-baseweb="input"]');
            if (input) {
                input.value = vin;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });
    </script>
    """, unsafe_allow_html=True)
