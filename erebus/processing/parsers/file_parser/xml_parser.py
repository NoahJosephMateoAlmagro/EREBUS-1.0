from xml.etree import ElementTree as ET

import shared.constants as C
from shared.logger import Logger
from .base import BaseFileParser


class XmlParser(BaseFileParser):
    """
    Parser responsible for extracting text content from XML files.
    """

    technique = C.TECHNIQUE_FILE_XML
    extensions = {".xml"}

    def extract_text(self, content: bytes) -> str:
        """
        Extracts text content from XML bytes.

        Args:
            content (bytes): Raw XML file content

        Returns:
            str: Extracted text
        """
        try:
            root = ET.fromstring(content)
            texts = []

            for elem in root.iter():
                if elem.text:
                    text = elem.text.strip()
                    if text:
                        texts.append(text)

            return "\n".join(texts)

        except Exception as e:
            Logger.error(
                f"XML parsing error: {e}",
                context=self.__class__.__name__
            )
            return ""