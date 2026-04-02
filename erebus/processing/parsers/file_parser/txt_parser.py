from .base import BaseFileParser

import shared.constants as C
from shared.logger import Logger


class TxtParser(BaseFileParser):
    """
    Parser responsible for extracting text content from plain text files.
    """

    technique = C.TECHNIQUE_FILE_TXT
    extensions = {".txt"}

    def extract_text(self, content: bytes) -> str:
        """
        Extracts text content from raw TXT bytes.

        Args:
            content (bytes): Raw file content

        Returns:
            str: Decoded text
        """
        try:
            return content.decode("utf-8", errors="ignore")

        except Exception as e:
            Logger.error(
                f"TXT parsing error: {e}",
                context=self.__class__.__name__
            )
            return ""