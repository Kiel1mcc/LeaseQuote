import streamlit as st
import pandas as pd

def show_settings() -> None:
    """Display the settings sidebar and handle reset functionality."""
    county_rates_df = pd.read_csv("County_Tax_Rates.csv")
    county_rates_df.columns = county_rates_df.columns.str.strip()
    counties = county_rates_df["County"].tolist()
    tax_rates = dict(zip(county_rates_df["County"], county_rates_df["Tax Rate"]))
    DEFAULT_COUNTY = "Marion"

    defaults = {
        "default_county": DEFAULT_COUNTY,
        "counties": counties,
        "tax_rates": tax_rates,
        "money_factors": {
            # (term, mileage): base money factor
            (36, 10000): 0.00256,
            (36, 12000): 0.00275,
            # …
        },
        "residuals": {
            (36, 10000): 60,    # percent
            (36, 12000): 58,    # percent
            # …
        },
        "money_factor_markup": 0.0000,
    }

    # Initialize session state for settings if not already present
    if "settings" not in st.session_state or not st.session_state.settings:
        st.session_state.settings = defaults.copy()

    st.header("⚙️ Settings")
    s = st.session_state.settings

    s["default_county"] = st.selectbox(
        "Default County", s["counties"], index=s["counties"].index(s["default_county"])
    )
    s["money_factor_markup"] = st.number_input(
        "Global Money Factor Mark-up",
        min_value=0.0,
        format="%.4f",
        value=s["money_factor_markup"],
    )

    st.markdown("---")
    if st.button("Reset to Defaults"):
        st.session_state.settings = {}
        st.experimental_rerun()
