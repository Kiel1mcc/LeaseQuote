import streamlit as st
from PIL import Image, UnidentifiedImageError
import pytesseract
import re
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


def render_right_sidebar(
    quote_options: List[Dict[str, Any]]
) -> Tuple[float, float, str, List[int], List[int], bool]:
    st.markdown('<div class="right-sidebar">', unsafe_allow_html=True)
    st.header("Financial Settings")
    with st.expander("Trade & Down Payment", expanded=True):
        trade_value, money_down = render_trade_down_section()
        create_quote_clicked = st.button("Create Customer Quote")
    with st.expander("Filters"):
        term_filter, mileage_filter = render_filters_section(quote_options)
    st.markdown("</div>", unsafe_allow_html=True)
    sort_by = DEFAULT_SORT_BY
    return trade_value, money_down, sort_by, term_filter, mileage_filter, create_quote_clicked


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

        selected = st.checkbox(
            "Include", value=is_selected, key=f"sel_{option_key}"
        )
        if selected:
            st.session_state.selected_quotes.add(option_key)
        else:
            st.session_state.selected_quotes.discard(option_key)

        st.markdown("</div></div>", unsafe_allow_html=True)



def extract_vin_from_image(image_file):
    """Return a VIN string from an uploaded image if detected."""
    image = Image.open(image_file)
    text = pytesseract.image_to_string(image)
    vin_match = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", text)
    if vin_match:
        return vin_match.group(0)
    return None


def render_vin_scanner_button() -> None:
    """Allow user to upload a VIN photo and autofill the text input."""
    uploaded_file = st.file_uploader(
        "\U0001F4F7 Take or upload a photo of the VIN label",
        type=["jpg", "jpeg", "png"],
        key="vin_photo_uploader",
    )
    if uploaded_file:
        vin = extract_vin_from_image(uploaded_file)
        if vin:
            st.success(f"\u2705 VIN Detected: {vin}")
            st.session_state.vin_input = vin
        else:
            st.warning("\u26A0\uFE0F Couldn't detect a VIN in the image. Try again.")


def render_customer_quote_page(selected_options: List[Dict[str, Any]], tax_rate: float) -> None:
    """Display a print-friendly customer quote screen."""
    col1, col2 = st.columns([1, 1])
    if col1.button("\u2190 Back"):
        st.session_state.page = "quote"
    if col2.button("Print"):
        st.session_state.trigger_print = True
    if st.session_state.get("trigger_print"):
        st.markdown("<script>window.print()</script>", unsafe_allow_html=True)
        st.session_state.trigger_print = False

    if not selected_options:
        st.info("No quotes selected")
        return

    cols = st.columns(len(selected_options))
    for col, opt in zip(cols, selected_options[:4]):
        with col:
            st.markdown(f"### {opt['term']} Mo | {opt['mileage']:,} mi/yr")
            for down in [0, 1500, 2500]:
                payment = calculate_option_payment(
                    selling_price=opt['selling_price'],
                    lease_cash_used=opt['lease_cash_used'],
                    residual_value=opt['residual_value'],
                    money_factor=opt['money_factor'],
                    term=opt['term'],
                    trade_val=0.0,
                    cash_down=down,
                    tax_rt=tax_rate,
                )["payment"]
                st.write(f"${down:,.0f} Down: ${payment:,.2f}/mo")
            custom_key = f"custom_down_{opt['index']}"
            custom_down = st.number_input("Custom Down", value=0.0, key=custom_key, step=100.0)
            custom_payment = calculate_option_payment(
                selling_price=opt['selling_price'],
                lease_cash_used=opt['lease_cash_used'],
                residual_value=opt['residual_value'],
                money_factor=opt['money_factor'],
                term=opt['term'],
                trade_val=0.0,
                cash_down=custom_down,
                tax_rt=tax_rate,
            )["payment"]
            st.write(f"Custom: ${custom_payment:,.2f}/mo")
