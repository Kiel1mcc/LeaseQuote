import streamlit as st

# default values used across the application
DEFAULT_SETTINGS = {
    "default_county": "Adams",
    "counties": [
        "Adams",
        "Allen",
        "Ashland",
        "Ashtabula",
        "Athens",
        # …and all your counties
    ],
    "tax_rates": {
        "Adams": 7.25,
        "Allen": 6.85,
        "Ashland": 7.00,
        # …
    },
    "money_factors": {
        # (term, mileage): base money factor
        (36, 10000): 0.00256,
        (36, 12000): 0.00275,
        # …
    },
    "residuals": {
        (36, 10000): 60,  # percent
        (36, 12000): 58,  # percent
        # …
    },
    "money_factor_markup": 0.0000,
}


def show_settings() -> None:
    """Display the settings sidebar and handle reset functionality."""

    # Initialize session state for settings if not already present
    if "settings" not in st.session_state or not st.session_state.settings:
        st.session_state.settings = DEFAULT_SETTINGS.copy()

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
        st.session_state.settings = DEFAULT_SETTINGS.copy()
        st.experimental_rerun()
