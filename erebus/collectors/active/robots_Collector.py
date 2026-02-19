import requests
from collectors.base import PassiveCollector


class RobotsCollector(PassiveCollector):

    def __init__(self, timeout=8):
        self.timeout = timeout

    def collect(self, domain: str):
        results = {
            "paths": [],
            "sitemaps": []
        }

        print(f"[ROBOTS] Analizando dominio: {domain}")

        # Intentamos HTTPS primero, luego HTTP
        urls_to_try = [
            f"https://{domain}/robots.txt",
            f"http://{domain}/robots.txt"
        ]

        content = None

        for url in urls_to_try:
            print(f"[ROBOTS] Intentando: {url}")

            try:
                r = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={"User-Agent": "EREBUS/1.0"}
                )

                print(f"[ROBOTS] Status: {r.status_code}")

                if r.status_code == 200 and r.text:
                    print(f"[ROBOTS] ✔ robots.txt encontrado en {url}")
                    content = r.text
                    break
                else:
                    print(f"[ROBOTS] ❌ No válido o vacío.")

            except requests.RequestException as e:
                print(f"[ROBOTS ERROR] {url} -> {e}")

        if not content:
            print("[ROBOTS] ❌ No se encontró robots.txt")
            return results

        seen_paths = set()
        seen_sitemaps = set()

        for raw_line in content.splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            # Eliminamos comentarios inline
            if "#" in line:
                line = line.split("#", 1)[0].strip()

            lower = line.lower()

            # -------------------------
            # Disallow
            # -------------------------
            if lower.startswith("disallow:"):
                path = line.split(":", 1)[1].strip()

                if not path:
                    continue

                if not path.startswith("/"):
                    print(f"[ROBOTS] ⚠ Ignorado path no estructural: {path}")
                    continue

                if path not in seen_paths:
                    seen_paths.add(path)
                    results["paths"].append(path)
                    print(f"[ROBOTS] ➕ Path añadido: {path}")

            # -------------------------
            # Sitemap
            # -------------------------
            elif lower.startswith("sitemap:"):
                sitemap = line.split(":", 1)[1].strip()

                if not sitemap:
                    continue

                if sitemap not in seen_sitemaps:
                    seen_sitemaps.add(sitemap)
                    results["sitemaps"].append(sitemap)
                    print(f"[ROBOTS] ➕ Sitemap añadido: {sitemap}")

        print(f"[ROBOTS] Total paths: {len(results['paths'])}")
        print(f"[ROBOTS] Total sitemaps: {len(results['sitemaps'])}")

        return results
