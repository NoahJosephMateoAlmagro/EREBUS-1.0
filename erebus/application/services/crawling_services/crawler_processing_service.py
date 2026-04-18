from urllib.parse import urlparse

import shared.constants as C
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class CrawlerProcessingService:
    """
    Service responsible for processing crawled pages, persisting raw crawl results
    and extracting emails and credentials from HTML content.
    """

    def __init__(self, uow, email_analyzer, cred_parser):
        """
        Args:
            uow: Unit of Work for persistence operations
            email_analyzer: Analyzer responsible for extracting and normalizing emails
            cred_parser: Parser responsible for extracting credentials
        """
        self.uow = uow
        self.email_analyzer = email_analyzer
        self.cred_parser = cred_parser

    def run(self, context) -> dict[str, int]:
        """
        Processes crawled pages and returns aggregated metrics.

        Args:
            context: Execution context containing crawl results and execution metadata

        Returns:
            dict: Processing metrics
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting crawler processing execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

        metrics = {
            "pages_processed": 0,
            "emails_matched_raw": 0,
            "emails_normalized": 0,
            "emails_duplicates_skipped": 0,
            "emails_inserted": 0,
            "credentials_matched_raw": 0,
            "credentials_duplicates_skipped": 0,
            "credentials_inserted": 0
        }

        try:
            for page in context.crawl_results:
                self._process_page(context, page, metrics)

        except Exception as e:
            Logger.error(
                f"Crawler processing error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )
            raise CollectorError(f"Crawler processing error: {e}") from e

        Logger.info(
            f"Finished crawler processing execution_id={execution_id} metrics={metrics}",
            context=self.__class__.__name__
        )

        return metrics

    def _process_page(
            self,
            context,
            page: dict[str, object],
            metrics: dict[str, int]
    ) -> None:
        """
        Processes a single crawled page, persists raw crawl data and extracts
        emails and credentials from HTML content.

        Args:
            context: Execution context containing execution metadata and deduplication state
            page: Crawled page data
            metrics: Mutable metrics dictionary updated in place
        """
        page_url = page["url"]
        html = page.get("html", "") or ""
        links = page.get("links", []) or []
        scripts = page.get("scripts", []) or []

        domain = urlparse(page_url).netloc
        origin = page.get("origin", "discovered")

        metrics["pages_processed"] += 1

        # -------- persist raw crawl result --------
        self.uow.crawler.insert_crawler_result(
            context.execution.ID,
            page_url,
            [],
            links,
            scripts
        )

        # -------- process emails --------
        extracted_emails = self.email_analyzer.extract(html)

        for raw in extracted_emails:
            metrics["emails_matched_raw"] += 1

            email = self.email_analyzer.normalize(raw)
            if not email:
                continue

            metrics["emails_normalized"] += 1

            if not context.is_new_email(email):
                metrics["emails_duplicates_skipped"] += 1
                continue

            self.uow.emails.insert_email(
                context.execution.ID,
                email,
                domain,
                technique=C.TECHNIQUE_CRAWLER_HTML,
                source=page_url,
                context=origin
            )

            metrics["emails_inserted"] += 1

        # -------- process credentials --------
        creds = self.cred_parser.parse(html, source=C.SOURCE_HTML)

        for ctype, value, _ in creds:
            metrics["credentials_matched_raw"] += 1

            if not context.is_new_credential(ctype, value):
                metrics["credentials_duplicates_skipped"] += 1
                continue

            self.uow.credentials.insert_credential(
                context.execution.ID,
                ctype,
                value,
                technique=C.TECHNIQUE_CRAWLER_HTML,
                source=page_url,
                context=origin
            )

            metrics["credentials_inserted"] += 1