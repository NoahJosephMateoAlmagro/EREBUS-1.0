from urllib.parse import urlparse

from collectors.passive.dns import DNSCollector
from collectors.passive.DNS_Details.DNS_MX_Collector import DNS_MX_Collector
from collectors.passive.DNS_Details.DNS_TXT_Collector import DNS_TXT_Collector
from collectors.passive.DNS_Details.DNS_CNAME_Collector import DNS_CNAME_Collector
from collectors.passive.DNS_Details.DNS_NS_Collector import DNS_NS_Collector
from collectors.passive.subdomains import SubdomainCollector
from collectors.passive.whoisCollector import WhoisCollector
from collectors.passive.emails import EmailCollector
from collectors.passive.crawler import Crawler
from collectors.passive.js_parser import JSParser
from collectors.passive.credential_parser import CredentialParser
from collectors.active.scraper import Scraper
from normalizers.email_normalizer import normalize_email
from collectors.passive.robots import RobotsCollector
from collectors.passive.sitemap import SitemapCollector
from collectors.passive.DNS_Details.DNS_Details_Analyzer import DNS_Details_Analyzer
from collectors.passive.waybackMachine import WaybackCollector
from collectors.passive.security_headers import SecurityHeadersCollector

import core.constants as C
from core.execution_stats import ExecutionStats

class Orchestrator:

    def __init__(self, database):
        self.database = database

    # -------------------------------------------------
    # Utils - Prints
    # -------------------------------------------------
    def _print_summary(self, metrics, stats):
        print("\n========== SUMARY ==========")
        self._print_db_metrics(metrics)
        self._print_execution_stats(stats)
        self._print_mail_DNS_info()

        print("========== END SUMARY ==========")

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

    def _print_execution_stats (self, stats: ExecutionStats):

        print("\n========== EXECUTION STATS ==========")

        print("\n--- CRAWLER (LIVE) ---")
        print(f"[CRAWLER] live pages visited: {stats.live_pages_visited}")
        print(f"[CRAWLER] visited from robots.txt: {stats.visited_from_robots}")
        print(f"[CRAWLER] visited from sitemap.xml (y las derivadas de las mismas): {stats.visited_from_sitemap}")
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

    def _print_mail_DNS_info(self):
        mail = self.database.get_dns_mail_summary()
        if mail:
            print("\n========== DNS MAIL ==========")
            print(f"[MAIL] domain: {mail['domain']}")
            print(f"[MAIL] provider: {mail['mail_provider']}")
            print(f"[MAIL] SPF policy: {mail['spf_policy']}")
            print(f"[MAIL] external services: {', '.join(mail['external_services'])}")
            print("========== END DNS MAIL ==========")


    # -------------------------------------------------
    # Utils - Validations
    # -------------------------------------------------
    def _is_valid_domain(self, value: str):
        if not value:
            return None

        value = value.strip().lower()

        # permitir localhost para pruebas
        if value.startswith("localhost"):
            return value

        if ":" in value:
            value = value.split(":")[0]

        if value.endswith("."):
            value = value[:-1]

        if "." not in value:
            return None

        if any(x in value for x in ["/", "\\", "@", " "]):
            return None

        return value
    def _build_crawl_urls(self, domain: str):
        print("Creando urls para crawl...")
        return [
            f"https://{domain}",
            f"https://www.{domain}",
            f"http://{domain}",
            f"http://www.{domain}",
        ]
    def _validate_cfg(self, cfg):
        if cfg is None:
            raise ValueError("Configuración requerida: cfg no puede ser None")

        if not isinstance(cfg, dict):
            raise TypeError("Configuración inválida: cfg debe ser un dict")

        if "modules" not in cfg or "limits" not in cfg or "timeouts" not in cfg:
            raise ValueError(
                "Configuración inválida: se esperaban las claves 'modules' y 'limits'"
            )

    # -------------------------------------------------
    # Utils - Initialization
    # -------------------------------------------------
    def _init_collectors(self, cfg):

        # Pasivos
        self.subdomain_collector = SubdomainCollector(
            timeout=cfg["timeouts"]["http_subdomains"],
            limit = cfg["limits"]["subdomain_max"]
        )

        self.whois_collector = WhoisCollector()

        #DNS
        self.dns_collector = DNSCollector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )
        self.dns_mx_collector = DNS_MX_Collector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )
        self.dns_txt_collector = DNS_TXT_Collector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )

        self.dns_cname_collector = DNS_CNAME_Collector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )

        self.dns_ns_collector = DNS_NS_Collector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )

        self.email_collector = EmailCollector(
            timeout=cfg["timeouts"]["http_passive_email"]
        )

        #Robots y sitemaps

        self.robots_collector = RobotsCollector(
            timeout=cfg["timeouts"]["http_robots"]
        )

        self.sitemap_collector = SitemapCollector(
            timeout=cfg["timeouts"]["http_sitemap"],
            max_urls=int(cfg["limits"]["sitemap_max_urls"])
        )

        # Crawler (LIVE / WAYBACK separados)
        self.crawler_cls = Crawler
        self.crawler_live_timeout = cfg["timeouts"]["crawler_live_page"]
        self.crawler_live_max_pages = int(cfg["limits"]["crawler_live_max_pages"])

        self.crawler_wayback_timeout = cfg["timeouts"]["crawler_wayback_page"]
        self.crawler_wayback_max_pages = int(cfg["limits"]["crawler_wayback_max_pages"])

        # JS
        self.js_parser = JSParser(
            connect_timeout=cfg["timeouts"]["js_connect"],
            read_timeout=cfg["timeouts"]["js_read"]
        )

        # Credenciales
        self.cred_parser = CredentialParser()

        # Scraping (activo)
        self.scraper = Scraper(
            timeout=cfg["timeouts"]["scraping_page_load"]
        )

        #Cabeceras
        self.security_headers_collector = SecurityHeadersCollector(
            timeout=cfg["timeouts"]["http_security_headers"]
        )

        # Wayback (CDX)
        self.wayback_collector = WaybackCollector(
            timeout=cfg["timeouts"]["wayback_cdx_api"],
            limit=int(cfg["limits"]["wayback_max_snapshots"]),
            cdx_limit=int(cfg["limits"]["cdx_url_limit"]),
            min_year=int(cfg["limits"]["wayback_min_year"])
        )

    # -----------------------------
    # Utils - Dedup logic (orchestration)
    # -----------------------------

    # Sets de deduplicado lógico.
    # Permiten conservar la primera aparición temporal de cada entidad
    # sin afectar a las métricas de detección.

    def _is_new_email(self, email, seen):
          if email in seen:
              return False
          seen.add(email)
          return True
    def _is_new_credential(self, ctype, value, seen):
        key = (ctype, value.lower())
        if key in seen:
            return False
        seen.add(key)
        return True
    def _is_new_domain(self, domain, seen):
        if domain in seen:
            return False
        seen.add(domain)
        return True

    # -----------------------------
    # Utils - Helpers
    # -----------------------------
    def _calculate_base_domain_dns_context(self, execution, base_domain):

        print(f"[DNS] Analizando MX/TXT del dominio base: {base_domain}")

        # -------------------------
        # MX
        # -------------------------
        mx_results = self.dns_mx_collector.collect(base_domain)
        mx_hosts = sorted({
            r["record"].lower()
            for r in mx_results
            if r.get("record")
        })

        # -------------------------
        # TXT
        # -------------------------
        txt_results = self.dns_txt_collector.collect(base_domain)
        txt_records = [
            r["value"].lower()
            for r in txt_results
            if r.get("value")
        ]

        # -------------------------
        # ANALYSIS (Analyzer)
        # -------------------------
        dns_context = DNS_Details_Analyzer.analyze_mail_dns_context(
            mx_hosts=mx_hosts,
            txt_records=txt_records
        )

        # -------------------------
        # PERSISTENCE
        # -------------------------
        self.database.update_domain_dns_context(
            execution.ID,
            base_domain,
            mx_records=", ".join(mx_hosts) if mx_hosts else None,
            mail_provider=dns_context["mail_provider"],
            spf_policy=dns_context["spf_policy"],
            external_services=(
                ", ".join(dns_context["external_services"])
                if dns_context["external_services"]
                else None
            )
        )

    # -------------------------------------------------
    # Main
    # -------------------------------------------------

    def _run_subdomains(self, execution, all_domains, seen_domains):
        print("Encontrando subdominios...")
        subdomains = self.subdomain_collector.collect(execution.TARGET, )

        for s in subdomains:
            domain = self._is_valid_domain(s.get("value"))
            if domain:
                all_domains.add(domain)

        for domain in all_domains:
            if self._is_new_domain(domain, seen_domains):
                self.database.insert_domain(
                    execution.ID,
                    domain,
                    source=C.TECHNIQUE_SUBDOMAINS,
                    status=C.DOMAIN_STATUS_NOT_EVALUATED
                )
    def _run_dns(self, execution, cfg, all_domains):
        print("Resolviendo DNS...")

        base_domain = execution.TARGET

        # DNS contextual del dominio base
        self._calculate_base_domain_dns_context(execution, base_domain)

        # Resolución IPs
        max_dns = int(cfg["limits"]["dns_max_domains"])
        domains_to_resolve = list(all_domains)[:max_dns]

        for domain in domains_to_resolve:
            clean_domain = self._is_valid_domain(domain)
            if not clean_domain:
                continue

            # ----------------------
            # RESOLUCIÓN A IP
            # ---------------------
            dns_results = self.dns_collector.collect(clean_domain)

            if dns_results:
                self.database.update_domain_status(
                    execution.ID,
                    clean_domain,
                    C.DOMAIN_STATUS_RESOLVABLE
                )

                for r in dns_results:
                    self.database.insert_resolved_domain(
                        execution.ID,
                        r["domain"],
                        r["ip"],
                        r["source"]
                    )
            else:
                self.database.update_domain_status(
                    execution.ID,
                    clean_domain,
                    C.DOMAIN_STATUS_NOT_RESOLVABLE
                )

            # ---------------------
            # DNS DETAILS
            # ---------------------
            self._run_dns_observations_for_domain(execution, clean_domain)

            # ---------------------
            # CABECERAS
            # ---------------------
            print("[DEBUG] Después de DNS_OBS, antes de headers", clean_domain)

            if cfg["modules"].get("security_headers"):
                print("[DEBUG] Ejecutando security headers", clean_domain)
                self._run_security_headers(execution, clean_domain)

    def _run_dns_observations_for_domain(self, execution, domain):
        print(f"[DNS-OBS] Analizando {domain}")

        # ---------------------
        # CNAME
        # ---------------------
        cname_results = self.dns_cname_collector.collect(domain)

        for r in cname_results:
            record_value = (r.get("record") or "").strip().lower()
            if record_value.endswith("."):
                record_value = record_value[:-1]
            if not record_value:
                continue

            provider = DNS_Details_Analyzer.detect_provider_from_record(
                record_value,
                "CNAME"
            )

            target_resolvable = self.database.get_domain_resolution_status(
                execution.ID,
                record_value
            )

            if target_resolvable is None:
                # Resolver bajo demanda (por si no se ha recogido de la fase de recolección dicho subdominio, entonces devuelve none)
                dns_results = self.dns_collector.collect(record_value)

                if dns_results:
                    self.database.insert_domain(
                        execution.ID,
                        record_value,
                        source=C.TECHNIQUE_DNS_CNAME,
                        status=C.DOMAIN_STATUS_RESOLVABLE
                    )

                    for r in dns_results:
                        self.database.insert_resolved_domain(
                            execution.ID,
                            r["domain"],
                            r["ip"],
                            r["source"]
                        )

                    target_resolvable = True
                else:
                    self.database.insert_domain(
                        execution.ID,
                        record_value,
                        source=C.TECHNIQUE_DNS_CNAME,
                        status=C.DOMAIN_STATUS_NOT_RESOLVABLE
                    )
                    target_resolvable = False

            exposure_level = DNS_Details_Analyzer.calculate_exposure_level(
                record_type="CNAME",
                provider=provider,
                target_resolvable=target_resolvable
            )

            self.database.insert_dns_observation(
                execution.ID,
                domain,
                "CNAME",
                record_value,
                source="dns_resolver",
                technique=C.TECHNIQUE_DNS_CNAME,
                provider=provider,
                target_resolvable=target_resolvable,
                exposure_level=exposure_level
            )

        # ---------------------
        # NS
        # ---------------------
        ns_results = self.dns_ns_collector.collect(domain)

        for r in ns_results:
            record_value = (r.get("record") or "").strip().lower()
            if record_value.endswith("."):
                record_value = record_value[:-1]
            if not record_value:
                continue

            provider = DNS_Details_Analyzer.detect_provider_from_record(
                record_value,
                "NS"
            )

            exposure_level = DNS_Details_Analyzer.calculate_exposure_level(
                record_type="NS",
                provider=provider,
                target_resolvable=None
            )

            self.database.insert_dns_observation(
                execution.ID,
                domain,
                "NS",
                record_value,
                source="dns_resolver",
                technique=C.TECHNIQUE_DNS_NS,
                provider=provider,
                target_resolvable=None,
                exposure_level=exposure_level
            )

    def _run_security_headers(self, execution, domain):
        print("Ejecutando _run_security_headers")
        urls = [
            f"https://{domain}",
            f"https://www.{domain}",
            f"http://{domain}",
            f"http://www.{domain}",
        ]
        result = None
        used_url = None

        for url in urls:
            result = self.security_headers_collector.collect(url)
            if result:
                used_url = url
                break

        if not result:
            return

        for header, value in result.items():

            if value:
                status = "present"
            else:
                status = "missing"

            self.database.insert_security_header(
                execution.ID,
                domain,
                used_url,
                header,
                value,
                status
            )

    def _run_whois(self, execution):
        print("Consultando WHOIS...")
        whois_data = self.whois_collector.collect(execution.TARGET)
        if whois_data:
            self.database.insert_whois_result(
                execution.ID,
                execution.TARGET,
                whois_data
            )
    def _run_passive_emails(self, execution, seen_emails):
        print("Buscando emails pasivos...")
        email_results = self.email_collector.collect(execution.TARGET)

        for r in email_results:
            email = normalize_email(r["value"])
            if not email:
                continue

            if self._is_new_email(email, seen_emails):
                self.database.insert_email(
                    execution.ID,
                    email,
                    execution.TARGET,
                    technique=C.TECHNIQUE_PASSIVE_HTML,
                    source=r["context"],
                    context=r["context"]
                )
    def _run_crawler(self, execution, cfg, stats):

        wayback_results = []

        # -------------------------
        # LIVE CRAWLER
        # -------------------------
        crawl_urls = set()
        sources = {}  # url -> base | robots | sitemap

        # Base domain seeds
        for u in self._build_crawl_urls(execution.TARGET):
            crawl_urls.add(u)
            sources[u] = "base"

        # Robots + sitemap
        self._run_robots_and_sitemap(
            execution,
            cfg,
            crawl_urls,
            sources,
            stats
        )

        crawler_live = self.crawler_cls(
            start_url=list(crawl_urls),
            max_pages=self.crawler_live_max_pages,
            timeout=self.crawler_live_timeout,
            allowed_domain=execution.TARGET,
            sources=sources
        )

        print("Buscando emails mediante crawler (live + wayback)...")

        live_results = crawler_live.run()
        stats.live_pages_visited = len(live_results)

        # Contadores de páginas LIVE visitadas por origen
        stats.visited_from_robots = 0
        stats.visited_from_sitemap = 0
        stats.visited_discovered = 0

        for page in live_results:
            origin = page.get("origin", "discovered")

            if origin == "robots":
                stats.visited_from_robots += 1
            elif origin == "sitemap":
                stats.visited_from_sitemap += 1
            else:
                stats.visited_discovered += 1

        # -------------------------
        # WAYBACK CRAWLER
        # -------------------------
        if cfg["modules"].get("wayback"):
            print("Recolectando URLs históricas desde Wayback Machine...")
            wayback_urls = self.wayback_collector.collect(execution.TARGET)
            stats.wayback_urls_collected = len(wayback_urls)

            if wayback_urls:
                crawler_wb = self.crawler_cls(
                    start_url=[u["url"] for u in wayback_urls],
                    max_pages=self.crawler_wayback_max_pages,
                    timeout=self.crawler_wayback_timeout,
                    allowed_domain=None
                )

                wayback_results = crawler_wb.run()
                stats.wayback_pages_visited = len(wayback_results)

                for page in wayback_results:
                    page["origin"] = "wayback"

        return live_results, wayback_results

    def _run_robots_and_sitemap(self, execution, cfg, urls, sources, stats):
        print("Analizando robots.txt y sitemap.xml...")

        robots = self.robots_collector.collect(execution.TARGET)
        max_robots = int(cfg["limits"].get("robots_max_urls", 0))
        robots_added = 0

        for path in robots.get("paths", []):
            if max_robots and robots_added >= max_robots:
                break

            if "*" in path or "$" in path:
                continue

            url = f"https://{execution.TARGET}{path}"
            if url not in sources:
                urls.add(url)
            sources[url] = "robots"
            robots_added += 1

        print(f"[ROBOTS] URLs añadidas: {robots_added}")

        # Sitemaps
        sitemaps = robots.get("sitemaps", [])
        sitemap_urls_added = 0
        max_sitemap_urls = self.sitemap_collector.max_urls

        for sitemap_url in sitemaps:
            if sitemap_urls_added >= max_sitemap_urls:
                break

            sitemap_urls = self.sitemap_collector.collect(sitemap_url)

            for u in sitemap_urls:
                if sitemap_urls_added >= max_sitemap_urls:
                    break

                if u not in sources:
                    urls.add(u)
                    sources[u] = "sitemap"
                    sitemap_urls_added += 1

        print(f"[ROBOTS] Sitemaps detectados: {sitemaps}")
        print(f"[SITEMAP] URLs añadidas: {sitemap_urls_added}")
    def _process_crawl_results(self,execution,crawl_results,seen_emails,seen_creds):

        for page in crawl_results:
            page_url = page["url"]
            domain = urlparse(page_url).netloc
            origin = page.get("origin", "discovered")

            self.database.insert_crawler_result(
                execution.ID,
                page_url,
                page.get("emails", []),
                page.get("links", []),
                page.get("scripts", [])
            )

            # Emails HTML
            for e in page.get("emails", []):
                email = normalize_email(e)
                if not email:
                    continue

                if self._is_new_email(email, seen_emails):
                    self.database.insert_email(
                        execution.ID,
                        email,
                        domain,
                        technique=C.TECHNIQUE_CRAWLER_HTML,
                        source=page_url,
                        context=origin
                    )

            # Credenciales HTML
            raw_html = page.get("raw_html", "")
            creds = self.cred_parser.parse(raw_html, source=C.SOURCE_HTML)

            for ctype, value, source in creds:

                if self._is_new_credential(ctype, value, seen_creds):
                    self.database.insert_credential(
                        execution.ID,
                        ctype,
                        value,
                        technique=C.TECHNIQUE_CRAWLER_HTML,
                        source=page_url,
                        context=origin
                    )
    def _run_js_parsing(self, execution, cfg, live_results, seen_emails, seen_creds, stats):
        print("Parseando JS (solo live)...")

        stats.scripts_parse_limit = int(cfg["limits"]["js_max_scripts"])

        if not live_results:
            print("[JS] No hay páginas LIVE, se omite parsing JS")

        base_domain = urlparse(live_results[0]["url"]).netloc

        for page in live_results:
            if stats.scripts_parsed_ok >= stats.scripts_parse_limit:
                break

            if "@" in page["url"]:
                continue

            for script_url in page.get("scripts", []):
                if stats.scripts_parsed_ok >= stats.scripts_parse_limit:
                    break

                parsed = self.js_parser.parse(script_url, base_domain)
                if not parsed:
                    continue

                stats.scripts_parsed_ok += 1

                self.database.insert_js_result(
                    execution.ID,
                    parsed["script_url"],
                    parsed.get("emails", []),
                    parsed.get("urls", [])
                )

                # Emails JS
                for e in parsed.get("emails", []):
                    email = normalize_email(e)

                    if email:

                        if self._is_new_email(email, seen_emails):

                            self.database.insert_email(
                                execution.ID,
                                email,
                                urlparse(script_url).netloc,
                                technique=C.TECHNIQUE_JS_STATIC,
                                source=script_url,
                                context=" "
                            )

                # Credenciales JS
                raw_js = parsed.get("raw", "")
                creds = self.cred_parser.parse(raw_js, source=C.SOURCE_JS)

                for ctype, value, source in creds:

                    if self._is_new_credential(ctype, value, seen_creds):
                        self.database.insert_credential(
                            execution.ID,
                            ctype,
                            value,
                            technique=C.TECHNIQUE_JS_STATIC,
                            source=script_url,
                            context=" "
                        )
    def _run_scraping(self, execution, live_results, seen_emails, seen_creds, stats):
        print("Realizando scraping activo (solo live)...")

        if not live_results:
            print("[SCRAPING] No hay páginas LIVE, se omite scraping")

        for page in live_results:
            if "@" in page["url"]:
                continue

            stats.scrape_attempted += 1
            result = self.scraper.scrape(page["url"])
            if not result:
                stats.scrape_failed += 1
                continue

            stats.scrape_succeeded += 1

            for e in result["emails_dom"]:
                email = normalize_email(e)
                if email and self._is_new_email(email, seen_emails):
                    self.database.insert_email(
                        execution.ID,
                        email,
                        urlparse(page["url"]).hostname,
                        technique=C.TECHNIQUE_SCRAPING_DOM,
                        source=page["url"],
                        context=" "
                    )

            for ctype, value, source in result["credentials_dom"]:
                if self._is_new_credential(ctype, value, seen_creds):
                    self.database.insert_credential(
                        execution.ID,
                        ctype,
                        value,
                        technique=C.TECHNIQUE_SCRAPING_DOM,
                        source=page["url"],
                        context=" "
                    )

            for e in result["emails_json"]:
                email = normalize_email(e)
                if email and self._is_new_email(email, seen_emails):
                    self.database.insert_email(
                        execution.ID,
                        email,
                        urlparse(page["url"]).netloc,
                        technique=C.TECHNIQUE_SCRAPING_JSON,
                        source=page["url"],
                        context=" "
                    )

            for ctype, value, source in result["credentials_json"]:
                if self._is_new_credential(ctype, value, seen_creds):
                    self.database.insert_credential(
                        execution.ID,
                        ctype,
                        value,
                        technique=C.TECHNIQUE_SCRAPING_JSON,
                        source=page["url"],
                        context=" "
                    )


    def run(self, execution, cfg):

        self._validate_cfg(cfg)
        self._init_collectors(cfg)
        stats = ExecutionStats()

        # -------------------------------------------------
        # 0. Estado inicial
        # -------------------------------------------------

        seen_emails = set()
        seen_creds = set()
        seen_domains = set()

        all_domains = set()
        all_domains.add(execution.TARGET)

        live_results = []


        # -------------------------------------------------
        # 1. Subdominios (pasivo)
        # -------------------------------------------------

        if cfg["modules"]["subdomains"]:
            self._run_subdomains(execution, all_domains, seen_domains)

        # -------------------------------------------------
        # 2. WHOIS
        # -------------------------------------------------

        if cfg["modules"]["whois"]:
            self._run_whois(execution)

        # -------------------------------------------------
        # 3. DNS
        # -------------------------------------------------

        if cfg["modules"]["dns"]:
            self._run_dns(execution, cfg, all_domains)

        # -------------------------------------------------
        # 4. Emails pasivos (HTML simple)
        # -------------------------------------------------

        if cfg["modules"]["emails_passive"]:
            self._run_passive_emails(execution, seen_emails)

        # -------------------------------------------------
        # 5. Crawling HTML (LIVE + WAYBACK)
        # -------------------------------------------------

        if cfg["modules"]["crawler"]:
            live_results, wayback_results = self._run_crawler(execution, cfg, stats)

            self._process_crawl_results(
                execution,
                live_results + wayback_results,
                seen_emails,
                seen_creds)

        # -------------------------------------------------
        # 6. Parsing JS (SOLO LIVE)
        # -------------------------------------------------

        if cfg["modules"]["js_parsing"]:
            self._run_js_parsing(
                execution,
                cfg,
                live_results,
                seen_emails,
                seen_creds, stats)

        # -------------------------------------------------
        # 7. Scraping activo (SOLO LIVE)
        # -------------------------------------------------

        if cfg["modules"]["scraping"]:
            self._run_scraping(
                execution,
                live_results,
                seen_emails,
                seen_creds,
                stats
            )

        self.database.insert_metrics(execution.ID)

        metrics = self.database.get_execution_metrics(execution.ID)
        self._print_summary(metrics, stats)

