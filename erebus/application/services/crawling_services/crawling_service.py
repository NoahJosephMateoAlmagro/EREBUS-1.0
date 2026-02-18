class CrawlingService:

    def __init__(
        self,
        crawler_cls,
        seed_discovery_service,
        wayback_collector,
        live_timeout,
        live_max_pages,
        wayback_timeout,
        wayback_max_pages,
    ):
        self.crawler_cls = crawler_cls
        self.seed_discovery_service = seed_discovery_service
        self.wayback_collector = wayback_collector

        self.live_timeout = live_timeout
        self.live_max_pages = live_max_pages
        self.wayback_timeout = wayback_timeout
        self.wayback_max_pages = wayback_max_pages


    def run(self, context):

        # 1️⃣ Obtener seeds desde servicio externo
        crawl_urls, sources = self.seed_discovery_service.get_seeds(context)

        # -------------------------
        # LIVE CRAWLER
        # -------------------------
        crawler_live = self.crawler_cls(
            start_url=list(crawl_urls),
            max_pages=self.live_max_pages,
            timeout=self.live_timeout,
            allowed_domain=context.execution.TARGET,
            sources=sources
        )

        print("Buscando emails mediante crawler (live + wayback)...")

        live_results = crawler_live.run()
        context.stats.live_pages_visited = len(live_results)

        context.stats.visited_from_robots = 0
        context.stats.visited_from_sitemap = 0
        context.stats.visited_discovered = 0

        for page in live_results:
            origin = page.get("origin", "discovered")

            if origin == "robots":
                context.stats.visited_from_robots += 1
            elif origin == "sitemap":
                context.stats.visited_from_sitemap += 1
            else:
                context.stats.visited_discovered += 1

        # -------------------------
        # WAYBACK
        # -------------------------
        wayback_results = []

        if context.cfg["modules"].get("wayback"):
            print("Recolectando URLs históricas desde Wayback Machine...")

            wayback_urls = self.wayback_collector.collect(context.execution.TARGET)
            context.stats.wayback_urls_collected = len(wayback_urls)

            if wayback_urls:
                crawler_wb = self.crawler_cls(
                    start_url=[u["url"] for u in wayback_urls],
                    max_pages=self.wayback_max_pages,
                    timeout=self.wayback_timeout,
                    allowed_domain=None
                )

                wayback_results = crawler_wb.run()
                context.stats.wayback_pages_visited = len(wayback_results)

                for page in wayback_results:
                    page["origin"] = "wayback"

        context.live_results = live_results
        context.wayback_results = wayback_results
        context.crawl_results = live_results + wayback_results
