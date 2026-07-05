"""
Results presentation constants for the EREBUS graphical interface.

This module contains constants used to build and display the execution results
summary shown in the graphical results page.
"""

RESULTS_IMPORTANT_METRIC_ORDER = [
    "emails_inserted",
    "domains_resolvable",
    "ports_found",
    "domains_inserted",
    "domains_not_resolvable",
    "credentials_inserted",
    "ports_discovered",
    "pages_processed",
    "live_pages",
    "wayback_pages",
    "total_pages",
    "files_processed",
    "scripts_processed",
    "subdomains_found",
    "hosts_found",
    "whois_record_found",
]

RESULTS_METRIC_LABELS = {
    "domains_inserted": "Domains discovered",
    "domains_resolvable": "Resolvable domains",
    "domains_not_resolvable": "Non-resolvable domains",
    "emails_inserted": "Emails found",
    "credentials_inserted": "Credentials found",
    "ports_found": "Ports found",
    "ports_discovered": "Ports found",
    "pages_processed": "Pages processed",
    "live_pages": "Live pages",
    "wayback_pages": "Wayback pages",
    "total_pages": "Total pages",
    "files_processed": "Files processed",
    "scripts_processed": "Scripts processed",
    "subdomains_found": "Subdomains found",
    "hosts_found": "Hosts found",
    "whois_record_found": "WHOIS record found",

}

RESULTS_EXPORT_WORD_BUTTON = "Download report"

RESULTS_STATUS_EXPORTING_WORD = "Exporting execution report to Word..."
RESULTS_STATUS_EXPORT_WORD_CANCELLED = "Word export cancelled."
RESULTS_STATUS_EXPORT_WORD_SUCCESS = "Word report exported successfully."
RESULTS_STATUS_EXPORT_WORD_ERROR = "Could not export Word report."

RESULTS_EXPORT_WORD_SUCCESS_TITLE = "Word report exported"
RESULTS_EXPORT_WORD_SUCCESS_MESSAGE = (
    "The execution report was exported successfully.\n\n"
    "File:\n{path}"
)

RESULTS_EXPORT_WORD_ERROR_TITLE = "Word export error"
RESULTS_EXPORT_WORD_ERROR_MESSAGE = (
    "The execution report could not be exported to Word.\n\n"
    "{error}"
)