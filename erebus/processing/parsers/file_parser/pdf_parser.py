from io import BytesIO
from pdfminer.high_level import extract_text
from .base import BaseFileParser
import shared.constants as C

class PdfParser(BaseFileParser):

    technique = C.TECHNIQUE_FILE_PDF
    extensions = (".pdf",)

    def can_parse(self, url: str) -> bool:
        return url.lower().endswith(".pdf")

    def extract_text(self, content: bytes) -> str:
        try:
            return extract_text(BytesIO(content))
        except Exception:
            return ""
