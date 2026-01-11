import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from normalizers.email_normalizer import normalize_obfuscated
from collectors.passive.credential_parser import CredentialParser
import core.constants as C


class Scraper:

    def __init__(self, timeout=15000):
        self.timeout = timeout
        self.cred_parser = CredentialParser()

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
                page = browser.new_page(user_agent="EREBUS/1.0")

                page.on("response", handle_response)

                if not url.endswith("/"):
                    url = url + "/"

                page.goto(url, timeout=self.timeout)
                page.wait_for_load_state("networkidle", timeout=self.timeout)

                html = page.content()
                browser.close()

            soup = BeautifulSoup(html, "html.parser")
            visible_text = soup.get_text()

            emails_dom = normalize_obfuscated(visible_text)
            creds_dom = self.cred_parser.parse(
                visible_text,
                source=C.TECHNIQUE_SCRAPING_DOM
            )

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
                "emails_dom": emails_dom,
                "credentials_dom": creds_dom,
                "emails_json": emails_json,
                "credentials_json": creds_json,
                "raw_html": html
            }

        except Exception as e:
            print(f"[SCRAPER ERROR] {url} -> {e}")
            return None
