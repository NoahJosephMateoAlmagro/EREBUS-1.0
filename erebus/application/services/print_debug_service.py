class PrintDebugService:

    def __init__(self, uow):
        self.uow = uow

    # ----------------------------------------
    # Public API
    # ----------------------------------------

    def print_summary(self, execution_id, stats):

        metrics = self.uow.metrics.get_execution_metrics(execution_id)

        print("\n========== SUMMARY ==========")

        self._print_db_metrics(metrics)
        self._print_execution_stats(stats)
        self._print_mail_dns_info()

        print("========== END SUMMARY ==========")

    # ----------------------------------------
    # Internal
    # ----------------------------------------

    def _print_db_metrics(self, metrics):

        print("========== DB METRICS ==========")

        print("\n--- EMAILS ---")
        print(f"[EMAILS] total: {metrics.get('emails_total', 0)}")
        print(f"[EMAILS] crawler_html: {metrics.get('emails_crawler_html', 0)}")
        print(f"[EMAILS] js_static: {metrics.get('emails_js_static', 0)}")
        print(f"[EMAILS] scraping_dom: {metrics.get('emails_scraping_dom', 0)}")
        print(f"[EMAILS] scraping_json: {metrics.get('emails_scraping_json', 0)}")
        print(f"[EMAILS] detected_by_scraping: {metrics.get('emails_detected_by_scraping', 0)}")
        print(f"[EMAILS] detected_without_scraping: {metrics.get('emails_detected_without_scraping', 0)}")

        print("\n--- CREDENTIALS ---")
        print(f"[CREDS] total: {metrics.get('creds_total', 0)}")
        print(f"[CREDS] creds_detected_by_scraping: {metrics.get('creds_detected_by_scraping', 0)}")
        print(f"[CREDS] creds_detected_without_scraping: {metrics.get('creds_detected_without_scraping', 0)}")

        print("\n========== END METRICS ==========\n")

    def _print_execution_stats(self, stats):

        print("\n========== EXECUTION STATS ==========")

        print("\n--- CRAWLER (LIVE) ---")
        print(f"[CRAWLER] live pages visited: {stats.live_pages_visited}")
        print(f"[CRAWLER] visited from robots.txt: {stats.visited_from_robots}")
        print(f"[CRAWLER] visited from sitemap.xml: {stats.visited_from_sitemap}")
        print(f"[CRAWLER] visited discovered (links): {stats.visited_discovered}")

        print("\n--- CRAWLER (WAYBACK) ---")
        print(f"[CRAWLER] wayback urls collected: {stats.wayback_urls_collected}")
        print(f"[CRAWLER] wayback pages visited: {stats.wayback_pages_visited}")

        print("\n--- JS PARSING ---")
        print(f"[JS] scripts parsed: {stats.scripts_parsed_ok}/{stats.scripts_parse_limit}")

        print("\n--- SCRAPING ---")
        print(f"[SCRAPING] attempted: {stats.scrape_attempted}")
        print(f"[SCRAPING] succeeded: {stats.scrape_succeeded}")
        print(f"[SCRAPING] failed: {stats.scrape_failed}")

        print("\n========== END STATS ==========")

    def _print_mail_dns_info(self):

        mail = self.uow.domains.get_dns_mail_summary()

        if not mail:
            return

        print("\n========== DNS MAIL ==========")
        print(f"[MAIL] domain: {mail['domain']}")
        print(f"[MAIL] provider: {mail['mail_provider']}")
        print(f"[MAIL] SPF policy: {mail['spf_policy']}")
        print(f"[MAIL] external services: {', '.join(mail['external_services'])}")
        print("========== END DNS MAIL ==========")