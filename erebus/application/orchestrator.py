from datetime import datetime

from application.bootstrap.service_builder import ServiceBuilder
from application.objects.execution_context import ExecutionContext
from application.objects.responses.ExecutionResponse import ExecutionResponse
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
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

        started_at = datetime.utcnow()

        builder = ServiceBuilder(self.uow, cfg, is_valid_domain)
        services = builder.build()

        context = ExecutionContext(execution, cfg)

        module_results = []

        # --------------------------------
        # Ejecución segura de módulos
        # --------------------------------

        def execute(module_key, service_key):

            if not cfg["modules"].get(module_key):
                return

            service = services.get(service_key)

            if not service:
                raise RuntimeError(f"Service not found: {service_key}")

            try:
                result = service.run(context)

                if not result:
                    raise ValueError("Module returned empty response")

                module_results.append(result)

            except Exception as e:

                module_results.append(
                    ModuleResponse(
                        module_name=module_key,
                        status=ModuleStatus.FAILED,
                        started_at=datetime.utcnow(),
                        finished_at=datetime.utcnow(),
                        errors=[str(e)]
                    )
                )
        # Pipeline de módulos
        # --------------------------------

        print("\n========== SUBDOMAINS ==========")
        execute("subdomains", "subdomain")

        print("\n========== WHOIS ==========")
        execute("whois", "whois")

        print("\n========== DNS ==========")
        execute("dns", "dns")

        print("\n========== NMAP ==========")
        execute("nmap", "nmap")

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

        # --------------------------------
        # Persistir métricas globales
        # --------------------------------

        try:
            for r in module_results:

                if r.metrics:
                    self.uow.metrics.insert_module_metrics(
                        execution.ID,
                        r.module_name,
                        r.metrics
                    )

            self.uow.metrics.insert_derived_metrics(execution.ID)
        except Exception as e:
            print("Warning: metrics persistence failed:", e)

        # --------------------------------
        # Summary uniforme
        # --------------------------------

        print("\n========== EXECUTION SUMMARY ==========")

        for r in module_results:

            print(f"[{r.module_name}]")
            print("  Status:", r.status)
            print("  Duration:", r.duration_seconds)
            print("  Metrics:", r.metrics)

            if r.errors:
                print("  Errors:", r.errors)

            print()

        print("=======================================\n")

        # --------------------------------
        # Execution response
        # --------------------------------

        return ExecutionResponse(
            execution_id=execution.ID,
            target=execution.TARGET,
            started_at=started_at,
            modules=module_results
        )