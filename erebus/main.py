from application.execution import Execution
from application.orchestrator import Orchestrator
from persistence.database import Database
from persistence.uow import UnitOfWork
from application.config import APP_CONFIG
from shared.logger import Logger
from shared.domain_validator import valid_domain


def main():
    """
    Entry point of the EREBUS engine.

    """

    Logger.info("Starting EREBUS", context="Main")

    target = input("Enter target domain: ").strip()

    if not target:
        Logger.error("Empty target provided", context="Main")
        return

    # ----------------------------
    # Initialize DB
    # ----------------------------

    db = Database()

    if APP_CONFIG.get("debug", {}).get("clear_db_on_run"):
        Logger.info("Clearing database (debug mode)", context="Main")
        db.clear_all()

    uow = UnitOfWork(db.conn)

    # ----------------------------
    # Create execution
    # ----------------------------

    execution = Execution(target)
    uow.executions.insert(execution)

    orchestrator = Orchestrator(uow)

    try:

        cfg = {
            "modules": APP_CONFIG.get("modules", {}),
            "limits": APP_CONFIG.get("limits", {}),
            "timeouts": APP_CONFIG.get("timeouts", {})
        }

        Logger.info(
            f"Running orchestrator execution_id={execution.ID} target={execution.TARGET}",
            context="Main"
        )

        orchestrator.run(execution, cfg)

        execution.finish()

        Logger.info(
            f"Execution finished execution_id={execution.ID}",
            context="Main"
        )

    except Exception as e:

        execution.fail()

        Logger.error(
            f"Execution failed execution_id={execution.ID} error={e}",
            context="Main"
        )

    finally:

        uow.executions.update(execution)

        Logger.info(
            f"Execution persisted execution_id={execution.ID} status={execution.STATUS}",
            context="Main"
        )

    Logger.info("END EREBUS", context="Main")


if __name__ == "__main__":
    main()