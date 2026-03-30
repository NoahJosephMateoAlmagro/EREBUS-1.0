from datetime import datetime
from urllib.parse import urlparse

import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
from shared.logger import Logger


class ScrapingService:
    """
    Service responsible for scraping live pages and extracting emails
    and credentials from HTML and JSON content.
    """

    def __init__(self, scraper, cred_parser, email_analyzer, uow):
        """
        Args:
            scraper: Collector responsible for retrieving page content
            cred_parser: Parser responsible for extracting credentials
            email_analyzer: Analyzer responsible for extracting and normalizing emails
            uow: Unit of Work for persistence operations
        """
        self.scraper = scraper
        self.cred_parser = cred_parser
        self.email_analyzer = email_analyzer
        self.uow = uow

    def run(self, context) -> ModuleResponse:
        """
        Executes scraping workflow over live page results.

        Args:
            context: Execution context containing target, execution metadata
                and live page results

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting scraping module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

        response = ModuleResponse(
            module_name="scraping",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "pages_attempted": 0,
            "pages_succeeded": 0,
            "pages_failed": 0,
            "emails_matched_raw": 0,
            "emails_normalized_ok": 0,
            "emails_skipped_duplicate": 0,
            "emails_inserted": 0,
            "credentials_matched_raw": 0,
            "credentials_skipped_duplicate": 0,
            "credentials_inserted": 0
        }

        if not context.live_results:
            response.metrics = metrics
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished scraping module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

            return response

        try:
            for page in context.live_results:
                try:
                    page_url = page["url"]

                    if "@" in page_url:
                        continue

                    metrics["pages_attempted"] += 1

                    result = self.scraper.collect(page_url)

                    if not result:
                        metrics["pages_failed"] += 1
                        continue

                    self._process(context, page, result, metrics)
                    metrics["pages_succeeded"] += 1

                except CollectorError as e:
                    metrics["pages_failed"] += 1

                    Logger.error(
                        f"Scraping collector error execution_id={execution_id} "
                        f"target={target} url={page.get('url', 'unknown')}: {e}",
                        context=self.__class__.__name__
                    )

                except Exception as e:
                    metrics["pages_failed"] += 1

                    Logger.error(
                        f"Unexpected scraping page error execution_id={execution_id} "
                        f"target={target} url={page.get('url', 'unknown')}: {e}",
                        context=self.__class__.__name__
                    )

            response.metrics = metrics

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in scraping module: {e}")

            Logger.error(
                f"Unexpected scraping module error execution_id={execution_id} "
                f"target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished scraping module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response

    def _process(self, context, page, result, metrics):
        """
        Processes a scraped page result and extracts emails and credentials
        from HTML and JSON content.

        Args:
            context: Execution context containing execution metadata and deduplication state
            page: Original page metadata
            result: Scraper output for the page
            metrics: Mutable metrics dictionary updated in place
        """
        html = result.get("html", "") or ""
        json_texts = result.get("json_texts", []) or []
        json_objects = result.get("json_objects", []) or []

        final_url = result.get("final_url") or page["url"]
        domain = urlparse(final_url).hostname

        emails_dom = self.email_analyzer.extract(html)

        for raw in emails_dom:
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
                technique=C.TECHNIQUE_SCRAPING_DOM,
                source=final_url,
                context=""
            )

            metrics["emails_inserted"] += 1

        creds_dom = self.cred_parser.parse(html, source=C.SOURCE_HTML)

        for ctype, value, _ in creds_dom:
            metrics["credentials_matched_raw"] += 1

            if not context.is_new_credential(ctype, value):
                metrics["credentials_skipped_duplicate"] += 1
                continue

            self.uow.credentials.insert_credential(
                context.execution.ID,
                ctype,
                value,
                technique=C.TECHNIQUE_SCRAPING_DOM,
                source=final_url,
                context=""
            )

            metrics["credentials_inserted"] += 1

        full_json_text = "\n".join(json_texts)
        emails_json = self.email_analyzer.extract(full_json_text)

        for raw in emails_json:
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
                technique=C.TECHNIQUE_SCRAPING_JSON,
                source=page["url"],
                context=""
            )

            metrics["emails_inserted"] += 1

        for obj in json_objects:
            creds_json = self.cred_parser.parse_json(obj, source=C.SOURCE_JSON)

            for ctype, value, _ in creds_json:
                metrics["credentials_matched_raw"] += 1

                if not context.is_new_credential(ctype, value):
                    metrics["credentials_skipped_duplicate"] += 1
                    continue

                self.uow.credentials.insert_credential(
                    context.execution.ID,
                    ctype,
                    value,
                    technique=C.TECHNIQUE_SCRAPING_JSON,
                    source=page["url"],
                    context=""
                )

                metrics["credentials_inserted"] += 1