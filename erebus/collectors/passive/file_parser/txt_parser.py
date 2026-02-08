from .base import BaseFileParser
import core.constants as C

class TxtParser(BaseFileParser):

    technique = C.TECHNIQUE_FILE_TXT
    extensions = (".txt",)

    def can_parse(self, url: str) -> bool:
        return url.lower().endswith(".txt")

    def extract_text(self, content: bytes) -> str:
        try:
            return content.decode("utf-8", errors="ignore")
        except Exception:
            return ""
