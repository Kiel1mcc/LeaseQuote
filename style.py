BASE_CSS = """
<style>
/* Existing styles remain... */

/* Enhanced quote card */
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
    transition: box-shadow 0.2s;
}
.quote-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.lowest-payment {
    border-color: #059669 !important;  /* Green highlight for lowest */
}

/* Print view styling */
/* Print view styling */
@media print {
    .right-sidebar, button, [data-testid="stSidebar"], [data-testid="stHeader"], input, .stButton, .stRadio {
        display: none !important;
    }
    body {
        font-size: 12pt;
        margin: 0.5in;
        color: black;
    }
    .quote-summary {
        page-break-inside: avoid;
        border: 1px solid #ddd;
        padding: 1rem;
        border-radius: 0.25rem;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: right;
    }
    th {
        background-color: #f2f2f2;
        text-align: center;
    }
    .signature-section {
        margin-top: 2rem;
        border-top: 1px solid #ddd;
        padding-top: 1rem;
        font-style: italic;
    }
    .disclaimers {
        font-size: 10pt;
        font-style: italic;
        margin-top: 1rem;
    }
}

/* On-screen styling for print page */
.quote-summary {
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 0.5rem;
    padding: 1.5rem;
    margin: 1rem 0;
}
.signature-section {
    margin-top: 2rem;
    border-top: 1px dashed #d1d5db;
    padding-top: 1rem;
    font-style: italic;
}

/* Responsive grid: 3 cols desktop, 2 tablet, 1 mobile */
@media (min-width: 1024px) {
    div[data-testid="stHorizontalBlock"] {
        grid-template-columns: repeat(3, 1fr) !important;
    }
}
@media (min-width: 768px) and (max-width: 1023px) {
    div[data-testid="stHorizontalBlock"] {
        grid-template-columns: repeat(2, 1fr) !important;
    }
}
@media (max-width: 767px) {
    div[data-testid="stHorizontalBlock"] {
        grid-template-columns: 1fr !important;
    }
    .quote-card-retainer {
        margin-bottom: 1.5rem !important;
    }
}

/* Spinner centering */
.stSpinner {
    text-align: center;
    margin: 1rem 0;
}
</style>
"""
