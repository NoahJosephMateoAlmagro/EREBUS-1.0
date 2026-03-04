import json
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError

from exceptions.exceptions import CollectorError


class Scraper:

    def __init__(self, timeout: int = 30000):
        self.timeout = timeout

    @staticmethod
    def _block_resources(route, request):
        if request.resource_type in ["image", "font", "media"]:
            route.abort()
        else:
            route.continue_()

    def collect(self, url: str):

        result = {
            "url": url,
            "final_url": None,
            "html": None,
            "json_texts": [],
            "json_objects": []
        }

        def handle_response(response):
            try:
                ct = response.headers.get("content-type", "").lower()

                if "json" in ct or response.url.lower().endswith(".json"):

                    resp_domain = urlparse(response.url).netloc
                    page_domain = urlparse(url).netloc

                    if resp_domain == page_domain or resp_domain.endswith("." + page_domain):
                        text = response.text()
                        result["json_texts"].append(text)

                        try:
                            result["json_objects"].append(json.loads(text))
                        except Exception:
                            pass
            except Exception:
                # Nunca rompemos el scraping por una respuesta malformada
                pass

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)

                context = browser.new_context(
                    user_agent="EREBUS/1.0",
                    java_script_enabled=True
                )

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
                    # Timeout → devolvemos resultado vacío estructurado
                    page.close()
                    context.close()
                    browser.close()
                    return result

                result["final_url"] = page.url
                result["html"] = page.content()

                page.close()
                context.close()
                browser.close()

        except Exception as e:
            raise CollectorError(f"Scraper internal error for {url}: {e}")

        return result