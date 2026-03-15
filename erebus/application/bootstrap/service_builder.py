from application.services.crawling_services.crawler_live_service import CrawlerLiveService
from application.services.crawling_services.crawler_wayback_service import CrawlerWaybackService
from collectors.passive.subdomains_Collector import SubdomainCollector
from collectors.passive.whois_Collector import WhoisCollector
from collectors.active.emails_Collector import EmailCollector
from collectors.passive.DNS_Collector import DNSCollector
from collectors.passive.DNS_Details.DNS_MX_Collector import DNS_MX_Collector
from collectors.passive.DNS_Details.DNS_TXT_Collector import DNS_TXT_Collector
from collectors.passive.DNS_Details.DNS_CNAME_Collector import DNS_CNAME_Collector
from collectors.passive.DNS_Details.DNS_NS_Collector import DNS_NS_Collector
from collectors.active.robots_Collector import RobotsCollector
from collectors.active.sitemap_Collector import SitemapCollector
from collectors.passive.waybackMachine_Collector import WaybackCollector
from collectors.active.http_headers_Collector import HttpHeadersCollector
from collectors.active.crawler import Crawler
from collectors.active.scraper import Scraper
from collectors.active.nmap_collector import NmapCollector
from application.services.nmap_service import NmapService
from application.services.APIs.shodan_service import ShodanService
from collectors.passive.APIs.shodan_collector import ShodanCollector

from processing.parsers.js_parser import JSParser
from processing.parsers.credential_parser import CredentialParser
from processing.parsers.file_parser.file_parser import FileParser
from processing.parsers.file_parser.txt_parser import TxtParser
from processing.parsers.file_parser.pdf_parser import PdfParser
from processing.parsers.file_parser.xml_parser import XmlParser
from processing.normalizers.email_normalizer import EmailAnalyzer
from processing.parsers.nmap_parser import NmapParser

from application.services.subdomain_service import SubdomainService
from application.services.whois_service import WhoisService
from application.services.passive_email_service import EmailPassiveService
from application.services.dns_services.dns_service import DNSService
from application.services.dns_services.dns_context_service import DNSContextService
from application.services.dns_services.dns_resolution_service import DNSResolutionService
from application.services.dns_services.dns_observation_service import DNSObservationService
from application.services.dns_services.http_headers_service import HttpHeadersService
from application.services.crawling_services.crawler_processing_service import CrawlerProcessingService
from application.services.crawling_services.seed_discovery_service import SeedDiscoveryService
from application.services.crawling_services.crawling_service import CrawlingService
from application.services.JS_parsing_service import JSParsingService
from application.services.file_parsing_service import FileParsingService
from application.services.scraping_service import ScrapingService
from application.services.print_debug_service import PrintDebugService



class ServiceBuilder:

    def __init__(self, uow, cfg, domain_validator):
        self.uow = uow
        self.cfg = cfg
        self.domain_validator = domain_validator

    def build(self):

        cfg = self.cfg
        uow = self.uow
        email_analyzer = EmailAnalyzer()

        # ---------- Collectors ----------

        subdomain_collector = SubdomainCollector(
            timeout=cfg["timeouts"]["http_subdomains"],
            limit=cfg["limits"]["subdomain_max"]
        )

        whois_collector = WhoisCollector()

        dns_collector = DNSCollector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )

        dns_mx_collector = DNS_MX_Collector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )

        dns_txt_collector = DNS_TXT_Collector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )

        dns_cname_collector = DNS_CNAME_Collector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )

        dns_ns_collector = DNS_NS_Collector(
            timeout=cfg["timeouts"]["dns_resolution"]
        )

        email_collector = EmailCollector(
            timeout=cfg["timeouts"]["http_passive_email"],
        )

        robots_collector = RobotsCollector(
            timeout=cfg["timeouts"]["http_robots"]
        )

        sitemap_collector = SitemapCollector(
            timeout=cfg["timeouts"]["http_sitemap"],
            max_urls=int(cfg["limits"]["sitemap_max_urls"])
        )

        wayback_collector = WaybackCollector(
            timeout=cfg["timeouts"]["wayback_cdx_api"],
            cdx_limit=int(cfg["limits"]["cdx_url_limit"])
        )

        http_headers_collector = HttpHeadersCollector(
            timeout=cfg["timeouts"]["http_headers"]
        )

        crawler_cls = Crawler

        js_parser = JSParser(
            email_analyzer=email_analyzer,
            connect_timeout=cfg["timeouts"]["js_connect"],
            read_timeout=cfg["timeouts"]["js_read"]
        )

        file_parser = FileParser(
            parsers=[TxtParser(), PdfParser(), XmlParser()],
            timeout=cfg["timeouts"].get("file_download"),
            max_size=int(cfg["limits"].get("file_max_size"))
        )

        cred_parser = CredentialParser()

        scraper = Scraper(
            timeout=cfg["timeouts"]["scraping_page_load"]
        )

        nmap_collector = NmapCollector(
            timeout=cfg["timeouts"].get("nmap_scan", 60),
            nmap_path=cfg.get("tools", {}).get("nmap_path")
        )
        nmap_parser = NmapParser()

        shodan_collector = ShodanCollector(timeout=cfg["timeouts"].get("http_subdomains"))

        # ---------- Services ----------

        subdomain_service = SubdomainService(
            subdomain_collector=subdomain_collector,
            uow=uow,
            domain_validator=self.domain_validator
        )

        whois_service = WhoisService(whois_collector, uow)

        email_passive_service = EmailPassiveService(
            email_collector,
            email_analyzer,
            uow
        )

        dns_service = DNSService(
            context_service=DNSContextService(dns_mx_collector, dns_txt_collector, uow),
            resolution_service=DNSResolutionService(dns_collector, uow, self.domain_validator),
            observation_service=DNSObservationService(dns_cname_collector, dns_ns_collector, dns_collector, uow),
            headers_service=HttpHeadersService(http_headers_collector, uow),
        )

        seed_discovery_service = SeedDiscoveryService(
            robots_collector=robots_collector,
            sitemap_collector=sitemap_collector
        )

        crawler_wayback_service = CrawlerWaybackService(
            wayback_collector=wayback_collector,
            limit=int(cfg["limits"]["wayback_max_snapshots"]),
            min_year=int(cfg["limits"]["wayback_min_year"])
        )
        crawler_live_service = CrawlerLiveService(
            crawler_cls=crawler_cls,
            timeout=cfg["timeouts"]["crawler_live_page"],
            max_pages=int(cfg["limits"]["crawler_live_max_pages"]),
        )
        crawler_processing_service = CrawlerProcessingService(
            uow,
            email_analyzer,
            cred_parser
        )

        crawling_service = CrawlingService(
            seed_discovery_service=seed_discovery_service,
            crawler_live_service=crawler_live_service,
            crawler_wayback_service=crawler_wayback_service,
            crawler_processing_service=crawler_processing_service,
        )

        js_parsing_service = JSParsingService(
            js_parser,
            cred_parser,
            email_analyzer,
            uow
        )

        file_parsing_service = FileParsingService(
            file_parser,
            cred_parser,
            email_analyzer,
            uow
        )

        scraping_service = ScrapingService(
            scraper,
            cred_parser,
            email_analyzer,
            uow
        )

        nmap_service = NmapService(
            nmap_collector,
            nmap_parser,
            uow
        )

        shodan_service = ShodanService(
            shodan_collector,
            uow,
            self.domain_validator
        )

        print_debug_service = PrintDebugService(uow)

        return {
            "subdomain": subdomain_service,
            "whois": whois_service,
            "emails_passive": email_passive_service,
            "dns": dns_service,
            "nmap": nmap_service,
            "crawling": crawling_service,
            "crawler_processing": crawler_processing_service,
            "js": js_parsing_service,
            "file": file_parsing_service,
            "scraping": scraping_service,
            "debug": print_debug_service,
            "shodan": shodan_service
        }
