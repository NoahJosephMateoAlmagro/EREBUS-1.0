APP_CONFIG = {

    "debug": {
        "clear_db_on_run": True,
        "show_debug_popups": True,
    },

    "modules": {
        "subdomains": True,
        "whois": True,
        "dns": True,
        "emails_passive": True,
        "crawler": True,
        "js_parsing": False,
        "scraping": False,
        "wayback": True

    },

    "limits": {
        "max_dns": 20,
        "max_pages": 300,
        "max_scripts": 300
    },

    "timeouts": {

        # -------------------------
        # HTTP requests (requests)
        # -------------------------
        "http_crawler_page": 300,  # Crawler HTML (requests.get)
        "http_email_passive": 20,  # EmailCollector (HTML pasivo)
        "http_subdomains": 25,  # crt.sh

        # -------------------------
        # DNS
        # -------------------------
        "dns_resolution": 5,  # dns.resolver lifetime

        # -------------------------
        # JS static parsing
        # -------------------------
        "js_connect": 3,  # conexión HTTP
        "js_read": 5,  # lectura contenido JS

        # -------------------------
        # Active scraping (Playwright)
        # -------------------------
        "scraping_page_load": 15000,  # ms (page.goto / networkidle)

        # -------------------------
        # Fuentes externas
        # -------------------------
        "wayback_timeout": 300
    }

}
