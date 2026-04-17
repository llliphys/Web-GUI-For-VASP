"""
styles.py — Global CSS styles for the VASP GUI application.

All shared CSS rules (sidebar, buttons, cards, headers, footer, etc.)
are defined here as a single constant so that every page can inject
them with one call to st.markdown(COMMON_STYLES, unsafe_allow_html=True).
"""

# ---------------------------------------------------------------------------
# Common CSS styles shared across all pages
# ---------------------------------------------------------------------------
COMMON_STYLES = """
<style>
    /* ── Sidebar: hide auto-generated page links ────────────────────── */
    section[data-testid="stSidebar"] > div > div > div > ul,
    section[data-testid="stSidebar"] div[data-testid="stVerticalPageNav"],
    section[data-testid="stSidebar"] nav,
    section[data-testid="stSidebar"] [data-testid="stPageNav"],
    [data-testid="stSidebarContent"] > div > ul {
        display: none !important;
        visibility: hidden !important;
    }

    /* ── Sidebar: borderless buttons ────────────────────────────────── */
    section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] button {
        border: 0px !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        -webkit-box-shadow: none !important;
        background-color: transparent !important;
    }
    .stButton > button {
        border: none !important;
        background: none !important;
        padding: 0 !important;
        font-weight: normal !important;
        color: inherit !important;
        box-shadow: none !important;
    }
    .stButton > button:hover {
        background: none !important;
        color: inherit !important;
        border: none !important;
        box-shadow: none !important;
    }
    .stButton > button:focus {
        border: none !important;
        box-shadow: none !important;
    }
    .stButton > button:active {
        border: none !important;
        box-shadow: none !important;
    }

    /* ── Page header / sub-header ───────────────────────────────────── */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #2E86AB;
        text-align: left;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: left;
        margin-bottom: 2rem;
    }

    /* ── Footer ─────────────────────────────────────────────────────── */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        text-align: center;
        padding: 1rem;
        background-color: #f8f9fa;
        border-top: 1px solid #e9ecef;
        font-size: 0.9rem;
        color: #6c757d;
    }

    /* ── Feature card (home page) ───────────────────────────────────── */
    .feature-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #2E86AB;
    }

    /* ── Step number badge (home page quick-start) ──────────────────── */
    .step-number {
        background-color: #2E86AB;
        color: white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 10px;
    }

    /* ── Sidebar nav items ──────────────────────────────────────────── */
    .nav-item {
        padding: 0.6rem 1rem;
        border-radius: 5px;
        margin-bottom: 0.3rem;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .nav-item:hover {
        background-color: #e0e5eb;
    }
    .nav-item.active {
        background-color: #2E86AB;
        color: white;
    }

    /* ── Sidebar button fine-tuning ─────────────────────────────────── */
    section[data-testid="stSidebar"] button {
        border: 0px !important;
        outline: none !important;
        outline-offset: 0px !important;
        box-shadow: none !important;
        -webkit-box-shadow: none !important;
        background-color: transparent !important;
        padding: 0px !important;
        color: inherit !important;
        font-weight: normal !important;
        text-align: left !important;
        width: 100% !important;
        margin: 0px !important;
    }
    section[data-testid="stSidebar"] button:hover {
        border: 0px !important;
        background-color: transparent !important;
        color: #2E86AB !important;
    }
    section[data-testid="stSidebar"] button:focus {
        border: 0px !important;
        outline: none !important;
        outline-offset: 0px !important;
    }
    section[data-testid="stSidebar"] button:active {
        border: 0px !important;
        outline: none !important;
    }
    section[data-testid="stSidebar"] [data-testid="stButton"] {
        border: 0px !important;
    }

    /* ── Sidebar gap removal ───────────────────────────────────────── */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 0rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0rem !important;
    }
    [data-testid="stSidebar"] > div {
        gap: 0rem !important;
    }
    section[data-testid="stSidebar"] > div > div {
        gap: 0rem !important;
    }

    /* ── Section headers ───────────────────────────────────────────── */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2E86AB;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #2E86AB;
    }

    /* ── Input section card ────────────────────────────────────────── */
    .input-section {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    /* ── File preview (dark terminal style) ────────────────────────── */
    .file-preview {
        background-color: #2c3e50;
        color: #ecf0f1;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        max-height: 200px;
        overflow-y: auto;
    }

    /* ── Tab buttons ───────────────────────────────────────────────── */
    .tab-btn {
        padding: 10px 20px;
        border: 1px solid #ddd;
        border-radius: 5px 5px 0 0;
        cursor: pointer;
        margin-right: 5px;
    }

    /* ── Folder / file cards (project browser) ─────────────────────── */
    .folder-card {
        background-color: #f0f4f8;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .folder-card:hover { background-color: #dde4eb; }
    .item-row { display: flex; align-items: center; }
    .folder-icon { font-size: 2.5rem; margin-right: 1rem; }
    .file-icon { font-size: 2.5rem; margin-right: 1rem; }
    .item-text { font-size: 1.5rem; }

    /* ── Global button font size ───────────────────────────────────── */
    button {
        font-size: 1.4em !important;
    }
</style>
"""
