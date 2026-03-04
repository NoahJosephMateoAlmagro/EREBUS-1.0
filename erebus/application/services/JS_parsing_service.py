from datetime import datetime
from urllib.parse import urlparse

import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus


class JSParsingService:

    def __init__(self, js_parser, cred_parser, email_analyzer, uow):
        self.js_parser = js_parser
        self.cred_parser = cred_parser
        self.email_analyzer = email_analyzer
        self.uow = uow

    # ----------------------------------------
    # Public API
    # ----------------------------------------

    def run(self, context) -> ModuleResponse:

        response = ModuleResponse(
            module_name="js_parsing",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "scripts_limit": int(context.cfg["limits"]["js_max_scripts"]),
            "scripts_processed": 0,

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

                if metrics["scripts_processed"] >= metrics["scripts_limit"]:
                    break

                if "@" in page["url"]:
                    continue

                self._process_page(context, page, metrics)

            response.metrics = metrics

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"JS parsing error: {e}")

        finally:
            response.finished_at = datetime.utcnow()

        return response

    # ----------------------------------------
    # Internal
    # ----------------------------------------

    def _process_page(self, context, page, metrics):

        origin = page.get("origin")

        technique = (
            C.TECHNIQUE_JS_STATIC_WAYBACK
            if origin == "wayback"
            else C.TECHNIQUE_JS_STATIC
        )

        base_domain = self._extract_base_domain(page["url"])
        if not base_domain:
            return

        scripts = page.get("scripts", []) or []

        for script_url in scripts:

            if metrics["scripts_processed"] >= metrics["scripts_limit"]:
                break

            parsed = self.js_parser.parse(script_url, base_domain)
            if not parsed:
                continue

            metrics["scripts_processed"] += 1

            self.uow.crawler.insert_js_result(
                context.execution.ID,
                parsed["script_url"],
                parsed.get("emails", []),
                parsed.get("urls", [])
            )

            self._process_emails(context, parsed, script_url, technique, metrics)
            self._process_credentials(context, parsed, script_url, technique, metrics)

    def _process_emails(self, context, parsed, script_url, technique, metrics):

        for raw in parsed.get("emails", []):
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
                urlparse(script_url).netloc,
                technique=technique,
                source=script_url,
                context=" "
            )

            metrics["emails_inserted"] += 1

    def _process_credentials(self, context, parsed, script_url, technique, metrics):

        raw_js = parsed.get("raw", "") or ""
        creds = self.cred_parser.parse(raw_js, source=C.SOURCE_JS)

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
                source=script_url,
                context=" "
            )

            metrics["credentials_inserted"] += 1

    def _extract_base_domain(self, page_url: str):

        if "web.archive.org" in page_url:
            try:
                original = page_url.split("/web/", 1)[1]
                original_url = original.split("/", 1)[1]
                return urlparse(original_url).netloc
            except Exception:
                return None

        return urlparse(page_url).netloc