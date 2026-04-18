import re

"""
Centralized constants used across EREBUS modules.
Includes domain status, techniques, sources and file handling rules.
"""

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
TECHNIQUE_DNS_NS = "dns_ns"
TECHNIQUE_DNS_CNAME = "dns_cname"

TECHNIQUE_FILE_TXT = "file_txt"
TECHNIQUE_FILE_PDF = "file_pdf"
TECHNIQUE_FILE_XML = "file_xml"

TECHNIQUE_NMAP = "nmap_scan"
TECHNIQUE_SHODAN = "shodan"

# ---------------------------------------------
# Execution status
# ---------------------------------------------

EXECUTION_STATUS_RUNNING = "running"
EXECUTION_STATUS_FINISHED = "finished"
EXECUTION_STATUS_ERROR = "error"

# ---------------------------------------------
# Logging
# ---------------------------------------------

LOG_MODE_TRACE = "TRACE"
LOG_MODE_INFO = "INFO"
LOG_MODE_ERROR = "ERROR"
LOG_MODE_SILENT = "SILENT"

LOG_MODE_PRIORITIES = {
    LOG_MODE_TRACE: 10,
    LOG_MODE_INFO: 20,
    LOG_MODE_ERROR: 30,
    LOG_MODE_SILENT: 100,
}

LOG_LEVEL_PRIORITIES = {
    LOG_MODE_TRACE: 10,
    LOG_MODE_INFO: 20,
    LOG_MODE_ERROR: 30,
}

# ---------------------------------------------
# Sources
# ---------------------------------------------

SOURCE_HTML = "html"
SOURCE_JS = "js"
SOURCE_SCRAPING_DOM = "scraping_dom"
SOURCE_SCRAPING_JSON = "scraping_json"
SOURCE_FILE = "file"
SOURCE_JSON = "json"
SOURCE_SHODAN = "shodan"

# ---------------------------------------------
# File parsing
# ---------------------------------------------

FILE_EXTENSIONS_TO_PARSE = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".txt",
    ".csv"
}

JSON_USER_KEYS = {"user", "username", "login"}
JSON_PASS_KEYS = {"password", "pwd", "pass"}
JSON_TOKEN_KEYS = {"apikey", "api_key", "token", "secret"}

USER_REGEX = re.compile(
    r"\b(user(name)?|login)[\w\-]*\s*=\s*['\"]([^'\"\s]{3,})['\"]",
    re.IGNORECASE
)

PASS_REGEX = re.compile(
    r"\b(pass(word)?|pwd)[\w\-]*\s*=\s*['\"]([^'\"\s]{3,})['\"]",
    re.IGNORECASE
)

TOKEN_REGEX = re.compile(
    r"\b(api[_-]?key|token|secret)[\w\-]*\s*=\s*['\"]([^'\"\s]{8,})['\"]",
    re.IGNORECASE
)

URL_REGEX = r"https?://[^\s\"']+"
USER_AGENT = "EREBUS/1.0"

# ---------------------------------------------
# Normalizers and Analyzers constants
# ---------------------------------------------

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

OBFUSCATED_PATTERNS = [
    (r"\s*\[\s*at\s*\]\s*", "@"),
    (r"\s*\(\s*at\s*\)\s*", "@"),
    (r"\s+at\s+", "@"),
    (r"\s*\[\s*dot\s*\]\s*", "."),
    (r"\s*\(\s*dot\s*\)\s*", "."),
    (r"\s+dot\s+", "."),
]

CONCAT_REGEX = re.compile(
    r"['\"]([a-zA-Z0-9._%+-]+)['\"]\s*\+\s*['\"]@['\"]\s*\+\s*['\"]([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})['\"]"
)

BASE64_CALL_REGEX = re.compile(
    r"atob\(\s*['\"]([A-Za-z0-9+/=]{20,})['\"]\s*\)"
)

BASE64_TOKEN_REGEX = re.compile(
    r"\b[A-Za-z0-9+/=]{24,}\b"
)

SECURITY_HEADERS = {
    "strict-transport-security": "Forces HTTPS",
    "content-security-policy": "Mitigates XSS",
    "x-frame-options": "Clickjacking protection",
    "x-content-type-options": "MIME sniffing protection",
    "referrer-policy": "Controls referrer leakage",
    "permissions-policy": "Controls browser features"
}

TECH_HEADERS = {
    # Core stack
    "server": "Web server",
    "x-powered-by": "Backend technology",
    "x-generator": "CMS / Generator",

    # Infra / proxy
    "via": "Proxy / Gateway",
    "x-forwarded-for": "Reverse proxy",
    "x-forwarded-proto": "TLS offloading",

    # Sessions / load balancing
    "set-cookie": "Session technology",

    # Cloud / CDN
    "cf-ray": "Cloudflare identifier",
    "cf-cache-status": "Cloudflare cache",
    "x-amz-cf-id": "AWS CloudFront",
    "x-cache": "Reverse proxy cache",

    # Microsoft stack
    "x-aspnet-version": "ASP.NET version",
    "x-aspnetmvc-version": "ASP.NET MVC version",
}

CNAME_PROVIDER_PATTERNS = {
    "cloudfront.net": "AWS",
    "amazonaws.com": "AWS",
    "azurewebsites.net": "Azure",
    "trafficmanager.net": "Azure",
    "cloudapp.azure.com": "Azure",
    "herokudns.com": "Heroku",
    "github.io": "GitHub Pages",
    "pages.dev": "Cloudflare Pages",
    "cdn.cloudflare.net": "Cloudflare",
    "fastly.net": "Fastly",
    "netlify.app": "Netlify",
    "vercel.app": "Vercel",
}

NS_PROVIDER_PATTERNS = {
    "cloudflare.com": "Cloudflare",
    "googledomains.com": "Google",
    "domaincontrol.com": "GoDaddy",
    "awsdns-": "AWS Route 53",
    "azure-dns.": "Azure DNS",
    "registrar-servers.com": "Namecheap",
    "ovh.net": "OVH",
}

RESOLVER_NAMESERVERS = ["8.8.8.8", "1.1.1.1"]

# ---------------------------------------------
# Non-HTML / asset extensions
# ---------------------------------------------

BAD_EXTENSIONS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif",
    ".svg", ".ico", ".woff", ".woff2", ".ttf",
    ".zip", ".rar", ".7z"
}

# ---------------------------------------------
# Collectors variables
# ---------------------------------------------

CDX_URL = "https://web.archive.org/cdx/search/cdx"