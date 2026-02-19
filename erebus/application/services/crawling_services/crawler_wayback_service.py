from collections import defaultdict
from urllib.parse import urlparse


class CrawlerWaybackService:

    BAD_EXTENSIONS = (
        ".css", ".js", ".png", ".jpg", ".jpeg", ".gif",
        ".svg", ".ico", ".woff", ".woff2", ".ttf",
        ".zip", ".rar", ".7z"
    )

    def __init__(self, wayback_collector, limit=50, min_year=2008):
        self.wayback_collector = wayback_collector
        self.limit = limit
        self.min_year = min_year

    def _is_valid_html_url(self, url: str) -> bool:
        parsed = urlparse(url)

        if not parsed.scheme.startswith("http"):
            print(f"[WAYBACK][FILTER] ❌ No HTTP scheme → {url}")
            return False

        for ext in self.BAD_EXTENSIONS:
            if parsed.path.lower().endswith(ext):
                print(f"[WAYBACK][FILTER] ❌ Extensión inválida → {url}")
                return False

        return True

    def _build_snapshot_url(self, timestamp, original):
        return f"https://web.archive.org/web/{timestamp}/{original}"

    def run(self, domain: str):

        print(f"[WAYBACK][SERVICE] Iniciando colección histórica para: {domain}")
        print(f"[WAYBACK][SERVICE] min_year={self.min_year} | limit={self.limit}")

        raw_entries = self.wayback_collector.collect(domain)

        print(f"[WAYBACK][SERVICE] Entradas crudas recibidas: {len(raw_entries)}")

        grouped = defaultdict(list)

        for entry in raw_entries:
            timestamp = entry["timestamp"]
            original = entry["original"]

            year = int(timestamp[:4])

            if year < self.min_year:
                print(f"[WAYBACK][FILTER] ❌ Año {year} < {self.min_year} → {original}")
                continue

            if not self._is_valid_html_url(original):
                continue

            grouped[original].append(entry)

        print(f"[WAYBACK][SERVICE] URLs únicas tras filtrado: {len(grouped)}")

        results = []

        for i, original in enumerate(sorted(grouped.keys())[:self.limit], start=1):

            entries = sorted(grouped[original], key=lambda x: x["timestamp"])

            first = entries[0]
            last = entries[-1]

            print(
                f"[WAYBACK][SELECT] ({i}) {original} "
                f"→ snapshots totales={len(entries)} "
                f"→ first={first['timestamp']} "
                f"→ last={last['timestamp']}"
            )

            snapshots = {
                self._build_snapshot_url(first["timestamp"], original),
                self._build_snapshot_url(last["timestamp"], original),
            }

            for snap in snapshots:
                print(f"[WAYBACK][RESULT] ✔ {snap}")
                results.append({
                    "url": snap,
                    "source": "wayback"
                })

        print(f"[WAYBACK][SERVICE] Snapshots finales generados: {len(results)}")

        return results
