from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
from exceptions.exceptions import CollectorError
import shared.constants as C
from shared.logger import Logger

class CrawlerWaybackService:
    """
    Service responsible for retrieving, filtering and transforming Wayback Machine
    results into crawlable snapshot URLs.
    """

    def __init__(self, wayback_collector, limit=50, min_year=2008):
        """
        Args:
            wayback_collector: Collector responsible for retrieving Wayback entries
            limit (int): Maximum number of unique original URLs to transform
            min_year (int): Minimum snapshot year accepted
        """
        self.wayback_collector = wayback_collector
        self.limit = limit
        self.min_year = min_year

    def _is_valid_html_url(self, url: str) -> bool:
        """
        Determines whether a URL is a valid HTTP(S) candidate and not a filtered asset type.

        Args:
            url (str): Original URL to validate

        Returns:
            bool: True if the URL is accepted, False otherwise
        """
        parsed = urlparse(url)

        if not parsed.scheme.startswith("http"):
            return False

        for ext in C.BAD_EXTENSIONS:
            if parsed.path.lower().endswith(ext):
                return False

        return True

    def _build_snapshot_url(self, timestamp: str, original: str) -> str:
        """
        Builds a Wayback snapshot URL from timestamp and original URL.

        Args:
            timestamp (str): Wayback snapshot timestamp
            original (str): Original archived URL

        Returns:
            str: Full Wayback snapshot URL
        """
        return f"https://web.archive.org/web/{timestamp}/{original}"

    def run(self, domain: str) -> ModuleResponse | None:
        """
        Executes Wayback URL discovery workflow.

        Args:
            domain (str): Target domain

        Returns:
            ModuleResponse: Execution result with metrics, errors and generated snapshot data
        """
        Logger.info(
            f"Starting wayback module domain={domain}",
            context=self.__class__.__name__
        )

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
                entries = sorted(grouped[original], key=lambda item: item["timestamp"])

                first = entries[0]
                last = entries[-1]

                snapshots = {
                    self._build_snapshot_url(first["timestamp"], original),
                    self._build_snapshot_url(last["timestamp"], original),
                }

                for snapshot_url in snapshots:
                    results.append({
                        "url": snapshot_url,
                        "source": "wayback"
                    })

            metrics["snapshots_generated"] = len(results)

            response.metrics = metrics
            response.data = results

        except CollectorError as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(str(e))

            Logger.error(
                f"Wayback collector error domain={domain}: {e}",
                context=self.__class__.__name__
            )

        except Exception as e:
            response.status = ModuleStatus.FAILED
            response.errors.append(f"Unexpected error in wayback module: {e}")

            Logger.error(
                f"Unexpected wayback error domain={domain}: {e}",
                context=self.__class__.__name__
            )

        finally:
            response.finished_at = datetime.utcnow()

            Logger.info(
                f"Finished wayback module domain={domain} "
                f"status={response.status} metrics={metrics}",
                context=self.__class__.__name__
            )

        return response