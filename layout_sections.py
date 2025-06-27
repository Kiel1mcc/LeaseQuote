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
        trade_value = st.number_input("Trade-in Value ($)", min_value=0.0, value=0.0, step=100.0)
        default_money_down = st.number_input("Customer Cash Down ($)", min_value=0.0, value=0.0, step=100.0)
        apply_markup = st.checkbox("Apply Money Factor Markup (+0.0004)", value=False)
        st.session_state['apply_markup'] = apply_markup

    with st.expander("Filters & Sorting", expanded=True):
        sort_options = {
            "Lowest Payment": "payment",
            "Lowest Term": "term",
            "Lowest Mileage": "mileage",
            "Most Lease Cash Available": "available_lease_cash",
        }
        sort_by = st.selectbox("Sort by:", list(sort_options.keys()))
        term_filter = st.multiselect(
            "Filter by Term:",
            sorted(list(set(opt['term'] for opt in quote_options))),
            default=sorted(list(set(opt['term'] for opt in quote_options))),
        )
        mileage_filter = st.multiselect(
            "Filter by Mileage:",
            sorted(list(set(opt['mileage'] for opt in quote_options))),
            default=sorted(list(set(opt['mileage'] for opt in quote_options))),
        )

    with st.expander("Quote Summary", expanded=True):
        st.write(f"**Selected Quotes:** {len(st.session_state.selected_quotes)}/3")
        if st.session_state.selected_quotes:
            st.write("**Selected Options:**")
            for quote_key in st.session_state.selected_quotes:
                parts = quote_key.split('_')
                st.write(f"• {parts[0]} months, {int(parts[1]):,} mi/yr")

        if st.button("Clear All Selections", type="secondary"):
            st.session_state.selected_quotes = []
            st.rerun()

    return trade_value, default_money_down, sort_by, term_filter, mileage_filter


def render_quote_card(option, option_key, trade_value, default_money_down, tax_rate):
    """Display a single quote card."""
    is_selected = option_key in st.session_state.selected_quotes
    bg_style = (
        "background: #e0f2fe; border: 2px solid #0284c7;"
        if is_selected else
        "background: white; border: 1px solid #e6e9ef;"
    )

    st.markdown(
        f"""
        <div style="{bg_style} border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f'<p class="term-mileage">{option["term"]} Months | {option["mileage"]:,} mi/yr</p>', unsafe_allow_html=True)

    new_selling_price = st.number_input(
        "Selling Price ($)",
        value=float(option['selling_price']),
        key=f"sp_{option_key}",
        step=100.0,
    )
    new_lease_cash = st.number_input(
        f"Lease Cash Used (Max: ${option['available_lease_cash']:,.2f})",
        min_value=0.0,
        max_value=float(option['available_lease_cash']),
        value=float(option['lease_cash_used']),
        key=f"lc_{option_key}",
        step=100.0,
    )

    payment_data = calculate_option_payment(
        new_selling_price, new_lease_cash, option['residual_value'],
        option['money_factor'], option['term'], trade_value, default_money_down, tax_rate
    )

    st.markdown(f'<div class="payment-highlight">${payment_data["payment"]:.2f}/mo</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="caption-text">Base: ${payment_data["base_payment"]:.2f} + Tax: ${payment_data["tax_payment"]:.2f}</p>', unsafe_allow_html=True)

    button_text = "Remove" if is_selected else "Select"
    button_type = "secondary" if is_selected else "primary"
    if st.button(button_text, key=f"action_{option_key}", type=button_type):
        if is_selected:
            st.session_state.selected_quotes.remove(option_key)
        else:
            if len(st.session_state.selected_quotes) < 3:
                st.session_state.selected_quotes.append(option_key)
            else:
                st.warning("Maximum 3 quotes can be selected")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
