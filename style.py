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
@media print {
    .right-sidebar, button, [data-testid="stSidebar"], [data-testid="stHeader"] {
        display: none !important;
    }
    .quote-card-retainer, .quote-card {
        page-break-inside: avoid;
    }
    body {
        font-size: 12pt;
        margin: 0;
    }
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
