"""Araç listesi (Arac_Listesi.xlsx): motor kodu -> araç, hacim, beygir, yakıt, şanzıman, yıllar."""
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field

from openpyxl import load_workbook

MARKALAR = ["Mercedes-Benz", "Volkswagen", "Skoda", "Seat", "Audi", "Porsche", "Smart", "Cupra"]


def kaynak_yolu(ad):
    """Exe içinde (PyInstaller) ve geliştirmede dosya yolunu bulur."""
    kok = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(kok, ad)


@dataclass
class AracSatiri:
    marka: str
    model: str          # marka hariç ad, ör. "Golf VII 1.6 TDI (5G)"
    model_adi: str      # ilk kelime, ör. "Golf"
    kasa: str           # parantez içi, ör. "5G"
    hacim: str          # ör. "1.6"
    motor_kodlari: list
    beygir: str
    yakit: str
    sanziman: str
    yil_bas: int
    yil_bit: int

    @property
    def yillar(self):
        return f"{self.yil_bas}–{self.yil_bit}" if self.yil_bas != self.yil_bit else str(self.yil_bas)


def kod_normal(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def _kodlar(s):
    return [k for k in re.split(r"[\s,/()]+", (s or "").upper())
            if re.fullmatch(r"[A-Z0-9.]{2,9}", k) and k not in ("EURO", "LPG", "BIFUEL")]


class AracListesi:
    def __init__(self, yol=None):
        self.satirlar = []
        self.motor = defaultdict(list)     # motor kodu -> [AracSatiri]
        yol = yol or kaynak_yolu(os.path.join("veri", "Arac_Listesi.xlsx"))
        ws = load_workbook(yol, read_only=True)["Tümü"]
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i == 0 or not r or not r[0]:
                continue
            ad, kod, hp, yakit, sz, yil = (list(r) + [None] * 6)[:6]
            marka = next((m for m in MARKALAR if ad.startswith(m + " ")), ad.split()[0])
            model = ad[len(marka):].strip()
            kasa = re.findall(r"\(([^)]*)\)", model)
            yy = [int(y) for y in re.findall(r"\d{4}", str(yil or ""))]
            hacim = re.search(r"(?<!\d)(\d[.,]\d)(?!\d)", model)
            s = AracSatiri(
                marka=marka, model=model, model_adi=model.split()[0] if model else "",
                kasa=kasa[-1] if kasa else "", hacim=hacim.group(1).replace(",", ".") if hacim else "",
                motor_kodlari=_kodlar(kod), beygir=str(hp or "").replace(" beygir", ""),
                yakit=yakit or "", sanziman=(sz or "").replace(" Şanzıman", ""),
                yil_bas=min(yy) if yy else 0, yil_bit=max(yy) if yy else 0)
            self.satirlar.append(s)
            for k in s.motor_kodlari:
                self.motor[kod_normal(k)].append(s)

    def motor_kodu_ile(self, kod):
        return self.motor.get(kod_normal(kod), [])

    def model_ile(self, marka, model_adi, yil_bas=0, yil_bit=9999):
        """Marka + model adı (ve yıl aralığı) uyan satırlar."""
        m, ma = (marka or "").lower(), (model_adi or "").lower()
        out = []
        for s in self.satirlar:
            if m and m not in s.marka.lower():
                continue
            if ma and not s.model.lower().startswith(ma):
                continue
            if s.yil_bit and (s.yil_bit < yil_bas or s.yil_bas > yil_bit):
                continue
            out.append(s)
        return out
