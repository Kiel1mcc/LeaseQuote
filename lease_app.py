import streamlit as st
st.write("🔥 Loaded lease_app.py v2 at", __file__)
import streamlit as st
from setting_page import show_settings, DEFAULT_SETTINGS
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
            st.session_state.settings["default_county"]
        ),
    )
    msrp = st.number_input("MSRP (Selling Price)", min_value=0.0, format="%.2f")
    money_down = st.number_input("Money Down", min_value=0.0, format="%.2f")
    rebate = st.number_input("Rebate", min_value=0.0, format="%.2f")
    term = st.selectbox("Term (months)", [24, 36, 48, 60], index=1)
    mileage = st.selectbox("Annual Mileage", [10000, 12000, 15000], index=0)
    credit_score = st.slider("Estimated Credit Score", 300, 850, 800)

    # look up tax rate from session_state
    tax_rate = st.session_state.settings["tax_rates"][county] / 100.0

    # look up base money factor & residual from session_state tables
    base_mf = st.session_state.settings["money_factors"][(term, mileage)]
    residual_pct = st.session_state.settings["residuals"][(term, mileage)] / 100.0

    # apply any global markup
    mf = base_mf + st.session_state.settings["money_factor_markup"]

    if st.button("Calculate Lease"):
        results = calculate_payment(
            msrp=msrp,
            money_factor=mf,
            residual_pct=residual_pct,
            term=term,
            mileage=mileage,
            tax_rate=tax_rate,
            money_down=money_down,
            rebate=rebate,
        )
        st.subheader("📊 Results")
        for label, val in results.items():
            st.write(f"**{label}:** ${val:,.2f}")

def main():
    # initialize settings on first run
    if "settings" not in st.session_state or not st.session_state.settings:
        st.session_state.settings = DEFAULT_SETTINGS.copy()
    # sidebar navigation
    st.sidebar.title("Main Menu")
    page = st.sidebar.radio("Go to", ["Quote", "Settings"])
    if page == "Settings":
        show_settings()
    else:
        show_quote_page()

if __name__ == "__main__":
    main()
