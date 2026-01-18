import json
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup

from normalizers.email_normalizer import normalize_obfuscated
from collectors.passive.credential_parser import CredentialParser
import core.constants as C


class Scraper:
    """
    Scraper activo basado en Playwright.
    - Renderiza DOM
    - Intercepta respuestas JSON (fetch / xhr)
    - Bloquea recursos pesados
    - Extrae emails y credenciales
    """

    def __init__(self, timeout=30000):
        self.timeout = timeout
        self.cred_parser = CredentialParser()

    # -------------------------------------------------
    # Bloqueo selectivo de recursos
    # -------------------------------------------------

    @staticmethod
    def _block_resources(route, request):
        if request.resource_type in ["image", "font", "media"]:
            route.abort()
        else:
            route.continue_()

    # -------------------------------------------------
    # Scraping principal
    # -------------------------------------------------

    def scrape(self, url: str):
        json_texts = []
        json_objects = []

        def handle_response(response):
            try:
                ct = response.headers.get("content-type", "").lower()
                if "json" in ct or response.url.lower().endswith(".json"):
                    resp_domain = urlparse(response.url).netloc
                    page_domain = urlparse(url).netloc

                    if resp_domain == page_domain or resp_domain.endswith("." + page_domain):
                        text = response.text()
                        json_texts.append(text)

                        try:
                            json_objects.append(json.loads(text))
                        except Exception:
                            pass
            except Exception:
                pass

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)

                context = browser.new_context(
                    user_agent="EREBUS/1.0",
                    java_script_enabled=True
                )

                # Interceptor de red (IMPORTANTE: se desregistrará al final)
                context.route("**/*", self._block_resources)

                page = context.new_page()
                page.on("response", handle_response)

                if not url.endswith("/"):
                    url += "/"

                try:
                    page.goto(
                        url,
                        timeout=self.timeout,
                        wait_until="domcontentloaded"
                    )
                except TimeoutError:
                    print(f"[SCRAPER TIMEOUT] {url}")
                    page.unroute("**/*")
                    page.close()
                    context.close()
                    browser.close()
                    return None

                final_url = page.url
                html = page.content()

                #CIERRE CORRECTO
                page.unroute("**/*")
                page.close()
                context.close()
                browser.close()

            # -------------------------------------------------
            # Procesado del contenido
            # -------------------------------------------------

            soup = BeautifulSoup(html, "html.parser")
            visible_text = soup.get_text()

            # Emails y credenciales desde DOM renderizado
            emails_dom = normalize_obfuscated(visible_text)
            creds_dom = self.cred_parser.parse(
                visible_text,
                source=C.TECHNIQUE_SCRAPING_DOM
            )

            # Emails y credenciales desde JSON
            json_text = "\n".join(json_texts)
            emails_json = normalize_obfuscated(json_text)

            creds_json = []
            for obj in json_objects:
                creds_json.extend(
                    self.cred_parser.parse_json(
                        obj,
                        source=C.TECHNIQUE_SCRAPING_JSON
                    )
                )

            return {
                "url": url,
                "final_url": final_url,
                "emails_dom": emails_dom,
                "credentials_dom": creds_dom,
                "emails_json": emails_json,
                "credentials_json": creds_json,
                "raw_html": html
            }

        except Exception as e:
            print(f"[SCRAPER ERROR] {url} -> {e}")
            return None
