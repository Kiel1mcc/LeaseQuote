import streamlit as st

def show_settings() -> None:
    """Display the settings sidebar (always called at app start)."""

    # Initialize settings in session_state
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "counties": ["Adams", "Boulder", "Denver"],
            "default_county": "Adams",
            "credit_tiers": ["Tier 1 (740+)", "Tier 2 (720–739)", "Tier 3 (700–719)"],
            "default_tier": "Tier 1 (740+)",
            "auto_apply_lease_cash": False,
            "money_factor_markup": 0.0,
            "enable_debug": False,
        }

    st.sidebar.title("Settings")

    # County dropdown
    counties = st.session_state.settings["counties"]
    default_county = st.sidebar.selectbox(
        "Default Tax County",
        counties,
        index=counties.index(st.session_state.settings["default_county"])
    )

    # Tier dropdown
    tiers = st.session_state.settings["credit_tiers"]
    default_tier = st.sidebar.selectbox(
        "Default Credit Tier",
        tiers,
        index=tiers.index(st.session_state.settings["default_tier"])
    )

    # Other controls
    auto_apply = st.sidebar.checkbox(
        "Auto-apply Lease Cash",
        value=st.session_state.settings["auto_apply_lease_cash"]
    )
    mf_markup = st.sidebar.number_input(
        "Money Factor Markup",
        min_value=0.0, max_value=0.1,
        value=st.session_state.settings["money_factor_markup"],
        step=0.0001
    )
    debug_on = st.sidebar.checkbox(
        "Enable Debug Display",
        value=st.session_state.settings["enable_debug"]
    )

    # Save back to session
    st.session_state.settings.update({
        "default_county": default_county,
        "default_tier": default_tier,
        "auto_apply_lease_cash": auto_apply,
        "money_factor_markup": mf_markup,
        "enable_debug": debug_on,
    })

    if st.sidebar.button("Reset to Defaults"):
        st.session_state.settings.clear()
        st.experimental_rerun()
