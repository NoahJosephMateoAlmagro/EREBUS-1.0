from collectors.passive.waybackMachine import WaybackCollector
from collectors.passive.crawler import Crawler

TARGET = "urjc.es"


def test_wayback_to_crawler():
    print("\n[TEST] Wayback → Crawler → Emails\n")

    # 1️⃣ Ejecutar Wayback
    wayback = WaybackCollector(limit=20, timeout=10)
    urls = wayback.collect(TARGET)

    print(f"[WAYBACK] urls devueltas: {len(urls)}")

    if not urls:
        print("\n❌ ERROR: Wayback NO ha devuelto URLs")
        print("➡️ El problema NO es del crawler")
        print("➡️ El problema está en:")
        print("   - la query CDX")
        print("   - o los filtros del WaybackCollector")
        print("\nℹ️ Siguiente paso recomendado:")
        print("   - revisar 'url' (*.dominio/* vs dominio/*)")
        print("   - revisar 'filter=statuscode:200'")
        assert False, "Wayback no ha devuelto URLs"

    # Mostrar algunas URLs
    print("\n[WAYBACK] ejemplo URLs:")
    for u in list(urls)[:5]:
        print(" ", u)

    # 2️⃣ Ejecutar crawler SOLO con URLs de Wayback
    crawler = Crawler(
        start_url=list(urls),
        max_pages=20,
        timeout=8,
        allowed_domain=None  # IMPORTANTE: permitir dominios históricos
    )

    results = crawler.run()

    print(f"\n[CRAWLER] páginas crawladas: {len(results)}")
    assert results, "El crawler no ha devuelto páginas"

    # 3️⃣ Extraer emails
    emails = set()

    for page in results:
        for e in page.get("emails", []):
            emails.add(e)

    print(f"\n[CRAWLER] emails encontrados: {len(emails)}")

    if not emails:
        print("\n❌ ERROR: El crawler NO ha encontrado emails")
        print("➡️ Wayback SÍ devuelve URLs")
        print("➡️ El crawler SÍ funciona")
        print("➡️ El HTML histórico NO contiene emails parseables")
        assert False, "Crawler no ha encontrado emails desde Wayback"

    for e in sorted(emails):
        print(" ", e)

    # 4️⃣ Assert clave de dominio
    assert any("@urjc.es" in e for e in emails), (
        "No se han detectado emails @urjc.es desde Wayback"
    )

    print("\n✅ TEST OK: Wayback → Crawler → Emails funciona correctamente\n")


if __name__ == "__main__":
    test_wayback_to_crawler()
