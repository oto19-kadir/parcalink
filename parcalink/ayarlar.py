"""Kullanıcı ayarları ve önbellek: Windows'ta %APPDATA%\\ParcaLink, diğerlerinde ~/.parcalink.

API anahtarı sadece kullanıcının bilgisayarında bu klasörde durur; programın içinde veya depoda değildir.
"""
import json
import os
import time

ONBELLEK_GUN = 30


def klasor():
    kok = os.environ.get("APPDATA") or os.path.expanduser("~")
    yol = os.path.join(kok, "ParcaLink" if os.environ.get("APPDATA") else ".parcalink")
    os.makedirs(yol, exist_ok=True)
    return yol


def _oku(ad, varsayilan):
    try:
        with open(os.path.join(klasor(), ad), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return varsayilan


def _yaz(ad, veri):
    yol = os.path.join(klasor(), ad)
    with open(yol + ".tmp", "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=1)
    os.replace(yol + ".tmp", yol)


def api_anahtari():
    return os.environ.get("ANTHROPIC_API_KEY") or _oku("ayarlar.json", {}).get("api_anahtari", "")


def api_anahtari_kaydet(anahtar):
    a = _oku("ayarlar.json", {})
    a["api_anahtari"] = anahtar.strip()
    _yaz("ayarlar.json", a)


def onbellekten(anahtar):
    k = _oku("onbellek.json", {}).get(anahtar)
    if k and time.time() - k.get("zaman", 0) < ONBELLEK_GUN * 86400:
        return k["veri"]
    return None


def onbellege(anahtar, veri):
    o = _oku("onbellek.json", {})
    o[anahtar] = {"zaman": time.time(), "veri": veri}
    _yaz("onbellek.json", o)


def onbellek_sil(anahtar=None):
    o = _oku("onbellek.json", {})
    if anahtar is None:
        o = {}
    else:
        o.pop(anahtar, None)
    _yaz("onbellek.json", o)
