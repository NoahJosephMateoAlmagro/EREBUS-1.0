class CrawlerLiveService:

    def __init__(self, crawler_cls, timeout, max_pages):
        self.crawler_cls = crawler_cls
        self.timeout = timeout
        self.max_pages = max_pages

    def run(self, context, crawl_urls, sources):

        crawler = self.crawler_cls(
            start_url=list(crawl_urls),
            max_pages=self.max_pages,
            timeout=self.timeout,
            allowed_domain=context.execution.TARGET
        )

        results = crawler.collect()

        for page in results:
            page["origin"] = sources.get(page["url"], "live")

        return results
