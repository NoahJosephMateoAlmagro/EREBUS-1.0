from io import BytesIO

from pdfminer.high_level import extract_text

import shared.constants as C
from shared.logger import Logger
from .base import BaseFileParser

import logging

# Suppress noisy pdfminer logs
logging.getLogger("pdfminer").setLevel(logging.ERROR)


class PdfParser(BaseFileParser):
    """
    Parser responsible for extracting text content from PDF files.
    """

    technique = C.TECHNIQUE_FILE_PDF
    extensions = {".pdf"}


    def extract_text(self, content: bytes) -> str:
        """
        Extracts text content from PDF bytes.

        Args:
            content (bytes): Raw PDF file content

        Returns:
            str: Extracted text
        """
        try:
            text = extract_text(BytesIO(content))
            return text or ""

        except Exception as e:
            Logger.error(
                f"PDF parsing error: {e}",
                context=self.__class__.__name__
            )
            return ""