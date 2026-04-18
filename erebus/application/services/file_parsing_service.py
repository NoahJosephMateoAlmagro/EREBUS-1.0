from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import threading

import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import ParserError
from shared.logger import Logger


class FileParsingService:
    """
    Service responsible for discovering parsable file links, extracting text content
    and storing emails and credentials found in those files.
    """

    def __init__(self, file_parser, cred_parser, email_analyzer, uow):
        """
        Args:
            file_parser: Parser responsible for retrieving and extracting file text
            cred_parser: Parser responsible for extracting credentials
            email_analyzer: Analyzer responsible for extracting and normalizing emails
            uow: Unit of Work for persistence operations
        """
        self.file_parser = file_parser
        self.cred_parser = cred_parser
        self.email_analyzer = email_analyzer
        self.uow = uow

    def run(self, context) -> ModuleResponse:
        """
        Executes file parsing workflow over file links discovered during crawling.

        Args:
            context: Execution context containing crawl results, configuration
                and execution metadata

        Returns:
            ModuleResponse: Execution result with status, metrics and errors
        """
        target = context.execution.TARGET
        execution_id = context.execution.ID

        Logger.info(
            f"Starting file parsing module execution_id={execution_id} target={target}",
            context=self.__class__.__name__
        )

        seen_files = set()

        response = ModuleResponse(
            module_name="file_parsing",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "file_links_seen": 0,
            "files_attempted": 0,
            "files_processed": 0,
            "files_failed": 0,
            "emails_matched_raw": 0,
            "emails_normalized_ok": 0,
            "emails_skipped_duplicate": 0,
            "emails_inserted": 0,
            "credentials_matched_raw": 0,
            "credentials_skipped_duplicate": 0,
            "credentials_inserted": 0,
        }

        if not context.crawl_results:
            response.metrics = metrics
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished file parsing module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

            return response

        try:
            # -------- collect file links --------

            file_links = []

            for page in context.crawl_results:
                origin = page.get("origin", "discovered")

                for url in page.get("links", []):
                    metrics["file_links_seen"] += 1

                    parsed = urlparse(url)
                    ext = Path(parsed.path).suffix.lower()

                    if ext not in C.FILE_EXTENSIONS_TO_PARSE:
                        continue

                    if url in seen_files:
                        continue

                    seen_files.add(url)
                    file_links.append((url, origin))

            # -------- limits --------

            max_files = context.cfg["limits"].get("file_max_files", 100)
            max_workers = context.cfg["limits"].get("file_max_workers", 4)

            file_links = file_links[:max_files]

            lock = threading.Lock()

            # -------- parallel execution --------

            def worker(url, origin) -> None:
                with lock:
                    metrics["files_attempted"] += 1

                try:
                    result = self.file_parser.parse(url)

                    if not result:
                        with lock:
                            metrics["files_failed"] += 1
                        return

                    text = result.get("text", "")
                    technique = result.get("technique", "file_parser")

                    with lock:
                        metrics["files_processed"] += 1

                    self._process_emails(context, text, url, technique, origin, metrics, lock)
                    self._process_credentials(context, text, url, technique, origin, metrics, lock)

                except ParserError as e:
                    with lock:
                        metrics["files_failed"] += 1

                    Logger.error(
                        f"File parser error execution_id={execution_id} "
                        f"target={target} url={url}: {e}",
                        context=self.__class__.__name__
                    )

                except Exception as e:
                    with lock:
                        metrics["files_failed"] += 1

                    Logger.error(
                        f"Unexpected file worker error execution_id={execution_id} "
                        f"target={target} url={url}: {e}",
                        context=self.__class__.__name__
                    )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(worker, url, origin)
                    for url, origin in file_links
                ]

                for future in futures:
                    future.result()

            response.metrics = metrics

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in file parsing module: {e}")

            Logger.error(
                f"Unexpected file parsing error execution_id={execution_id} target={target}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished file parsing module execution_id={execution_id} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response

    def _process_emails(self, context, text, url, technique, origin, metrics, lock) -> None:
        """
        Extracts, normalizes and persists emails from parsed file text.

        Args:
            context: Execution context containing execution metadata and deduplication state
            text: Parsed file text
            url: Original file URL
            technique: Persistence technique label
            origin: Source origin label
            metrics: Mutable metrics dictionary updated in place
            lock: Lock used for thread-safe metric updates
        """
        emails = self.email_analyzer.extract_from_file_text(text)

        for raw in emails:
            with lock:
                metrics["emails_matched_raw"] += 1

            email = self.email_analyzer.normalize(raw)
            if not email:
                continue

            with lock:
                metrics["emails_normalized_ok"] += 1

            if not context.is_new_email(email):
                with lock:
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

            with lock:
                metrics["emails_inserted"] += 1

    def _process_credentials(self, context, text, url, technique, origin, metrics, lock) -> None:
        """
        Extracts and persists credentials from parsed file text.

        Args:
            context: Execution context containing execution metadata and deduplication state
            text: Parsed file text
            url: Original file URL
            technique: Persistence technique label
            origin: Source origin label
            metrics: Mutable metrics dictionary updated in place
            lock: Lock used for thread-safe metric updates
        """
        creds = self.cred_parser.parse(text, source=C.SOURCE_FILE)

        for ctype, value, _ in creds:
            with lock:
                metrics["credentials_matched_raw"] += 1

            if not context.is_new_credential(ctype, value):
                with lock:
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

            with lock:
                metrics["credentials_inserted"] += 1