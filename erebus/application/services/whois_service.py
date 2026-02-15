class WhoisService:

    def __init__(self, whois_collector, uow):
        self.whois_collector = whois_collector
        self.uow = uow

    def run(self, context):

        print("Consultando WHOIS...")

        whois_data = self.whois_collector.collect(
            context.execution.TARGET
        )

        if whois_data:
            self.uow.whois.insert_whois_result(
                context.execution.ID,
                context.execution.TARGET,
                whois_data
            )
