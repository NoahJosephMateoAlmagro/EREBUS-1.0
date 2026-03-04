from datetime import datetime
from urllib.parse import urlparse

import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus


class FileParsingService:

    def __init__(self, file_parser, cred_parser, email_analyzer, uow):
        self.file_parser = file_parser
        self.cred_parser = cred_parser
        self.email_analyzer = email_analyzer
        self.uow = uow

    def run(self, context) -> ModuleResponse:

        response = ModuleResponse(
            module_name="file_parsing",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            # archivos
            "files_processed": 0,

            # emails
            "emails_matched_raw": 0,
            "emails_normalized_ok": 0,
            "emails_skipped_duplicate": 0,
            "emails_inserted": 0,

            # creds
            "credentials_matched_raw": 0,
            "credentials_skipped_duplicate": 0,
            "credentials_inserted": 0,
        }

        if not context.crawl_results:
            response.metrics = metrics
            response.finished_at = datetime.utcnow()
            return response

        try:
            for page in context.crawl_results:
                self._process_page(context, page, metrics)

            response.metrics = metrics

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"File parsing error: {e}")

        finally:
            response.finished_at = datetime.utcnow()

        return response

    # ----------------------------------------
    # Internal
    # ----------------------------------------

    def _process_page(self, context, page, metrics):

        origin = page.get("origin", "discovered")

        for url in page.get("links", []):

            result = self.file_parser.parse(url)
            if not result:
                continue

            metrics["files_processed"] += 1

            text = result["text"]
            technique = result["technique"]

            self._process_emails(context, text, url, technique, origin, metrics)
            self._process_credentials(context, text, url, technique, origin, metrics)

    def _process_emails(self, context, text, url, technique, origin, metrics):

        emails = self.email_analyzer.extract_from_file_text(text)

        for raw in emails:
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
                urlparse(url).netloc,
                technique=technique,
                source=url,
                context=origin
            )

            metrics["emails_inserted"] += 1

    def _process_credentials(self, context, text, url, technique, origin, metrics):

        creds = self.cred_parser.parse(text, source=C.SOURCE_FILE)

        for ctype, value, source in creds:
            metrics["credentials_matched_raw"] += 1

            if not context.is_new_credential(ctype, value):
                metrics["credentials_skipped_duplicate"] += 1
                continue

            self.uow.credentials.insert_credential(
                context.execution.ID,
                ctype,
                value,
                technique=technique,
                source=url,
                context=origin
            )

            metrics["credentials_inserted"] += 1