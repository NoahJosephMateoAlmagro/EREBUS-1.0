from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

import shared.constants as C
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus


class FileParsingService:

    def __init__(self, file_parser, cred_parser, email_analyzer, uow):
        self.file_parser = file_parser
        self.cred_parser = cred_parser
        self.email_analyzer = email_analyzer
        self.uow = uow

    def run(self, context) -> ModuleResponse | None:

        self.seen_files = set()

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
            return response

        try:

            # -------- recolectar archivos --------

            file_links = []

            for page in context.crawl_results:

                origin = page.get("origin", "discovered")

                for url in page.get("links", []):

                    metrics["file_links_seen"] += 1

                    parsed = urlparse(url)
                    ext = Path(parsed.path).suffix.lower()

                    if ext not in C.FILE_EXTENSIONS_TO_PARSE:
                        continue

                    if url in self.seen_files:
                        continue

                    self.seen_files.add(url)

                    file_links.append((url, origin))

            # -------- límites --------

            max_files = context.cfg["limits"].get("file_max_files", 100)
            max_workers = context.cfg["limits"].get("file_max_workers", 4)

            file_links = file_links[:max_files]

            lock = threading.Lock()

            # -------- ejecución paralela --------

            def worker(url, origin):


                with lock:
                    metrics["files_attempted"] += 1
                try:
                    result = self.file_parser.parse(url)
                except Exception as e:
                    with lock:
                        metrics["files_failed"] += 1
                    return

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

            with ThreadPoolExecutor(max_workers=max_workers) as executor:

                futures = [
                    executor.submit(worker, url, origin)
                    for url, origin in file_links
                ]

                for f in futures:
                    f.result()

            response.metrics = metrics

        except Exception as e:

            response.status = ModuleStatus.FAILED
            response.errors.append(f"File parsing error: {e}")

        finally:

            response.finished_at = datetime.utcnow()

        return response

    # ----------------------------------------

    def _process_emails(self, context, text, url, technique, origin, metrics, lock):

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

    # ----------------------------------------

    def _process_credentials(self, context, text, url, technique, origin, metrics, lock):

        creds = self.cred_parser.parse(text, source=C.SOURCE_FILE)

        for ctype, value, source in creds:

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