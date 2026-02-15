from application.execution_stats import ExecutionStats

class ExecutionContext:

    def __init__(self, execution, cfg):
        self.execution = execution
        self.cfg = cfg

        self.stats = ExecutionStats()

        self.seen_emails = set()
        self.seen_creds = set()
        self.seen_domains = set()

        self.all_domains = {execution.TARGET}

        self.live_results = []
        self.wayback_results = []
        self.crawl_results = []
