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

/* Quote card retainer wraps each quote for spacing */
.quote-card-retainer {
    border: 1px solid #d1d5db;
    border-radius: 0.75rem;
    padding: 1rem;
    margin-bottom: 1rem;
    background-color: #ffffff;
}

/* Quote card styling */
.quote-card,
.selected-quote {
    background: white;
    border: 2px solid #1e3a8a;
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 0;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.quote-card div[data-testid="stNumberInput"],
.quote-card div[data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}

.term-mileage {
    font-weight: 600;
    color: #374151;
    margin: 0;
}

.payment-highlight {
    font-size: 1.5rem;
    font-weight: 700;
    color: #059669;
    text-align: center;
    margin: 0;
    background-color: #f0fff4;
    padding: 0.25rem;
    border-radius: 0.375rem;
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
