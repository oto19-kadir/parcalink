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


CLAUDE_COK = "İnternet – 2+ kaynak"
CLAUDE_TEK = "İnternet – tek kaynak, kontrol edin"
MOTORDAN = "Motor kodundan – kontrol edin"


def claude_satirlari(veri, liste):
    """Claude Code cevabı (dict) + araç listesi -> tablo satırları. Motor kodu bulunursa Excel'den tamamlanır."""
    araclar = veri.get("araclar") or []
    kodlar = []
    for k in list(veri.get("motor_kodlari") or []) + [k for a in araclar for k in (a.get("motor_kodlari") or [])]:
        k = (k or "").strip().upper()
        if k and k not in kodlar:
            kodlar.append(k)

    def ayni(a, s):
        ilk = (a.get("model") or "").split()
        if not ilk or s.model_adi.lower() != ilk[0].lower():
            return False
        ab, ae = a.get("yil_bas") or 0, a.get("yil_bit") or 9999
        return not s.yil_bit or (s.yil_bas <= ae and ab <= s.yil_bit)

    satirlar, kullanilan = [], set()
    for kod in kodlar:
        for s in liste.motor_kodu_ile(kod):
            eslesen = [i for i, a in enumerate(araclar) if ayni(a, s)]
            if eslesen:
                kullanilan.update(eslesen)
                kaynak = max(len(araclar[i].get("kaynaklar") or []) for i in eslesen)
                durum = CLAUDE_COK if kaynak >= 2 else CLAUDE_TEK
            else:
                durum = MOTORDAN
            satirlar.append(excel_satiri(s, kod, durum))
    satirlar = birlestir(satirlar)

    for i, a in enumerate(araclar):  # listede karşılığı olmayan veya motor kodu olmayan araçlar
        if i in kullanilan:
            continue
        satirlar.append({"Marka": a.get("marka", ""), "Model": a.get("model", ""), "Kasa": a.get("kasa", ""),
                         "Hacim": a.get("hacim", ""), "Motor kodu": ", ".join(a.get("motor_kodlari") or []),
                         "Beygir": "", "Yakıt": "", "Şanzıman": "", "Yıllar": _yil(a.get("yil_bas"), a.get("yil_bit")),
                         "Durum": CLAUDE_COK if len(a.get("kaynaklar") or []) >= 2 else CLAUDE_TEK,
                         "_yil": (a.get("yil_bas"), a.get("yil_bit"))})
    sira = {CLAUDE_COK: 0, CLAUDE_TEK: 1, MOTORDAN: 2}
    satirlar.sort(key=lambda r: (sira.get(r["Durum"], 9), r["Marka"], r["Model"], r["Yıllar"]))
    return satirlar


def kaynak_adresleri(veri):
    out = []
    for a in veri.get("araclar") or veri.get("sonuclar") or []:
        for u in a.get("kaynaklar") or []:
            if u not in out:
                out.append(u)
    return out
