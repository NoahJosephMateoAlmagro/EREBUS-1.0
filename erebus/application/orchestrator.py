from urllib.parse import urlparse

from collectors.passive.DNS_Collector import DNSCollector
from collectors.passive.DNS_Details.DNS_MX_Collector import DNS_MX_Collector
from collectors.passive.DNS_Details.DNS_TXT_Collector import DNS_TXT_Collector
from collectors.passive.DNS_Details.DNS_CNAME_Collector import DNS_CNAME_Collector
from collectors.passive.DNS_Details.DNS_NS_Collector import DNS_NS_Collector
from collectors.passive.subdomains_Collector import SubdomainCollector
from collectors.passive.whois_Collector import WhoisCollector
from collectors.active.emails_Collector import EmailCollector
from collectors.active.crawler import Crawler
from processing.parsers.js_parser import JSParser
from processing.parsers.credential_parser import CredentialParser
from collectors.active.scraper import Scraper
from processing.normalizers.email_normalizer import normalize_email
from collectors.active.robots_Collector import RobotsCollector
from collectors.active.sitemap_Collector import SitemapCollector
from collectors.passive.waybackMachine_Collector import WaybackCollector
from collectors.active.http_headers_Collector import HttpHeadersCollector
from processing.parsers.file_parser.file_parser import FileParser
from processing.parsers.file_parser.txt_parser import TxtParser
from processing.parsers.file_parser.pdf_parser import PdfParser
from processing.parsers.file_parser.xml_parser import XmlParser
from application.objects.execution_context import ExecutionContext
from application.execution_stats import ExecutionStats


from application.services.subdomain_service import SubdomainService
from application.services.whois_service import WhoisService
from application.services.passive_email_service import EmailPassiveService
from application.services.dns_services.dns_service import DNSService
from application.services.dns_services.dns_context_service import DNSContextService
from application.services.dns_services.dns_resolution_service import DNSResolutionService
from application.services.dns_services.dns_observation_service import DNSObservationService
from application.services.dns_services.http_headers_service import HttpHeadersService
from application.services.crawling_services.crawler_processing_service import CrawlerProcessingService
from application.services.crawling_services.crawling_service import CrawlingService
from application.services.crawling_services.seed_discovery_service import SeedDiscoveryService
from application.services.JS_parsing_service import JSParsingService
from application.services.file_parsing_service import FileParsingService
from application.services.scraping_service import ScrapingService
from application.services.print_debug_service import PrintDebugService


class Orchestrator:

    def __init__(self, uow):
        self.uow = uow
    # -------------------------------------------------
    # Utils - Prints
    # -------------------------------------------------

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

        # File parser (archivos descargables)
        self.file_parser = FileParser(
            parsers=[
                TxtParser(),
                PdfParser(),
                XmlParser()
            ],
            timeout=cfg["timeouts"].get("file_download"),
            max_size=int(cfg["limits"].get("file_max_size"))
        )


        # Credenciales
        self.cred_parser = CredentialParser()

        # Scraping (activo)
        self.scraper = Scraper(
            timeout=cfg["timeouts"]["scraping_page_load"]
        )

        #Cabeceras
        self.http_headers_collector = HttpHeadersCollector(
            timeout=cfg["timeouts"]["http_headers"]
        )

        # Wayback (CDX)
        self.wayback_collector = WaybackCollector(
            timeout=cfg["timeouts"]["wayback_cdx_api"],
            limit=int(cfg["limits"]["wayback_max_snapshots"]),
            cdx_limit=int(cfg["limits"]["cdx_url_limit"]),
            min_year=int(cfg["limits"]["wayback_min_year"])
        )

        #SERVICIOS

        self.subdomain_service = SubdomainService(
            subdomain_collector=self.subdomain_collector,
            uow=self.uow,
            domain_validator=self._is_valid_domain
        )

        self.whois_service = WhoisService(
            whois_collector=self.whois_collector,
            uow=self.uow
        )

        self.email_passive_service = EmailPassiveService(
            email_collector=self.email_collector,
            uow=self.uow
        )

        self.dns_service = DNSService(
            context_service=DNSContextService(self.dns_mx_collector, self.dns_txt_collector, self.uow),
            resolution_service=DNSResolutionService(self.dns_collector, self.uow, self._is_valid_domain),
            observation_service=DNSObservationService(self.dns_cname_collector, self.dns_ns_collector, self.dns_collector, self.uow),
            headers_service=HttpHeadersService(self.http_headers_collector, self.uow),
        )

        self.crawler_processing_service = CrawlerProcessingService(
            uow=self.uow,
            cred_parser=self.cred_parser,
            normalize_email_func=normalize_email
        )

        self.seed_discovery_service = SeedDiscoveryService(
            robots_collector=self.robots_collector,
            sitemap_collector=self.sitemap_collector
        )

        self.crawling_service = CrawlingService(
            crawler_cls=self.crawler_cls,
            seed_discovery_service=self.seed_discovery_service,
            wayback_collector=self.wayback_collector,
            live_timeout=self.crawler_live_timeout,
            live_max_pages=self.crawler_live_max_pages,
            wayback_timeout=self.crawler_wayback_timeout,
            wayback_max_pages=self.crawler_wayback_max_pages,
        )

        self.js_parsing_service = JSParsingService(
            js_parser=self.js_parser,
            cred_parser=self.cred_parser,
            uow=self.uow
        )
        self.file_parsing_service = FileParsingService(
            file_parser=self.file_parser,
            cred_parser=self.cred_parser,
            uow=self.uow
        )
        self.scraping_service = ScrapingService(
            scraper=self.scraper,
            cred_parser=self.cred_parser,
            uow=self.uow
        )

        self.print_debug_service = PrintDebugService(self.uow)

    # -----------------------------
    # Utils - Helpers
    # -----------------------------
    def _extract_base_domain_for_js(self, page_url: str):
        if "web.archive.org" in page_url:
            try:
                original = page_url.split("/web/", 1)[1]
                original_url = original.split("/", 1)[1]
                return urlparse(original_url).netloc
            except Exception:
                return None
        return urlparse(page_url).netloc

        # En wayback se devuelve algo como https://web.archive.org/web/20180101010101/https://example.com/path/page.html,
        # este helper sirrve para que si viene de ahí coja example.com


    # -------------------------------------------------
    # Main
    # -------------------------------------------------

    def run(self, execution, cfg):

        self._validate_cfg(cfg)
        self._init_collectors(cfg)

        context = ExecutionContext(execution, cfg)

        # -------------------------------------------------
        # 1. Subdominios (pasivo)
        # -------------------------------------------------

        if cfg["modules"]["subdomains"]:
            self.subdomain_service.run(context)

        # -------------------------------------------------
        # 2. WHOIS
        # -------------------------------------------------

        if cfg["modules"]["whois"]:
            self.whois_service.run(context)

        # -------------------------------------------------
        # 3. DNS
        # -------------------------------------------------

        if cfg["modules"]["dns"]:
            self.dns_service.run(context)

        # -------------------------------------------------
        # 4. Emails pasivos (HTML simple)
        # -------------------------------------------------

        if cfg["modules"]["emails_passive"]:
            self.email_passive_service.run(context)

        # -------------------------------------------------
        # 5. Crawling HTML (LIVE + WAYBACK)
        # -------------------------------------------------


        if cfg["modules"]["crawler"]:
            self.crawling_service.run(context)
            self.crawler_processing_service.run(context)

        # -------------------------------------------------
        # 6. Parsing JS
        # -------------------------------------------------

        if cfg["modules"]["js_parsing"]:
            self.js_parsing_service.run(context)

        # -------------------------------------------------
        # 7. Parsing de archivos
        # -------------------------------------------------

        if cfg["modules"].get("file_parsing"):
            self.file_parsing_service.run(context)
        # -------------------------------------------------
        # 8. Scraping activo (SOLO LIVE)
        # -------------------------------------------------

        if cfg["modules"]["scraping"]:
            self.scraping_service.run(context)

        self.uow.metrics.insert_metrics(execution.ID)
        self.print_debug_service.print_summary(
            execution.ID,
            context.stats
        )


