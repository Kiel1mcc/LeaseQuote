BASE_CSS = """
<style>
/* Input Styling Fixes */
div[data-testid="stSelectbox"] > div {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
    box-shadow: none !important;
}
div[data-testid="stNumberInput"] {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
    box-shadow: none !important;
}
div[data-testid="stCheckbox"] {
    background-color: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0.25rem 0 !important;
}
div[data-testid="stMultiSelect"] div[data-baseweb="select"] {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
}
div[data-testid="stMultiSelect"] [role="combobox"] {
    background-color: white !important;
    border: none !important;
    box-shadow: none !important;
}
div[data-testid="stMultiSelect"] div[data-baseweb="tag"] {
    background-color: #f9fafb !important;
    color: #1f2937 !important;
    border-radius: 0.25rem !important;
    margin: 0.1rem !important;
}
/* Right sidebar styling to match left sidebar */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
    background-color: #f0f2f6 !important;
    padding: 1rem !important;
    border-radius: 0.5rem !important;
    border: 1px solid #e1e5e9 !important;
}

/* Keep expanders transparent with gray background */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stExpander"] {
    background-color: transparent !important;
    border: none !important;
    margin-bottom: 0.5rem !important;
}

/* White backgrounds for all input fields */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) input {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
}

/* White backgrounds for selectbox */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stSelectbox"] > div {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
}

/* White backgrounds for multiselect fields */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMultiSelect"] div[data-baseweb="select"] {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
}

div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMultiSelect"] [role="combobox"] {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
}

/* Transparent checkbox (no white box) */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stCheckbox"] {
    background-color: transparent !important;
    padding: 0 !important;
    border: none !important;
    margin: 0.25rem 0 !important;
}

/* White backgrounds for buttons */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
}

/* Quote card styling */
.quote-card {
    background: white;
    border: 1px solid #e6e9ef;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.selected-quote {
    background: #e0f2fe;
    border: 2px solid #0284c7;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.term-mileage {
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
}

.payment-highlight {
    font-size: 1.5rem;
    font-weight: 700;
    color: #059669;
    text-align: center;
    margin: 0.5rem 0;
}

.caption-text {
    font-size: 0.875rem;
    color: #6b7280;
    text-align: center;
    margin-bottom: 0.5rem;
}
</style>
"""
