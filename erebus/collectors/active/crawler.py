from typing import Union, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class Crawler:

    def __init__(
        self,
        start_url: Union[str, List[str]],
        max_pages: int = 30,
        timeout: int = 8,
        allowed_domain: str | None = None
    ):
        self.max_pages = max_pages
        self.timeout = timeout
        self.allowed_domain = allowed_domain

        self.visited = set()
        self.queue = []

        if isinstance(start_url, list):
            self.queue.extend(start_url)
            first = start_url[0] if start_url else ""
        else:
            self.queue.append(start_url)
            first = start_url

        self.domain = urlparse(first).netloc if first else ""

        print(f"[CRAWLER] Inicializado para dominio: {self.domain}")
        print(f"[CRAWLER] Seeds iniciales: {len(self.queue)}")
        print(f"[CRAWLER] Límite de páginas: {self.max_pages}")


    def _normalize(self, url: str) -> str:
        return url.split("#")[0].rstrip("/")


    def _is_internal(self, url: str) -> bool:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()

        if not netloc:
            return False

        if ":" in netloc:
            netloc = netloc.split(":")[0]

        if self.allowed_domain:
            return (
                netloc == self.allowed_domain
                or netloc.endswith("." + self.allowed_domain)
            )

        return netloc == self.domain


    def collect(self):
        results = []

        print("[CRAWLER] Iniciando crawling...")

        while self.queue and len(self.visited) < self.max_pages:

            print(f"\n[CRAWLER] Cola: {len(self.queue)} | Visitadas: {len(self.visited)}")

            url = self._normalize(self.queue.pop(0))

            if url in self.visited:
                print(f"[CRAWLER] ⚠ Ya visitada: {url}")
                continue

            print(f"[CRAWLER] ➡ Visitando: {url}")

            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={"User-Agent": "EREBUS/1.0"}
                )

                status = response.status_code
                print(f"[CRAWLER] Status: {status}")

                content_type = response.headers.get("Content-Type", "")
                print(f"[CRAWLER] Content-Type: {content_type}")

                if "text/html" not in content_type:
                    print(f"[CRAWLER] ❌ No es HTML, se omite.")
                    continue

                self.visited.add(url)

                soup = BeautifulSoup(response.text, "html.parser")

                links = set()
                for a in soup.find_all("a", href=True):
                    href = a["href"]

                    if "@" in href:
                        continue

                    full_url = self._normalize(urljoin(url, href))

                    if self._is_internal(full_url):
                        links.add(full_url)

                        if full_url not in self.visited:
                            self.queue.append(full_url)

                print(f"[CRAWLER] ✔ Links internos encontrados: {len(links)}")

                scripts = set()
                for s in soup.find_all("script", src=True):
                    full = self._normalize(urljoin(url, s["src"]))
                    if self._is_internal(full):
                        scripts.add(full)

                print(f"[CRAWLER] ✔ Scripts internos encontrados: {len(scripts)}")

                results.append({
                    "url": url,
                    "html": response.text,
                    "links": list(links),
                    "scripts": list(scripts)
                })

            except Exception as e:
                print(f"[CRAWLER ERROR] {url} -> {e}")
                continue

        print("\n[CRAWLER] Finalizado.")
        print(f"[CRAWLER] Total páginas visitadas: {len(self.visited)}")
        print(f"[CRAWLER] Total resultados devueltos: {len(results)}")

        return results
