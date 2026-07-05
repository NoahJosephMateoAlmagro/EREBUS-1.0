from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import shared.constants as C


class Logger:
    class Logger:
        """
        Simple centralized logger for EREBUS.
        Supports DEBUG, INFO, ERROR and SILENT modes.
        """

    TIMEZONE = "UTC"
    MODE = C.LOG_MODE_INFO

    @classmethod
    def configure(cls, timezone: str, mode: str = C.LOG_MODE_INFO) -> None:
        """
        Configures logger runtime options.

        Args:
            timezone (str): IANA timezone name (e.g. 'Europe/Madrid', 'UTC')
            mode (str): Logging mode ('DEBUG', 'INFO', 'ERROR', 'SILENT')
        """
        cls.TIMEZONE = timezone

        normalized_mode = (mode or C.LOG_MODE_INFO).upper()
        if normalized_mode not in C.LOG_MODE_PRIORITIES:
            normalized_mode = C.LOG_MODE_INFO

        cls.MODE = normalized_mode

    @classmethod
    def _should_log(cls, level: str) -> bool:
        """
        Determines whether a message should be printed based on the current mode.

        Args:
            level (str): Log level ('DEBUG', 'INFO', 'ERROR')
        Returns:
            bool: True if the message should be printed, False otherwise
        """
        current_mode_priority = C.LOG_MODE_PRIORITIES.get(
            cls.MODE,
            C.LOG_MODE_PRIORITIES[C.LOG_MODE_INFO]
        )
        level_priority = C.LOG_LEVEL_PRIORITIES[level]

        return level_priority >= current_mode_priority

    @classmethod
    def _get_now(cls) -> datetime:
        """
        Returns the current datetime using the configured timezone.
        Falls back to UTC if the timezone is not available.
        """
        try:
            if cls.TIMEZONE.upper() == "UTC":
                return datetime.now(timezone.utc)

            return datetime.now(ZoneInfo(cls.TIMEZONE))

        except ZoneInfoNotFoundError:
            return datetime.now(timezone.utc)

    @classmethod
    def _log(cls, level: str, message: str, context: Optional[str] = None) -> None:
        """
        Internal logging method.

        Args:
            level (str): Log level (TRACE, INFO, ERROR)
            message (str): Log message
            context (Optional[str]): Optional context (e.g. collector name)
        """
        if not cls._should_log(level):
            return

        timestamp = cls._get_now().strftime("%Y-%m-%d %H:%M:%S %Z")

        if context:
            print(f"[{timestamp}] [{level}] [{context}] {message}")
        else:
            print(f"[{timestamp}] [{level}] {message}")

    @classmethod
    def debug(cls, message: str, context: Optional[str] = None) -> None:
        """
        Debug log.
        """
        cls._log(C.LOG_MODE_DEBUG, message, context)

    @classmethod
    def info(cls, message: str, context: Optional[str] = None) -> None:
        """
        Informational log.
        """
        cls._log(C.LOG_MODE_INFO, message, context)

    @classmethod
    def error(cls, message: str, context: Optional[str] = None) -> None:
        """
        Error log.
        """
        cls._log(C.LOG_MODE_ERROR, message, context)