from datetime import datetime
from typing import Optional


class Logger:
    """
    Simple centralized logger for EREBUS.
    Supports basic log levels (DEBUG, INFO, ERROR).
    """

    DEBUG_ENABLED = True  # Toggle all debug logs globally

    @staticmethod
    def _log(level: str, message: str, context: Optional[str] = None) -> None:
        """
        Internal logging method.

        Args:
            level (str): Log level (DEBUG, INFO, ERROR)
            message (str): Log message
            context (Optional[str]): Optional context (e.g. collector name)
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        if context:
            print(f"[{timestamp}] [{level}] [{context}] {message}")
        else:
            print(f"[{timestamp}] [{level}] {message}")

    @classmethod
    def debug(cls, message: str, context: Optional[str] = None) -> None:
        """
        Debug log (only printed if DEBUG_ENABLED is True).
        """
        if cls.DEBUG_ENABLED:
            cls._log("DEBUG", message, context)

    @classmethod
    def info(cls, message: str, context: Optional[str] = None) -> None:
        """
        Informational log (always printed).
        """
        cls._log("INFO", message, context)

    @classmethod
    def error(cls, message: str, context: Optional[str] = None) -> None:
        """
        Error log (always printed).
        """
        cls._log("ERROR", message, context)