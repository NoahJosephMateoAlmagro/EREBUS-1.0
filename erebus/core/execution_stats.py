class ExecutionStats:
    def __init__(self):
        self.live_pages_visited = 0
        self.wayback_pages_visited = 0
        self.wayback_urls_collected = 0

        self.scripts_parsed_ok = 0
        self.scripts_parse_limit = 0

        self.scrape_attempted = 0
        self.scrape_succeeded = 0
        self.scrape_failed = 0
