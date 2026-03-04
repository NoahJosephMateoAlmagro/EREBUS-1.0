from urllib.parse import urlparse

import shared.constants as C
from exceptions.exceptions import CollectorError


class CrawlerProcessingService:

    def __init__(self, uow, email_analyzer, cred_parser):
        self.uow = uow
        self.email_analyzer = email_analyzer
        self.cred_parser = cred_parser

    def run(self, context):

        metrics = {
            "pages_processed": 0,

            "emails_matched_raw": 0,
            "emails_normalized_ok": 0,
            "emails_skipped_duplicate": 0,
            "emails_inserted": 0,

            "credentials_matched_raw": 0,
            "credentials_skipped_duplicate": 0,
            "credentials_inserted": 0
        }

        try:
            for page in context.crawl_results:
                self._process_page(context, page, metrics)

        except Exception as e:
            raise CollectorError(f"Crawler processing error: {e}")

        return metrics

    def _process_page(self, context, page, metrics):

        page_url = page["url"]
        html = page.get("html", "") or ""
        links = page.get("links", []) or []
        scripts = page.get("scripts", []) or []

        domain = urlparse(page_url).netloc
        origin = page.get("origin", "discovered")

        metrics["pages_processed"] += 1

        # 1️⃣ Persistir resultado bruto
        self.uow.crawler.insert_crawler_result(
            context.execution.ID,
            page_url,
            [],
            links,
            scripts
        )

        # 2️⃣ Emails
        extracted_emails = self.email_analyzer.extract(html)

        for raw in extracted_emails:
            metrics["emails_matched_raw"] += 1

            email = self.email_analyzer.normalize(raw)
            if not email:
                continue

            metrics["emails_normalized_ok"] += 1

            if not context.is_new_email(email):
                metrics["emails_skipped_duplicate"] += 1
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

        # 3️⃣ Credenciales
        creds = self.cred_parser.parse(html, source=C.SOURCE_HTML)

        for ctype, value, source in creds:
            metrics["credentials_matched_raw"] += 1

            if not context.is_new_credential(ctype, value):
                metrics["credentials_skipped_duplicate"] += 1
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