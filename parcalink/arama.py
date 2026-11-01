"""Claude + internet araması: OEM kodu -> uyan araçlar, ya da "Caddy motor triger" -> OEM kodları."""
import json
import re
from typing import List, Optional

import anthropic
from pydantic import BaseModel

MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
ARAMA_ARACI = {"type": "web_search_20260209", "name": "web_search", "max_uses": 8}


class Arac(BaseModel):
    marka: str
    model: str
    kasa: str = ""
    yil_bas: Optional[int] = None
    yil_bit: Optional[int] = None
    hacim: str = ""
    motor_kodlari: List[str] = []
    kaynaklar: List[str] = []


class OemSonuc(BaseModel):
    parca_adi: str
    motor_parcasi: bool
    araclar: List[Arac]
    motor_kodlari: List[str]
    esdeger_kodlar: List[str]
    notlar: str = ""


class KodBulgusu(BaseModel):
    oem_kodu: str
    aciklama: str
    araclar: str = ""
    motor: str = ""
    kaynaklar: List[str] = []


class MetinSonuc(BaseModel):
    arac: str
    parca: str
    sonuclar: List[KodBulgusu]
    notlar: str = ""


SISTEM = """Sen bir otomotiv yedek parça uzmanısın. Kullanıcı Türkiye'de bir yedek parçacı; sonuçlarını
müşteriye parça satarken kullanacak, bu yüzden yanlış bilgi zarara yol açar.

Görevin: web_search aracıyla araştırıp sadece bulduğun kaynaklarda yazanı raporlamak.
- Kaynakta yazmayan aracı, motor kodunu veya yılı ekleme. Emin olmadığın şeyi "notlar"a yaz.
- OEM kodunun sonundaki harf(ler) farklı parça demektir (038906461, 038906461B, 038906461C farklı dönemler).
  Aranan koddan farklı ekli bir kodun bilgisini aranan koda aktarma; onu "esdeger_kodlar"a ve "notlar"a yaz.
- Her araç satırına o bilgiyi gördüğün sayfaların adreslerini "kaynaklar" olarak koy.
- Mümkünse en az iki bağımsız kaynak bul (satıcı katalogları, üretici parça siteleri, parça eşleştirme siteleri).
- Motor parçasıysa motor kodlarını mutlaka ara (ör. CLHA, CRBC); hacmi (1.6, 2.0) yaz.
- Model adlarını yaygın Türkçe kullanımla yaz (Golf VII, Passat B8, Octavia III, Sprinter W906).
- Metinleri Türkçe yaz.

Araştırma bitince cevabını SADECE tek bir JSON nesnesi olarak ver, başka metin yazma."""

OEM_SABLON = """{"parca_adi": "...", "motor_parcasi": true/false,
 "araclar": [{"marka": "...", "model": "...", "kasa": "...", "yil_bas": 2013, "yil_bit": 2020,
              "hacim": "1.6", "motor_kodlari": ["CLHA"], "kaynaklar": ["https://..."]}],
 "motor_kodlari": ["..."], "esdeger_kodlar": ["..."], "notlar": "..."}"""

METIN_SABLON = """{"arac": "...", "parca": "...",
 "sonuclar": [{"oem_kodu": "...", "aciklama": "...", "araclar": "...", "motor": "...", "kaynaklar": ["https://..."]}],
 "notlar": "..."}"""


class AramaHatasi(Exception):
    pass


def _istemci(api_anahtari):
    if not api_anahtari:
        raise AramaHatasi("API anahtarı girilmemiş. Ayarlar'dan Anthropic API anahtarınızı girin.")
    return anthropic.Anthropic(api_key=api_anahtari, timeout=300.0, max_retries=2)


def _calistir(istemci, mesaj):
    """Arama turunu yürütür; pause_turn olursa kaldığı yerden devam ettirir. (cevap metni, kaynak adresleri)"""
    mesajlar = [{"role": "user", "content": mesaj}]
    adresler = []
    for _ in range(6):
        try:
            yanit = istemci.beta.messages.create(
                model=MODEL, max_tokens=16000, system=SISTEM, messages=mesajlar, tools=[ARAMA_ARACI],
                output_config={"effort": "medium"}, betas=[FALLBACK_BETA], fallbacks="default")
        except anthropic.AuthenticationError:
            raise AramaHatasi("API anahtarı geçersiz. Ayarlar'dan kontrol edin.")
        except anthropic.RateLimitError:
            raise AramaHatasi("Çok sık arama yapıldı, biraz bekleyip tekrar deneyin.")
        except anthropic.APIConnectionError:
            raise AramaHatasi("İnternet bağlantısı yok veya servis erişilemiyor.")
        except anthropic.APIStatusError as e:
            raise AramaHatasi(f"Servis hatası ({e.status_code}). Biraz sonra tekrar deneyin.")
        for b in yanit.content:
            if b.type == "web_search_tool_result" and isinstance(b.content, list):
                adresler += [r.url for r in b.content if getattr(r, "url", None)]
        if yanit.stop_reason == "refusal":
            raise AramaHatasi("Bu arama yapılamadı (servis isteği reddetti).")
        if yanit.stop_reason == "pause_turn":
            mesajlar.append({"role": "assistant", "content": yanit.content})
            continue
        metin = "".join(b.text for b in yanit.content if b.type == "text")
        return metin, list(dict.fromkeys(adresler))
    raise AramaHatasi("Arama çok uzun sürdü, tekrar deneyin.")


def _json_al(istemci, metin, sema):
    """Cevaptaki JSON'u çıkarır; bozuksa ikinci, araçsız bir çağrıyla şemaya dönüştürür."""
    m = re.search(r"\{.*\}", metin, re.S)
    if m:
        try:
            return sema.model_validate(json.loads(m.group(0)))
        except Exception:
            pass
    yanit = istemci.messages.parse(
        model=MODEL, max_tokens=16000, output_config={"effort": "low"}, output_format=sema,
        messages=[{"role": "user", "content": "Aşağıdaki araştırma notunu verilen şemaya dönüştür. "
                   "Notta olmayan bilgi ekleme.\n\n" + metin}])
    if yanit.stop_reason == "refusal" or yanit.parsed_output is None:
        raise AramaHatasi("Sonuç okunamadı, tekrar deneyin.")
    return yanit.parsed_output


def oem_ara(api_anahtari, kod, ipucu):
    istemci = _istemci(api_anahtari)
    ek = "; ".join(f"{k}: {v}" for k, v in ipucu.items() if v)
    mesaj = (f"OEM parça kodu: {kod}\n"
             f"Kodun biçiminden çıkan ipucu (kesin değil, kaynakla doğrula): {ek or 'yok'}\n\n"
             "Bu parça nedir ve hangi araçlara uyar? Motor parçasıysa motor kodları ve hacimleriyle.\n"
             f"Cevap biçimi:\n{OEM_SABLON}")
    metin, adresler = _calistir(istemci, mesaj)
    return _json_al(istemci, metin, OemSonuc), adresler


def metin_ara(api_anahtari, metin_sorgu):
    istemci = _istemci(api_anahtari)
    mesaj = (f"Arama: {metin_sorgu}\n\nBu araç ve parça için OEM parça kod(lar)ını bul. Motor parçasıysa "
             "hangi motor kodu ve hacim için olduğunu ayrı ayrı yaz.\n"
             f"Cevap biçimi:\n{METIN_SABLON}")
    metin, adresler = _calistir(istemci, mesaj)
    return _json_al(istemci, metin, MetinSonuc), adresler
