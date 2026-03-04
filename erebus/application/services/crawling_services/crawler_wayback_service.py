from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError


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
            return False

        for ext in self.BAD_EXTENSIONS:
            if parsed.path.lower().endswith(ext):
                return False

        return True

    def _build_snapshot_url(self, timestamp, original):
        return f"https://web.archive.org/web/{timestamp}/{original}"

    def run(self, domain: str) -> ModuleResponse | None:

        response = ModuleResponse(
            module_name="wayback",
            status=ModuleStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

        metrics = {
            "raw_entries": 0,
            "unique_urls": 0,
            "snapshots_generated": 0
        }

        try:
            raw_entries = self.wayback_collector.collect(domain)
            metrics["raw_entries"] = len(raw_entries)

            grouped = defaultdict(list)

            for entry in raw_entries:
                timestamp = entry["timestamp"]
                original = entry["original"]

                try:
                    year = int(timestamp[:4])
                except Exception:
                    continue

                if year < self.min_year:
                    continue

                if not self._is_valid_html_url(original):
                    continue

                grouped[original].append(entry)

            metrics["unique_urls"] = len(grouped)

            results = []

            for original in sorted(grouped.keys())[:self.limit]:

                entries = sorted(grouped[original], key=lambda x: x["timestamp"])

                first = entries[0]
                last = entries[-1]

                snapshots = {
                    self._build_snapshot_url(first["timestamp"], original),
                    self._build_snapshot_url(last["timestamp"], original),
                }

                for snap in snapshots:
                    results.append({
                        "url": snap,
                        "source": "wayback"
                    })

            metrics["snapshots_generated"] = len(results)

            response.metrics = metrics
            response.data = results if hasattr(response, "data") else None

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

        except Exception:
            response.status = ModuleStatus.FAILED
            response.errors.append("Unexpected error in wayback module")

        finally:
            response.finished_at = datetime.utcnow()

        return response