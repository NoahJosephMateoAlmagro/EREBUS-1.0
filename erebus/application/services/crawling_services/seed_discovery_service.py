class SeedDiscoveryService:

    def __init__(self, robots_collector, sitemap_collector):
        self.robots_collector = robots_collector
        self.sitemap_collector = sitemap_collector

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def get_seeds(self, context):
        """
        Devuelve:
            - crawl_urls (set)
            - sources (dict url -> origin)
        """

        crawl_urls = set()
        sources = {}

        # 1️⃣ Base domain seeds
        base_urls = self._build_base_urls(context.execution.TARGET)
        for url in base_urls:
            crawl_urls.add(url)
            sources[url] = "base"

        # 2️⃣ Robots + Sitemap discovery
        self._discover_from_robots_and_sitemap(
            context,
            crawl_urls,
            sources
        )

        return crawl_urls, sources

    # -------------------------------------------------
    # Internal helpers
    # -------------------------------------------------

    def _build_base_urls(self, domain: str):
        return [
            f"https://{domain}",
            f"https://www.{domain}",
            f"http://{domain}",
            f"http://www.{domain}",
        ]
    def _discover_from_robots_and_sitemap(self, context, urls, sources):

        print("Analizando robots.txt y sitemap.xml...")

        robots = self.robots_collector.collect(context.execution.TARGET)
        max_robots = int(context.cfg["limits"].get("robots_max_urls", 0))
        robots_added = 0

        # -------------------------
        # Robots paths
        # -------------------------
        for path in robots.get("paths", []):

            if max_robots and robots_added >= max_robots:
                break

            if "*" in path or "$" in path:
                continue

            url = f"https://{context.execution.TARGET}{path}"

            if url not in sources:
                urls.add(url)

            sources[url] = "robots"
            robots_added += 1

        print(f"[ROBOTS] URLs añadidas: {robots_added}")

        # -------------------------
        # Sitemaps
        # -------------------------
        sitemap_urls_added = 0
        max_sitemap_urls = self.sitemap_collector.max_urls

        for sitemap_url in robots.get("sitemaps", []):

            if sitemap_urls_added >= max_sitemap_urls:
                break

            sitemap_urls = self.sitemap_collector.collect(sitemap_url)

            for u in sitemap_urls:

                if sitemap_urls_added >= max_sitemap_urls:
                    break

                if u not in sources:
                    urls.add(u)
                    sources[u] = "sitemap"
                    sitemap_urls_added += 1

        print(f"[SITEMAP] URLs añadidas: {sitemap_urls_added}")
