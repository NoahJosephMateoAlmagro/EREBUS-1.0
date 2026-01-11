from urllib.parse import urlparse

from collectors.passive.dns import DNSCollector
from collectors.passive.subdomains import SubdomainCollector
from collectors.passive.whoisCollector import WhoisCollector
from collectors.passive.emails import EmailCollector
from collectors.passive.crawler import Crawler
from collectors.passive.js_parser import JSParser
from collectors.passive.credential_parser import CredentialParser
from collectors.active.scraper import Scraper
from normalizers.email_normalizer import normalize_email

from collectors.passive.waybackMachine import WaybackCollector

import core.constants as C



class Orchestrator:

    def __init__(self, database):
        self.database = database


    # -------------------------------------------------
    # Utils
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

        if "modules" not in cfg or "limits" not in cfg:
            raise ValueError(
                "Configuración inválida: se esperaban las claves 'modules' y 'limits'"
            )
    def _init_collectors(self, cfg):

        # -------------------------------------------------
        # Inicialización de collectors (desde cfg)
        # -------------------------------------------------

        # Pasivos
        self.subdomain_collector = SubdomainCollector(
            timeout=cfg["timeouts"]["http_subdomains"]
        )

        self.whois_collector = WhoisCollector()

        self.dns_collector = DNSCollector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )

        self.email_collector = EmailCollector(
            timeout=cfg["timeouts"]["http_email_passive"]
        )

        # Crawler
        self.crawler_cls = Crawler
        self.crawler_timeout = cfg["timeouts"]["http_crawler_page"]
        self.crawler_max_pages = int(cfg["limits"]["max_pages"])

        # JS
        self.js_parser = JSParser(
            connect_timeout=cfg["timeouts"]["js_connect"],
            read_timeout=cfg["timeouts"]["js_read"]
        )

        # Credenciales
        self.cred_parser = CredentialParser()

        # Scraping
        self.scraper = Scraper(
            timeout=cfg["timeouts"]["scraping_page_load"]
        )

        # Emails en URLS históricas

        self.wayback_collector = WaybackCollector(
            timeout=cfg["timeouts"].get("wayback_timeout", 10),
            limit=cfg["limits"].get("wayback_urls", 50)
        )

    # -----------------------------
    # Dedup logic (orchestration)
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
    # -------------------------------------------------
    # Main
    # -------------------------------------------------


    def run(self, execution, cfg):

        self._validate_cfg(cfg)
        self._init_collectors(cfg)

        # -------------------------------------------------
        # 0. Estado inicial
        # -------------------------------------------------

        seen_emails = set()
        seen_creds = set()
        seen_domains = set()

        all_domains = set()
        all_domains.add(execution.TARGET)

        emails_html = set()
        emails_crawler = set()
        emails_js = set()
        emails_scraping_dom = set()
        emails_scraping_json = set()
        emails_from_wayback = set()
        emails_from_live = set()

        creds_html = set()
        creds_js = set()
        creds_scraping_dom = set()
        creds_scraping_json = set()


        # -------------------------------------------------
        # 1. Subdominios (pasivo)
        # -------------------------------------------------

        if cfg["modules"]["subdomains"]:
            print("Encontrando subdominios...")
            subdomains = self.subdomain_collector.collect(execution.TARGET)

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

        # -------------------------------------------------
        # 2. WHOIS
        # -------------------------------------------------

        if cfg["modules"]["whois"]:
            print("Consultando WHOIS...")
            whois_data = self.whois_collector.collect(execution.TARGET)
            if whois_data:
                self.database.insert_whois_result(
                    execution.ID,
                    execution.TARGET,
                    whois_data
                )

        # -------------------------------------------------
        # 3. DNS
        # -------------------------------------------------

        if cfg["modules"]["dns"]:
            print("Resolviendo DNS...")
            max_dns = int(cfg["limits"]["max_dns"])
            domains_to_resolve = list(all_domains)[:max_dns]

            for domain in domains_to_resolve:
                clean_domain = self._is_valid_domain(domain)
                if not clean_domain:
                    continue

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

        # -------------------------------------------------
        # 4. Emails pasivos (HTML simple)
        # -------------------------------------------------

        if cfg["modules"]["emails_passive"]:
            print("Buscando emails pasivos...")
            email_results = self.email_collector.collect(execution.TARGET)

            for r in email_results:
                email = normalize_email(r["value"])
                if email:
                    emails_html.add(email)  # Métricas

                    if self._is_new_email(email, seen_emails):
                        self.database.insert_email(
                            execution.ID,
                            email,
                            execution.TARGET,
                            technique=C.TECHNIQUE_PASSIVE_HTML,
                            source=r["context"],
                            context=r["context"]
                        )

        # -------------------------------------------------
        # 5. Crawling HTML (LIVE + WAYBACK)
        # -------------------------------------------------

        if cfg["modules"]["crawler"]:
            print("Buscando emails mediante crawler (live + wayback)...")

            live_results = []
            wayback_results = []

            # -------------------------
            # LIVE CRAWLER
            # -------------------------
            live_urls = list(self._build_crawl_urls(execution.TARGET))

            crawler_live = self.crawler_cls(
                start_url=live_urls,
                max_pages=self.crawler_max_pages,
                timeout=self.crawler_timeout,
                allowed_domain=execution.TARGET
            )

            live_results = crawler_live.run()

            for page in live_results:
                page["origin"] = "live"

            # -------------------------
            # WAYBACK CRAWLER (SOLO HTML)
            # -------------------------
            if cfg["modules"].get("wayback"):
                print("Recolectando URLs históricas desde Wayback Machine...")
                wayback_urls = self.wayback_collector.collect(execution.TARGET)

                if wayback_urls:
                    crawler_wb = self.crawler_cls(
                        start_url=list(wayback_urls),
                        max_pages=cfg["limits"].get("wayback_pages", 20),
                        timeout=self.crawler_timeout,
                        allowed_domain=None
                    )

                    wayback_results = crawler_wb.run()

                    for page in wayback_results:
                        page["origin"] = "wayback"

            # -------------------------
            # PROCESADO HTML UNIFICADO
            # -------------------------
            all_crawl_results = live_results + wayback_results

            for page in all_crawl_results:
                page_url = page["url"]
                domain = urlparse(page_url).netloc
                origin = page["origin"]

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

                    emails_crawler.add(email)

                    if origin == "wayback":
                        emails_from_wayback.add(email)
                    else:
                        emails_from_live.add(email)

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
                    creds_html.add((ctype, value))

                    if self._is_new_credential(ctype, value, seen_creds):
                        self.database.insert_credential(
                            execution.ID,
                            ctype,
                            value,
                            technique=C.TECHNIQUE_CRAWLER_HTML,
                            source=page_url,
                            context=origin
                        )

        # -------------------------------------------------
        # 6. Parsing JS (SOLO LIVE)
        # -------------------------------------------------

        if cfg["modules"]["js_parsing"]:
            print("Parseando JS (solo live)...")

            max_scripts = int(cfg["limits"]["max_scripts"])
            parsed_scripts = 0

            base_domain = urlparse(live_urls[0]).netloc

            for page in live_results:
                if parsed_scripts >= max_scripts:
                    break

                if "@" in page["url"]:
                    continue

                for script_url in page.get("scripts", []):
                    if parsed_scripts >= max_scripts:
                        break

                    parsed = self.js_parser.parse(script_url, base_domain)
                    if not parsed:
                        continue

                    parsed_scripts += 1

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
                            emails_js.add(email)

                            if self._is_new_email(email, seen_emails):
                                self.database.insert_email(
                                    execution.ID,
                                    email,
                                    urlparse(script_url).netloc,
                                    technique=C.TECHNIQUE_JS_STATIC,
                                    source=script_url,
                                    context="live"
                                )

                    # Credenciales JS
                    raw_js = parsed.get("raw", "")
                    creds = self.cred_parser.parse(raw_js, source=C.SOURCE_JS)

                    for ctype, value, source in creds:
                        creds_js.add((ctype, value))

                        if self._is_new_credential(ctype, value, seen_creds):
                            self.database.insert_credential(
                                execution.ID,
                                ctype,
                                value,
                                technique=C.TECHNIQUE_JS_STATIC,
                                source=script_url,
                                context="live"
                            )

            print(f"[JS] Scripts parseados: {parsed_scripts}/{max_scripts}")

        # -------------------------------------------------
        # 7. Scraping activo (SOLO LIVE)
        # -------------------------------------------------

        if cfg["modules"]["scraping"]:
            print("Realizando scraping activo (solo live)...")

            for page in live_results:
                if "@" in page["url"]:
                    continue

                result = self.scraper.scrape(page["url"])
                if not result:
                    continue

                for e in result["emails_dom"]:
                    email = normalize_email(e)
                    if email:
                        emails_scraping_dom.add(email)

                        if self._is_new_email(email, seen_emails):
                            self.database.insert_email(
                                execution.ID,
                                email,
                                urlparse(page["url"]).hostname,
                                technique=C.TECHNIQUE_SCRAPING_DOM,
                                source=page["url"],
                                context="rendered_dom"
                            )

                for ctype, value, source in result["credentials_dom"]:
                    creds_scraping_dom.add((ctype, value))

                    if self._is_new_credential(ctype, value, seen_creds):
                        self.database.insert_credential(
                            execution.ID,
                            ctype,
                            value,
                            technique=C.TECHNIQUE_SCRAPING_DOM,
                            source=page["url"],
                            context="rendered"
                        )

                for e in result["emails_json"]:
                    email = normalize_email(e)
                    if email:
                        emails_scraping_json.add(email)

                        if self._is_new_email(email, seen_emails):
                            self.database.insert_email(
                                execution.ID,
                                email,
                                urlparse(page["url"]).netloc,
                                technique=C.TECHNIQUE_SCRAPING_JSON,
                                source=page["url"],
                                context="fetch/xhr"
                            )

                for ctype, value, source in result["credentials_json"]:
                    creds_scraping_json.add((ctype, value))

                    if self._is_new_credential(ctype, value, seen_creds):
                        self.database.insert_credential(
                            execution.ID,
                            ctype,
                            value,
                            technique=C.TECHNIQUE_SCRAPING_JSON,
                            source=page["url"],
                            context="fetch/xhr"
                        )

        #--------------------------------------------------
        # Métrica A/B (scraping vs no scraping)
        # -------------------------------------------------

        baseline = emails_html | emails_crawler | emails_js
        baseline_creds = creds_html | creds_js

        emails_scraping_total = emails_scraping_dom | emails_scraping_json
        creds_scraping_total = creds_scraping_dom | creds_scraping_json

        emails_scraping_new = emails_scraping_total - baseline
        creds_scraping_new = creds_scraping_total - baseline_creds

        emails_total_with_wayback = emails_from_live | emails_from_wayback

        # ---- Logs ----

        print(f"[EMAILS] passive_html: {len(emails_html)}")
        print(f"[EMAILS] crawler_html: {len(emails_crawler)}")
        print(f"[EMAILS] js_static: {len(emails_js)}")
        print(f"[EMAILS] scraping_dom: {len(emails_scraping_dom)}")
        print(f"[EMAILS] scraping_json: {len(emails_scraping_json)}")
        print(f"[EMAILS] scraping_total: {len(emails_scraping_total)}")
        print(f"[EMAILS] nuevas por scraping: {len(emails_scraping_new)}")

        print(f"[CREDS] html: {len(creds_html)}")
        print(f"[CREDS] js_static: {len(creds_js)}")
        print(f"[CREDS] scraping_dom: {len(creds_scraping_dom)}")
        print(f"[CREDS] scraping_json: {len(creds_scraping_json)}")
        print(f"[CREDS] scraping_total: {len(creds_scraping_total)}")
        print(f"[CREDS] nuevas por scraping: {len(creds_scraping_new)}")

        # ---- Persistencia ----

        self.database.insert_metric(execution.ID, "emails_passive_html", len(emails_html))
        self.database.insert_metric(execution.ID, "emails_crawler_html", len(emails_crawler))
        self.database.insert_metric(execution.ID, "emails_js_static", len(emails_js))
        self.database.insert_metric(execution.ID, "emails_scraping_dom", len(emails_scraping_dom))
        self.database.insert_metric(execution.ID, "emails_scraping_json", len(emails_scraping_json))
        self.database.insert_metric(execution.ID, "emails_scraping_total", len(emails_scraping_total))
        self.database.insert_metric(execution.ID, "emails_scraping_new", len(emails_scraping_new))

        self.database.insert_metric(execution.ID, "creds_html", len(creds_html))
        self.database.insert_metric(execution.ID, "creds_js_static", len(creds_js))
        self.database.insert_metric(execution.ID, "creds_scraping_dom", len(creds_scraping_dom))
        self.database.insert_metric(execution.ID, "creds_scraping_json", len(creds_scraping_json))
        self.database.insert_metric(execution.ID, "creds_scraping_total", len(creds_scraping_total))
        self.database.insert_metric(execution.ID, "creds_scraping_new", len(creds_scraping_new))

        self.database.insert_metric(execution.ID,"wayback_urls",len(wayback_urls))
        self.database.insert_metric(execution.ID, "emails_from_wayback", len(emails_from_wayback))
        self.database.insert_metric(execution.ID,"emails_from_live",len(emails_from_live))
        self.database.insert_metric(execution.ID,"emails_total_with_wayback",len(emails_total_with_wayback))


