"""Programın veri klasörü: Windows'ta %APPDATA%\\ParcaLink, diğerlerinde ~/.parcalink."""
import os


def klasor():
    kok = os.environ.get("APPDATA") or os.path.expanduser("~")
    yol = os.path.join(kok, "ParcaLink" if os.environ.get("APPDATA") else ".parcalink")
    os.makedirs(yol, exist_ok=True)
    return yol



def depo_yolu():
    return os.path.join(klasor(), "parcalar.db")
