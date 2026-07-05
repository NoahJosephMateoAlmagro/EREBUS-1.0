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

    The orchestrator is responsible for executing the configured modules
    in the correct order, grouping compatible modules into parallel phases
    and collecting their execution responses.

    Cancellation is cooperative: when a cancel_event is provided and set,
    the orchestrator stops starting new modules or phases, but it does not
    forcibly kill already running module threads.
    """

    def __init__(self, uow):
        """
        Initializes the orchestrator.

        Args:
            uow: Unit of Work used by the services and repositories.
        """
        self.uow = uow

    def _validate_cfg(self, cfg):
        """
        Validates the runtime configuration.

        Args:
            cfg: Runtime configuration dictionary.

        Raises:
            ValueError: If cfg is None or missing required keys.
            TypeError: If cfg is not a dictionary.
        """
        if cfg is None:
            Logger.error(
                "Invalid configuration: cfg is None",
                context=self.__class__.__name__,
            )
            raise ValueError("Configuration required: cfg cannot be None")

        if not isinstance(cfg, dict):
            Logger.error(
                f"Invalid configuration type: expected dict, got {type(cfg)}",
                context=self.__class__.__name__,
            )
            raise TypeError("Invalid configuration: cfg must be a dict")

        required_keys = {"modules", "limits", "timeouts", "tools", "retries"}
        missing = required_keys - cfg.keys()

        if missing:
            Logger.error(
                f"Invalid configuration: missing keys {missing}",
                context=self.__class__.__name__,
            )
            raise ValueError(
                "Invalid configuration: expected keys "
                "'modules', 'limits', 'timeouts', 'tools' and 'retries'"
            )

    def run(self, execution, cfg, cancel_event=None, progress_callback=None):
        """
        Runs the configured EREBUS module pipeline.

        Args:
            execution: Execution entity for the current run.
            cfg: Runtime configuration dictionary.
            cancel_event: Optional threading.Event used to request cancellation.
            progress_callback: Optional callback used to notify module progress.
                Expected signature: progress_callback(event_type, module_key)

        Returns:
            ExecutionResponse: Response containing module results generated
            before normal completion or cancellation.
        """
        self._validate_cfg(cfg)

        started_at = datetime.now(timezone.utc)

        Logger.info("Starting execution", context="Orchestrator")

        builder = ServiceBuilder(self.uow, cfg, Utils.validate_and_normalize_domain)
        services = builder.build()

        context = ExecutionContext(execution, cfg)

        module_results = []
        lock = threading.Lock()
        cancelled = False

        # --------------------------------
        # Cancellation helpers
        # --------------------------------

        def cancellation_requested():
            """
            Checks whether cancellation has been requested.

            Returns:
                bool: True if cancellation has been requested, False otherwise.
            """
            return cancel_event is not None and cancel_event.is_set()

        def mark_cancelled(reason):
            """
            Marks the orchestration as cancelled and logs the reason.

            Args:
                reason: Human-readable cancellation point.
            """
            nonlocal cancelled

            if not cancelled:
                cancelled = True

                Logger.info(
                    f"Cancellation requested: {reason}",
                    context="Orchestrator",
                )

        def notify_progress(event_type, module_key):
            """
            Notifies the UI about module progress.

            Args:
                event_type: Progress event type: start, end or error.
                module_key: Internal module key.
            """
            if not progress_callback:
                return

            try:
                progress_callback(event_type, module_key)
            except Exception as e:
                Logger.error(
                    f"Progress callback failed event={event_type} module={module_key}: {e}",
                    context="Orchestrator",
                )

        # --------------------------------
        # Safe module execution
        # --------------------------------

        def execute(module_key, service_key):
            """
            Executes one module safely.

            This method catches module exceptions and converts them into
            ModuleResponse objects with FAILED status, so one failing module
            does not crash the whole orchestration.

            Args:
                module_key: Key used in cfg["modules"].
                service_key: Key used in the service builder output.
            """

            if cancellation_requested():
                Logger.info(
                    f"Skipping module because cancellation was requested: {module_key}",
                    context="Orchestrator",
                )
                return

            if not cfg.get("modules", {}).get(module_key):
                Logger.debug(
                    f"{module_key} disabled in config",
                    context="Orchestrator",
                )
                return

            service = services.get(service_key)

            if not service:
                raise RuntimeError(f"Service not found: {service_key}")

            Logger.info(f"START module: {module_key}", context="Orchestrator")
            notify_progress("start", module_key)

            try:
                result = service.run(context)

                if not result:
                    raise ValueError("Module returned empty response")

                with lock:
                    module_results.append(result)

                Logger.info(f"END module: {module_key}", context="Orchestrator")
                notify_progress("end", module_key)

                if cancellation_requested():
                    Logger.info(
                        f"Cancellation detected after module finished: {module_key}",
                        context="Orchestrator",
                    )

            except Exception as e:
                Logger.error(
                    f"ERROR module: {module_key} -> {e}",
                    context="Orchestrator",
                )

                notify_progress("error", module_key)

                with lock:
                    module_results.append(
                        ModuleResponse(
                            module_name=module_key,
                            status=ModuleStatus.FAILED,
                            started_at=datetime.now(timezone.utc),
                            finished_at=datetime.now(timezone.utc),
                            errors=[str(e)],
                        )
                    )

        # --------------------------------
        # Module pipeline
        # --------------------------------

        if cancellation_requested():
            mark_cancelled("before SUBDOMAINS phase")
        else:
            Logger.info("PHASE: SUBDOMAINS", context="Orchestrator")
            execute("subdomains", "subdomains")

        if cancellation_requested():
            mark_cancelled("after SUBDOMAINS phase")
        else:
            Logger.info("PHASE: WHOIS", context="Orchestrator")
            execute("whois", "whois")

        if cancellation_requested():
            mark_cancelled("after WHOIS phase")
        else:
            Logger.info("PHASE: DNS", context="Orchestrator")
            execute("dns", "dns")

        # --------------------------------
        # Parallel infrastructure phase
        # --------------------------------

        if cancellation_requested():
            mark_cancelled("before PARALLEL INFRASTRUCTURE phase")
        else:
            Logger.info("PHASE: PARALLEL INFRASTRUCTURE", context="Orchestrator")

            parallel_modules = [
                ("nmap", "nmap"),
                ("shodan", "shodan"),
                ("email_passive", "email_passive"),
                ("crawling", "crawling"),
            ]

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []

                for module_key, service_key in parallel_modules:
                    if cancellation_requested():
                        mark_cancelled(
                            f"while scheduling parallel module: {module_key}"
                        )
                        break

                    futures.append(
                        executor.submit(execute, module_key, service_key)
                    )

                for future in futures:
                    future.result()

            Logger.info(
                "Infrastructure phase finished",
                context="Orchestrator",
            )

        # --------------------------------
        # Content parsing phase
        # --------------------------------

        if cancellation_requested():
            mark_cancelled("before CONTENT PARSING phase")
        else:
            Logger.info("PHASE: CONTENT PARSING", context="Orchestrator")

            parsers = [
                ("js_parsing", "js_parsing"),
                ("file_parsing", "file_parsing"),
            ]

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = []

                for module_key, service_key in parsers:
                    if cancellation_requested():
                        mark_cancelled(
                            f"while scheduling parser module: {module_key}"
                        )
                        break

                    futures.append(
                        executor.submit(execute, module_key, service_key)
                    )

                for future in futures:
                    future.result()

            Logger.info(
                "Content parsing phase finished",
                context="Orchestrator",
            )

        # --------------------------------
        # Final scraping
        # --------------------------------

        if cancellation_requested():
            mark_cancelled("before SCRAPING phase")
        else:
            Logger.info("PHASE: SCRAPING", context="Orchestrator")
            execute("scraping", "scraping")

        if cancellation_requested():
            mark_cancelled("after SCRAPING phase")

        # --------------------------------
        # Summary
        # --------------------------------

        Logger.info("EXECUTION SUMMARY", context="Orchestrator")

        if cancelled:
            Logger.info(
                "Execution was cancelled cooperatively. "
                "Only completed module results are included.",
                context="Orchestrator",
            )

        for result in module_results:
            Logger.info(f"[{result.module_name}]", context="Orchestrator")
            Logger.info(f"Status: {result.status}", context="Orchestrator")
            Logger.info(
                f"Duration: {result.duration_seconds}",
                context="Orchestrator",
            )
            Logger.info(f"Metrics: {result.metrics}", context="Orchestrator")

            if result.errors:
                Logger.error(
                    f"Errors: {result.errors}",
                    context="Orchestrator",
                )

        # --------------------------------
        # Performance
        # --------------------------------

        real_duration = (datetime.now(timezone.utc) - started_at).total_seconds()

        modules_duration = sum(
            result.duration_seconds
            for result in module_results
            if result.duration_seconds
        )

        Logger.info("PERFORMANCE", context="Orchestrator")
        Logger.info(
            f"Real execution time: {real_duration:.2f} seconds",
            context="Orchestrator",
        )
        Logger.info(
            f"Sum of module durations: {modules_duration:.2f} seconds",
            context="Orchestrator",
        )

        if modules_duration > 0 and real_duration > 0:
            efficiency = modules_duration / real_duration
            Logger.info(
                f"Concurrency factor: {efficiency:.2f}x",
                context="Orchestrator",
            )

        # --------------------------------
        # Execution response
        # --------------------------------

        return ExecutionResponse(
            execution_id=execution.ID,
            target=execution.TARGET,
            started_at=started_at,
            modules=module_results,
        )