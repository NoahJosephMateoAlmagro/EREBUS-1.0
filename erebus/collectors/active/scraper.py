import json
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError


class Scraper:

    def __init__(self, timeout=30000):
        self.timeout = timeout

    @staticmethod
    def _block_resources(route, request):
        if request.resource_type in ["image", "font", "media"]:
            route.abort()
        else:
            route.continue_()

    def collect(self, url: str):

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
                    page.unroute("**/*")
                    page.close()
                    context.close()
                    browser.close()
                    return None

                final_url = page.url
                html = page.content()

                page.unroute("**/*")
                page.close()
                context.close()
                browser.close()

            return {
                "url": url,
                "final_url": final_url,
                "html": html,
                "json_texts": json_texts,
                "json_objects": json_objects
            }

        except Exception:
            return None
