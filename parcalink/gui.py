"""ParçaLink masaüstü penceresi (PySide6)."""
import html
import sys

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QAction, QColor, QGuiApplication
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView,
                               QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSplitter, QTableWidget,
                               QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget)

from . import ayarlar, arama, kurallar
from .birlestir import SUTUNLAR, kopyala_metni, oem_satirlari
from .veri import AracListesi

SURUM = "0.1"
METIN_SUTUNLARI = ["OEM kodu", "Açıklama", "Araçlar", "Motor", "Kaynak"]
RENK = {"Doğrulandı": "#e5f4e4", "Kaynakta var": "#e7f1fb", "Motor kodundan": "#f9eeda", "Kontrol edin": "#fbebeb"}


class Isci(QObject):
    bitti = Signal(dict)
    hata = Signal(str)

    def __init__(self, sorgu, liste, yenile=False):
        super().__init__()
        self.sorgu, self.liste, self.yenile = sorgu, liste, yenile

    def calis(self):
        try:
            self.bitti.emit(ara(self.sorgu, self.liste, self.yenile))
        except arama.AramaHatasi as e:
            self.hata.emit(str(e))
        except Exception as e:  # beklenmeyen hata programı kapatmasın
            self.hata.emit(f"Beklenmeyen hata: {e}")


def ara(sorgu, liste, yenile=False):
    """Arayüzden bağımsız arama: {'tur': 'oem'|'metin', ...}."""
    anahtar_api = ayarlar.api_anahtari()
    if kurallar.oem_gibi_mi(sorgu):
        kod = kurallar.kod_normal(sorgu)
        ok = "oem:" + kod
        veri = None if yenile else ayarlar.onbellekten(ok)
        ipucu = kurallar.ipucu(kod)
        if veri is None:
            sonuc, adresler = arama.oem_ara(anahtar_api, kod, ipucu)
            veri = {"sonuc": sonuc.model_dump(), "adresler": adresler}
            ayarlar.onbellege(ok, veri)
            onbellek = False
        else:
            onbellek = True
        sonuc = arama.OemSonuc.model_validate(veri["sonuc"])
        return {"tur": "oem", "kod": kod, "ipucu": ipucu, "sonuc": sonuc, "satirlar": oem_satirlari(sonuc, liste),
                "adresler": veri["adresler"], "onbellek": onbellek}
    ok = "metin:" + " ".join(sorgu.lower().split())
    veri = None if yenile else ayarlar.onbellekten(ok)
    onbellek = veri is not None
    if veri is None:
        sonuc, adresler = arama.metin_ara(anahtar_api, sorgu)
        veri = {"sonuc": sonuc.model_dump(), "adresler": adresler}
        ayarlar.onbellege(ok, veri)
    sonuc = arama.MetinSonuc.model_validate(veri["sonuc"])
    satirlar = [{"OEM kodu": b.oem_kodu, "Açıklama": b.aciklama, "Araçlar": b.araclar, "Motor": b.motor,
                 "Kaynak": b.kaynaklar[0] if b.kaynaklar else ""} for b in sonuc.sonuclar]
    return {"tur": "metin", "sonuc": sonuc, "satirlar": satirlar, "adresler": veri["adresler"], "onbellek": onbellek}


class AyarPenceresi(QDialog):
    def __init__(self, ust):
        super().__init__(ust)
        self.setWindowTitle("Ayarlar")
        y = QVBoxLayout(self)
        y.addWidget(QLabel("Anthropic API anahtarı (sadece bu bilgisayarda saklanır):"))
        self.anahtar = QLineEdit(ayarlar.api_anahtari())
        self.anahtar.setEchoMode(QLineEdit.Password)
        self.anahtar.setMinimumWidth(420)
        y.addWidget(self.anahtar)
        sil = QPushButton("Kayıtlı aramaları (önbelleği) temizle")
        sil.clicked.connect(lambda: (ayarlar.onbellek_sil(), QMessageBox.information(self, "ParçaLink", "Önbellek temizlendi.")))
        y.addWidget(sil)
        d = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        d.accepted.connect(self.kaydet)
        d.rejected.connect(self.reject)
        y.addWidget(d)

    def kaydet(self):
        ayarlar.api_anahtari_kaydet(self.anahtar.text())
        self.accept()


class Pencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ParçaLink {SURUM}")
        self.resize(1250, 760)
        self.liste = AracListesi()
        self.son = None
        self.thread = None

        orta = QWidget()
        y = QVBoxLayout(orta)
        ust = QHBoxLayout()
        self.kutu = QLineEdit()
        self.kutu.setPlaceholderText("OEM kodu yazın (ör. 04L129766N) ya da araç ve parça (ör. Caddy motor triger)")
        self.kutu.setMinimumHeight(38)
        self.kutu.returnPressed.connect(lambda: self.baslat(False))
        self.ara_dugme = QPushButton("Ara")
        self.ara_dugme.setMinimumHeight(38)
        self.ara_dugme.clicked.connect(lambda: self.baslat(False))
        self.yenile_dugme = QPushButton("İnternetten yenile")
        self.yenile_dugme.setToolTip("Kayıtlı sonucu kullanmadan yeniden ara")
        self.yenile_dugme.clicked.connect(lambda: self.baslat(True))
        ayar = QPushButton("Ayarlar")
        ayar.clicked.connect(lambda: AyarPenceresi(self).exec())
        for w in (self.kutu, self.ara_dugme, self.yenile_dugme, ayar):
            ust.addWidget(w)
        ust.setStretch(0, 1)
        y.addLayout(ust)

        self.bilgi = QLabel("Bir OEM kodu veya araç ve parça adı yazıp Ara'ya basın.")
        self.bilgi.setWordWrap(True)
        self.bilgi.setTextInteractionFlags(Qt.TextSelectableByMouse)
        y.addWidget(self.bilgi)

        bol = QSplitter(Qt.Vertical)
        self.tablo = QTableWidget(0, len(SUTUNLAR))
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setSortingEnabled(True)
        self.tablo.cellDoubleClicked.connect(self.cift_tik)
        bol.addWidget(self.tablo)
        self.kaynaklar = QTextBrowser()
        self.kaynaklar.setOpenExternalLinks(True)
        bol.addWidget(self.kaynaklar)
        bol.setSizes([520, 160])
        y.addWidget(bol)

        alt = QHBoxLayout()
        k1 = QPushButton("Tümünü kopyala")
        k1.clicked.connect(lambda: self.kopyala(False))
        k2 = QPushButton("Seçilileri kopyala")
        k2.clicked.connect(lambda: self.kopyala(True))
        self.aciklama = QLabel("Renkler: yeşil = en az 2 kaynakta doğrulandı, mavi = kaynakta var, "
                               "sarı = sadece motor kodundan, kırmızı = kontrol edin. Kesin uyum için ETKA ile kontrol edin.")
        self.aciklama.setWordWrap(True)
        alt.addWidget(k1)
        alt.addWidget(k2)
        alt.addWidget(self.aciklama, 1)
        y.addLayout(alt)
        self.setCentralWidget(orta)
        kop = QAction("Kopyala", self)
        kop.setShortcut("Ctrl+C")
        kop.triggered.connect(lambda: self.kopyala(True))
        self.addAction(kop)
        self.statusBar().showMessage(f"Araç listesi yüklendi: {len(self.liste.satirlar)} satır.")

    # ---- arama ----
    def baslat(self, yenile):
        sorgu = self.kutu.text().strip()
        if not sorgu or self.thread is not None:
            return
        if not ayarlar.api_anahtari():
            QMessageBox.warning(self, "ParçaLink", "Önce Ayarlar'dan API anahtarınızı girin.")
            return
        self.ara_dugme.setEnabled(False)
        self.yenile_dugme.setEnabled(False)
        self.statusBar().showMessage("Aranıyor… (internet araması 30–90 saniye sürebilir)")
        self.thread = QThread()
        self.isci = Isci(sorgu, self.liste, yenile)
        self.isci.moveToThread(self.thread)
        self.thread.started.connect(self.isci.calis)
        self.isci.bitti.connect(self.goster)
        self.isci.hata.connect(self.hata)
        self.isci.bitti.connect(self.thread.quit)
        self.isci.hata.connect(self.thread.quit)
        self.thread.finished.connect(self.temizle)
        self.thread.start()

    def temizle(self):
        self.thread.deleteLater()
        self.thread = None
        self.ara_dugme.setEnabled(True)
        self.yenile_dugme.setEnabled(True)

    def hata(self, mesaj):
        self.statusBar().showMessage("Arama yapılamadı.")
        QMessageBox.warning(self, "ParçaLink", mesaj)

    def goster(self, s):
        self.son = s
        sutunlar = SUTUNLAR if s["tur"] == "oem" else METIN_SUTUNLARI
        self.tablo.setSortingEnabled(False)
        self.tablo.clear()
        self.tablo.setColumnCount(len(sutunlar))
        self.tablo.setHorizontalHeaderLabels(sutunlar)
        self.tablo.setRowCount(len(s["satirlar"]))
        for i, r in enumerate(s["satirlar"]):
            for j, c in enumerate(sutunlar):
                it = QTableWidgetItem(str(r.get(c, "")))
                if s["tur"] == "oem" and r.get("Güven") in RENK:
                    it.setBackground(QColor(RENK[r["Güven"]]))
                self.tablo.setItem(i, j, it)
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tablo.horizontalHeader().setStretchLastSection(True)
        self.tablo.setSortingEnabled(True)

        sonuc = s["sonuc"]
        if s["tur"] == "oem":
            ip = s["ipucu"]
            parca = [f"<b>{html.escape(s['kod'])}</b>: {html.escape(sonuc.parca_adi)}"]
            if sonuc.motor_parcasi:
                parca.append("motor parçası")
            if ip.get("arac"):
                parca.append(f"kod ipucu: {html.escape(ip['arac'])}")
            if ip.get("motor_ailesi"):
                parca.append(f"motor ailesi: {html.escape(ip['motor_ailesi'])}")
            if sonuc.esdeger_kodlar:
                parca.append("eşdeğer / benzer kodlar: " + html.escape(", ".join(sonuc.esdeger_kodlar)))
            metin = " · ".join(parca)
        else:
            metin = f"<b>{html.escape(sonuc.arac)}</b>, {html.escape(sonuc.parca)}: {len(s['satirlar'])} kod bulundu. " \
                    "Bir koda çift tıklayınca o kodun uyduğu araçlar aranır."
        if sonuc.notlar:
            metin += f"<br><i>Not: {html.escape(sonuc.notlar)}</i>"
        self.bilgi.setText(metin)
        adresler = s["adresler"]
        self.kaynaklar.setHtml("<b>İncelenen kaynaklar</b><br>" + "<br>".join(
            f'<a href="{html.escape(a)}">{html.escape(a)}</a>' for a in adresler) if adresler else "Kaynak yok.")
        self.statusBar().showMessage(f"{len(s['satirlar'])} satır" + (" (kayıtlı sonuç)" if s["onbellek"] else ""))

    def cift_tik(self, satir, sutun):
        if self.son and self.son["tur"] == "metin":
            kod = self.tablo.item(satir, 0).text()
            self.kutu.setText(kod)
            self.baslat(False)

    def kopyala(self, secili):
        if not self.son:
            return
        sutunlar = [self.tablo.horizontalHeaderItem(j).text() for j in range(self.tablo.columnCount())]
        satirlar = sorted({i.row() for i in self.tablo.selectedIndexes()}) if secili else range(self.tablo.rowCount())
        veri = [{c: (self.tablo.item(i, j).text() if self.tablo.item(i, j) else "") for j, c in enumerate(sutunlar)}
                for i in satirlar]
        if not veri:
            return
        QGuiApplication.clipboard().setText(kopyala_metni(veri, sutunlar))
        self.statusBar().showMessage(f"{len(veri)} satır kopyalandı. Excel'e veya WhatsApp'a yapıştırabilirsiniz.")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ParçaLink")
    p = Pencere()
    p.show()
    sys.exit(app.exec())
