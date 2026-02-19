class SeedDiscoveryService:

    def __init__(self, robots_collector, sitemap_collector):
        self.robots_collector = robots_collector
        self.sitemap_collector = sitemap_collector

    def get_seeds(self, context):
        """
        Devuelve:
            - crawl_urls (set)
            - sources (dict url -> origin)
        """

        crawl_urls = set()
        sources = {}

        # 1️⃣ Base seeds
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


    # -----------------------------------------
    # Helpers
    # -----------------------------------------

    def _build_base_urls(self, domain: str):
        return [
            f"https://{domain}",
            f"https://www.{domain}",
            f"http://{domain}",
            f"http://www.{domain}",
        ]


    def _discover_from_robots_and_sitemap(self, context, urls, sources):

        target = context.execution.TARGET
        limits = context.cfg.get("limits", {})

        max_robots = int(limits.get("robots_max_urls", 0))
        max_sitemap_urls = int(limits.get("sitemap_max_urls", 0))

        robots_added = 0
        sitemap_added = 0

        robots = self.robots_collector.collect(target)

        # -------------------------
        # Robots paths
        # -------------------------

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

        # -------------------------
        # Sitemaps declarados en robots
        # -------------------------

        for sitemap_url in robots.get("sitemaps", []):

            if max_sitemap_urls and sitemap_added >= max_sitemap_urls:
                break

            sitemap_urls = self.sitemap_collector.collect(sitemap_url)

            for u in sitemap_urls:

                if max_sitemap_urls and sitemap_added >= max_sitemap_urls:
                    break

                if u not in sources:
                    urls.add(u)
                    sources[u] = "sitemap"
                    sitemap_added += 1

        # -------------------------
        # Sitemaps por defecto
        # -------------------------

        default_sitemaps = [
            f"https://{target}/sitemap.xml",
            f"https://{target}/sitemap_index.xml"
        ]

        for sitemap_url in default_sitemaps:

            if max_sitemap_urls and sitemap_added >= max_sitemap_urls:
                break

            sitemap_urls = self.sitemap_collector.collect(sitemap_url)

            for u in sitemap_urls:

                if max_sitemap_urls and sitemap_added >= max_sitemap_urls:
                    break

                if u not in sources:
                    urls.add(u)
                    sources[u] = "sitemap"
                    sitemap_added += 1
