import re
import base64
import html


class EmailAnalyzer:

    EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    OBFUSCATED_PATTERNS = [
        (r"\s*\[\s*at\s*\]\s*", "@"),
        (r"\s*\(\s*at\s*\)\s*", "@"),
        (r"\s+at\s+", "@"),
        (r"\s*\[\s*dot\s*\]\s*", "."),
        (r"\s*\(\s*dot\s*\)\s*", "."),
        (r"\s+dot\s+", "."),
    ]

    CONCAT_REGEX = re.compile(
        r"['\"]([a-zA-Z0-9._%+-]+)['\"]\s*\+\s*['\"]@['\"]\s*\+\s*['\"]([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})['\"]"
    )

    BASE64_CALL_REGEX = re.compile(
        r"atob\(\s*['\"]([A-Za-z0-9+/=]{20,})['\"]\s*\)"
    )

    BASE64_TOKEN_REGEX = re.compile(
        r"\b[A-Za-z0-9+/=]{24,}\b"
    )

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def extract(self, text: str) -> set[str]:
        """
        Extrae emails incluyendo:
        - Emails en claro
        - Ofuscaciones [at]/[dot]
        - Concatenaciones JS
        - HTML entities
        - Base64
        """
        found = set()

        if not text:
            return found

        lowered = text.lower()

        # 1️⃣ Emails en claro
        for e in re.findall(self.EMAIL_REGEX, lowered):
            found.add(e)

        # 2️⃣ Sustituciones [at]/[dot]
        candidate = lowered
        for pattern, repl in self.OBFUSCATED_PATTERNS:
            candidate = re.sub(pattern, repl, candidate)

        for e in re.findall(self.EMAIL_REGEX, candidate):
            found.add(e)

        # 3️⃣ Concatenaciones simples tipo "info" + "@" + "example.com"
        for user, domain in self.CONCAT_REGEX.findall(text):
            email = f"{user}@{domain}".lower()
            if re.match(self.EMAIL_REGEX, email):
                found.add(email)

        # 4️⃣ HTML entities y escapes JS
        unescaped = html.unescape(text)

        try:
            unescaped = unescaped.encode().decode("unicode_escape")
        except Exception:
            pass

        for e in re.findall(self.EMAIL_REGEX, unescaped.lower()):
            found.add(e)

        # 5️⃣ Base64 en llamadas atob()
        for token in self.BASE64_CALL_REGEX.findall(text):
            self._decode_base64_email(token, found)

        # 6️⃣ Base64 suelto
        compact = re.sub(r"\s+", "", text)

        for token in self.BASE64_TOKEN_REGEX.findall(compact):
            self._decode_base64_email(token, found)

        return found

    def normalize(self, email: str) -> str | None:
        """
        Normalización mínima estructural.
        """
        if not email:
            return None

        email = email.strip().lower()

        if "@" not in email:
            return None

        return email

    def extract_from_file_text(self, text: str) -> set[str]:
        """
        Alias semántico para uso en FileParser.
        """
        return self.extract(text)

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------

    def _decode_base64_email(self, token: str, found: set):
        try:
            decoded = base64.b64decode(token).decode("utf-8", errors="ignore")
            for e in re.findall(self.EMAIL_REGEX, decoded.lower()):
                found.add(e)
        except Exception:
            pass
