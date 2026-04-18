from datetime import datetime
from urllib.parse import urlparse

import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import ParserError
from shared.logger import Logger


class JSParsingService:
    """
    Service responsible for parsing JavaScript resources extracted from live results
    and storing discovered emails and credentials.
    """

    def __init__(self, js_parser, cred_parser, email_analyzer, uow):
        """
        Args:
            js_parser: Parser responsible for retrieving and analyzing JavaScript resources
            cred_parser: Parser responsible for extracting credentials
            email_analyzer: Analyzer responsible for normalizing email values
            uow: Unit of Work for persistence operations
        """
        self.js_parser = js_parser
        self.cred_parser = cred_parser
        self.email_analyzer = email_analyzer
        self.uow = uow

    def run(self, context) -> ModuleResponse:
        """
        Executes JavaScript parsing workflow over collected live results.

        Args:
            context: Execution context containing target, execution metadata,
                configuration and live page results

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID
        scripts_limit = int(context.cfg["limits"]["js_max_scripts"])

        Logger.info(
            f"Starting JS parsing module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

        response = ModuleResponse(
            module_name="js_parsing",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "scripts_failed": 0,
            "scripts_processed": 0,
            "emails_matched_raw": 0,
            "emails_normalized": 0,
            "emails_duplicates_skipped": 0,
            "emails_inserted": 0,
            "credentials_matched_raw": 0,
            "credentials_duplicates_skipped": 0,
            "credentials_inserted": 0
        }

        if not context.live_results:
            response.status = ModuleStatus.SKIPPED
            response.metrics = metrics
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Skipping JS parsing module execution_id={execution_id} target={target} "
                f"because there are no live results to process",
                context=self.__class__.__name__
            )

            Logger.info(
                f"Finished JS parsing module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

            return response

        try:
            for page in context.live_results:
                if metrics["scripts_processed"] >= scripts_limit:
                    break

                try:
                    page_url = page.get("url")
                    if not page_url or "@" in page_url:
                        continue

                    self._process_page(context, page, metrics, response, scripts_limit)

                except Exception as e:
                    Logger.error(
                        f"Unexpected JS parsing page error execution_id={execution_id} "
                        f"target={target} url={page.get('url', 'unknown')}: {e}",
                        context=self.__class__.__name__
                    )

            if metrics["scripts_processed"] == 0 and metrics["scripts_failed"] == 0:
                response.status = ModuleStatus.SKIPPED
            elif metrics["scripts_processed"] == 0 and metrics["scripts_failed"] > 0:
                response.status = ModuleStatus.FAILED
            elif metrics["scripts_failed"] > 0:
                response.status = ModuleStatus.PARTIAL
            else:
                response.status = ModuleStatus.SUCCESS

            response.metrics = metrics

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in JS parsing module: {e}")

            Logger.error(
                f"Unexpected JS parsing error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished JS parsing module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response

    def _process_page(self, context, page, metrics, response, scripts_limit) -> None:
        """
        Processes JavaScript references from a single page result.

        Args:
            context: Execution context containing execution metadata and deduplication state
            page: Page result containing the source URL and script references
            metrics: Mutable metrics dictionary updated in place
            response: Module response used to accumulate non-fatal errors
        """
        origin = page.get("origin")

        technique = (
            C.TECHNIQUE_JS_STATIC_WAYBACK
            if origin == "wayback"
            else C.TECHNIQUE_JS_STATIC
        )

        page_url = page.get("url")
        page_host = self._extract_page_host(page_url)

        if not page_host:
            return

        scripts = page.get("scripts", []) or []

        for script_url in scripts:
            if metrics["scripts_processed"] >= scripts_limit:
                break

            try:
                parsed = self.js_parser.parse(script_url, page_host)
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

            except ParserError as e:
                metrics["scripts_failed"] += 1

                Logger.error(
                    f"JS parsing script error execution_id={context.execution.ID} "
                    f"script_url={script_url}: {e}",
                    context=self.__class__.__name__
                )

                response.errors.append(f"Script parse failed: {script_url} ({e})")
                continue

            except Exception as e:
                metrics["scripts_failed"] += 1

                Logger.error(
                    f"Unexpected JS script error execution_id={context.execution.ID} "
                    f"script_url={script_url}: {e}",
                    context=self.__class__.__name__
                )

                response.errors.append(
                    f"Unexpected script error in {script_url}: {e}"
                )
                continue

    def _process_emails(self, context, parsed, script_url, technique, metrics) -> None:
        """
        Extracts, normalizes and persists emails from parsed JavaScript content.

        Args:
            context: Execution context containing execution metadata and deduplication state
            parsed: Parsed JavaScript result
            script_url: Script source URL
            technique: Persistence technique label
            metrics: Mutable metrics dictionary updated in place
        """
        for raw in parsed.get("emails", []):
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
                urlparse(script_url).netloc,
                technique=technique,
                source=script_url,
                context=""
            )

            metrics["emails_inserted"] += 1

    def _process_credentials(self, context, parsed, script_url, technique, metrics) -> None:
        """
        Extracts and persists credentials from parsed JavaScript content.

        Args:
            context: Execution context containing execution metadata and deduplication state
            parsed: Parsed JavaScript result
            script_url: Script source URL
            technique: Persistence technique label
            metrics: Mutable metrics dictionary updated in place
        """
        raw_js = parsed.get("raw", "") or ""
        creds = self.cred_parser.parse(raw_js, source=C.SOURCE_JS)

        for ctype, value, _ in creds:
            metrics["credentials_matched_raw"] += 1

            if not context.is_new_credential(ctype, value):
                metrics["credentials_duplicates_skipped"] += 1
                continue

            self.uow.credentials.insert_credential(
                context.execution.ID,
                ctype,
                value,
                technique=technique,
                source=script_url,
                context=""
            )

            metrics["credentials_inserted"] += 1

    def _extract_page_host(self, page_url: str) -> str | None:
        """
        Extracts the host associated with a page URL, including original host
        recovery for Wayback URLs.

        Args:
            page_url (str): Page URL to inspect

        Returns:
            str | None: Extracted host or None if it cannot be determined
        """
        if "web.archive.org" in page_url:
            try:
                original = page_url.split("/web/", 1)[1]
                original_url = original.split("/", 1)[1]
                return urlparse(original_url).netloc
            except Exception:
                return None

        return urlparse(page_url).netloc