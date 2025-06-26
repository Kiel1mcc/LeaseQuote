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
    @media (max-width: 768px) {
        .three-column .stContainer {
            flex-direction: column;
        }
        .three-column .stContainer > div {
            width: 100%;
        }
        .main-content {
            padding: 0;
        }
    }
    @media print {
        .no-print { display: none !important; }
    }
</style>
""", unsafe_allow_html=True)

# Set page config to minimize header and padding
st.set_page_config(page_title="Lease Quote Tool", layout="wide", initial_sidebar_state="expanded")

# ... all unchanged code above ...

# Display quote options in three columns
st.markdown('<div class="main-content">', unsafe_allow_html=True)



st.subheader(f"Available Lease Options ({len(filtered_options)} options)")
with st.container():
    columns = st.columns(3, gap="small")
    for i, option in enumerate(filtered_options):
        with columns[i % 3]:
            option_key = f"{option['term']}_{option['mileage']}_{option['index']}"
            is_selected = option_key in st.session_state.selected_quotes
            card_class = "selected-quote" if is_selected else "quote-card"

            with st.container():
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

# ... continue with the quote generation section ...
