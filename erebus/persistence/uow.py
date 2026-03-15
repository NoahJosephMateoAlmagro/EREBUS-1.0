import sqlite3
from persistence.repositories.domain_repository import DomainRepository
from persistence.repositories.email_repository import EmailRepository
from persistence.repositories.crawl_repository import CrawlRepository
from persistence.repositories.credential_repository import CredentialRepository
from persistence.repositories.header_repository import HeaderRepository
from persistence.repositories.whois_repository import WhoisRepository
from persistence.repositories.metrics_repository import MetricsRepository
from persistence.repositories.execution_repository import ExecutionRepository
from persistence.repositories.nmap_repository import NmapRepository
from persistence.repositories.api_repository import ApiRepository

class UnitOfWork:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

        self.domains = DomainRepository(conn)
        self.emails = EmailRepository(conn)
        self.crawler = CrawlRepository(conn)
        self.credentials = CredentialRepository(conn)
        self.headers = HeaderRepository(conn)
        self.whois = WhoisRepository(conn)
        self.metrics = MetricsRepository(conn)
        self.executions = ExecutionRepository(conn)
        self.nmap = NmapRepository(conn)
        self.apis = ApiRepository(conn)