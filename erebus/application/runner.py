from copy import deepcopy

from application.execution import Execution
from application.orchestrator import Orchestrator
from persistence.database import Database
from persistence.uow import UnitOfWork
from application.config import APP_CONFIG
from shared.logger import Logger


def build_runtime_config(config_overrides=None):
    """
    Builds the configuration used by one execution.

    APP_CONFIG is never modified directly.
    A deep copy is created and then runtime overrides are applied.

    Args:
        config_overrides: Optional dictionary containing runtime configuration changes.

    Returns:
        dict: Runtime configuration for one execution.
    """
    cfg = deepcopy(APP_CONFIG)

    if config_overrides:
        deep_update(cfg, config_overrides)

    return cfg


def deep_update(base, overrides):
    """
    Recursively updates a dictionary without replacing complete nested sections.

    Example:
        If overrides only changes modules.nmap,
        the rest of base["modules"] remains unchanged.

    Args:
        base: Base dictionary to update.
        overrides: Dictionary containing override values.
    """
    for key, value in overrides.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            deep_update(base[key], value)
        else:
            base[key] = value


def run_erebus(
    target,
    config_overrides=None,
    cancel_event=None,
    progress_callback=None,
):
    """
    Runs an EREBUS execution.

    This function is the execution entry point used by the graphical interface.
    It creates a runtime configuration, initializes the database, creates the
    execution record and launches the orchestrator.

    Args:
        target: Target domain.
        config_overrides: Runtime configuration overrides.
        cancel_event: Optional threading.Event used to request cancellation.
        progress_callback: Optional callback used to notify the UI about module progress.

    Returns:
        dict | None: Dictionary containing:
            - execution: Persisted execution entity
            - execution_response: Structured orchestrator response
        Returns None if the target is empty.
    """
    if not target:
        Logger.error("Empty target provided", context="Runner")
        return None

    cfg = build_runtime_config(config_overrides)

    Logger.configure(
        timezone=cfg["logging"]["timezone"],
        mode=cfg["logging"]["mode"],
    )

    Logger.info("Starting EREBUS", context="Runner")

    db = Database()

    if cfg.get("debug", {}).get("clear_db_on_run"):
        Logger.info("Clearing database (debug mode)", context="Runner")
        db.clear_all()

    uow = UnitOfWork(db.conn)

    execution = Execution(target)
    uow.executions.insert(execution)

    orchestrator = Orchestrator(uow)
    execution_response = None

    try:
        Logger.info(
            f"Running orchestrator execution_id={execution.ID} target={execution.TARGET}",
            context="Runner",
        )

        execution_response = orchestrator.run(
            execution,
            cfg,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
        )

        if cancel_event and cancel_event.is_set():
            execution.fail()
            execution.STATUS = "CANCELLED"

            Logger.info(
                f"Execution cancelled execution_id={execution.ID}",
                context="Runner",
            )
        else:
            execution.finish()

            Logger.info(
                f"Execution finished execution_id={execution.ID}",
                context="Runner",
            )

    except Exception as e:
        execution.fail()

        Logger.error(
            f"Execution failed execution_id={execution.ID} error={e}",
            context="Runner",
        )

    finally:
        try:
            uow.executions.update(execution)

            Logger.info(
                f"Execution persisted execution_id={execution.ID} status={execution.STATUS}",
                context="Runner",
            )

        except Exception as e:
            Logger.error(
                f"Failed to persist execution execution_id={execution.ID}: {e}",
                context="Runner",
            )

    Logger.info("END EREBUS", context="Runner")

    return {
        "execution": execution,
        "execution_response": execution_response,
    }