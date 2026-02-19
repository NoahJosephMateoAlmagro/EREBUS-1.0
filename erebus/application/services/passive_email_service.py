import shared.constants as C
from processing.normalizers.email_normalizer import normalize_email

class EmailPassiveService:

    def __init__(self, email_collector, uow, normalize_email_func):
        self.email_collector = email_collector
        self.uow = uow
        self.normalize_email = normalize_email_func

    def run(self, context):

        print("Buscando emails pasivos...")

        email_results = self.email_collector.collect(
            context.execution.TARGET
        )

        for r in email_results:

            email = self.normalize_email(r.get("value"))

            if not email:
                continue

            if context.is_new_email(email):
                context.seen_emails.add(email)

                self.uow.emails.insert_email(
                    context.execution.ID,
                    email,
                    context.execution.TARGET,
                    technique=C.TECHNIQUE_PASSIVE_HTML,
                    source=r.get("context"),
                    context=r.get("context")
                )
