# styles.py
# Description: Contains the application's complete stylesheet for the dark theme.
# Changes:
# - FIXED: Corrected all f-string formatting errors by escaping literal
#   CSS curly braces (e.g., changing `{` to `{{` and `}` to `}}`).
# - ADDED: Styles for the enhanced Backup History tab, including alternating row colors,
#          status indicators, and refined action buttons.

class Style:
    # --- Dark Theme Color Palette ---
    DARK_BG_PRIMARY = "#10141A"
    DARK_BG_SECONDARY = "#1A2028"
    DARK_BG_TERTIARY = "#2C3A4F"
    DARK_BORDER = "#2C3A4F"
    DARK_ACCENT_PRIMARY = "#00E5FF"
    DARK_ACCENT_HOVER = "#80F2FF"
    DARK_ACCENT_PRESSED = "#00B8CC"
    DARK_TEXT_PRIMARY = "#EBF2FC"
    DARK_TEXT_SECONDARY = "#9EB0C8"
    DARK_TEXT_DISABLED = "#5C6A7F"
    
    # Status Colors
    STATUS_GREEN = "#4CAF50"
    STATUS_YELLOW = "#FFC107"
    STATUS_RED = "#F44336"

    DARK_THEME_STYLESHEET = f"""
    * {{
        font-family: "Roboto", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 14px;
        color: {DARK_TEXT_PRIMARY};
        border: none;
        outline: none;
    }}
    
    QMainWindow {{
        background-color: {DARK_BG_PRIMARY};
    }}

    /* --- Sidebar Styles --- */
    #sidebar {{
        background-color: {DARK_BG_SECONDARY};
        border-right: 1px solid {DARK_BORDER};
    }}
    #logoLabel {{
        font-size: 28px;
        font-weight: 900;
        letter-spacing: 2px;
        color: {DARK_ACCENT_PRIMARY};
        padding: 10px;
    }}
    #navList {{
        background-color: transparent;
    }}
    #navList::item {{
        padding: 14px 25px;
        color: {DARK_TEXT_SECONDARY};
        border-radius: 5px;
        margin: 4px 10px;
    }}
    #navList::item:hover {{
        background-color: {DARK_BG_TERTIARY};
        color: {DARK_TEXT_PRIMARY};
    }}
    #navList::item:selected {{
        background-color: {DARK_ACCENT_PRIMARY};
        color: #000000;
        font-weight: bold;
    }}
    #navList::item:selected:hover {{
        background-color: {DARK_ACCENT_HOVER};
    }}
    #navList QListWidgetItem::icon {{
        padding-right: 10px;
    }}

    /* --- Content Area Styles --- */
    #contentArea, #dashboardPage, #settingsPage, #devicesPage, #logsPage, #deviceDetailPage, QScrollArea, QScrollArea > QWidget > QWidget {{
        background-color: {DARK_BG_PRIMARY};
    }}
    #scrollArea {{
        border: none;
    }}
    
    /* --- General Widget Styles --- */
    QLabel {{
        background-color: transparent;
    }}
    QFrame#separator {{
        background-color: {DARK_BORDER};
        height: 1px;
        margin: 0px 15px;
    }}

    /* --- Page/Panel Titles --- */
    #pageTitle {{
        font-size: 26px;
        font-weight: bold;
        color: {DARK_TEXT_PRIMARY};
    }}
    #pageSubtext, #cardSubtext, #settingSubtext, #activitySubtext, #legendLabel, #tableSubtext {{
        color: {DARK_TEXT_SECONDARY};
        font-size: 13px;
    }}
    #panelTitle {{
        font-size: 18px;
        font-weight: bold;
        color: {DARK_TEXT_PRIMARY};
    }}

    /* --- Card & Panel Styles --- */
    #CardWidget, #PanelWidget, #SettingsCard {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {DARK_BG_SECONDARY}, stop:1 #1E2530);
        border: 1px solid {DARK_BORDER};
        border-radius: 12px;
    }}
    #cardValue {{
        font-size: 36px;
        font-weight: bold;
        color: {DARK_TEXT_PRIMARY};
    }}
    #cardTitle {{
        font-size: 14px;
        color: {DARK_TEXT_SECONDARY};
    }}
    
    /* --- Activity List Styles --- */
    #activityTitle {{
        font-weight: bold;
    }}
    #activityTime {{
        color: {DARK_TEXT_DISABLED};
        font-size: 12px;
    }}

    /* --- Button Styles --- */
    QPushButton {{
        background-color: {DARK_ACCENT_PRIMARY};
        color: #000000;
        border-radius: 6px;
        padding: 10px 18px;
        font-weight: bold;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background-color: {DARK_ACCENT_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {DARK_ACCENT_PRESSED};
    }}
    QPushButton#outlineButton {{
        background-color: transparent;
        color: {DARK_ACCENT_PRIMARY};
        border: 1px solid {DARK_ACCENT_PRIMARY};
    }}
    QPushButton#outlineButton:hover {{
        background-color: {DARK_ACCENT_PRIMARY};
        color: #000000;
    }}
    QPushButton#textButton {{
        background-color: transparent;
        color: {DARK_TEXT_SECONDARY};
        font-weight: normal;
    }}
    QPushButton#textButton:hover {{
        color: {DARK_TEXT_PRIMARY};
        text-decoration: underline;
    }}
    QPushButton#iconButton {{
        background-color: transparent;
        border: 1px solid {DARK_BORDER};
        border-radius: 6px;
        padding: 8px;
    }}
    QPushButton#iconButton:hover {{
        background-color: {DARK_BG_TERTIARY};
        border-color: {DARK_ACCENT_PRIMARY};
    }}
    QPushButton#dangerButton {{
        background-color: {STATUS_RED};
        color: #FFFFFF;
    }}
    QPushButton#dangerButton:hover {{
        background-color: #E53935;
    }}

    /* --- Form Widget Styles --- */
    QLineEdit, QComboBox {{
        background-color: {DARK_BG_PRIMARY};
        border: 1px solid {DARK_BORDER};
        border-radius: 6px;
        padding: 10px 12px;
        color: {DARK_TEXT_PRIMARY};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {DARK_ACCENT_PRIMARY};
    }}
    QLineEdit#codeFont {{
        font-family: "Courier New", monospace;
    }}
    #searchInput {{
        min-width: 350px;
        padding-left: 15px;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left: 1px solid {DARK_BORDER};
    }}
    QComboBox::down-arrow {{
        image: url(./resources/icons/chevron-down.svg);
    }}

    QRadioButton {{
        spacing: 10px;
    }}
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 9px;
        border: 2px solid {DARK_BORDER};
    }}
    QRadioButton::indicator:hover {{
        border-color: {DARK_ACCENT_HOVER};
    }}
    QRadioButton::indicator:checked {{
        background-color: {DARK_ACCENT_PRIMARY};
        border-color: {DARK_ACCENT_PRIMARY};
    }}
    QRadioButton::indicator:checked:hover {{
        border-color: {DARK_ACCENT_HOVER};
        background-color: {DARK_ACCENT_HOVER};
    }}

    /* --- Table Styles --- */
    #devicesTable, #logsTable {{
        background-color: transparent;
        gridline-color: transparent;
    }}
    #devicesTable::item, #logsTable::item {{
        border-bottom: 1px solid {DARK_BORDER};
        padding: 10px;
        color: {DARK_TEXT_SECONDARY};
    }}
    #devicesTable::item:hover, #logsTable::item:hover {{
        background-color: {DARK_BG_TERTIARY};
    }}
    QHeaderView::section {{
        background-color: transparent;
        border: none;
        border-bottom: 2px solid {DARK_BORDER};
        padding: 12px 10px;
        font-weight: bold;
        color: {DARK_TEXT_SECONDARY};
        font-size: 12px;
        text-transform: uppercase;
    }}
    #tableName {{
        font-weight: bold;
        color: {DARK_TEXT_PRIMARY};
    }}
    
    /* --- Log Page Specific Styles --- */
    QPushButton#filterButton {{
        background-color: transparent;
        color: {DARK_TEXT_SECONDARY};
        border: 1px solid {DARK_BORDER};
        padding: 10px 18px;
    }}
    QPushButton#filterButton:hover {{
        border-color: {DARK_ACCENT_PRIMARY};
        color: {DARK_ACCENT_PRIMARY};
    }}
    QPushButton#filterButton:checked {{
        background-color: {DARK_ACCENT_PRIMARY};
        border-color: {DARK_ACCENT_PRIMARY};
        color: #000000;
    }}

    #logINFO, #logDEBUG, #logWARNING, #logERROR, #logCRITICAL {{
        font-weight: bold;
        border-radius: 4px;
        padding: 5px 10px;
        min-width: 60px;
        text-align: center;
    }}
    #logINFO, #logDEBUG {{
        background-color: #2E7D32;
        color: #FFFFFF;
    }}
    #logWARNING {{
        background-color: #FF8F00;
        color: #000000;
    }}
    #logERROR, #logCRITICAL {{
        background-color: #D32F2F;
        color: #FFFFFF;
    }}

    /* --- Device Detail Page Styles --- */
    #infoLabel {{
        color: {DARK_TEXT_SECONDARY};
    }}
    #infoValue {{
        font-weight: bold;
        font-size: 15px;
    }}
    QTabWidget::pane {{
        border: none;
    }}
    QTabWidget::tab-bar {{
        alignment: left;
    }}
    QTabBar::tab {{
        background: transparent;
        border: none;
        padding: 12px 20px;
        color: {DARK_TEXT_SECONDARY};
        font-weight: bold;
    }}
    QTabBar::tab:hover {{
        color: {DARK_TEXT_PRIMARY};
    }}
    QTabBar::tab:selected {{
        color: {DARK_TEXT_PRIMARY};
        background-color: {DARK_BG_TERTIARY};
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    #configText {{
        background-color: {DARK_BG_PRIMARY};
        border: 1px solid {DARK_BORDER};
        border-radius: 8px;
        font-family: "Courier New", monospace;
        color: {DARK_TEXT_SECONDARY};
        padding: 10px;
    }}
    /* --- Scheduler Page Card Styles --- */
    #JobCard {{
        background-color: {DARK_BG_SECONDARY};
        border-radius: 10px;
        border: 1px solid {DARK_BORDER};
        padding: 20px;
    }}
    #noJobsLabel {{
        font-size: 16px;
        color: {DARK_TEXT_DISABLED};
        padding: 50px;
    }}
    #jobName {{
        font-size: 18px;
        font-weight: bold;
        color: {DARK_TEXT_PRIMARY};
    }}
    #jobSchedule, #jobNextRun {{
        font-size: 13px;
        color: {DARK_TEXT_SECONDARY};
    }}
    /* --- Toast Notification Styles --- */
    #ToastFrame {{
        border-radius: 8px;
        background-color: {DARK_BG_TERTIARY};
        border: 1px solid {DARK_BORDER};
    }}
    #toastMessage {{
        color: {DARK_TEXT_SECONDARY};
    }}

    /* Contextual styling based on property */
    #ToastFrame[toast_type="success"] {{
        background-color: #1A3C2B; /* Dark Green */
        border-color: {STATUS_GREEN};
    }}
    #ToastFrame[toast_type="error"] {{
        background-color: #4D1F1F; /* Dark Red */
        border-color: {STATUS_RED};
    }}
    #ToastFrame[toast_type="info"] {{
        background-color: #1A2028; /* Default */
        border-color: {DARK_ACCENT_PRIMARY};
    }}
    /* --- Enhanced Device Detail Page Styles --- */
    #InfoCard {{
        background-color: {DARK_BG_TERTIARY};
        border-radius: 8px;
        padding: 15px;
    }}
    #infoCardLabel {{
        font-size: 13px;
        color: {DARK_TEXT_DISABLED};
    }}
    #infoCardValue {{
        font-size: 16px;
        font-weight: bold;
        color: {DARK_TEXT_PRIMARY};
    }}
    /* --- Hyperlink Style (e.g., 'Export') --- */
    QLabel {{
        background-color: transparent;
    }}

    QLabel:link {{
        color: #00E5FF;
        text-decoration: underline;
    }}

    QLabel:link:hover {{
        color: #80F2FF;
    }}

    /* --- Enhanced Backup History Table Styles --- */
    #backupTable {{
        background-color: transparent;
        gridline-color: transparent; /* Remove grid lines */
    }}

    #backupTable::item {{
        border-bottom: 1px solid {DARK_BORDER}; /* Subtle separator */
        padding: 12px 10px; /* More vertical padding */
        color: {DARK_TEXT_PRIMARY}; /* Primary text color for items */
    }}

    #backupTable::item:alternate {{
        background-color: {DARK_BG_SECONDARY}; /* Slightly different background for alternate rows */
    }}

    #backupTable::item:selected {{
        background-color: {DARK_BG_TERTIARY}; /* Highlight selected row */
        color: {DARK_TEXT_PRIMARY};
    }}

    /* Style for the action button in the backup table */
    QPushButton#backupActionButton {{
        background-color: transparent;
        color: {DARK_ACCENT_PRIMARY};
        border: 1px solid {DARK_ACCENT_PRIMARY};
        border-radius: 6px;
        padding: 5px 10px;
        font-weight: bold;
        min-width: 60px; /* Ensure consistent width */
        min-height: 25px; /* Ensure consistent height */
    }}

    QPushButton#backupActionButton:hover {{
        background-color: {DARK_ACCENT_PRIMARY};
        color: #000000;
    }}

    QPushButton#backupActionButton:pressed {{
        background-color: {DARK_ACCENT_PRESSED};
    }}

    /* --- Scrollbar Styling --- */
    QScrollBar:vertical {{
        border: none;
        background-color: {DARK_BG_PRIMARY};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {DARK_BG_TERTIARY};
        border-radius: 5px;
        min-height: 25px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {DARK_TEXT_DISABLED};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
        background: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    /* --- Hyperlink Support for QLabel Export Links --- */
    QLabel:link {{
        color: #00E5FF;
        text-decoration: underline;
    }}
    QLabel:link:hover {{
        color: #80F2FF;
    }}

    

    """

    @staticmethod
    def get_stylesheet(theme="dark"):
        if theme == "dark":
            return Style.DARK_THEME_STYLESHEET
        else:
            return ""

