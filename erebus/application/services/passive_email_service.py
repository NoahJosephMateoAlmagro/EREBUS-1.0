import shared.constants as C
from processing.normalizers.email_normalizer import normalize_email

class EmailPassiveService:

    def __init__(self, email_collector, uow):
        self.email_collector = email_collector
        self.uow = uow

    def run(self, context):

        print("Buscando emails pasivos...")

        email_results = self.email_collector.collect(
            context.execution.TARGET
        )

        for r in email_results:

            email = normalize_email(r.get("value"))
            if not email:
                continue

            if email not in context.seen_emails:
                context.seen_emails.add(email)

                self.uow.emails.insert_email(
                    context.execution.ID,
                    email,
                    context.execution.TARGET,
                    technique=C.TECHNIQUE_PASSIVE_HTML,
                    source=r.get("context"),
                    context=r.get("context")
                )
