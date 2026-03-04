from application.bootstrap.service_builder import ServiceBuilder
from application.objects.execution_context import ExecutionContext
from shared.domain_validator import is_valid_domain


class Orchestrator:

    def __init__(self, uow):
        self.uow = uow

    def _validate_cfg(self, cfg):
        if cfg is None:
            raise ValueError("Configuración requerida: cfg no puede ser None")

        if not isinstance(cfg, dict):
            raise TypeError("Configuración inválida: cfg debe ser un dict")

        if "modules" not in cfg or "limits" not in cfg or "timeouts" not in cfg:
            raise ValueError(
                "Configuración inválida: se esperaban las claves 'modules', 'limits' y 'timeouts'"
            )

    def run(self, execution, cfg):

        self._validate_cfg(cfg)

        builder = ServiceBuilder(self.uow, cfg, is_valid_domain)
        services = builder.build()

        context = ExecutionContext(execution, cfg)

        module_results = []

        # -----------------------------
        # Ejecutar módulos homogéneos
        # -----------------------------

        def execute(module_key, service_key):
            if cfg["modules"].get(module_key):
                result = services[service_key].run(context)
                module_results.append(result)

        print("\n========== SUBDOMAINS ==========")
        execute("subdomains", "subdomain")
        print("\n========== WHOIS ==========")
        execute("whois", "whois")
        print("\n========== DNS ==========")
        execute("dns", "dns")
        print("\n========== EMAILS PASSIVE ==========")
        execute("emails_passive", "emails_passive")
        print("\n========== CRAWLER ==========")
        execute("crawler", "crawling")
        print("\n========== JS PARSING ==========")
        execute("js_parsing", "js")
        print("\n========== FILE PARSING ==========")
        execute("file_parsing", "file")
        print("\n========== SCRAPING ==========")
        execute("scraping", "scraping")

        # -----------------------------
        # Persistir métricas globales
        # -----------------------------

        self.uow.metrics.insert_metrics(execution.ID)

        # -----------------------------
        # Print uniforme
        # -----------------------------
        for r in module_results:
            print("DEBUG TYPE:", type(r))


        print("\n========== EXECUTION SUMMARY ==========")

        for r in module_results:
            print(f"[{r.module_name}]")
            print("  Status:", r.status)
            print("  Metrics:", r.metrics)
            if r.errors:
                print("  Errors:", r.errors)
            print()

        print("=======================================\n")

        return module_results