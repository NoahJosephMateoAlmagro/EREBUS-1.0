from urllib.parse import urlparse
import shared.constants as C
from processing.normalizers.email_normalizer import (
    normalize_email,
    extract_emails_from_text
)


class FileParsingService:

    def __init__(self, file_parser, cred_parser, uow):
        self.file_parser = file_parser
        self.cred_parser = cred_parser
        self.uow = uow

    # ----------------------------------------
    # Public API
    # ----------------------------------------

    def run(self, context):

        print("Parseando archivos descargables...")

        if not context.crawl_results:
            return

        for page in context.crawl_results:
            self._process_page(context, page)

    # ----------------------------------------
    # Internal
    # ----------------------------------------

    def _process_page(self, context, page):

        origin = page.get("origin", "discovered")

        for url in page.get("links", []):

            print(f"[FILE] probando link: {url}")

            result = self.file_parser.parse(url)

            if not result:
                continue

            text = result["text"]
            technique = result["technique"]

            print(
                f"[FILE] OK | technique={technique} | "
                f"text_len={len(text)}"
            )

            self._process_emails(context, text, url, technique, origin)
            self._process_credentials(context, text, url, technique, origin)
    def _process_emails(self, context, text, url, technique, origin):

        emails = extract_emails_from_text(text)

        for e in emails:

            email = normalize_email(e)

            if not email:
                continue

            if context.is_new_email(email):

                print(f"[FILE][EMAIL] {email}")

                self.uow.emails.insert_email(
                    context.execution.ID,
                    email,
                    urlparse(url).netloc,
                    technique=technique,
                    source=url,
                    context=origin
                )
    def _process_credentials(self, context, text, url, technique, origin):

        creds = self.cred_parser.parse(text, source=C.SOURCE_FILE)

        for ctype, value, source in creds:

            if context.is_new_credential(ctype, value):

                self.uow.credentials.insert_credential(
                    context.execution.ID,
                    ctype,
                    value,
                    technique=technique,
                    source=url,
                    context=origin
                )
