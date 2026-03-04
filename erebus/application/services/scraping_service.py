from datetime import datetime
from urllib.parse import urlparse

import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleStatus, ModuleResponse


class ScrapingService:

    def __init__(self, scraper, cred_parser, email_analyzer, uow):
        self.scraper = scraper
        self.cred_parser = cred_parser
        self.email_analyzer = email_analyzer
        self.uow = uow

    def run(self, context) -> ModuleResponse:

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
            return response

        try:
            for page in context.live_results:

                if "@" in page["url"]:
                    continue

                metrics["pages_attempted"] += 1

                result = self.scraper.collect(page["url"])

                if not result:
                    metrics["pages_failed"] += 1
                    continue

                metrics["pages_succeeded"] += 1

                self._process(context, page, result, metrics)

            response.metrics = metrics

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Scraping module error: {e}")

        finally:
            response.finished_at = datetime.utcnow()

        return response

    def _process(self, context, page, result, metrics):

        html = result.get("html", "") or ""
        json_texts = result.get("json_texts", []) or []
        json_objects = result.get("json_objects", []) or []

        final_url = result.get("final_url") or page["url"]
        domain = urlparse(final_url).hostname

        # -------------------
        # DOM parsing
        # -------------------

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
                context=" "
            )

            metrics["emails_inserted"] += 1

        creds_dom = self.cred_parser.parse(html, source=C.SOURCE_HTML)

        for ctype, value, source in creds_dom:
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
                context=" "
            )

            metrics["credentials_inserted"] += 1

        # -------------------
        # JSON parsing
        # -------------------

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
                context=" "
            )

            metrics["emails_inserted"] += 1

        for obj in json_objects:
            creds_json = self.cred_parser.parse_json(obj, source=C.SOURCE_JSON)

            for ctype, value, source in creds_json:
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
                    context=" "
                )

                metrics["credentials_inserted"] += 1