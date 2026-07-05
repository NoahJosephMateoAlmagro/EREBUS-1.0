"""
User-facing text and status message constants for the EREBUS presentation layer.
"""


TAB_EXECUTION = "execution"
TAB_DATA = "data"
TAB_API_KEYS = "api_keys"
TAB_RESULTS = "results"
TAB_CONSOLE = "console"

TAB_LABELS = {
    TAB_EXECUTION: "Execution",
    TAB_DATA: "Data",
    TAB_API_KEYS: "API key settings",
    TAB_RESULTS: "Results",
    TAB_CONSOLE: "Console",
}

APP_SUBTITLE = "Footprinting, public exposure and digital attack surface analysis"

PLACEHOLDER_DATA_TEXT = "Data view pending"
PLACEHOLDER_RESULTS_TEXT = "Results view pending"

EXECUTION_TITLE = "New execution"
EXECUTION_DESCRIPTION = (
    "Enter the target domain and start the analysis using the selected configuration."
)

GENERAL_CONFIGURATION_TITLE = "General configuration"
GENERAL_CONFIGURATION_DESCRIPTION = "These values affect the whole execution."

MODULES_TITLE = "Analysis modules"
MODULES_DESCRIPTION = (
    "Enable the modules you want to execute. If a module depends on another one, "
    "its dependency must be enabled first."
)

CONSOLE_TITLE = "Runtime console"
CONSOLE_READY_TEXT = "[Console ready]\n"

RESULTS_TITLE = "Latest results"
RESULTS_EMPTY_TEXT = "No execution summary available yet."
RESULTS_LATEST_EXECUTION_TITLE = "Latest execution"
RESULTS_FINDINGS_TITLE = "Most important findings"
RESULTS_MODULE_SUMMARY_TITLE = "Module summary"
RESULTS_NO_FINDINGS_TEXT = "No important findings were generated."
RESULTS_NO_MODULE_RESULTS_TEXT = "No module results available."
RESULTS_NO_MODULE_FINDINGS_TEXT = "No relevant findings for this module."

RESULTS_LABEL_TARGET = "Target"
RESULTS_LABEL_STARTED_AT = "Started at"
RESULTS_LABEL_DURATION = "Duration"
RESULTS_LABEL_ACTIVE_MODULES = "Active modules"

RESULTS_STATUS_PREFIX = "Status:"
RESULTS_DURATION_PREFIX = "Duration:"
RESULTS_NO_RESULTS = "No results"
RESULTS_STATUS_UNKNOWN = "Unknown"
RESULTS_VALUE_EMPTY = "-"
RESULTS_UTC_SUFFIX = "UTC"
RESULTS_DURATION_FORMAT = "{seconds:.2f} s"

STATUS_READY = "Status: Ready"
STATUS_RUNNING = "Status: Running"
STATUS_CANCELLING = "Status: Cancelling"
STATUS_CANCELLED = "Status: Cancelled"
STATUS_MISSING_DOMAIN = "Status: Missing domain"
STATUS_ALREADY_RUNNING = "Status: Execution already running"
STATUS_NO_EXECUTION_RUNNING = "Status: No execution running"
STATUS_EXECUTION_FAILED = "Status: Execution failed"
STATUS_ALL_MODULES_ENABLED = "Status: All modules enabled"
STATUS_ALL_MODULES_DISABLED = "Status: All modules disabled"

STOP_REQUESTED_POPUP = (
    "Stop requested. To avoid data corruption, EREBUS will not interrupt "
    "the module that is currently running. The execution will stop safely "
    "as soon as the current module or phase finishes. Current module: {current}."
)

STOP_REQUESTED_UPDATE = (
    "Stop requested. To avoid data corruption, EREBUS will stop when "
    "the current module finishes. Current module: {current}."
)

STOP_REQUESTED_CONSOLE = (
    "[GUI] Stop requested. EREBUS will stop after the current module "
    "or current phase finishes."
)

EXECUTION_CANCELLED_POPUP = (
    "Execution cancelled safely. Results generated before cancellation "
    "have been preserved."
)

EXECUTION_STARTING_POPUP = (
    "EREBUS is starting an analysis for domain: {target}."
)

EXECUTION_FINISHED_POPUP = (
    "Execution finished for domain: {target}. Final status: {status}."
)

EXECUTION_FAILED_POPUP = (
    "Execution failed for domain: {target}. Check the runtime console for details."
)

OPTION_LOGGING_MODES = ["DEBUG", "INFO", "ERROR", "SILENT"]