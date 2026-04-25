MODULE_UI_CONFIG = {
    "subdomains": {
        "title": "Subdomains",
        "description": "Discovers subdomains associated with the target domain.",
        "depends_on": [],
        "settings": [
            ("limits", "subdomain_max"),
            ("timeouts", "http_subdomains"),
            ("retries", "crtsh_max_attempts"),
        ],
    },
    "whois": {
        "title": "WHOIS",
        "description": "Retrieves public domain registration information.",
        "depends_on": [],
        "settings": [],
    },
    "dns": {
        "title": "DNS",
        "description": "Resolves domains and subdomains into valid IP addresses.",
        "depends_on": ["subdomains"],
        "settings": [
            ("limits", "dns_max_domains"),
            ("timeouts", "dns_resolution"),
        ],
    },
    "nmap": {
        "title": "Nmap",
        "description": "Performs active scanning against resolved hosts.",
        "depends_on": ["dns"],
        "settings": [
            ("tools", "nmap_path"),
            ("limits", "nmap_batch_size"),
            ("timeouts", "nmap_scan"),
        ],
    },
    "http_headers": {
        "title": "HTTP Headers",
        "description": "Analyzes HTTP security headers exposed by the target services.",
        "depends_on": ["dns"],
        "settings": [
            ("timeouts", "http_headers"),
        ],
    },
    "email_passive": {
        "title": "Passive Email Discovery",
        "description": "Searches for exposed email addresses using public sources.",
        "depends_on": [],
        "settings": [
            ("timeouts", "http_passive_email"),
        ],
    },
    "crawling": {
        "title": "Crawling",
        "description": "Crawls target web pages and collects reachable URLs.",
        "depends_on": [],
        "settings": [
            ("limits", "crawler_live_max_pages"),
            ("limits", "crawler_wayback_max_pages"),
            ("limits", "sitemap_max_urls"),
            ("limits", "robots_max_urls"),
            ("timeouts", "crawler_live_page"),
            ("timeouts", "crawler_wayback_page"),
            ("timeouts", "http_robots"),
            ("timeouts", "http_sitemap"),
        ],
    },
    "js_parsing": {
        "title": "JavaScript Parsing",
        "description": "Analyzes JavaScript files to extract emails, URLs and possible exposed secrets.",
        "depends_on": ["crawling"],
        "settings": [
            ("limits", "js_max_scripts"),
            ("timeouts", "js_connect"),
            ("timeouts", "js_read"),
        ],
    },
    "file_parsing": {
        "title": "File Parsing",
        "description": "Analyzes discovered or downloaded files to extract useful exposure indicators.",
        "depends_on": ["crawling"],
        "settings": [
            ("limits", "file_max_size"),
            ("limits", "file_max_files"),
            ("limits", "file_max_workers"),
            ("timeouts", "file_download"),
        ],
    },
    "scraping": {
        "title": "Active Scraping",
        "description": "Loads pages with a controlled browser to detect dynamically generated content.",
        "depends_on": ["crawling"],
        "settings": [
            ("timeouts", "scraping_page_load"),
        ],
    },
    "wayback": {
        "title": "Wayback Machine",
        "description": "Queries historical snapshots and archived URLs related to the target domain.",
        "depends_on": [],
        "settings": [
            ("limits", "wayback_max_snapshots"),
            ("limits", "wayback_min_year"),
            ("limits", "cdx_url_limit"),
            ("timeouts", "wayback_cdx_api"),
        ],
    },
    "shodan": {
        "title": "Shodan",
        "description": "Queries public exposure information from Shodan.",
        "depends_on": ["dns"],
        "settings": [],
    },
}


SETTING_LABELS = {
    "nmap_path": "Nmap path",

    "subdomain_max": "Max subdomains",
    "dns_max_domains": "Max DNS domains",

    "crawler_live_max_pages": "Max live crawler pages",
    "crawler_wayback_max_pages": "Max Wayback crawler pages",
    "sitemap_max_urls": "Max sitemap URLs",
    "robots_max_urls": "Max robots.txt URLs",

    "wayback_max_snapshots": "Max Wayback snapshots",
    "wayback_min_year": "Minimum Wayback year",
    "cdx_url_limit": "CDX URL limit",

    "js_max_scripts": "Max JavaScript files",

    "nmap_batch_size": "Nmap batch size",

    "file_max_size": "Max file size",
    "file_max_files": "Max files",
    "file_max_workers": "File workers",

    "http_passive_email": "Passive email HTTP timeout",
    "http_subdomains": "Subdomain HTTP timeout",
    "http_headers": "HTTP headers timeout",

    "dns_resolution": "DNS resolution timeout",

    "nmap_scan": "Nmap scan timeout",

    "crawler_live_page": "Live crawler page timeout",
    "crawler_wayback_page": "Wayback crawler page timeout",
    "http_robots": "robots.txt HTTP timeout",
    "http_sitemap": "sitemap.xml HTTP timeout",

    "js_connect": "JavaScript connection timeout",
    "js_read": "JavaScript read timeout",

    "file_download": "File download timeout",

    "scraping_page_load": "Scraping page load timeout",

    "wayback_cdx_api": "Wayback CDX API timeout",

    "crtsh_max_attempts": "crt.sh max attempts",

    "timezone": "Timezone",
    "mode": "Log level",
    "clear_db_on_run": "Clear database on run",
}

SETTING_TOOLTIPS = {
    "timezone": "Timezone used by the logger to display execution timestamps.",
    "mode": "Controls the logging verbosity: TRACE, INFO, ERROR or SILENT.",
    "clear_db_on_run": "If enabled, the database is cleared before starting a new execution.",

    "nmap_path": "Absolute path to the Nmap executable used by the active scanning module.",

    "subdomain_max": "Maximum number of subdomains to collect before stopping subdomain discovery.",
    "dns_max_domains": "Maximum number of domains or subdomains that will be resolved through DNS.",

    "crawler_live_max_pages": "Maximum number of live web pages that the crawler will visit.",
    "crawler_wayback_max_pages": "Maximum number of archived Wayback pages that the crawler will process.",
    "sitemap_max_urls": "Maximum number of URLs extracted from sitemap.xml files.",
    "robots_max_urls": "Maximum number of URLs extracted from robots.txt files.",

    "wayback_max_snapshots": "Maximum number of historical snapshots retrieved from Wayback Machine.",
    "wayback_min_year": "Oldest year accepted when collecting historical Wayback data.",
    "cdx_url_limit": "Maximum number of URLs requested from the Wayback CDX API.",

    "js_max_scripts": "Maximum number of JavaScript files to download and analyze.",

    "nmap_batch_size": "Number of hosts scanned per Nmap batch.",

    "file_max_size": "Maximum file size accepted for download and parsing.",
    "file_max_files": "Maximum number of files that can be downloaded and analyzed.",
    "file_max_workers": "Maximum number of parallel workers used for file processing.",

    "http_passive_email": "HTTP timeout used while collecting passive email information.",
    "http_subdomains": "HTTP timeout used while collecting subdomains from public sources.",
    "http_headers": "HTTP timeout used while checking security headers.",

    "dns_resolution": "Maximum time allowed for DNS resolution operations.",

    "nmap_scan": "Maximum time allowed for an Nmap scan batch.",

    "crawler_live_page": "Timeout used when requesting live crawler pages.",
    "crawler_wayback_page": "Timeout used when requesting archived Wayback pages.",
    "http_robots": "Timeout used when requesting robots.txt.",
    "http_sitemap": "Timeout used when requesting sitemap.xml.",

    "js_connect": "Connection timeout used when downloading JavaScript files.",
    "js_read": "Read timeout used when downloading JavaScript files.",

    "file_download": "Timeout used when downloading files.",

    "scraping_page_load": "Maximum page load time for browser-based scraping.",
    "wayback_cdx_api": "Timeout used when querying the Wayback CDX API.",

    "crtsh_max_attempts": "Maximum number of retry attempts when querying crt.sh.",
}