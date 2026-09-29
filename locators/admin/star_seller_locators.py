"""Selectors for star marking and the objective change on the admin seller cue card (/admin/notes/<uid>).

Confirmed in the JSX:
  * rail blocks are `<div class=adminCardClass>` with an `<h6>` title ("Company's Objective",
    "Additional details for this seller") (AdminSidebarSections.js); the block reads the h6's parent;
  * modals are MUI Modals (`.MuiModal-root`) — CommonModal for Additional Details / Cue card edit,
    a bare Modal for the objective (CompanyObjectiveModal.js);
  * each Additional Details category is a Box whose first child is an `<h6>` Typography subtitle1
    ("Star", "Growth", ...; "Star" can carry a "Pending requirements" pill) followed by MUI Chips;
  * a selected chip gets `backgroundColor: #175CD3` through `sx`, with no class of its own;
  * the objective dropdown (and the Data Room upload modal's "Select Document Type") is CustomSelect:
    `.filter-label` opens it, options are `.filter-list-item`;
  * the Data Room lists each file as `.data-room-list-view` with an MUI DeleteOutlineRounded icon
    (admins only, CuecardDataroom/index.js:319); subsections are `div.p-3.rounded` with the label first;
  * tabs (cue card inner tabs, sellers list tabs) are CustomTabs `div.tab-item`.
"""
MODAL = ".MuiModal-root"
H6 = "h6"
CATEGORY_TITLE = "h6.MuiTypography-subtitle1"
CHIP = ".MuiChip-root"
SELECTED_CHIP_BG = "rgb(23, 92, 211)"      # #175CD3

OBJECTIVE_DROPDOWN = ".filter-label"
OBJECTIVE_OPTION = ".filter-list-item"
FILE_INPUT = "input[type='file']"
# The objective-change upload option's button: CustomFileUpload wraps the CTA in this label (CustomFileUpload/index.js).
UPLOAD_OPTION = "label.custom-upload-label"

TAB = "div.tab-item"
DATA_ROOM_SUBSECTION = "div.p-3.rounded"
DATA_ROOM_FILE = ".data-room-list-view"
DATA_ROOM_DELETE = "[data-testid='DeleteOutlineRoundedIcon']"

SNACKBAR = ".MuiSnackbar-root, [role='alert']"
SELLER_ROWS = ".custom-table-grid-container table tbody tr:has(td)"
# Sellers list search: a magnifier that opens a "Type Keywords to search" box; Enter searches in the open tab.
SELLER_SEARCH_TOGGLE = ".search-filter-container .filter-label"
SELLER_SEARCH_INPUT = "input[placeholder='Type Keywords to search']"
# The row's "Actions" column "View" chip: the only /notes/ link in a row (SellerDataModel.js `notes`, new tab).
ROW_VIEW = "a[href*='/notes/']"
