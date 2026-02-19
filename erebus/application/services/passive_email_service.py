import shared.constants as C


class EmailPassiveService:

    def __init__(self, email_collector, email_analyzer, uow):
        self.email_collector = email_collector
        self.email_analyzer = email_analyzer
        self.uow = uow

    def run(self, context):

        print("Buscando emails pasivos...")

        pages = self.email_collector.collect(
            context.execution.TARGET
        )

        for page in pages:

            html = page.get("html", "")
            source_url = page.get("url")

            emails = self.email_analyzer.extract(html)

            for e in emails:

                email = self.email_analyzer.normalize(e)

                if not email:
                    continue

                if context.is_new_email(email):

                    self.uow.emails.insert_email(
                        context.execution.ID,
                        email,
                        context.execution.TARGET,
                        technique=C.TECHNIQUE_PASSIVE_HTML,
                        source=source_url,
                        context=source_url
                    )
