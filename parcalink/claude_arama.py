"""Bilgisayardaki Claude Code ile internet araması (kullanıcının Claude aboneliği; ek ücret yok).

Claude Code kurulu ve giriş yapılmış olmalı. Program `claude -p` komutunu sadece internet arama ve sayfa okuma
araçlarına izin vererek çalıştırır; dosya, komut gibi başka araçlar kapalıdır.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ARACLAR = "WebSearch,WebFetch"
ZAMAN_ASIMI = 300  # saniye

OEM_SEMA = {
    "type": "object",
    "properties": {
        "parca_adi": {"type": "string"},
        "motor_parcasi": {"type": "boolean"},
        "motor_kodlari": {"type": "array", "items": {"type": "string"}},
        "araclar": {"type": "array", "items": {"type": "object", "properties": {
            "marka": {"type": "string"}, "model": {"type": "string"}, "kasa": {"type": "string"},
            "hacim": {"type": "string"}, "yil_bas": {"type": ["integer", "null"]}, "yil_bit": {"type": ["integer", "null"]},
            "motor_kodlari": {"type": "array", "items": {"type": "string"}},
            "kaynaklar": {"type": "array", "items": {"type": "string"}}},
            "required": ["marka", "model", "kaynaklar"]}},
        "esdeger_kodlar": {"type": "array", "items": {"type": "string"}},
        "notlar": {"type": "string"}},
    "required": ["parca_adi", "motor_parcasi", "motor_kodlari", "araclar", "notlar"],
}

METIN_SEMA = {
    "type": "object",
    "properties": {
        "sonuclar": {"type": "array", "items": {"type": "object", "properties": {
            "oem_kodu": {"type": "string"}, "aciklama": {"type": "string"}, "araclar": {"type": "string"},
            "motor": {"type": "string"}, "kaynaklar": {"type": "array", "items": {"type": "string"}}},
            "required": ["oem_kodu", "aciklama", "kaynaklar"]}},
        "notlar": {"type": "string"}},
    "required": ["sonuclar", "notlar"],
}

KURALLAR = """Sen bir otomotiv yedek parça uzmanısın; sonuçlar Türkiye'de bir yedek parçacıda satışta kullanılacak.
- Sadece bulduğun kaynaklarda yazanı ver. Kaynakta olmayan aracı, motor kodunu veya yılı ekleme; emin olmadığını notlara yaz.
- OEM kodunun sonundaki harf farklı parça demektir (038906461, 038906461B, 038906461C farklı). Farklı ekli kodun bilgisini
  aranan koda aktarma; onu esdeger_kodlar ve notlara yaz.
- Her araca o bilgiyi gördüğün sayfa adreslerini kaynaklar olarak ekle; mümkünse en az iki bağımsız kaynak bul.
- Motor parçasıysa motor kodlarını mutlaka ara ve yaz (CLHA, CRBC gibi), hacmi (1.6, 2.0) ekle.
- Model adlarını Türkiye'de yaygın biçimde yaz (Golf VII, Passat B8, Octavia III, Sprinter W906). Metinler Türkçe."""


class ClaudeYok(Exception):
    pass


class AramaHatasi(Exception):
    pass


def claude_yolu():
    """Claude Code'u PATH'te veya varsayılan kurulum yerinde arar."""
    for aday in [shutil.which("claude"),
                 os.path.join(os.path.expanduser("~"), ".local", "bin", "claude.exe"),
                 os.path.join(os.path.expanduser("~"), ".local", "bin", "claude")]:
        if aday and os.path.isfile(aday):
            return aday
    return None


def _calistir(istem, sema):
    yol = claude_yolu()
    if not yol:
        raise ClaudeYok("Bu bilgisayarda Claude Code bulunamadı.")
    komut = [yol, "-p", istem, "--output-format", "json", "--json-schema", json.dumps(sema),
             "--tools", ARACLAR, "--allowedTools", ARACLAR, "--permission-mode", "dontAsk",
             "--no-session-persistence"]
    bayrak = 0x08000000 if sys.platform == "win32" else 0  # Windows'ta siyah pencere açılmasın
    try:
        p = subprocess.run(komut, capture_output=True, text=True, encoding="utf-8", timeout=ZAMAN_ASIMI,
                           cwd=tempfile.gettempdir(), creationflags=bayrak)
    except subprocess.TimeoutExpired:
        raise AramaHatasi("Arama çok uzun sürdü (5 dakika). Tekrar deneyin.")
    try:
        cikti = json.loads(p.stdout)
    except ValueError:
        hata = (p.stderr or p.stdout or "").strip()[:400]
        if "login" in hata.lower() or "auth" in hata.lower():
            raise AramaHatasi("Claude Code'a giriş yapılmamış. Komut ekranında `claude` yazıp giriş yapın.")
        raise AramaHatasi("Claude Code cevap vermedi. " + hata)
    if cikti.get("is_error"):
        mesaj = str(cikti.get("result") or cikti.get("subtype") or "")
        if "limit" in mesaj.lower():
            raise AramaHatasi("Claude kullanım sınırına ulaşıldı; bir süre sonra tekrar deneyin. " + mesaj[:200])
        raise AramaHatasi("Claude araması başarısız: " + mesaj[:300])
    veri = cikti.get("structured_output")
    if veri is None:
        try:
            veri = json.loads(cikti.get("result") or "")
        except ValueError:
            raise AramaHatasi("Claude'un cevabı okunamadı. Tekrar deneyin.")
    return veri


def oem_ara(kod, ipucu):
    ek = "; ".join(f"{k}: {v}" for k, v in ipucu.items() if v and isinstance(v, str))
    istem = (f"{KURALLAR}\n\nOEM parça kodu: {kod}\nKodun biçiminden çıkan tahmin (kesin değil, kaynakla doğrula): "
             f"{ek or 'yok'}\n\nİnternette araştır: bu parça nedir, hangi araçlara uyar? Motor parçasıysa motor kodları ve hacimleri.")
    return _calistir(istem, OEM_SEMA)


def metin_ara(metin):
    istem = (f"{KURALLAR}\n\nArama: {metin}\n\nİnternette araştır ve bu araç ve parça için OEM parça kod(lar)ını bul. "
             "Motor parçasıysa hangi motor kodu ve hacim için olduğunu ayrı ayrı yaz.")
    return _calistir(istem, METIN_SEMA)
