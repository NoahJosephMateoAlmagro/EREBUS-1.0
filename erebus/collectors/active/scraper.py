import json
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError

from exceptions.exceptions import CollectorError
from shared.logger import Logger


class Scraper:
    """
    Scraper that loads a web page using Playwright and captures
    final URL after redirects, full HTML content and JSON responses (same-domain only)
    """
    def __init__(self, timeout: int = 30000):
        """
        Args:
            timeout (int): Page load timeout in milliseconds
        """
        self.timeout = timeout

    @staticmethod
    def _block_resources(route, request):
        """
        Blocks non-essential resources to improve performance.
        """
        if request.resource_type in ["image", "font", "media"]:
            route.abort()
        else:
            route.continue_()

    def collect(self, url: str):
        """
        Executes the scraping process for a given URL.

        Args:
           url (str): Target URL

        Returns:
           dict: Scraped data including HTML and JSON responses
        """

        Logger.info(f"Starting scraping for {url}", context=self.__class__.__name__)


        result = {
            "url": url,
            "final_url": None,
            "html": None,
            "json_texts": [],
            "json_objects": []
        }

        def handle_response(response):
            """
            Intercepts network responses and extracts JSON data
            from same-domain requests.
            """
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
                            # Ignore malformed JSON (non-critical)
                            pass

            except Exception:
                # Never break scraping due to malformed response
                pass

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)

                context = browser.new_context(
                    user_agent="EREBUS/1.0",
                    java_script_enabled=True
                )

                # Block unnecessary resources
                context.route("**/*", self._block_resources)

                page = context.new_page()
                page.on("response", handle_response)

                # Normalize URL
                if not url.endswith("/"):
                    url += "/"

                try:
                    page.goto(
                        url,
                        timeout=self.timeout,
                        wait_until="domcontentloaded"
                    )
                except TimeoutError:
                    # Timeout (return partial structured result)
                    Logger.debug("Page load timeout", context=self.__class__.__name__)

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
            Logger.error(f"Scraper internal error: {e}", context=self.__class__.__name__)
            raise CollectorError(f"Scraper internal error for {url}: {e}")

        Logger.info(
            f"Scraping completed (HTML: {'yes' if result['html'] else 'no'}, JSON: {len(result['json_objects'])})",
            context=self.__class__.__name__
        )
        return result