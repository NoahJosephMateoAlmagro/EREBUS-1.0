"""
Execution controller for EREBUS.

This module contains the controller responsible for starting and stopping the
background execution thread, updating the execution page, tracking module
progress and persisting stable user preferences related to the execution form.
"""

import sys
import threading

from application.runner import run_erebus

import presentation.constants as C
from presentation.module_ui_metadata import MODULE_UI_CONFIG


class ExecutionController:
    """
    Controls execution lifecycle and progress updates for the GUI.
    """

    def __init__(
        self,
        app,
        execution_page,
        notification_popup,
        user_preferences_service,
    ):
        """
        Initializes the execution controller.

        Args:
            app: Root application instance.
            execution_page: Execution page widget.
            notification_popup: Notification popup widget.
            user_preferences_service: Service used to load and save persistent
                execution form preferences.
        """
        self.app = app
        self.execution_page = execution_page
        self.notification_popup = notification_popup
        self.user_preferences_service = user_preferences_service

        self.execution_thread = None
        self.cancel_event = None
        self.running_modules = set()

    def load_persistent_state(self) -> None:
        """
        Loads persisted execution form preferences and applies them to the page.
        """
        data = self.user_preferences_service.load_preferences()
        execution_data = data.get("execution_form", {})

        if isinstance(execution_data, dict):
            self.execution_page.apply_persistent_state(execution_data)

    def save_persistent_state(self) -> None:
        """
        Saves the current execution form preferences to disk.
        """
        current_data = self.user_preferences_service.load_preferences()

        if not isinstance(current_data, dict):
            current_data = {}

        current_data["execution_form"] = self.execution_page.get_persistent_state()
        self.user_preferences_service.save_preferences(current_data)

    def start_execution(self) -> None:
        """
        Starts an EREBUS execution in a background thread.
        """
        target = self.execution_page.get_target()

        if not target:
            self.execution_page.set_status(C.STATUS_MISSING_DOMAIN)
            return

        if self.execution_thread and self.execution_thread.is_alive():
            self.execution_page.set_status(C.STATUS_ALREADY_RUNNING)
            return

        self.save_persistent_state()

        config_overrides = self.execution_page.get_config_overrides()

        self.cancel_event = threading.Event()
        self.running_modules.clear()

        self.notification_popup.show(
            C.EXECUTION_STARTING_POPUP.format(target=target),
            closable=True,
            play_sound=True,
        )
        self.execution_page.set_running_state(True)
        self.execution_page.set_status(C.STATUS_RUNNING)

        self.execution_thread = threading.Thread(
            target=self._run_in_background,
            args=(target, config_overrides, self.cancel_event),
            daemon=True,
        )
        self.execution_thread.start()

    def stop_execution(self) -> None:
        """
        Requests the current execution to stop safely.
        """
        if not self.execution_thread or not self.execution_thread.is_alive():
            self.execution_page.set_status(C.STATUS_NO_EXECUTION_RUNNING)
            return

        if self.cancel_event:
            self.cancel_event.set()

        current = self._get_running_modules_text()

        self.execution_page.set_cancelling_state()

        self.notification_popup.show(
            C.STOP_REQUESTED_POPUP.format(current=current),
            closable=True,
            play_sound=True,
        )

        print(C.STOP_REQUESTED_CONSOLE)

    def on_module_progress(self, event_type, module_key) -> None:
        """
        Receives module progress events from the orchestrator.

        Args:
            event_type: Event type. Expected values are 'start', 'end' or 'error'.
            module_key: Internal module key.
        """
        if self.app._closing or not self.app.winfo_exists():
            return

        self.app.after(
            0,
            lambda: self._handle_module_progress(event_type, module_key),
        )

    def _run_in_background(self, target, config_overrides, cancel_event) -> None:
        """
        Runs the EREBUS engine in a background thread.

        Args:
            target: Target domain.
            config_overrides: Runtime configuration overrides from the UI.
            cancel_event: Event used to request safe cancellation.
        """
        try:
            execution = run_erebus(
                target=target,
                config_overrides=config_overrides,
                cancel_event=cancel_event,
                progress_callback=self.on_module_progress,
            )

            if cancel_event and cancel_event.is_set():
                message = C.STATUS_CANCELLED
                popup_message = C.EXECUTION_CANCELLED_POPUP

            elif execution:
                message = f"Status: {execution.STATUS}"
                popup_message = C.EXECUTION_FINISHED_POPUP.format(
                    target=target,
                    status=execution.STATUS,
                )

            else:
                message = C.STATUS_EXECUTION_FAILED
                popup_message = C.EXECUTION_FAILED_POPUP.format(target=target)

        except Exception as exc:
            message = C.STATUS_EXECUTION_FAILED
            popup_message = C.EXECUTION_FAILED_POPUP.format(target=target)
            print(f"[GUI] Execution failed: {exc}", file=sys.stderr)

        if self.app._closing or not self.app.winfo_exists():
            return

        self.app.after(0, lambda: self.execution_page.set_status(message))
        self.app.after(0, lambda: self.execution_page.set_running_state(False))
        self.app.after(0, self.running_modules.clear)

        if popup_message:
            self.app.after(
                0,
                lambda: self.notification_popup.show(
                    popup_message,
                    closable=True,
                    play_sound=True,
                ),
            )

    def _handle_module_progress(self, event_type, module_key) -> None:
        """
        Updates the UI with the current running module information.

        Args:
            event_type: Event type.
            module_key: Internal module key.
        """
        module_name = MODULE_UI_CONFIG.get(module_key, {}).get("title", module_key)

        if event_type == "start":
            self.running_modules.add(module_name)

        elif event_type in {"end", "error"}:
            self.running_modules.discard(module_name)

        if self.cancel_event and self.cancel_event.is_set():
            current = self._get_running_modules_text()

            self.notification_popup.update_message(
                C.STOP_REQUESTED_UPDATE.format(current=current)
            )

    def _get_running_modules_text(self) -> str:
        """
        Gets a readable text with the currently running modules.

        Returns:
            str: Current running modules text.
        """
        if not self.running_modules:
            return "finishing current phase"

        return ", ".join(sorted(self.running_modules))