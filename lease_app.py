import streamlit as st
from setting_page import show_settings
from lease_calculations import calculate_payment


def show_quote_page():
    """
    Main quote page: gather inputs and display lease calculation results.
    """
    st.title("🔑 Lease Quote")

    vin = st.text_input("Enter VIN or Stock #")
    county = st.selectbox(
        "Select Tax County",
        st.session_state.settings["counties"],
        index=st.session_state.settings["counties"].index(
            st.session_state.settings.get("default_county", st.session_state.settings["counties"][0])
        ),
    )
    credit_tier = st.selectbox(
        "Credit Tier",
        st.session_state.settings["credit_tiers"],
        index=st.session_state.settings["credit_tiers"].index(
            st.session_state.settings.get("default_tier", st.session_state.settings["credit_tiers"][0])
        ),
    )
    lease_cash = st.checkbox(
        "Apply Lease Cash",
        value=st.session_state.settings.get("auto_apply_lease_cash", False),
    )
    down_payment = st.number_input(
        "Down Payment", min_value=0.0, step=100.0, value=0.0,
        help="Amount of cash down to reduce cap cost"
    )

    if st.button("Calculate"):
        # Call into your existing lease calculation logic
        result = calculate_payment(
            vin=vin,
            county=county,
            credit_tier=credit_tier,
            lease_cash=lease_cash,
            down_payment=down_payment,
        )
        st.subheader("### Quote Results")
        # You can format the output as you like: table, JSON, or cards
        st.json(result)


def main():
    # Initialize default settings if not present
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "counties": ["Adams", "Boulder", "Denver"],
            "default_county": "Adams",
            "credit_tiers": ["Tier 1 (740+)", "Tier 2 (720-739)", "Tier 3 (700-719)"],
            "default_tier": "Tier 1 (740+)",
            "auto_apply_lease_cash": False,
        }

    # Sidebar navigation
    st.sidebar.title("Main Menu")
    page = st.sidebar.radio("Go to", ["Quote", "Settings"] )

    if page == "Settings":
        show_settings()
        if st.sidebar.button("← Back to Quote"):
            page = "Quote"
    if page == "Quote":
        show_quote_page()


if __name__ == "__main__":
    main()
