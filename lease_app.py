import streamlit as st
from setting_page import show_settings
from lease_calculations import calculate_base_and_monthly_payment as calculate_payment

def show_quote_page():
    st.header("🔑 Lease Quote")

    vin = st.text_input("Enter VIN or Stock #")
    county = st.selectbox(
        "Select Tax County",
        st.session_state.settings["counties"],
        index=st.session_state.settings["counties"].index(
            st.session_state.settings["default_county"]
        ),
    )
    credit_tier = st.selectbox(
        "Credit Tier",
        st.session_state.settings["credit_tiers"],
        index=st.session_state.settings["credit_tiers"].index(
            st.session_state.settings["default_tier"]
        ),
    )
    lease_cash = st.checkbox(
        "Apply Lease Cash",
        value=st.session_state.settings["auto_apply_lease_cash"],
    )
    down = st.number_input(
        "Down Payment",
        min_value=0.0,
        step=100.0,
        value=0.0,
    )

    if st.button("Calculate"):
        base, monthly = calculate_payment(
            vin, county, credit_tier, lease_cash, down
        )
        st.subheader(f"Monthly Payment: ${monthly:,.2f}")
        st.write(f"**Base Payment:** ${base:,.2f}")

def main():
    st.sidebar.title("Main Menu")
    page = st.sidebar.radio("Go to", ["Quote", "Settings"])

    if page == "Settings":
        st.header("⚙️ Settings")
        show_settings()
    else:
        show_quote_page()

if __name__ == "__main__":
    main()
