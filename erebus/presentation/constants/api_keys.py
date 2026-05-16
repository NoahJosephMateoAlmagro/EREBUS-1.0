"""
API key settings text constants for the EREBUS presentation layer.

This module contains texts used by the API key settings page.
"""

API_KEYS_TITLE = "API key settings"

API_KEYS_DESCRIPTION = (
    "Configure API credentials used by optional EREBUS modules. "
    "At the moment, this page stores the Shodan API key used by the Shodan "
    "module when that module is enabled."
)

API_KEYS_FUTURE_TITLE = "Future API providers"

API_KEYS_FUTURE_TEXT = (
    "More API providers and token policy options will be added in future "
    "versions."
)

SHODAN_API_TITLE = "Shodan API key"

SHODAN_API_DESCRIPTION = (
    "This API key will be stored in the local EREBUS database and used by the "
    "Shodan module during execution. If a key already exists, it is loaded here "
    "automatically."
)

SHODAN_API_TOKEN_POLICY_TEXT = (
    "The saved Shodan key will be used by the Shodan module under the selected "
    "token policy."
)

SHODAN_API_KEY_LABEL = "API key"
SHODAN_API_KEY_PLACEHOLDER = "Enter your Shodan API key"
SHODAN_API_KEY_DESCRIPTION = "Shodan API key used by the EREBUS Shodan module."
SHODAN_API_DISPLAY_NAME = "Shodan"

API_KEY_SHOW_BUTTON = "👁"
API_KEY_HIDE_BUTTON = "Hide"
API_KEY_SAVE_BUTTON = "Save key"

API_KEY_STATUS_READY = "Ready."
API_KEY_STATUS_EMPTY = "No Shodan API key is currently stored."
API_KEY_STATUS_LOADED = "Stored Shodan API key loaded."
API_KEY_STATUS_EMPTY_KEY = "Enter a Shodan API key before saving."
API_KEY_STATUS_SAVED = "Shodan API key saved successfully."
API_KEY_STATUS_LOAD_ERROR = "Could not load the stored Shodan API key."
API_KEY_STATUS_SAVE_ERROR = "Could not save the Shodan API key."

API_KEY_SAVED_POPUP = "{provider} API key saved successfully."