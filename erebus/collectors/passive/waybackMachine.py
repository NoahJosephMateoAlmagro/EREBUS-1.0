import requests
from urllib.parse import urlparse


class WaybackCollector:

    CDX_URL = "http://web.archive.org/cdx/search/cdx"
    name = "wayback"

    BAD_EXTENSIONS = (
        ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
        ".woff", ".woff2", ".ttf", ".eot",
        ".zip", ".rar", ".7z"
    )

    def __init__(self, timeout=10, limit=500, min_year=2008):
        self.timeout = timeout
        self.limit = limit
        self.min_year = min_year

    def _is_valid_html_url(self, url: str) -> bool:
        """
        Filtra URLs no útiles para crawling HTML.
        """
        url = url.lower()

        # artefactos típicos de Wayback / PageSpeed
        if ",a.media" in url or ".pagespeed." in url:
            return False

        parsed = urlparse(url)

        if not parsed.scheme.startswith("http"):
            return False

        path = parsed.path

        # excluir recursos estáticos
        for ext in self.BAD_EXTENSIONS:
            if path.endswith(ext):
                return False

        return True

    def _build_snapshot_url(self, timestamp, original):
        return f"https://web.archive.org/web/{timestamp}/{original}"

    def collect(self, domain: str):
        """
        Devuelve SOLO URLs históricas HTML válidas del dominio. No interesa acceder a archivos que no existen ya
        """
        results = set()

        params = {
            "url": f"*.{domain}/*",
            "output": "json",
            "fl": "timestamp,original,statuscode",
            "collapse": "digest",
            "limit": self.limit,
        }

        try:
            r = requests.get(
                self.CDX_URL,
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "EREBUS/1.0"}
            )

            if r.status_code in [502,503,504] :
                print("[WAYBACK] API caída, no disponible en estos momentos")
                return results

            if r.status_code != 200:
                return results

            data = r.json()

            print(f"[WAYBACK][DEBUG] CDX rows: {len(data) - 1}")

            # Primera fila = cabecera
            for row in data[1:]:

                timestamp, original, status = row

                year = int(timestamp[:4])

                if status != "200":
                    continue

                if year < self.min_year:
                    continue

                if not self._is_valid_html_url(original):
                    continue

                snapshot_url = self._build_snapshot_url(timestamp, original)
                results.add(snapshot_url)

                print(f"[WAYBACK][DEBUG] example snapshot: {timestamp} {original}")
                break


        except requests.exceptions.RequestException as e:

            print(f"[WAYBACK] Error de conexión: {e}")

        except Exception as e:

            print(f"[WAYBACK] Error inesperado: {e}")

        return results
