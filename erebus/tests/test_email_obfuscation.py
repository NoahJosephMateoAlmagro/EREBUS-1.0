from normalizers.email_normalizer import normalize_obfuscated

text = """
Contacto: info [at] example [dot] com
Soporte: soporte(at)empresa(dot)es
Encoded: aW5mb0BleGFtcGxlLmNvbQ==
"""

print(normalize_obfuscated(text))
