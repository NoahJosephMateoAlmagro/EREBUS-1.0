from urllib.parse import urlparse
import shared.constants as C
from processing.normalizers.email_normalizer import normalize_email


class JSParsingService:

    def __init__(self, js_parser, cred_parser, uow):
        self.js_parser = js_parser
        self.cred_parser = cred_parser
        self.uow = uow

    # ----------------------------------------
    # Public API
    # ----------------------------------------

    def run(self, context):

        print("Parseando JS (live + wayback)...")

        context.stats.scripts_parse_limit = int(
            context.cfg["limits"]["js_max_scripts"]
        )

        if not context.live_results:
            print("[JS] No hay páginas LIVE, se omite parsing JS")
            return

        for page in context.live_results:

            if context.stats.scripts_parsed_ok >= context.stats.scripts_parse_limit:
                break

            if "@" in page["url"]:
                continue

            self._process_page(context, page)

    # ----------------------------------------
    # Internal
    # ----------------------------------------

    def _process_page(self, context, page):

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

        print(
            f"[DEBUG][JS] page_url={page['url']} | "
            f"origin={origin} | "
            f"base_domain={base_domain} | "
            f"scripts_found={len(scripts)}"
        )

        for script_url in scripts:

            if context.stats.scripts_parsed_ok >= context.stats.scripts_parse_limit:
                break

            parsed = self.js_parser.parse(script_url, base_domain)
            if not parsed:
                continue

            context.stats.scripts_parsed_ok += 1

            self.uow.crawler.insert_js_result(
                context.execution.ID,
                parsed["script_url"],
                parsed.get("emails", []),
                parsed.get("urls", [])
            )

            self._process_emails(context, parsed, script_url, technique)
            self._process_credentials(context, parsed, script_url, technique)
    def _process_emails(self, context, parsed, script_url, technique):

        for e in parsed.get("emails", []):
            email = normalize_email(e)

            if not email:
                continue

            if context.is_new_email(email):

                self.uow.emails.insert_email(
                    context.execution.ID,
                    email,
                    urlparse(script_url).netloc,
                    technique=technique,
                    source=script_url,
                    context=" "
                )
    def _process_credentials(self, context, parsed, script_url, technique):

        raw_js = parsed.get("raw", "")
        creds = self.cred_parser.parse(raw_js, source=C.SOURCE_JS)

        for ctype, value, source in creds:

            if context.is_new_credential(ctype, value):

                self.uow.credentials.insert_credential(
                    context.execution.ID,
                    ctype,
                    value,
                    technique=technique,
                    source=script_url,
                    context=" "
                )
    def _extract_base_domain(self, page_url: str):

        if "web.archive.org" in page_url:
            try:
                original = page_url.split("/web/", 1)[1]
                original_url = original.split("/", 1)[1]
                return urlparse(original_url).netloc
            except Exception:
                return None

        return urlparse(page_url).netloc
