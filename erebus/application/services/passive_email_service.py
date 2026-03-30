from datetime import datetime
import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus


class EmailPassiveService:

    def __init__(self, email_collector, email_analyzer, uow):
        self.email_collector = email_collector
        self.email_analyzer = email_analyzer
        self.uow = uow

    def run(self, context) -> ModuleResponse | None:

        response = ModuleResponse(
            module_name="email_passive",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "pages_fetched": 0,

            "emails_matched_raw": 0,
            "emails_normalized_ok": 0,
            "emails_skipped_duplicate": 0,
            "emails_inserted": 0
        }

        try:
            pages = self.email_collector.collect(context.execution.TARGET)
            metrics["pages_fetched"] = len(pages)

            for page in pages:
                html = page.get("html", "") or ""
                source_url = page.get("url")

                emails = self.email_analyzer.extract(html)

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
                        context.execution.TARGET,
                        technique=C.TECHNIQUE_PASSIVE_HTML,
                        source=source_url,
                        context=source_url
                    )

                    metrics["emails_inserted"] += 1

            response.metrics = metrics

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Email passive error: {e}")

        finally:
            response.finished_at = datetime.utcnow()

        return response