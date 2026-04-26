"""
Console controller for EREBUS.

This module contains the controller responsible for redirecting stdout and
stderr to the GUI console page and processing queued console messages.
"""

import queue
import sys

import presentation.constants as C
from presentation.services.console_redirector import ConsoleRedirector


class ConsoleController:
    """
    Controls console redirection and message delivery to the GUI console page.
    """

    def __init__(self, app, console_page):
        """
        Initializes the console controller.

        Args:
            app: Root application instance.
            console_page: Console page widget that receives log messages.
        """
        self.app = app
        self.console_page = console_page
        self.console_queue = queue.Queue()

        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def start(self) -> None:
        """
        Starts stdout and stderr redirection to the GUI console.
        """
        sys.stdout = ConsoleRedirector(self.console_queue, "stdout")
        sys.stderr = ConsoleRedirector(self.console_queue, "stderr")

        self.app.after(C.CONSOLE_POLL_INTERVAL_MS, self._process_console_queue)

    def restore_streams(self) -> None:
        """
        Restores the original stdout and stderr streams.
        """
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def _process_console_queue(self) -> None:
        """
        Processes pending console messages from the queue.
        """
        if self.app._closing or not self.app.winfo_exists():
            return

        try:
            while True:
                stream_name, message = self.console_queue.get_nowait()

                if stream_name == "stderr":
                    self.console_page.append(message, is_error=True)
                else:
                    self.console_page.append(message)

        except queue.Empty:
            pass

        self.app.after(C.CONSOLE_POLL_INTERVAL_MS, self._process_console_queue)