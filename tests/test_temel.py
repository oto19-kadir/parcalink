"""Çalıştırma: python -m pytest -q  (veya python tests/test_temel.py)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from parcalink import kurallar
from parcalink.arama import Arac, OemSonuc
from parcalink.birlestir import kopyala_metni, oem_satirlari
from parcalink.veri import AracListesi

LISTE = AracListesi()


def test_oem_tanima():
    for k in ["04L129766N", "04L 129 766 N", "A9064640318", "5E0820951C", "038906461"]:
        assert kurallar.oem_gibi_mi(k), k
    for m in ["Caddy motor triger", "golf 7 fren balatası", "abc"]:
        assert not kurallar.oem_gibi_mi(m), m


def test_ipucu():
    assert "Crafter" in kurallar.ipucu("2E0857186")["arac"]
    assert "EA288" in kurallar.ipucu("04L129766N")["motor_ailesi"]
    assert kurallar.ipucu("A9064640318")["marka_grubu"] == "Mercedes-Benz"
    assert "906" in kurallar.ipucu("A9064640318")["arac"]


def test_motor_kodu_hacim():
    golf = [s for s in LISTE.motor_kodu_ile("CLHA") if s.model_adi == "Golf"]
    assert golf and all(s.hacim == "1.6" for s in golf)


def test_birlestir():
    sonuc = OemSonuc(parca_adi="Emme manifoldu", motor_parcasi=True, motor_kodlari=["CLHA", "DBGA"], esdeger_kodlar=[],
                     araclar=[Arac(marka="Volkswagen", model="Golf VII", yil_bas=2013, yil_bit=2020,
                                   kaynaklar=["https://a.example", "https://b.example"]),
                              Arac(marka="Volkswagen", model="Passat B8", kaynaklar=["https://c.example"])])
    satirlar = oem_satirlari(sonuc, LISTE)
    assert satirlar
    golf = [r for r in satirlar if r["Model"].startswith("Golf") and r["Motor kodu"] == "CLHA"]
    assert golf and golf[0]["Hacim"] == "1.6" and golf[0]["Güven"] == "Doğrulandı" and golf[0]["Beygir"]
    assert any(r["Güven"] == "Motor kodundan" for r in satirlar)          # ör. Kodiaq (DBGA)
    assert any(r["Model"] == "Passat B8" and r["Güven"] == "Kontrol edin" for r in satirlar)
    metin = kopyala_metni(satirlar)
    assert metin.splitlines()[0].startswith("Marka\tModel")


def test_pencere(monkeypatch=None):
    from PySide6.QtWidgets import QApplication
    from parcalink import gui
    app = QApplication.instance() or QApplication([])
    p = gui.Pencere()
    sonuc = OemSonuc(parca_adi="Intercooler", motor_parcasi=True, motor_kodlari=["CUSB"], esdeger_kodlar=[], araclar=[])
    p.goster({"tur": "oem", "kod": "04B145749K", "ipucu": kurallar.ipucu("04B145749K"), "sonuc": sonuc,
              "satirlar": oem_satirlari(sonuc, LISTE), "adresler": ["https://x.example"], "onbellek": False})
    assert p.tablo.rowCount() > 3
    p.kopyala(False)
    assert "CUSB" in app.clipboard().text()
    p.grab().save(os.path.join(os.path.dirname(__file__), "..", "docs", "ekran.png"))


if __name__ == "__main__":
    for ad, f in list(globals().items()):
        if ad.startswith("test_"):
            f()
            print("OK", ad)
