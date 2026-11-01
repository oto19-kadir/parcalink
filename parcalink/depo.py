"""Kullanıcının kendi parça kayıtları (SQLite): OEM kodu -> uyan araçlar. Excel'e dışa / içe aktarılır."""
import os
import re
import sqlite3
from datetime import date

from openpyxl import Workbook, load_workbook

from .kurallar import kod_normal

ARAC_ALANLARI = ["marka", "model", "kasa", "hacim", "motor_kodu", "beygir", "yakit", "sanziman", "yil_bas", "yil_bit"]
EXCEL_BASLIK = ["OEM kodu", "Parça adı", "Marka", "Model", "Kasa", "Hacim", "Motor kodu", "Beygir", "Yakıt",
                "Şanzıman", "Yıllar", "Not"]


class Depo:
    def __init__(self, yol):
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        self.db = sqlite3.connect(yol)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS parca(kod TEXT PRIMARY KEY, ad TEXT, notlar TEXT, tarih TEXT);
            CREATE TABLE IF NOT EXISTS uyum(kod TEXT REFERENCES parca(kod) ON DELETE CASCADE,
                marka TEXT, model TEXT, kasa TEXT, hacim TEXT, motor_kodu TEXT, beygir TEXT, yakit TEXT,
                sanziman TEXT, yil_bas INTEGER, yil_bit INTEGER);
            CREATE INDEX IF NOT EXISTS uyum_kod ON uyum(kod);""")

    # ---- okuma ----
    def getir(self, kod):
        k = kod_normal(kod)
        p = self.db.execute("SELECT kod, ad, notlar, tarih FROM parca WHERE kod=?", (k,)).fetchone()
        if not p:
            return None
        araclar = [dict(zip(ARAC_ALANLARI, r)) for r in self.db.execute(
            f"SELECT {', '.join(ARAC_ALANLARI)} FROM uyum WHERE kod=? ORDER BY marka, model, yil_bas", (k,))]
        return {"kod": p[0], "ad": p[1] or "", "notlar": p[2] or "", "tarih": p[3] or "", "araclar": araclar}

    def benzer(self, kod):
        """Aynı ana kod, farklı ek (038906461 / 038906461B)."""
        k = kod_normal(kod)
        ana = k[:9] if re.fullmatch(r"[0-9A-Z]{3}\d{6}[A-Z]{0,3}", k) else k  # VW: 9 hane ana kod + ek harf
        return [r[0] for r in self.db.execute("SELECT kod FROM parca WHERE kod LIKE ? AND kod<>? ORDER BY kod",
                                              (ana + "%", k))]

    def metinle_ara(self, metin):
        """Tüm kelimeler parça adında veya uyan araçlarda geçen kayıtlar."""
        kelimeler = [w for w in metin.lower().split() if w]
        out = []
        for kod, ad in self.db.execute("SELECT kod, ad FROM parca ORDER BY kod"):
            araclar = self.db.execute("SELECT marka, model, kasa, motor_kodu FROM uyum WHERE kod=?", (kod,)).fetchall()
            havuz = " ".join([kod.lower(), (ad or "").lower()] + [" ".join(map(str, a)).lower() for a in araclar])
            if all(_turkce(w) in _turkce(havuz) for w in kelimeler):
                modeller = sorted({f"{a[0]} {a[1].split(' (')[0]}" for a in araclar})
                motorlar = sorted({a[3] for a in araclar if a[3]})
                out.append({"OEM kodu": kod, "Parça adı": ad or "", "Araçlar": ", ".join(modeller),
                            "Motor kodları": ", ".join(motorlar)})
        return out

    def sayi(self):
        return self.db.execute("SELECT COUNT(*) FROM parca").fetchone()[0]

    # ---- yazma ----
    def kaydet(self, kod, ad, araclar, notlar=""):
        k = kod_normal(kod)
        with self.db:
            self.db.execute("INSERT INTO parca(kod, ad, notlar, tarih) VALUES(?,?,?,?) ON CONFLICT(kod) DO UPDATE "
                            "SET ad=excluded.ad, notlar=excluded.notlar, tarih=excluded.tarih",
                            (k, ad, notlar, date.today().isoformat()))
            self.db.execute("DELETE FROM uyum WHERE kod=?", (k,))
            self.db.executemany(f"INSERT INTO uyum(kod, {', '.join(ARAC_ALANLARI)}) VALUES(?{',?' * len(ARAC_ALANLARI)})",
                                [(k, *[a.get(f, "") for f in ARAC_ALANLARI]) for a in araclar])

    def sil(self, kod):
        with self.db:
            self.db.execute("DELETE FROM parca WHERE kod=?", (kod_normal(kod),))

    # ---- Excel ----
    def disa_aktar(self, yol):
        wb = Workbook()
        ws = wb.active
        ws.title = "Parcalar"
        ws.append(EXCEL_BASLIK)
        for (kod,) in self.db.execute("SELECT kod FROM parca ORDER BY kod").fetchall():
            p = self.getir(kod)
            for a in p["araclar"] or [{}]:
                yil = f"{a.get('yil_bas') or ''}-{a.get('yil_bit') or ''}".strip("-")
                ws.append([p["kod"], p["ad"], a.get("marka", ""), a.get("model", ""), a.get("kasa", ""),
                           a.get("hacim", ""), a.get("motor_kodu", ""), a.get("beygir", ""), a.get("yakit", ""),
                           a.get("sanziman", ""), yil, p["notlar"]])
        wb.save(yol)

    def ice_aktar(self, yol):
        """Aynı kodlar dosyadakiyle değiştirilir. Dönen: aktarılan parça sayısı."""
        ws = load_workbook(yol, read_only=True).worksheets[0]
        parcalar = {}
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i == 0 or not r or not r[0]:
                continue
            r = list(r) + [None] * 12
            kod = kod_normal(str(r[0]))
            p = parcalar.setdefault(kod, {"ad": r[1] or "", "notlar": r[11] or "", "araclar": []})
            if r[2] or r[3]:
                yy = [int(y) for y in re.findall(r"\d{4}", str(r[10] or ""))]
                p["araclar"].append({"marka": r[2] or "", "model": r[3] or "", "kasa": r[4] or "",
                                     "hacim": str(r[5] or ""), "motor_kodu": r[6] or "", "beygir": str(r[7] or ""),
                                     "yakit": r[8] or "", "sanziman": r[9] or "",
                                     "yil_bas": min(yy) if yy else None, "yil_bit": max(yy) if yy else None})
        for kod, p in parcalar.items():
            self.kaydet(kod, p["ad"], p["araclar"], p["notlar"])
        return len(parcalar)


def _turkce(s):
    return s.replace("ı", "i").replace("İ", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u") \
        .replace("ö", "o").replace("ç", "c")
