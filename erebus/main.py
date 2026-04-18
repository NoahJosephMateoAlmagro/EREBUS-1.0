from copy import deepcopy

from application.execution import Execution
from application.orchestrator import Orchestrator
from persistence.database import Database
from persistence.uow import UnitOfWork
from application.config import APP_CONFIG
from shared.logger import Logger


def main():
    """
    Entry point of the EREBUS engine.

    """

    Logger.configure(
        timezone=APP_CONFIG["logging"]["timezone"],
        mode=APP_CONFIG["logging"]["mode"]
    )

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
        cfg = deepcopy(APP_CONFIG)

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

        try:

            uow.executions.update(execution)

            Logger.info(

                f"Execution persisted execution_id={execution.ID} status={execution.STATUS}",

                context="Main"

            )

        except Exception as e:

            Logger.error(

                f"Failed to persist execution execution_id={execution.ID}: {e}",

                context="Main"

            )

        Logger.info(
            f"Execution persisted execution_id={execution.ID} status={execution.STATUS}",
            context="Main"
        )

    Logger.info("END EREBUS", context="Main")


if __name__ == "__main__":
    main()