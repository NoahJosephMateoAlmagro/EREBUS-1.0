class CrawlingService:

    def __init__(
        self,
        seed_discovery_service,
        crawler_live_service,
        crawler_wayback_service,
        crawler_processing_service,
    ):
        self.seed_discovery_service = seed_discovery_service
        self.crawler_live_service = crawler_live_service
        self.crawler_wayback_service = crawler_wayback_service
        self.crawler_processing_service = crawler_processing_service

    def run(self, context):

        print("[CRAWLING] Iniciando pipeline de crawling")

        # -----------------------------------------
        # 1️⃣ Descubrimiento de seeds
        # -----------------------------------------

        crawl_urls, sources = self.seed_discovery_service.get_seeds(context)

        print(f"[CRAWLING] Seeds totales descubiertas: {len(crawl_urls)}")

        # -----------------------------------------
        # 2️⃣ Crawler LIVE
        # -----------------------------------------

        live_results = self.crawler_live_service.run(
            context,
            crawl_urls,
            sources
        )

        context.stats.live_pages_visited = len(live_results)

        print(f"[CRAWLING] LIVE pages: {len(live_results)}")

        # -----------------------------------------
        # 3️⃣ Crawler WAYBACK
        # -----------------------------------------

        wayback_results = []

        if context.cfg["modules"].get("wayback"):

            wayback_results = self.crawler_wayback_service.run(context.execution.TARGET)

            context.stats.wayback_pages_visited = len(wayback_results)

            print(f"[CRAWLING] WAYBACK pages: {len(wayback_results)}")

        # -----------------------------------------
        # 4️⃣ Unificación de resultados
        # -----------------------------------------

        context.live_results = live_results
        context.wayback_results = wayback_results
        context.crawl_results = live_results + wayback_results

        print(f"[CRAWLING] Total páginas acumuladas: {len(context.crawl_results)}")

        # -----------------------------------------
        # 5️⃣ Procesamiento
        # -----------------------------------------

        self.crawler_processing_service.run(context)

        print("[CRAWLING] Procesamiento finalizado")
