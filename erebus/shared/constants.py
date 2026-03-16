# ---------------------------------------------
# Domain resolution status
# ---------------------------------------------

DOMAIN_STATUS_NOT_EVALUATED = "not_evaluated"
DOMAIN_STATUS_RESOLVABLE = "resolvable"
DOMAIN_STATUS_NOT_RESOLVABLE = "not_resolvable"

# ---------------------------------------------
# Techniques
# ---------------------------------------------

TECHNIQUE_PASSIVE_HTML = "passive_html"
TECHNIQUE_CRAWLER_HTML = "crawler_html"
TECHNIQUE_JS_STATIC = "js_static"
TECHNIQUE_JS_STATIC_WAYBACK = "js_static_wayback"
TECHNIQUE_SCRAPING_DOM = "scraping_dom"
TECHNIQUE_SCRAPING_JSON = "scraping_json"
TECHNIQUE_WHOIS = "whois"
TECHNIQUE_SUBDOMAINS = "subdomains_crtsh"
TECHNIQUE_DNS = "dns_resolver"
TECHNIQUE_DNS_MX = "dns_mx"
TECHNIQUE_DNS_TXT = "dns_txt"
TECHNIQUE_DNS_NS ="dns_ns"
TECHNIQUE_DNS_CNAME = "dns_cname"
TECHNIQUE_FILE_TXT = "file_txt"
TECHNIQUE_FILE_PDF = "file_pdf"
TECHNIQUE_FILE_XML = "file_xml"
TECHNIQUE_NMAP = "NMAP_scan"
TECHNIQUE_SHODAN = "Shodan"
# ---------------------------------------------
# Execution status
# ---------------------------------------------

EXECUTION_STATUS_RUNNING = "RUNNING"
EXECUTION_STATUS_FINISHED = "FINISHED"
EXECUTION_STATUS_ERROR = "ERROR"

# ---------------------------------------------
# SOURCES
# ---------------------------------------------
SOURCE_HTML = "html"
SOURCE_JS = "js"
SOURCE_SCRAPING_DOM = "scraping_dom"
SOURCE_SCRAPING_JSON = "scraping_json"
SOURCE_FILE = "file"
SOURCE_JSON = "json"


FILE_EXTENSIONS_TO_PARSE= {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".txt",
    ".csv"
}