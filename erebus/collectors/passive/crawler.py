import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from normalizers.email_normalizer import normalize_obfuscated
import re

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)


class Crawler:

    def __init__(self, start_url: str, max_pages : int = 30, timeout: int = 8, allowed_domain = None):
        self.max_pages = max_pages
        self.timeout = timeout
        self.visited = set()
        self.queue = []
        self.allowed_domain = allowed_domain

        if isinstance(start_url, list):
            self.queue.extend(start_url)
            first = start_url[0]
        else:
            self.queue.append(start_url)
            first = start_url

        self.domain = urlparse(first).netloc

    def _is_internal(self, url):
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()

        if not netloc:
            return False

        if ":" in netloc:
            netloc = netloc.split(":")[0]

        # PERMITIR WAYBACK
        if "web.archive.org" in netloc:
            return True

        if self.allowed_domain:
            return (
                    netloc == self.allowed_domain
                    or netloc.endswith("." + self.allowed_domain)
            )

        return netloc == self.domain

    def _normalize(self, url):
        return url.split("#")[0].rstrip("/")

    def run(self):
        results = []

        while self.queue and len(self.visited) < self.max_pages:
            url = self._normalize(self.queue.pop(0))

            if url in self.visited:
                continue

            # Detectar emails embebidos en la URL (ANTES del GET)
            page_emails = set()
            page_emails |= normalize_obfuscated(url)

            # Si la URL contiene '@', NO es crawlable
            if "@" in url:
                self.visited.add(url)

                if page_emails:
                    results.append({
                        "url": url,
                        "emails": list(page_emails),
                        "links": [],
                        "scripts": [],
                        "raw_html": ""
                    })

                continue

            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={"User-Agent": "EREBUS/1.0"}
                )

                if "text/html" not in response.headers.get("Content-Type", ""):
                    continue

                self.visited.add(url)

                soup = BeautifulSoup(response.text, "html.parser")

                # Emails SOLO de esta página
                page_emails = set()
                page_emails |= normalize_obfuscated(soup.get_text())
                page_emails |= normalize_obfuscated(response.text)

                links = set()

                for a in soup.find_all("a", href=True):
                    href = a["href"]

                    # Si contiene @, NO es una URL web válida (mailto, urls rotas...)
                    if "@" in href:
                        continue

                    full_url = self._normalize(
                        urljoin(url, href)
                    )

                    if self._is_internal(full_url):
                        links.add(full_url)
                        if full_url not in self.visited:
                            self.queue.append(full_url)

                scripts = set()
                for s in soup.find_all("script", src=True):
                    full = self._normalize(
                        urljoin(url, s["src"])
                    )
                    if self._is_internal(full):
                        scripts.add(full)

                results.append({
                    "url": url,
                    "emails": list(page_emails),
                    "links": list(links),
                    "scripts": list(scripts),
                    "raw_html": response.text
                })

            except Exception as e:
                print(f"[ERROR] {url} -> {e}")

        return results
