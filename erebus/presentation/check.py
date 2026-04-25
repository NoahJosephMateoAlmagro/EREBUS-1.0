import ctypes
import tkinter as tk
from pathlib import Path


def load_font(font_path):
    font_path = Path(font_path).resolve()

    if not font_path.exists():
        print(f"[ERROR] No existe: {font_path}")
        return False

    loaded = ctypes.windll.gdi32.AddFontResourceExW(str(font_path), 0x10, 0)

    if loaded == 0:
        print(f"[ERROR] No se pudo cargar: {font_path}")
        return False

    print(f"[OK] Fuente cargada: {font_path}")
    return True


def main():
    base_dir = Path(__file__).resolve().parent
    fonts_dir = base_dir / "assets" / "fonts"

    print(f"\nBuscando fuentes en:\n{fonts_dir}\n")

    load_font(fonts_dir / "Zekton-Regular.otf")
    load_font(fonts_dir / "SHUTTLE-X.ttf")

    ctypes.windll.user32.SendMessageW(0xFFFF, 0x001D, 0, 0)

    root = tk.Tk()
    root.withdraw()

    families = sorted(root.tk.call("font", "families"))

    print("\nNombres encontrados para usar en family:\n")

    found = False

    for family in families:
        name = family.lower()

        if "zek" in name or "shuttle" in name:
            print(f'family="{family}"')
            found = True

    if not found:
        print("No se encontraron fuentes con 'zek' o 'shuttle' en el nombre.")
        print("Prueba a instalarlas manualmente: clic derecho -> Instalar para todos los usuarios.")
        print("Luego cierra y abre de nuevo PyCharm/terminal.")

    root.destroy()


if __name__ == "__main__":
    main()