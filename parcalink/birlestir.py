"""Yapay zekâ sonucu + araç listesi -> sonuç tablosu satırları."""
from collections import OrderedDict

from .veri import kod_normal

SUTUNLAR = ["Marka", "Model", "Kasa", "Hacim", "Motor kodu", "Beygir", "Yakıt", "Şanzıman", "Yıllar", "Güven", "Kaynak"]

GUVEN_DOGRU = "Doğrulandı"        # en az 2 kaynak
GUVEN_KAYNAK = "Kaynakta var"     # 1 kaynak + araç listesiyle uyumlu
GUVEN_MOTOR = "Motor kodundan"    # araç sadece motor kodu eşleşmesinden geldi
GUVEN_KONTROL = "Kontrol edin"    # tek kaynak / kaynaksız


def _yil(a, b):
    if a and b:
        return f"{a}–{b}" if a != b else str(a)
    return str(a or b or "")


def _guven(kaynak_sayisi):
    return GUVEN_DOGRU if kaynak_sayisi >= 2 else GUVEN_KONTROL


def _ayni_model(ai_model, satir):
    ilk = (ai_model or "").split()
    return bool(ilk) and satir.model_adi.lower() == ilk[0].lower()


def oem_satirlari(sonuc, liste):
    satirlar = []
    kodlar = list(OrderedDict.fromkeys(
        kod_normal(k) for k in list(sonuc.motor_kodlari) + [k for a in sonuc.araclar for k in a.motor_kodlari] if k))
    kullanilan_ai = set()

    if kodlar:
        grup = OrderedDict()
        for kod in kodlar:
            for s in liste.motor_kodu_ile(kod):
                ai = next((a for a in sonuc.araclar if _ayni_model(a.model, s) and
                           (not a.yil_bas or not s.yil_bit or (s.yil_bas <= (a.yil_bit or 9999) and a.yil_bas <= s.yil_bit))),
                          None)
                if ai is not None:
                    kullanilan_ai.add(id(ai))
                    guven = GUVEN_DOGRU if len(ai.kaynaklar) >= 2 else GUVEN_KAYNAK
                    kaynak = ai.kaynaklar[0] if ai.kaynaklar else ""
                else:
                    guven, kaynak = GUVEN_MOTOR, ""
                model = s.model.split(" (")[0]
                anahtar = (s.marka, model, s.kasa, kod, s.beygir)
                if anahtar in grup:  # aynı aracın manuel / otomatik satırlarını birleştir
                    g = grup[anahtar]
                    if s.sanziman and s.sanziman not in g["Şanzıman"]:
                        g["Şanzıman"] += ", " + s.sanziman
                    continue
                grup[anahtar] = {"Marka": s.marka, "Model": model, "Kasa": s.kasa, "Hacim": s.hacim, "Motor kodu": kod,
                                 "Beygir": s.beygir, "Yakıt": s.yakit, "Şanzıman": s.sanziman,
                                 "Yıllar": s.yillar, "Güven": guven, "Kaynak": kaynak}
        satirlar += grup.values()

    for a in sonuc.araclar:  # listede karşılığı bulunmayan (veya motor kodu olmayan) araçlar
        if id(a) in kullanilan_ai:
            continue
        satirlar.append({"Marka": a.marka, "Model": a.model, "Kasa": a.kasa, "Hacim": a.hacim,
                         "Motor kodu": ", ".join(a.motor_kodlari), "Beygir": "", "Yakıt": "", "Şanzıman": "",
                         "Yıllar": _yil(a.yil_bas, a.yil_bit), "Güven": _guven(len(a.kaynaklar)),
                         "Kaynak": a.kaynaklar[0] if a.kaynaklar else ""})

    sira = {GUVEN_DOGRU: 0, GUVEN_KAYNAK: 1, GUVEN_MOTOR: 2, GUVEN_KONTROL: 3}
    satirlar.sort(key=lambda r: (sira.get(r["Güven"], 9), r["Marka"], r["Model"], r["Yıllar"]))
    return satirlar


def kopyala_metni(satirlar, sutunlar=SUTUNLAR):
    """Excel'e yapıştırılabilir (sekme ile ayrılmış) metin."""
    satir = ["\t".join(sutunlar)]
    satir += ["\t".join(str(r.get(s, "")) for s in sutunlar) for r in satirlar]
    return "\n".join(satir)
