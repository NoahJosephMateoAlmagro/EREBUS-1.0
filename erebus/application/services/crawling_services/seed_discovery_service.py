from exceptions.exceptions import CollectorError
from shared.logger import Logger


class SeedDiscoveryService:
    """
    Service responsible for building initial crawl seeds from base URLs,
    robots.txt and sitemap sources.
    """

    def __init__(self, robots_collector, sitemap_collector):
        """
        Args:
            robots_collector: Collector responsible for retrieving robots.txt data
            sitemap_collector: Collector responsible for retrieving sitemap URLs
        """
        self.robots_collector = robots_collector
        self.sitemap_collector = sitemap_collector

    def get_seeds(self, context):
        """
        Builds the initial set of crawl seeds and their discovery sources.

        Args:
            context: Execution context containing target and configuration

        Returns:
            tuple[set[str], dict[str, str]]: Seed URLs and their origin labels
        """
        target = context.execution.TARGET

        Logger.info(
            f"Starting seed discovery target={target}",
            context=self.__class__.__name__
        )

        crawl_urls = set()
        sources = {}

        base_urls = self._build_base_urls(target)

        for url in base_urls:
            crawl_urls.add(url)
            sources[url] = "base"

        try:
            self._discover_from_robots_and_sitemap(
                context,
                crawl_urls,
                sources
            )
        except CollectorError as e:
            Logger.error(
                f"Seed discovery collector error target={target}: {e}",
                context=self.__class__.__name__
            )

        Logger.info(
            f"Finished seed discovery target={target} seeds={len(crawl_urls)}",
            context=self.__class__.__name__
        )

        return crawl_urls, sources

    def _build_base_urls(self, domain: str):
        """
        Builds the default base URLs for a target domain.

        Args:
            domain (str): Target domain

        Returns:
            list[str]: Default base URLs
        """
        return [
            f"https://{domain}",
            f"https://www.{domain}",
            f"http://{domain}",
            f"http://www.{domain}",
        ]

    def _discover_from_robots_and_sitemap(self, context, urls, sources):
        """
        Enriches seed URLs using robots.txt and sitemap sources.

        Args:
            context: Execution context containing target and limits
            urls: Mutable set of discovered URLs
            sources: Mutable mapping of URL to origin label
        """
        target = context.execution.TARGET
        limits = context.cfg.get("limits", {})

        max_robots = int(limits.get("robots_max_urls", 0))
        max_sitemap_urls = int(limits.get("sitemap_max_urls", 0))

        robots_added = 0
        sitemap_added = 0

        # -------- robots.txt --------
        robots = self.robots_collector.collect(target)

        for path in robots.get("paths", []):
            if max_robots and robots_added >= max_robots:
                break

            if "*" in path or "$" in path:
                continue

            url = f"https://{target}{path}"

            if url not in sources:
                urls.add(url)
                sources[url] = "robots"
                robots_added += 1

        # -------- declared sitemaps --------
        for sitemap_url in robots.get("sitemaps", []):
            if max_sitemap_urls and sitemap_added >= max_sitemap_urls:
                break

            sitemap_urls = self.sitemap_collector.collect(sitemap_url)

            for url in sitemap_urls:
                if max_sitemap_urls and sitemap_added >= max_sitemap_urls:
                    break

                if url not in sources:
                    urls.add(url)
                    sources[url] = "sitemap"
                    sitemap_added += 1

        # -------- default sitemaps --------
        default_sitemaps = [
            f"https://{target}/sitemap.xml",
            f"https://{target}/sitemap_index.xml"
        ]

        for sitemap_url in default_sitemaps:
            if max_sitemap_urls and sitemap_added >= max_sitemap_urls:
                break

            sitemap_urls = self.sitemap_collector.collect(sitemap_url)

            for url in sitemap_urls:
                if max_sitemap_urls and sitemap_added >= max_sitemap_urls:
                    break

                if url not in sources:
                    urls.add(url)
                    sources[url] = "sitemap"
                    sitemap_added += 1