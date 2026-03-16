from io import BytesIO
from pdfminer.high_level import extract_text
from .base import BaseFileParser
import shared.constants as C
import logging

logging.getLogger("pdfminer").setLevel(logging.ERROR)

class PdfParser(BaseFileParser):

    technique = C.TECHNIQUE_FILE_PDF
    extensions = (".pdf",)


    def can_parse(self, url: str) -> bool:
        return url.lower().endswith(".pdf")

    def extract_text(self, content: bytes) -> str:

        try:
            text = extract_text(BytesIO(content))

            if not text:
                return ""

            return text

        except Exception as e:

            print(f"[PDF PARSER] Error: {e}")
            return ""