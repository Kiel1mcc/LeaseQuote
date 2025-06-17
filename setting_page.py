import streamlit as st

def show_settings() -> None:
    # Initialize defaults if first run
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "default_county": "Adams",
            "counties": ["Adams", "Boulder", "Denver"],    # ← replace with your real list
            "default_tier": "Tier 1",
            "credit_tiers": ["Tier 1", "Tier 2", "Tier 3"],
            "auto_apply_lease_cash": False,
            "money_factor_markup": 0.0,
            "enable_debug": False,
        }

    # Now render the controls into the main pane
    st.selectbox(
        "Default Tax County",
        st.session_state.settings["counties"],
        index=st.session_state.settings["counties"].index(
            st.session_state.settings["default_county"]
        ),
        key="default_county",
    )
    st.selectbox(
        "Default Credit Tier",
        st.session_state.settings["credit_tiers"],
        index=st.session_state.settings["credit_tiers"].index(
            st.session_state.settings["default_tier"]
        ),
        key="default_tier",
    )
    st.checkbox(
        "Auto-apply Lease Cash",
        value=st.session_state.settings["auto_apply_lease_cash"],
        key="auto_apply_lease_cash",
    )
    st.number_input(
        "Money Factor Markup",
        min_value=0.0,
        max_value=1.0,
        step=0.0001,
        value=st.session_state.settings["money_factor_markup"],
        key="money_factor_markup",
    )
    st.checkbox(
        "Enable Debug Logging",
        value=st.session_state.settings["enable_debug"],
        key="enable_debug",
    )
