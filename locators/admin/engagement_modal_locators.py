"""Selectors for the Unverified Deals engagement drill-down (DealsLink + ModalWrapper).

ModalWrapper renders an MUI <Modal> (`.MuiModal-root`) holding `.global-modal-container`; the title
is a plain div, the POC rows a CustomTableGrid, and "Close" an MUI Button (NewButton). The modal has
no onClose, so only "Close" dismisses it.
"""
import re

MODAL = ".MuiModal-root .global-modal-container"
TITLE = re.compile(r"^\s*Engagement for \S+\s*$")
HEADER_CELLS = "table thead th"
ROWS = "table tbody tr:has(td)"
CELLS = "td"
PRIMARY_CHIP = ".MuiChip-root"
