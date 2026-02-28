APP_CONFIG = {

    "debug": {
        "clear_db_on_run": True,
        "show_debug_popups": True,
    },

    "modules": {
        "subdomains": True,
        "whois": True,
        "dns": True,
        "http_headers": True,
        "emails_passive": True,
        "crawler": True,
        "js_parsing": False,
        "file_parsing": True,
        "scraping": False,
        "wayback": True
    },

    "limits": {
        # DNS
        "subdomain_max": 20,
        "dns_max_domains": 20,

        # Crawling
        "crawler_live_max_pages": 100,
        "crawler_wayback_max_pages": 30,
        "sitemap_max_urls": 20,
        "robots_max_urls": 20,

        # Wayback (CDX)
        "wayback_max_snapshots": 50,
        "wayback_min_year": 2000,
        "cdx_url_limit":200,

        # JS
        "js_max_scripts": 15,

        #Files
        "file_max_size": 5000000,
    },

    "timeouts": {
        # HTTP (requests)
        "http_passive_email": 20,
        "http_subdomains": 25,
        "http_headers": 5,

        # DNS
        "dns_resolution": 15,

        # Crawler (requests)

        "crawler_live_page": 3,
        "crawler_wayback_page": 8,
        "http_robots": 5,
        "http_sitemap": 8,

        # JS
        "js_connect": 3,
        "js_read": 5,

        #Files
        "file_download": 2,

        # Active scraping (Playwright)
        "scraping_page_load": 15000,  # ms

        # Wayback API (CDX)
        "wayback_cdx_api": 25
    }
}
