from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import threading

from application.bootstrap.service_builder import ServiceBuilder
from application.objects.execution_context import ExecutionContext
from application.objects.responses.ExecutionResponse import ExecutionResponse
from application.objects.responses.ModuleResponse import ModuleResponse, ModuleStatus
import shared.utils as Utils
from shared.logger import Logger


class Orchestrator:
    """
    Main orchestration component of the EREBUS engine.
    """

    def __init__(self, uow):
        self.uow = uow

    def _validate_cfg(self, cfg):
        if cfg is None:
            Logger.error(
                "Invalid configuration: cfg is None",
                context=self.__class__.__name__
            )
            raise ValueError("Configuration required: cfg cannot be None")

        if not isinstance(cfg, dict):
            Logger.error(
                f"Invalid configuration type: expected dict, got {type(cfg)}",
                context=self.__class__.__name__
            )
            raise TypeError("Invalid configuration: cfg must be a dict")

        required_keys = {"modules", "limits", "timeouts"}

        missing = required_keys - cfg.keys()

        if missing:
            Logger.error(
                f"Invalid configuration: missing keys {missing}",
                context=self.__class__.__name__
            )
            raise ValueError(
                "Invalid configuration: expected keys 'modules', 'limits' and 'timeouts'"
            )

    def run(self, execution, cfg):

        self._validate_cfg(cfg)

        started_at = datetime.now(timezone.utc)

        Logger.info("Starting execution", context="Orchestrator")

        builder = ServiceBuilder(self.uow, cfg, Utils.is_valid_domain)
        services = builder.build()

        context = ExecutionContext(execution, cfg)

        module_results = []
        lock = threading.Lock()

        # --------------------------------
        # Safe module execution
        # --------------------------------

        def execute(module_key, service_key):

            if not cfg.get("modules", {}).get(module_key):
                Logger.debug(f"{module_key} disabled in config", context="Orchestrator")
                return

            service = services.get(service_key)

            if not service:
                raise RuntimeError(f"Service not found: {service_key}")

            Logger.info(f"START module: {module_key}", context="Orchestrator")

            try:
                result = service.run(context)

                if not result:
                    raise ValueError("Module returned empty response")

                with lock:
                    module_results.append(result)

                Logger.info(f"END module: {module_key}", context="Orchestrator")

            except Exception as e:

                Logger.error(
                    f"ERROR module: {module_key} -> {e}",
                    context="Orchestrator"
                )

                with lock:
                    module_results.append(
                        ModuleResponse(
                            module_name=module_key,
                            status=ModuleStatus.FAILED,
                            started_at=datetime.now(timezone.utc),
                            finished_at=datetime.now(timezone.utc),
                            errors=[str(e)]
                        )
                    )

        # --------------------------------
        # Module pipeline
        # --------------------------------

        Logger.info("PHASE: SUBDOMAINS", context="Orchestrator")
        execute("subdomains", "subdomain")

        Logger.info("PHASE: WHOIS", context="Orchestrator")
        execute("whois", "whois")

        Logger.info("PHASE: DNS", context="Orchestrator")
        execute("dns", "dns")

        # --------------------------------
        # Parallel infrastructure phase
        # --------------------------------

        Logger.info("PHASE: PARALLEL INFRASTRUCTURE", context="Orchestrator")

        parallel_modules = [
            ("nmap", "nmap"),
            ("shodan", "shodan"),
            ("emails_passive", "emails_passive"),
            ("crawler", "crawling"),
        ]

        with ThreadPoolExecutor(max_workers=4) as executor:

            futures = [
                executor.submit(execute, module_key, service_key)
                for module_key, service_key in parallel_modules
            ]

            for f in futures:
                f.result()

        Logger.info("Infrastructure phase finished", context="Orchestrator")

        # --------------------------------
        # Content parsing phase
        # --------------------------------

        Logger.info("PHASE: CONTENT PARSING", context="Orchestrator")

        parsers = [
            ("js_parsing", "js"),
            ("file_parsing", "file"),
        ]

        with ThreadPoolExecutor(max_workers=2) as executor:

            futures = [
                executor.submit(execute, module_key, service_key)
                for module_key, service_key in parsers
            ]

            for f in futures:
                f.result()

        Logger.info("Content parsing phase finished", context="Orchestrator")

        # --------------------------------
        # Final scraping
        # --------------------------------

        Logger.info("PHASE: SCRAPING", context="Orchestrator")
        execute("scraping", "scraping")

        # --------------------------------
        # Persist metrics
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
            Logger.error(
                f"Metrics persistence failed: {e}",
                context="Orchestrator"
            )

        # --------------------------------
        # Summary
        # --------------------------------

        Logger.info("EXECUTION SUMMARY", context="Orchestrator")

        for r in module_results:

            Logger.info(f"[{r.module_name}]", context="Orchestrator")
            Logger.info(f"Status: {r.status}", context="Orchestrator")
            Logger.info(f"Duration: {r.duration_seconds}", context="Orchestrator")
            Logger.info(f"Metrics: {r.metrics}", context="Orchestrator")

            if r.errors:
                Logger.error(f"Errors: {r.errors}", context="Orchestrator")

        # --------------------------------
        # Performance
        # --------------------------------

        real_duration = (datetime.now(timezone.utc) - started_at).total_seconds()

        modules_duration = sum(
            r.duration_seconds for r in module_results if r.duration_seconds
        )

        Logger.info("PERFORMANCE", context="Orchestrator")
        Logger.info(f"Real execution time: {real_duration:.2f} seconds", context="Orchestrator")
        Logger.info(f"Sum of module durations: {modules_duration:.2f} seconds", context="Orchestrator")

        if modules_duration > 0:
            efficiency = modules_duration / real_duration
            Logger.info(f"Concurrency factor: {efficiency:.2f}x", context="Orchestrator")

        # --------------------------------
        # Execution response
        # --------------------------------

        return ExecutionResponse(
            execution_id=execution.ID,
            target=execution.TARGET,
            started_at=started_at,
            modules=module_results
        )