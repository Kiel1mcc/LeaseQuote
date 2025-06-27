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
    border: none !important;
    border-radius: 0 !important;
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

/* Right sidebar styling */
.right-sidebar {
    background-color: #f0f2f6 !important;
    padding: 1rem !important;
    border-radius: 0.5rem !important;
    border: 1px solid #e1e5e9 !important;
}
.right-sidebar div[data-testid="stExpander"] {
    background-color: transparent !important;
    border: none !important;
    margin-bottom: 0.5rem !important;
}
.right-sidebar input,
.right-sidebar div[data-testid="stSelectbox"] > div,
.right-sidebar div[data-testid="stMultiSelect"] div[data-baseweb="select"],
.right-sidebar div[data-testid="stMultiSelect"] [role="combobox"],
.right-sidebar button {
    background-color: white !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem !important;
}
.right-sidebar div[data-testid="stCheckbox"] {
    background-color: transparent !important;
    padding: 0 !important;
    border: none !important;
    margin: 0.25rem 0 !important;
}

/* Match far right column */
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

/* DEBUG STYLING FOR QUOTE CARDS */
.quote-card, .selected-quote {
    border: 3px dashed red !important;
    position: relative;
    padding: 1rem;
    margin-bottom: 1rem;
}
.quote-card::before, .selected-quote::before {
    content: "QUOTE CARD CONTAINER";
    position: absolute;
    top: -1.25rem;
    left: 0;
    font-size: 0.75rem;
    font-weight: bold;
    color: red;
}
.quote-card .term-mileage {
    border: 2px dotted orange;
    padding: 0.25rem;
}
.quote-card .term-mileage::before {
    content: "TERM LABEL";
    font-size: 0.65rem;
    color: orange;
    display: block;
}
.quote-card div[data-testid="stNumberInput"] {
    border: 2px solid green;
    padding: 0.25rem;
}
.quote-card div[data-testid="stNumberInput"]::before {
    content: "NUMBER INPUT";
    font-size: 0.65rem;
    color: green;
    display: block;
}
.quote-card .payment-highlight {
    border: 2px solid blue;
    background-color: #e0f7ff !important;
    position: relative;
}
.quote-card .payment-highlight::before {
    content: "PAYMENT HIGHLIGHT";
    position: absolute;
    top: -1.25rem;
    left: 0;
    font-size: 0.65rem;
    color: blue;
}

/* Caption and inner spacing */
.caption-text {
    font-size: 0.875rem;
    color: #6b7280;
    text-align: center;
    margin: 0;
}
section.main div[data-testid="block-container"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    padding: 0 !important;
}
div[data-testid="stHorizontalBlock"] {
    margin: 0 !important;
}
</style>
"""
