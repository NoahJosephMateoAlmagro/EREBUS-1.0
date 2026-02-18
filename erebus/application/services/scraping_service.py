from urllib.parse import urlparse
import shared.constants as C
from processing.normalizers.email_normalizer import normalize_email


class ScrapingService:

    def __init__(self, scraper, cred_parser, uow):
        self.scraper = scraper
        self.cred_parser = cred_parser
        self.uow = uow

    # ----------------------------------------
    # Public API
    # ----------------------------------------

    def run(self, context):

        print("Realizando scraping activo (solo live)...")

        if not context.live_results:
            print("[SCRAPING] No hay páginas LIVE, se omite scraping")
            return

        for page in context.live_results:

            if "@" in page["url"]:
                continue

            context.stats.scrape_attempted += 1

            result = self.scraper.scrape(page["url"])

            if not result:
                context.stats.scrape_failed += 1
                continue

            context.stats.scrape_succeeded += 1

            self._process_dom(context, page, result)
            self._process_json(context, page, result)

    # ----------------------------------------
    # Internal
    # ----------------------------------------

    def _process_dom(self, context, page, result):

        for e in result.get("emails_dom", []):

            email = normalize_email(e)

            if email and context.is_new_email(email):

                self.uow.emails.insert_email(
                    context.execution.ID,
                    email,
                    urlparse(page["url"]).hostname,
                    technique=C.TECHNIQUE_SCRAPING_DOM,
                    source=page["url"],
                    context=" "
                )
        for ctype, value, source in result.get("credentials_dom", []):

            if context.is_new_credential(ctype, value):
                self.uow.credentials.insert_credential(
                    context.execution.ID,
                    ctype,
                    value,
                    technique=C.TECHNIQUE_SCRAPING_DOM,
                    source=page["url"],
                    context=" "
                )

    def _process_json(self, context, page, result):

        for e in result.get("emails_json", []):

            email = normalize_email(e)

            if email and context.is_new_email(email):
                self.uow.emails.insert_email(
                    context.execution.ID,
                    email,
                    urlparse(page["url"]).netloc,
                    technique=C.TECHNIQUE_SCRAPING_JSON,
                    source=page["url"],
                    context=" "
                )

        for ctype, value, source in result.get("credentials_json", []):

            if context.is_new_credential(ctype, value):
                self.uow.credentials.insert_credential(
                    context.execution.ID,
                    ctype,
                    value,
                    technique=C.TECHNIQUE_SCRAPING_JSON,
                    source=page["url"],
                    context=" "
                )