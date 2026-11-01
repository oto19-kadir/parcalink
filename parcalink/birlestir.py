"""Kayıtlı parça / kod tahmini + araç listesi -> sonuç tablosu satırları."""
from collections import OrderedDict

SUTUNLAR = ["Marka", "Model", "Kasa", "Hacim", "Motor kodu", "Beygir", "Yakıt", "Şanzıman", "Yıllar", "Durum"]
METIN_SUTUNLARI = ["OEM kodu", "Parça adı", "Araçlar", "Motor kodları"]

KAYITLI = "Kayıtlı"
TAHMIN = "Tahmin – ETKA'dan kontrol edin"


def _yil(a, b):
    if a and b:
        return f"{a}–{b}" if a != b else str(a)
    return str(a or b or "")


def excel_satiri(s, motor_kodu=None, durum=TAHMIN):
    """veri.AracSatiri -> tablo satırı."""
    return {"Marka": s.marka, "Model": s.model.split(" (")[0], "Kasa": s.kasa, "Hacim": s.hacim,
            "Motor kodu": motor_kodu if motor_kodu is not None else ", ".join(s.motor_kodlari),
            "Beygir": s.beygir, "Yakıt": s.yakit, "Şanzıman": s.sanziman, "Yıllar": s.yillar, "Durum": durum,
            "_yil": (s.yil_bas, s.yil_bit)}


def birlestir(satirlar):
    """Aynı aracın manuel / otomatik satırlarını tek satırda toplar."""
    grup = OrderedDict()
    for r in satirlar:
        k = (r["Marka"], r["Model"], r["Kasa"], r["Motor kodu"], r["Beygir"], r["Yıllar"])
        if k in grup:
            if r["Şanzıman"] and r["Şanzıman"] not in grup[k]["Şanzıman"]:
                grup[k]["Şanzıman"] += ", " + r["Şanzıman"]
        else:
            grup[k] = dict(r)
    return list(grup.values())


def kayitli_satirlar(parca):
    return [{"Marka": a["marka"], "Model": a["model"], "Kasa": a["kasa"], "Hacim": a["hacim"],
             "Motor kodu": a["motor_kodu"], "Beygir": a["beygir"], "Yakıt": a["yakit"], "Şanzıman": a["sanziman"],
             "Yıllar": _yil(a["yil_bas"], a["yil_bit"]), "Durum": KAYITLI} for a in parca["araclar"]]


def tahmin_satirlari(ipucu, liste):
    """Kodun başından tahmin edilen aracın Excel'deki tüm motorları."""
    if ipucu.get("excel"):
        marka, model, a, b = ipucu["excel"]
        bulunan = [s for s in liste.model_ile(marka, model, a, b)
                   if not s.yil_bit or (min(b, s.yil_bit) - max(a, s.yil_bas) + 1) * 2 >= (s.yil_bit - s.yil_bas + 1)]
    elif ipucu.get("kasa"):
        bulunan = [s for s in liste.satirlar if s.marka == "Mercedes-Benz" and ipucu["kasa"] in s.kasa]
    else:
        bulunan = []
    return birlestir([excel_satiri(s) for s in bulunan])


def satirdan_arac(r):
    """Tablo satırı -> kayıt (depo) alanları."""
    yil = r.get("_yil") or (None, None)
    if yil == (None, None) and r.get("Yıllar"):
        p = str(r["Yıllar"]).replace("–", "-").split("-")
        yil = (int(p[0]), int(p[-1])) if p[0].isdigit() else (None, None)
    return {"marka": r["Marka"], "model": r["Model"], "kasa": r["Kasa"], "hacim": r["Hacim"],
            "motor_kodu": r["Motor kodu"], "beygir": r["Beygir"], "yakit": r["Yakıt"], "sanziman": r["Şanzıman"],
            "yil_bas": yil[0], "yil_bit": yil[1]}


def kopyala_metni(satirlar, sutunlar=SUTUNLAR):
    """Excel'e / WhatsApp'a yapıştırılabilir (sekme ile ayrılmış) metin."""
    out = ["\t".join(sutunlar)]
    out += ["\t".join(str(r.get(s, "")) for s in sutunlar) for r in satirlar]
    return "\n".join(out)
