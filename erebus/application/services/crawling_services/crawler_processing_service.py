from urllib.parse import urlparse
import shared.constants as C

class CrawlerProcessingService:
    def __init__(self, uow, cred_parser, normalize_email_func):
        self.uow = uow
        self.cred_parser = cred_parser
        self.normalize_email = normalize_email_func

    def run(self, context):
        for page in context.crawl_results:
            self._process_page(context, page)

    def _process_page(self, context, page):
        page_url = page["url"]
        domain = urlparse(page_url).netloc
        origin = page.get("origin", "discovered")

        # 1) persist crawler result bruto
        self.uow.crawler.insert_crawler_result(
            context.execution.ID,
            page_url,
            page.get("emails", []),
            page.get("links", []),
            page.get("scripts", [])
        )

        # 2) emails HTML
        for e in page.get("emails", []):
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

        # 3) credenciales HTML
        raw_html = page.get("raw_html", "") or ""
        creds = self.cred_parser.parse(raw_html, source=C.SOURCE_HTML)
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
