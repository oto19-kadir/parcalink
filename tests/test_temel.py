"""Çalıştırma: python -m pytest -q tests"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from parcalink import kurallar
from parcalink.birlestir import kayitli_satirlar, kopyala_metni, satirdan_arac, tahmin_satirlari
from parcalink.depo import Depo
from parcalink.veri import AracListesi

LISTE = AracListesi()


def _depo():
    return Depo(os.path.join(tempfile.mkdtemp(), "t.db"))


def test_oem_tanima():
    for k in ["04L129766N", "04L 129 766 N", "A9064640318", "5E0820951C", "038906461"]:
        assert kurallar.oem_gibi_mi(k), k
    for m in ["Caddy motor triger", "golf 7 fren balatası", "abc"]:
        assert not kurallar.oem_gibi_mi(m), m


def test_tahmin():
    r = tahmin_satirlari(kurallar.ipucu("2E0857186"), LISTE)
    assert r and all(x["Model"].startswith("Crafter") for x in r)
    r = tahmin_satirlari(kurallar.ipucu("5E0820951C"), LISTE)
    assert r and all("Octavia" in x["Model"] for x in r)
    r = tahmin_satirlari(kurallar.ipucu("A9064640318"), LISTE)
    assert r and all("906" in x["Kasa"] for x in r)
    assert "EA288" in kurallar.ipucu("04L129766N")["motor_ailesi"]


def test_kayit_ve_arama():
    d = _depo()
    araclar = [satirdan_arac(dict(r, Durum="")) for r in tahmin_satirlari(kurallar.ipucu("2E0857186"), LISTE)]
    d.kaydet("2E0 857 186", "Kapak (trim)", araclar, "deneme")
    p = d.getir("2E0857186")
    assert p and p["ad"] == "Kapak (trim)" and len(p["araclar"]) == len(araclar)
    assert kayitli_satirlar(p)[0]["Durum"] == "Kayıtlı"
    assert d.metinle_ara("crafter kapak") and not d.metinle_ara("golf kapak")
    d.kaydet("038906461B", "MAF", araclar[:1])
    assert d.benzer("038906461") == ["038906461B"]


def test_excel_aktarim():
    d = _depo()
    golf = [s for s in LISTE.motor_kodu_ile("CLHA") if s.model_adi == "Golf"]
    from parcalink.birlestir import excel_satiri
    d.kaydet("04L129766N", "Emme manifoldu", [satirdan_arac(excel_satiri(s, "CLHA")) for s in golf])
    yol = os.path.join(tempfile.mkdtemp(), "k.xlsx")
    d.disa_aktar(yol)
    d2 = _depo()
    assert d2.ice_aktar(yol) == 1
    assert len(d2.getir("04L129766N")["araclar"]) == len(golf)
    assert d2.getir("04L129766N")["araclar"][0]["hacim"] == "1.6"


def test_pencere():
    from PySide6.QtWidgets import QApplication
    from parcalink import gui
    app = QApplication.instance() or QApplication([])
    d = _depo()
    p = gui.Pencere(depo=d)
    p.kutu.setText("04B145749K")
    p.ara()
    assert p.tablo.rowCount() == 0 or "kayıtlı değil" in p.bilgi.text()
    # kayıt penceresi: motor kodundan getir ve kaydet
    k = gui.KayitPenceresi(p, d, p.liste, "04B145749K")
    k.ad.setText("Intercooler")
    k.motor.setText("CUSA, CUSB, CUTA")
    k.motordan()
    assert k.tablo.rowCount() >= 6
    k.kaydet()
    p.kod_goster("04B145749K")
    assert p.tablo.rowCount() >= 6 and "kayıtlı" in p.bilgi.text()
    p.kopyala(False)
    assert "CUSB" in app.clipboard().text()
    p.grab().save(os.path.join(os.path.dirname(__file__), "..", "docs", "ekran.png"))
    p.kutu.setText("2E0857186")
    p.ara()
    k.grab().save(os.path.join(os.path.dirname(__file__), "..", "docs", "ekran-kayit.png"))
    p.grab().save(os.path.join(os.path.dirname(__file__), "..", "docs", "ekran-tahmin.png"))


if __name__ == "__main__":
    for ad, f in list(globals().items()):
        if ad.startswith("test_"):
            f()
            print("OK", ad)
