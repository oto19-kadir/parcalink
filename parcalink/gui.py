"""ParçaLink masaüstü penceresi (PySide6). İnternet ve ücretli servis gerekmez."""
import sys
import webbrowser
from urllib.parse import quote_plus

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QGuiApplication
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSpinBox,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from . import ayarlar, kurallar
from .birlestir import (KAYITLI, METIN_SUTUNLARI, SUTUNLAR, birlestir, excel_satiri, kayitli_satirlar,
                        kopyala_metni, satirdan_arac, tahmin_satirlari)
from .depo import Depo
from .veri import AracListesi

SURUM = "0.2"
RENK_KAYITLI, RENK_TAHMIN = "#e5f4e4", "#f9eeda"


def tabloya_yaz(tablo, sutunlar, satirlar, isaret=False):
    tablo.setSortingEnabled(False)
    tablo.clear()
    tablo.setColumnCount(len(sutunlar) + (1 if isaret else 0))
    tablo.setHorizontalHeaderLabels((["Seç"] if isaret else []) + sutunlar)
    tablo.setRowCount(len(satirlar))
    for i, r in enumerate(satirlar):
        if isaret:
            it = QTableWidgetItem()
            it.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            it.setCheckState(Qt.Checked if r.get("_secili", True) else Qt.Unchecked)
            tablo.setItem(i, 0, it)
        for j, c in enumerate(sutunlar):
            it = QTableWidgetItem(str(r.get(c, "") or ""))
            it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            if r.get("Durum"):
                it.setBackground(QColor(RENK_KAYITLI if r["Durum"] == KAYITLI else RENK_TAHMIN))
            tablo.setItem(i, j + (1 if isaret else 0), it)
    tablo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    tablo.horizontalHeader().setStretchLastSection(True)
    tablo.setSortingEnabled(not isaret)


class KayitPenceresi(QDialog):
    """Bir OEM kodunu uyan araçlarıyla kaydetme / düzenleme."""

    def __init__(self, ust, depo, liste, kod, mevcut=None, oneriler=None):
        super().__init__(ust)
        self.depo, self.liste, self.kod = depo, liste, kurallar.kod_normal(kod)
        self.setWindowTitle(f"Kaydet: {self.kod}")
        self.resize(1150, 680)
        self.adaylar = []  # tablo satırları
        y = QVBoxLayout(self)

        s1 = QHBoxLayout()
        s1.addWidget(QLabel("Parça adı:"))
        self.ad = QLineEdit(mevcut["ad"] if mevcut else "")
        self.ad.setPlaceholderText("ör. Emme manifoldu, triger seti, cam düğmesi")
        s1.addWidget(self.ad, 1)
        y.addLayout(s1)

        s2 = QHBoxLayout()
        s2.addWidget(QLabel("Motor kodları:"))
        self.motor = QLineEdit()
        self.motor.setPlaceholderText("ETKA'daki motor kodları, virgülle: CLHA, CRBC, DDYA")
        s2.addWidget(self.motor, 1)
        b = QPushButton("Excel'den getir")
        b.clicked.connect(self.motordan)
        s2.addWidget(b)
        y.addLayout(s2)

        s3 = QHBoxLayout()
        s3.addWidget(QLabel("veya model:"))
        self.model = QLineEdit()
        self.model.setPlaceholderText("ör. Golf, Octavia, Crafter, C Serisi")
        s3.addWidget(self.model, 1)
        s3.addWidget(QLabel("yıl"))
        self.yil1, self.yil2 = QSpinBox(), QSpinBox()
        for sp, v in ((self.yil1, 1980), (self.yil2, 2026)):
            sp.setRange(1980, 2030)
            sp.setValue(v)
            s3.addWidget(sp)
        b2 = QPushButton("Listele")
        b2.clicked.connect(self.modelden)
        s3.addWidget(b2)
        y.addLayout(s3)

        y.addWidget(QLabel("İşaretli araçlar kaydedilir. Yanlış olanların işaretini kaldırın."))
        self.tablo = QTableWidget()
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        y.addWidget(self.tablo, 1)

        s4 = QHBoxLayout()
        for ad, f in (("Hepsini işaretle", lambda: self.isaretle(True)), ("İşaretleri kaldır", lambda: self.isaretle(False))):
            bb = QPushButton(ad)
            bb.clicked.connect(f)
            s4.addWidget(bb)
        s4.addStretch(1)
        y.addLayout(s4)
        self.notlar = QLineEdit(mevcut["notlar"] if mevcut else "")
        self.notlar.setPlaceholderText("Not (isteğe bağlı), ör. sadece manuel klimalı araçlar")
        y.addWidget(self.notlar)
        d = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        d.accepted.connect(self.kaydet)
        d.rejected.connect(self.reject)
        y.addWidget(d)

        if mevcut:
            self.ekle([dict(r, _secili=True) for r in kayitli_satirlar(mevcut)])
        elif oneriler:
            self.ekle([dict(r, _secili=False) for r in oneriler])

    def _isaretler(self):
        for i, r in enumerate(self.adaylar):
            it = self.tablo.item(i, 0)
            if it is not None:
                r["_secili"] = it.checkState() == Qt.Checked

    def ekle(self, satirlar):
        self._isaretler()
        var = {(r["Marka"], r["Model"], r["Kasa"], r["Motor kodu"], r["Yıllar"]) for r in self.adaylar}
        for r in satirlar:
            k = (r["Marka"], r["Model"], r["Kasa"], r["Motor kodu"], r["Yıllar"])
            if k not in var:
                self.adaylar.append(r)
                var.add(k)
        tabloya_yaz(self.tablo, SUTUNLAR[:-1], self.adaylar, isaret=True)

    def motordan(self):
        yeni = []
        for k in [x.strip().upper() for x in self.motor.text().replace(";", ",").split(",") if x.strip()]:
            bulunan = self.liste.motor_kodu_ile(k)
            if not bulunan:
                QMessageBox.information(self, "ParçaLink", f"{k} motor kodu araç listesinde yok.")
            yeni += [dict(excel_satiri(s, k), _secili=True) for s in bulunan]
        self.ekle(birlestir(yeni))

    def modelden(self):
        if not self.model.text().strip():
            return
        m = self.model.text().strip()
        marka = ""
        for mk in ("Volkswagen", "Seat", "Skoda", "Audi", "Porsche", "Mercedes-Benz", "Smart"):
            if m.lower().startswith(mk.lower() + " "):
                marka, m = mk, m[len(mk) + 1:]
        bulunan = self.liste.model_ile(marka, m, self.yil1.value(), self.yil2.value())
        if not bulunan:
            QMessageBox.information(self, "ParçaLink", "Bu model ve yıllarda araç bulunamadı.")
        self.ekle(birlestir([dict(excel_satiri(s), _secili=False) for s in bulunan]))

    def isaretle(self, deger):
        for i in range(self.tablo.rowCount()):
            self.tablo.item(i, 0).setCheckState(Qt.Checked if deger else Qt.Unchecked)

    def kaydet(self):
        self._isaretler()
        secili = [satirdan_arac(r) for r in self.adaylar if r.get("_secili")]
        if not secili:
            QMessageBox.warning(self, "ParçaLink", "En az bir aracı işaretleyin.")
            return
        self.depo.kaydet(self.kod, self.ad.text().strip(), secili, self.notlar.text().strip())
        self.accept()


class Pencere(QMainWindow):
    def __init__(self, depo=None):
        super().__init__()
        self.setWindowTitle(f"ParçaLink {SURUM}")
        self.resize(1250, 760)
        self.liste = AracListesi()
        self.depo = depo or Depo(ayarlar.depo_yolu())
        self.son = None

        orta = QWidget()
        y = QVBoxLayout(orta)
        ust = QHBoxLayout()
        self.kutu = QLineEdit()
        self.kutu.setPlaceholderText("OEM kodu yazın (ör. 04L129766N) ya da parça ve araç (ör. Caddy triger)")
        self.kutu.setMinimumHeight(38)
        self.kutu.returnPressed.connect(self.ara)
        b = QPushButton("Ara")
        b.setMinimumHeight(38)
        b.clicked.connect(self.ara)
        ust.addWidget(self.kutu, 1)
        ust.addWidget(b)
        y.addLayout(ust)

        self.bilgi = QLabel("Bir OEM kodu yazıp Ara'ya basın. Kayıtlı kodlar kesin, kayıtsız kodlar tahmin olarak gelir.")
        self.bilgi.setWordWrap(True)
        self.bilgi.setTextInteractionFlags(Qt.TextSelectableByMouse)
        y.addWidget(self.bilgi)

        self.tablo = QTableWidget(0, len(SUTUNLAR))
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.cellDoubleClicked.connect(self.cift_tik)
        y.addWidget(self.tablo, 1)

        alt = QHBoxLayout()
        self.kaydet_d = QPushButton("Kaydet / düzenle")
        self.kaydet_d.clicked.connect(self.kayit)
        self.google_d = QPushButton("Google'da ara")
        self.google_d.clicked.connect(self.google)
        k1 = QPushButton("Tümünü kopyala")
        k1.clicked.connect(lambda: self.kopyala(False))
        k2 = QPushButton("Seçilileri kopyala")
        k2.clicked.connect(lambda: self.kopyala(True))
        d1 = QPushButton("Kayıtları Excel'e aktar")
        d1.clicked.connect(self.disa)
        d2 = QPushButton("Excel'den kayıt al")
        d2.clicked.connect(self.ice)
        for w in (self.kaydet_d, self.google_d, k1, k2):
            alt.addWidget(w)
        alt.addStretch(1)
        alt.addWidget(d1)
        alt.addWidget(d2)
        y.addLayout(alt)
        y.addWidget(QLabel("Yeşil = kayıtlı (sizin onayınızla). Sarı = kodun başından tahmin, ETKA'dan kontrol edip kaydedin."))
        self.setCentralWidget(orta)
        kop = QAction("Kopyala", self)
        kop.setShortcut("Ctrl+C")
        kop.triggered.connect(lambda: self.kopyala(True))
        self.addAction(kop)
        self.durum()

    def durum(self, ek=""):
        self.statusBar().showMessage(f"Araç listesi: {len(self.liste.satirlar)} satır. Kayıtlı parça: {self.depo.sayi()}."
                                     + (f" {ek}" if ek else ""))

    # ---- arama ----
    def ara(self):
        sorgu = self.kutu.text().strip()
        if not sorgu:
            return
        if kurallar.oem_gibi_mi(sorgu):
            self.kod_goster(kurallar.kod_normal(sorgu))
        else:
            satirlar = self.depo.metinle_ara(sorgu)
            self.son = {"tur": "metin", "satirlar": satirlar, "sutunlar": METIN_SUTUNLARI}
            tabloya_yaz(self.tablo, METIN_SUTUNLARI, satirlar)
            self.bilgi.setText(f"“{sorgu}” için kayıtlı parçalarda {len(satirlar)} sonuç. Bir koda çift tıklayınca açılır."
                               if satirlar else f"“{sorgu}” kayıtlı parçalarda bulunamadı. OEM kodunu biliyorsanız kodla arayın.")
            self.kaydet_d.setEnabled(False)

    def kod_goster(self, kod):
        self.kaydet_d.setEnabled(True)
        parca = self.depo.getir(kod)
        ip = kurallar.ipucu(kod)
        benzer = self.depo.benzer(kod)
        if parca:
            satirlar = kayitli_satirlar(parca)
            metin = f"<b>{kod}</b>: {parca['ad'] or 'parça'} – kayıtlı, {len(satirlar)} araç ({parca['tarih']})."
            if parca["notlar"]:
                metin += f"<br><i>Not: {parca['notlar']}</i>"
        else:
            satirlar = tahmin_satirlari(ip, self.liste)
            metin = f"<b>{kod}</b> kayıtlı değil."
            if ip["arac"]:
                metin += f" Kodun başına göre tahmin: <b>{ip['arac']}</b> ({len(satirlar)} motor seçeneği aşağıda)."
            else:
                metin += " Kodun başından araç tahmin edilemedi."
            metin += " ETKA'dan kontrol edip <b>Kaydet</b> ile kaydedin."
        if ip["motor_ailesi"]:
            metin += f"<br>Motor ailesi: {ip['motor_ailesi']}."
        if benzer:
            metin += "<br>Benzer kayıtlı kodlar (farklı ek): " + ", ".join(benzer)
        self.son = {"tur": "kod", "kod": kod, "satirlar": satirlar, "sutunlar": SUTUNLAR, "parca": parca}
        tabloya_yaz(self.tablo, SUTUNLAR, satirlar)
        self.bilgi.setText(metin)
        self.durum()

    def cift_tik(self, satir, sutun):
        if self.son and self.son["tur"] == "metin":
            kod = self.tablo.item(satir, 0).text()
            self.kutu.setText(kod)
            self.kod_goster(kod)

    def kayit(self):
        if not self.son or self.son["tur"] != "kod":
            QMessageBox.information(self, "ParçaLink", "Önce bir OEM kodu arayın.")
            return
        s = self.son
        p = KayitPenceresi(self, self.depo, self.liste, s["kod"], s["parca"], None if s["parca"] else s["satirlar"])
        if p.exec():
            self.kod_goster(s["kod"])
            self.durum("Kaydedildi.")

    def google(self):
        q = self.son["kod"] if self.son and self.son["tur"] == "kod" else self.kutu.text().strip()
        if q:
            webbrowser.open("https://www.google.com/search?q=" + quote_plus(q))

    def kopyala(self, secili):
        if not self.son:
            return
        sutunlar = [self.tablo.horizontalHeaderItem(j).text() for j in range(self.tablo.columnCount())]
        satirlar = sorted({i.row() for i in self.tablo.selectedIndexes()}) if secili else range(self.tablo.rowCount())
        veri = [{c: (self.tablo.item(i, j).text() if self.tablo.item(i, j) else "") for j, c in enumerate(sutunlar)}
                for i in satirlar]
        if veri:
            QGuiApplication.clipboard().setText(kopyala_metni(veri, sutunlar))
            self.durum(f"{len(veri)} satır kopyalandı.")

    def disa(self):
        yol, _ = QFileDialog.getSaveFileName(self, "Kayıtları Excel'e aktar", "ParcaLink_kayitlar.xlsx", "Excel (*.xlsx)")
        if yol:
            self.depo.disa_aktar(yol)
            self.durum("Excel'e aktarıldı.")

    def ice(self):
        yol, _ = QFileDialog.getOpenFileName(self, "Excel'den kayıt al", "", "Excel (*.xlsx)")
        if yol:
            n = self.depo.ice_aktar(yol)
            self.durum(f"{n} parça alındı.")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ParçaLink")
    p = Pencere()
    p.show()
    sys.exit(app.exec())
