from application.execution import Execution
from application.orchestrator import Orchestrator
from persistence.database import Database
from persistence.uow import UnitOfWork
from application.config import APP_CONFIG


def main():

    print("\n========== EREBUS ==========\n")

    target = input("Introduce el dominio objetivo: ").strip()

    if not target:
        print("Error: dominio vacío")
        return

    # ----------------------------
    # Inicializar DB
    # ----------------------------

    db = Database()

    if APP_CONFIG["debug"]["clear_db_on_run"]:
        db.clear_all()

    uow = UnitOfWork(db.conn)

    # ----------------------------
    # Crear ejecución
    # ----------------------------

    execution = Execution(target)
    uow.executions.insert(execution)

    orchestrator = Orchestrator(uow)

    try:

        cfg = {
            "modules": APP_CONFIG["modules"],
            "limits": APP_CONFIG["limits"],
            "timeouts": APP_CONFIG["timeouts"]
        }

        orchestrator.run(execution, cfg)

        execution.finish()

    except Exception as e:

        execution.STATUS = "ERROR"
        execution.END = execution.END or execution.START

        print("\n[MAIN ERROR]", e)

    finally:

        uow.executions.update(execution)

    print("\n========== FIN ==========\n")


if __name__ == "__main__":
    main()