# lease_app.py
import streamlit as st
from setting_page import show_settings
from lease_calculations import calculate_base_and_monthly_payment as calculate_payment

def init_session_settings():
    """
    Ensure we always have a settings dict in session_state
    and all the keys we expect.
    """
    if "settings" not in st.session_state:
        st.session_state.settings = {}

    # default to empty lists / sensible defaults so we never KeyError
    st.session_state.settings.setdefault("counties", [])
    st.session_state.settings.setdefault("credit_tiers", [])
    st.session_state.settings.setdefault("default_county", 0)
    st.session_state.settings.setdefault("default_tier", 0)
    st.session_state.settings.setdefault("auto_apply_lease_cash", False)

def show_quote_page():
    """
    Main quote page: gather inputs and display results.
    """
    st.title("🔑 Lease Quote")

    # If the user hasn't picked any counties yet, prompt them:
    if not st.session_state.settings["counties"]:
        st.warning("⚠️ No tax‐counties configured yet. Please go to **Settings** and select at least one county.")
        return

    vin = st.text_input("Enter VIN or Stock #")

    county = st.selectbox(
        "Select Tax County",
        st.session_state.settings["counties"],
        index=st.session_state.settings["default_county"],
    )

    credit_tier = st.selectbox(
        "Credit Tier",
        st.session_state.settings["credit_tiers"],
        index=st.session_state.settings["default_tier"],
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

    rebate = st.number_input(
        "Rebate",
        min_value=0.0,
        step=100.0,
        value=0.0,
    )

    term = st.selectbox(
        "Term (months)",
        [36, 39, 48, 60],
        index=0,
    )

    mileage = st.selectbox(
        "Annual Mileage",
        [10_000, 12_000, 15_000, 20_000],
        index=0,
    )

    credit_score = st.slider(
        "Estimated Credit Score",
        min_value=300,
        max_value=850,
        value=700,
    )

    if st.button("Calculate"):
        # Call your calculation function
        base_payment, monthly_payment = calculate_payment(
            vin,
            county,
            credit_tier,
            lease_cash,
            down,
            rebate,
            term,
            mileage,
            credit_score,
        )

        # Display metrics
        st.metric("Base Payment", f"${base_payment:,.2f}")
        st.metric("Monthly Payment", f"${monthly_payment:,.2f}")

def main():
    # 1) Bootstrap our session_state.settings
    init_session_settings()

    # 2) Sidebar nav
    st.sidebar.title("Main Menu")
    page = st.sidebar.radio("Go to", ["Quote", "Settings"])

    # 3) Dispatch
    if page == "Settings":
        show_settings()
    else:
        show_quote_page()

if __name__ == "__main__":
    main()
