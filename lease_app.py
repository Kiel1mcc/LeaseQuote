import streamlit as st
from setting_page import show_settings
from lease_calculations import calculate_base_and_monthly_payment as calculate_payment

def show_quote_page():
    st.header("🔑 Lease Quote")

    vin = st.text_input("Enter VIN or Stock #")
    county = st.selectbox(
        "Select Tax County",
        st.session_state.settings["counties"],
        index=st.session_state.settings["counties"].index(st.session_state.settings["default_county"])
    )
    credit_tier = st.selectbox(
        "Credit Tier",
        st.session_state.settings["credit_tiers"],
        index=st.session_state.settings["credit_tiers"].index(st.session_state.settings["default_tier"])
    )
    lease_cash = st.checkbox(
        "Apply Lease Cash",
        value=st.session_state.settings["auto_apply_lease_cash"]
    )
    down = st.number_input(
        "Down Payment",
        min_value=0.0, step=100.0, value=0.0
    )

    if st.button("Calculate"):
        # replace these dummy args with your actual lookup logic:
        S = 30000      # Sale price
        RES = 13020.8  # Residual
        W = 48         # Months
        F = 0.00295    # Money factor
        M = down       # Down payment
        Q = None
        B = None; K = None; U = None; tau = 0.05

        result = calculate_payment(S, RES, W, F, M, Q, B, K, U, tau)
        st.subheader("### Quote Results")
        st.json(result)

def main():
    # ensure settings sidebar is built
    show_settings()

    st.sidebar.title("Main Menu")
    page = st.sidebar.radio("Go to", ["Quote", "Settings"], index=0)

    if page == "Quote":
        show_quote_page()
    # if they pick Settings, the sidebar is already showing the controls

if __name__ == "__main__":
    main()
