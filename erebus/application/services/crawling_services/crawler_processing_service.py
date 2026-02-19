from urllib.parse import urlparse
import shared.constants as C


class CrawlerProcessingService:

    def __init__(self, uow, email_extractor_func, cred_parser, normalize_email_func):
        self.uow = uow
        self.extract_emails = email_extractor_func
        self.cred_parser = cred_parser
        self.normalize_email = normalize_email_func

    def run(self, context):
        for page in context.crawl_results:
            self._process_page(context, page)


    def _process_page(self, context, page):

        page_url = page["url"]
        html = page.get("html", "") or ""
        links = page.get("links", [])
        scripts = page.get("scripts", [])

        domain = urlparse(page_url).netloc
        origin = page.get("origin", "discovered")

        # -----------------------------------------
        # 1️⃣ Persistir resultado bruto del crawler
        # -----------------------------------------

        self.uow.crawler.insert_crawler_result(
            context.execution.ID,
            page_url,
            [],  # ya no viene con emails
            links,
            scripts
        )

        # -----------------------------------------
        # 2️⃣ Emails (parseados aquí)
        # -----------------------------------------

        extracted_emails = self.extract_emails(html)

        for e in extracted_emails:
            email = self.normalize_email(e)
            if not email:
                continue

            if context.is_new_email(email):
                self.uow.emails.insert_email(
                    context.execution.ID,
                    email,
                    domain,
                    technique=C.TECHNIQUE_CRAWLER_HTML,
                    source=page_url,
                    context=origin
                )

        # -----------------------------------------
        # 3️⃣ Credenciales
        # -----------------------------------------

        creds = self.cred_parser.parse(html, source=C.SOURCE_HTML)

        for ctype, value, source in creds:
            if context.is_new_credential(ctype, value):
                self.uow.credentials.insert_credential(
                    context.execution.ID,
                    ctype,
                    value,
                    technique=C.TECHNIQUE_CRAWLER_HTML,
                    source=page_url,
                    context=origin
                )
