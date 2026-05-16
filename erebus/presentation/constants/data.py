"""
Data page text constants for the EREBUS presentation layer.

This module contains texts and configuration values used by the stored data page.
"""

DATA_TITLE = "Stored data"

DATA_DESCRIPTION = (
    "Inspect the information collected during EREBUS executions. "
    "Use the table selector to browse stored results and apply an execution filter "
    "to focus on a specific execution."
)

DATA_EXECUTION_FILTER_LABEL = "Execution filter"
DATA_EXECUTION_FILTER_PLACEHOLDER = "urjc_es, 20260510, 170427, urjc_es_20260510_170427"

DATA_EXECUTION_FILTER_HELP = (
    "Remember: the execution id is built using the normalized domain, date and time. "
    "For example: domain_es_20260510_170427. You can filter by domain, date, "
    "time or the full execution id."
)

DATA_REFRESH_BUTTON = "Refresh"

DATA_TABLES_TITLE = "Database tables"

DATA_STATUS_READY = "Ready."
DATA_STATUS_NO_DATABASE = "Database not found or empty."
DATA_STATUS_NO_COLUMNS = "The selected table has no readable columns."
DATA_STATUS_LOADED = "Loaded {shown} rows from {table} ({total} total rows)."
DATA_STATUS_FILTERED = (
    "Loaded {shown} rows from {table} filtered by '{filter_value}' "
    "({total} matching rows)."
)
DATA_STATUS_LOADING = "Loading {table}..."
DATA_STATUS_ERROR = "Error loading {table}."

DATA_NO_DATABASE_TEXT = (
    "No database data is available yet. Run an analysis first and return to this "
    "page when EREBUS has stored results."
)
DATA_NO_TABLE_SELECTED_TEXT = "No table selected."
DATA_NO_COLUMNS_TEXT = "The selected table does not contain readable columns."
DATA_NO_ROWS_TEXT = "No rows found for the selected table and filter."

DATA_EMPTY_VALUE = "-"

DATA_PAGE_SIZE_OPTIONS = ["25", "50", "100", "200"]
DATA_DEFAULT_PAGE_SIZE = 100