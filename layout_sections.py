import streamlit as st
from PIL import Image, UnidentifiedImageError
import pytesseract
import re
from utils import calculate_option_payment
from pdf_utils import generate_quote_pdf
from typing import List, Dict, Tuple, Any
from datetime import datetime

LOGO_PATH = "drivepath_logo.png"
LOGO_WIDTH = 300
DEFAULT_SORT_BY = "Lowest Payment"


def render_header(
    model_year: str, make: str, model: str, trim: str, msrp: float, vin: str
) -> None:
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
    money_down = st.number_input(
        "Money Down ($)", min_value=0.0, key="default_money_down"
    )
    return trade_value, money_down


def render_filters_section(
    quote_options: List[Dict[str, Any]]
) -> Tuple[List[int], List[int]]:
    terms = sorted({opt["term"] for opt in quote_options})
    mileages = sorted({opt["mileage"] for opt in quote_options})
    term_filter = st.multiselect(
        "Select Lease Terms", options=terms, default=terms, key="term_filter"
    )
    mileage_filter = st.multiselect(
        "Select Mileages", options=mileages, default=mileages, key="mileage_filter"
    )
    return term_filter, mileage_filter


def render_right_sidebar(
    quote_options: List[Dict[str, Any]]
) -> Tuple[float, float, str, List[int], List[int], bool, bool]:
    st.markdown('<div class="right-sidebar">', unsafe_allow_html=True)
    st.header("Financial Settings")
    with st.expander("Trade & Down Payment", expanded=True):
        trade_value, money_down = render_trade_down_section()
        create_quote_clicked = st.button("Create Customer Quote")
    with st.expander("Filters"):
        term_filter, mileage_filter = render_filters_section(quote_options)
    with st.expander("Markup", expanded=True):
        apply_markup = st.checkbox(
            "Add 0.0004 Money Factor Markup",
            value=st.session_state.get("apply_markup", True),
        )
    st.session_state.apply_markup = apply_markup
    st.markdown("</div>", unsafe_allow_html=True)
    sort_by = DEFAULT_SORT_BY
    return (
        trade_value,
        money_down,
        sort_by,
        term_filter,
        mileage_filter,
        create_quote_clicked,
        apply_markup,
    )


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
    is_lowest = option.get("is_lowest", False)
    css_class = (
        "selected-quote"
        if is_selected
        else "lowest-payment"
        if is_lowest
        else "quote-card"
    )

    with st.container():
        st.markdown('<div class="quote-card-retainer">', unsafe_allow_html=True)
        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)

        st.markdown(
            f'<p class="term-mileage">{option["term"]} Months | {option["mileage"]:,} mi/yr</p>',
            unsafe_allow_html=True,
        )

        new_selling_price = st.number_input(
            "Selling Price ($)",
            value=float(option["selling_price"]),
            key=f"sp_{option_key}",
            step=100.0,
            min_value=0.0,
            help="Adjust based on negotiations; must be positive.",
        )

        new_lease_cash = st.number_input(
            f"Lease Cash Used (Max: ${option['available_lease_cash']:.2f})",
            min_value=0.0,
            max_value=float(option["available_lease_cash"]),
            value=float(option["lease_cash_used"]),
            key=f"lc_{option_key}",
            step=100.0,
            help="Incentives applied; can't exceed available.",
        )

        with st.spinner("Calculating..."):
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
                st.markdown(
                    f'<div class="payment-highlight">${payment_data["payment"]:,.2f}/mo</div>',
                    unsafe_allow_html=True,
                )
            except Exception:
                st.markdown(
                    '<div class="payment-highlight">Monthly Payment: N/A</div>',
                    unsafe_allow_html=True,
                )

        with st.expander("Details"):
            st.write(
                f"Residual: {option['residual_pct']:.1f}% (${option['residual_value']:,.2f})"
            )
            st.write(f"Money Factor: {option['money_factor']:.6f}")
            st.write(f"Base Payment: ${payment_data['base_payment']:,.2f}")
            st.write(f"Tax: ${payment_data['tax_payment']:,.2f}")

        selected = st.checkbox("Include", value=is_selected, key=f"sel_{option_key}")
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


def render_vin_scanner_button() -> str | None:
    """Allow user to upload a VIN photo and return the detected text."""
    uploaded_file = st.file_uploader(
        "\U0001F4F7 Take or upload a photo of the VIN label",
        type=["jpg", "jpeg", "png"],
        key="vin_photo_uploader",
    )
    if uploaded_file:
        vin = extract_vin_from_image(uploaded_file)
        if vin:
            st.success(f"\u2705 VIN Detected: {vin}")
            return vin
        st.warning("\u26A0\uFE0F Couldn't detect a VIN in the image. Try again.")
    return None


def render_customer_quote_page(
    selected_options: List[Dict[str, Any]],
    tax_rate: float,
    base_down: float,
) -> None:
    """Display a print-friendly customer quote screen."""
    st.markdown(
        """
        <style>
        /* Base font and layout consistency */
        body, table, th, td {
            font-family: 'Arial', sans-serif;
            font-size: 15px;
            color: #000;
        }

        /* Style your main quote table like the on-screen version */
        table.lease-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            font-size: 15px;
        }
        .lease-table th {
            text-align: left;
            background-color: #f5f5f5;
            font-weight: 600;
            padding: 10px;
            border-bottom: 1px solid #ccc;
        }
        .lease-table td {
            padding: 10px;
            vertical-align: middle;
        }


        /* Print-friendly rules */
        @media print {
            header, footer, .stSidebar, .st-emotion-cache-1dtefog, .element-container:has(button) {
                display: none !important;
            }
            .stButton {
                display: none !important;
            }
            body {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1, 2])
    if col1.button("\u2190 Back"):
        st.session_state.page = "quote"
    with col2:
        st.markdown(
            """
            <button onclick="window.print()">\U0001F5A8\ufe0f Print This Page</button>
            """,
            unsafe_allow_html=True,
        )
    col3.info(
        "\U0001F4F1 On mobile, please use your browser's menu and choose 'Print' manually."
    )

    if not selected_options:
        st.info("No quotes selected")
        return

    # Professional Header
    st.markdown('<div class="quote-summary">', unsafe_allow_html=True)
    st.subheader("Lease Quote Summary")
    customer_name = st.session_state.get("customer_name", "N/A")
    phone = st.session_state.get("phone_number", "N/A")
    email = st.session_state.get("email", "N/A")
    vehicle_details = (
        f"{st.session_state.get('model_year', 'N/A')} {st.session_state.get('make', 'N/A')} "
        f"{st.session_state.get('model', 'N/A')} {st.session_state.get('trim', 'N/A')} | "
        f"MSRP: ${st.session_state.get('msrp', 0):,.2f} | VIN: {st.session_state.get('vin', 'N/A')}"
    )
    st.write(f"**Customer:** {customer_name}")
    st.write(f"**Phone:** {phone}  |  **Email:** {email}")
    st.write(f"**Vehicle:** {vehicle_details}")
    st.write(
        f"**Dealership:** Mathew's Hyundai | **Date:** {datetime.today().strftime('%B %d, %Y')}"
    )

    st.markdown(
        "<h4>Please select the term and mileage limit you would like us to submit to the bank.</h4>",
        unsafe_allow_html=True,
    )

    header_html = "<table class='lease-table'><tr><th>Down Payment</th>"
    for opt in selected_options:
        header_html += f"<th>{opt['term']} Mo | {opt['mileage']:,} mi/yr</th>"
    header_html += "</tr>"

    body_html = ""
    default_rows = [base_down + 1500 * i for i in range(3)]
    for down_val in default_rows:
        body_html += "<tr>"
        body_html += f"<td><strong>${down_val:,.2f} Down</strong></td>"
        for opt in selected_options:
            payment_data = calculate_option_payment(
                opt["selling_price"],
                opt["lease_cash_used"],
                opt["residual_value"],
                opt["money_factor"],
                opt["term"],
                0.0,
                down_val,
                tax_rate,
            )
            payment = payment_data["payment"]
            body_html += f'<td>☐ ${payment:,.2f}/mo</td>'
        body_html += "</tr>"

    footer_html = "</table>"
    st.markdown(header_html + body_html + footer_html, unsafe_allow_html=True)

    # Signature Line (printable)
    st.markdown('<div class="signature-section">', unsafe_allow_html=True)
    st.write(
        "Customer Signature: _______________________________ Date: _______________"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Disclaimers
    st.markdown('<div class="disclaimers">', unsafe_allow_html=True)
    st.write(
        "**Disclaimers:** Estimates only. Subject to credit approval, taxes, fees, and final dealer terms. Contact for details."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    vehicle_info = {
        "year": st.session_state.get("model_year", "N/A"),
        "make": st.session_state.get("make", "N/A"),
        "model": st.session_state.get("model", "N/A"),
        "trim": st.session_state.get("trim", "N/A"),
        "msrp": st.session_state.get("msrp", 0.0),
        "vin": st.session_state.get("vin", "N/A"),
    }
    try:
        pdf_buffer = generate_quote_pdf(
            selected_options,
            tax_rate,
            base_down,
            customer_name,
            vehicle_info,
        )
    except RuntimeError as e:
        st.error(str(e))
    else:
        st.download_button(
            "Download Quote PDF",
            pdf_buffer,
            "lease_quote.pdf",
            "application/pdf",
            key="export_pdf_main",
        )
