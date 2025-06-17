import streamlit as st

# Initialize session state for settings if not already present
if 'settings' not in st.session_state:
    st.session_state.settings = {
        "default_county": "Adams",
        "default_tier": "Tier 1",
        "auto_apply_lease_cash": False,
        "money_factor_markup": 0.0,
        "enable_debug": False
    }

# Sidebar for settings page
st.sidebar.title("Settings")

# Tax County dropdown
counties = ["Adams", "Boulder", "Denver"]  # Replace with your actual list
default_county = st.sidebar.selectbox(
    "Default Tax County",
    counties,
    index=counties.index(st.session_state.settings["default_county"]),
    help="Select the default county for tax calculations."
)

# Tier dropdown
tiers = ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"]
default_tier = st.sidebar.selectbox(
    "Default Tier",
    tiers,
    index=tiers.index(st.session_state.settings["default_tier"]),
    help="Select the default tier for lease calculations."
)

# Auto-apply lease cash checkbox
auto_apply_lease_cash = st.sidebar.checkbox(
    "Auto-apply Lease Cash",
    value=st.session_state.settings["auto_apply_lease_cash"],
    help="If checked, lease cash will be automatically applied."
)

# Money Factor Markup input
money_factor_markup = st.sidebar.number_input(
    "Money Factor Markup",
    min_value=0.0,
    max_value=0.1,
    value=st.session_state.settings["money_factor_markup"],
    step=0.0001,
    help="Add a markup to the base money factor (e.g., 0.001 increases the rate)."
)

# Enable Debug Display checkbox
enable_debug = st.sidebar.checkbox(
    "Enable Debug Display",
    value=st.session_state.settings["enable_debug"],
    help="If checked, additional debug information will be displayed."
)

# Save settings to session state
st.session_state.settings.update({
    "default_county": default_county,
    "default_tier": default_tier,
    "auto_apply_lease_cash": auto_apply_lease_cash,
    "money_factor_markup": money_factor_markup,
    "enable_debug": enable_debug
})

# Reset to defaults button
if st.sidebar.button("Reset to Defaults"):
    st.session_state.settings = {
        "default_county": "Adams",
        "default_tier": "Tier 1",
        "auto_apply_lease_cash": False,
        "money_factor_markup": 0.0,
        "enable_debug": False
    }
    st.experimental_rerun()

# Example main app integration (uncomment and adapt as needed)
"""
st.title("Lease Quote Calculator")
st.write("Settings applied from the sidebar:")
st.write(f"Default County: {st.session_state.settings['default_county']}")
st.write(f"Default Tier: {st.session_state.settings['default_tier']}")
st.write(f"Auto-apply Lease Cash: {st.session_state.settings['auto_apply_lease_cash']}")
st.write(f"Money Factor Markup: {st.session_state.settings['money_factor_markup']}")
if st.session_state.settings['enable_debug']:
    st.write("Debug mode is ON: Showing extra details here.")
"""
