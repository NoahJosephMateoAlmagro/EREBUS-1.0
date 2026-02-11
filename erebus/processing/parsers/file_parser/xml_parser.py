from .base import BaseFileParser
import xml.etree.ElementTree as ET
import shared.constants as C

class XmlParser(BaseFileParser):

    technique = C.TECHNIQUE_FILE_XML
    extensions = (".xml",)

    def can_parse(self, url: str) -> bool:
        return url.lower().endswith(".xml")

    def extract_text(self, content: bytes) -> str:
        try:
            root = ET.fromstring(content)
            texts = []

            for elem in root.iter():
                if elem.text:
                    texts.append(elem.text)

            return "\n".join(texts)
        except Exception:
            return ""
