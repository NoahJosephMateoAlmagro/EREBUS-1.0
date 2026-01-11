import re
import base64
import html

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

OBFUSCATED_PATTERNS = [
    (r"\s*\[\s*at\s*\]\s*", "@"),
    (r"\s*\(\s*at\s*\)\s*", "@"),
    (r"\s+at\s+", "@"),
    (r"\s*\[\s*dot\s*\]\s*", "."),
    (r"\s*\(\s*dot\s*\)\s*", "."),
    (r"\s+dot\s+", "."),
]

# "info" + "@" + "example.com"
CONCAT_REGEX = re.compile(
    r"['\"]([a-zA-Z0-9._%+-]+)['\"]\s*\+\s*['\"]@['\"]\s*\+\s*['\"]([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})['\"]"
)

# atob("...")
BASE64_CALL_REGEX = re.compile(r"atob\(\s*['\"]([A-Za-z0-9+/=]{20,})['\"]\s*\)")

BASE64_TOKEN_REGEX = re.compile(r"\b[A-Za-z0-9+/=]{24,}\b")

def normalize_obfuscated(text: str) -> set:
    found = set()
    if not text:
        return found

    lowered = text.lower()

    # 1. Emails en claro
    for e in re.findall(EMAIL_REGEX, lowered):
        found.add(e)

    # 2. Sustituciones [at]/[dot]
    candidate = lowered
    for pattern, repl in OBFUSCATED_PATTERNS:
        candidate = re.sub(pattern, repl, candidate)

    for e in re.findall(EMAIL_REGEX, candidate):
        found.add(e)

    # 3. Concatenaciones simples
    for user, domain in CONCAT_REGEX.findall(text):
        email = f"{user}@{domain}".lower()
        if re.match(EMAIL_REGEX, email):
            found.add(email)

    # 4. HTML entities y escapes JS
    unescaped = html.unescape(text)
    try:
        unescaped = unescaped.encode().decode("unicode_escape")
    except Exception:
        pass

    for e in re.findall(EMAIL_REGEX, unescaped.lower()):
        found.add(e)

    # 5. Base64 en llamadas atob()
    for token in BASE64_CALL_REGEX.findall(text):
        _decode_base64_email(token, found)

    # 6. Base64 suelto (más restrictivo)
    compact = re.sub(r"\s+", "", text)

    for token in BASE64_TOKEN_REGEX.findall(compact):
        _decode_base64_email(token, found)

    return found

def normalize_email(email: str) -> str | None:
    if not email:
        return None

    email = email.strip().lower()

    if "@" not in email:
        return None

    return email

def _decode_base64_email(token: str, found: set):
    try:
        decoded = base64.b64decode(token).decode("utf-8", errors="ignore")
        for e in re.findall(EMAIL_REGEX, decoded.lower()):
            found.add(e)
    except Exception:
        pass
