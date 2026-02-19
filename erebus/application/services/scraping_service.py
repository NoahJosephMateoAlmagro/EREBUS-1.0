from urllib.parse import urlparse
import shared.constants as C


class ScrapingService:

    def __init__(self, scraper, cred_parser, email_analyzer, uow):
        self.scraper = scraper
        self.cred_parser = cred_parser
        self.email_analyzer = email_analyzer
        self.uow = uow

    def run(self, context):

        print("Realizando scraping activo (solo live)...")

        if not context.live_results:
            print("[SCRAPING] No hay páginas LIVE, se omite scraping")
            return

        for page in context.live_results:

            if "@" in page["url"]:
                continue

            context.stats.scrape_attempted += 1

            result = self.scraper.collect(page["url"])

            if not result:
                context.stats.scrape_failed += 1
                continue

            context.stats.scrape_succeeded += 1

            self._process(context, page, result)

    def _process(self, context, page, result):

        html = result.get("html", "")
        json_texts = result.get("json_texts", [])
        json_objects = result.get("json_objects", [])

        final_url = result.get("final_url") or page["url"]
        domain = urlparse(final_url).hostname

        # -------------------
        # DOM parsing
        # -------------------

        emails_dom = self.email_analyzer.extract(html)

        for e in emails_dom:
            email = self.email_analyzer.normalize(e)

            if email and context.is_new_email(email):
                self.uow.emails.insert_email(
                    context.execution.ID,
                    email,
                    domain,
                    technique=C.TECHNIQUE_SCRAPING_DOM,
                    source=final_url,
                    context=" "
                )

        creds_dom = self.cred_parser.parse(
            html,
            source=C.SOURCE_HTML
        )

        for ctype, value, source in creds_dom:
            if context.is_new_credential(ctype, value):
                self.uow.credentials.insert_credential(
                    context.execution.ID,
                    ctype,
                    value,
                    technique=C.TECHNIQUE_SCRAPING_DOM,
                    source=final_url,
                    context=" "
                )

        # -------------------
        # JSON parsing
        # -------------------

        full_json_text = "\n".join(json_texts)
        emails_json = self.email_analyzer.extract(full_json_text)

        for e in emails_json:
            email = self.email_analyzer.normalize(e)
            if email and context.is_new_email(email):
                self.uow.emails.insert_email(
                    context.execution.ID,
                    email,
                    domain,
                    technique=C.TECHNIQUE_SCRAPING_JSON,
                    source=page["url"],
                    context=" "
                )

        for obj in json_objects:
            creds_json = self.cred_parser.parse_json(
                obj,
                source=C.SOURCE_JSON
            )

            for ctype, value, source in creds_json:
                if context.is_new_credential(ctype, value):
                    self.uow.credentials.insert_credential(
                        context.execution.ID,
                        ctype,
                        value,
                        technique=C.TECHNIQUE_SCRAPING_JSON,
                        source=page["url"],
                        context=" "
                    )
