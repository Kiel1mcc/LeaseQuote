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
.right-sidebar {
    background-color: #f0f2f6 !important;
    padding: 1rem !important;
    border-radius: 0.5rem !important;
    border: 1px solid #e1e5e9 !important;
}

/* Keep expanders transparent with gray background */
.right-sidebar div[data-testid="stExpander"] {
    background-color: transparent !important;
    border: none !important;
    margin-bottom: 0.5rem !important;
}

/* White backgrounds for all input fields */
.right-sidebar input {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
}

/* White backgrounds for selectbox */
.right-sidebar div[data-testid="stSelectbox"] > div {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
}

/* White backgrounds for multiselect fields */
.right-sidebar div[data-testid="stMultiSelect"] div[data-baseweb="select"] {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
}

.right-sidebar div[data-testid="stMultiSelect"] [role="combobox"] {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
}

/* Transparent checkbox (no white box) */
.right-sidebar div[data-testid="stCheckbox"] {
    background-color: transparent !important;
    padding: 0 !important;
    border: none !important;
    margin: 0.25rem 0 !important;
}

/* White backgrounds for buttons */
.right-sidebar button {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
}

/* Far right column styling to match sidebar */
section.main div[data-testid="block-container"] > div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(3) {
    background-color: #f0f2f6 !important;
    padding: 1rem !important;
    border-radius: 0.5rem !important;
    border: 1px solid #e1e5e9 !important;
}

section.main div[data-testid="block-container"] > div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(3) input,
section.main div[data-testid="block-container"] > div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(3) div[data-testid="stSelectbox"] > div,
section.main div[data-testid="block-container"] > div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(3) div[data-testid="stMultiSelect"] div[data-baseweb="select"],
section.main div[data-testid="block-container"] > div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(3) div[data-testid="stMultiSelect"] [role="combobox"],
section.main div[data-testid="block-container"] > div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(3) button {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
}

section.main div[data-testid="block-container"] > div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(3) div[data-testid="stCheckbox"] {
    background-color: transparent !important;
    padding: 0 !important;
    border: none !important;
    margin: 0.25rem 0 !important;
}

/* Quote card styling */
.quote-card,
.selected-quote {
    background: white;
    border: 2px solid #e6e9ef;
    border-radius: 0.5rem;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    gap: 1rem;
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
    background-color: #f0fff4;
    padding: 0.5rem;
    border-radius: 0.375rem;
}

.caption-text {
    font-size: 0.875rem;
    color: #6b7280;
    text-align: center;
    margin-bottom: 0.5rem;
}
</style>
"""

### Notes:
- **Boxing Options**: The `.quote-card` and `.selected-quote` classes in `style.py` now use a thicker border (`2px`), increased padding (`1.5rem`), and a larger margin (`1.5rem`) to create a more defined box around each option. The `display: flex; flex-direction: column; gap: 1rem;` ensures a clean vertical layout.
- **Monthly Payment**: The `render_quote_card` function now calculates and displays the monthly payment using `calculate_option_payment`, styled with `.payment-highlight` for emphasis.
- **No Changes to `lease_app.py`**: The main app logic remains unchanged as the updates are handled in the layout and style files.

Please ensure the `utils.py` file contains the `calculate_option_payment` function, or let me know if you need help implementing it. Test the updated code and let me know if you'd like further adjustments!
