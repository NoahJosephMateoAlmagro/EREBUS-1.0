"""
Data presentation constants for the EREBUS graphical interface.

This module contains constants used to build and display the database browsing
page shown in the graphical Data tab.
"""


DATA_TITLE = "Stored data"
DATA_DESCRIPTION = (
    "Inspect the information collected during EREBUS executions. "
    "Use the table selector to browse stored results and apply a domain filter "
    "to focus on a specific target."
)

DATA_DOMAIN_FILTER_LABEL = "Domain filter"
DATA_REFRESH_BUTTON = "Refresh"

DATA_TABLES_TITLE = "Database tables"

DATA_STATUS_READY = "Ready."
DATA_STATUS_NO_DATABASE = "Database not found or empty."
DATA_STATUS_NO_COLUMNS = "The selected table has no readable columns."
DATA_STATUS_LOADED = "Loaded {count} rows from {table}."
DATA_STATUS_FILTERED = "Loaded {count} rows from {table} filtered by '{domain}'."

DATA_NO_DATABASE_TEXT = (
    "No database data is available yet. Run an analysis first and return to this "
    "page when EREBUS has stored results."
)
DATA_NO_TABLE_SELECTED_TEXT = "No table selected."
DATA_NO_COLUMNS_TEXT = "The selected table does not contain readable columns."
DATA_NO_ROWS_TEXT = "No rows found for the selected table and filter."

DATA_EMPTY_VALUE = "-"
DATA_MAX_VISIBLE_COLUMNS = 6
DATA_COLUMNS_TRUNCATED_TEXT = (
    "Showing {visible} of {total} columns. Wider database tables are shortened "
    "to keep the interface readable."
)