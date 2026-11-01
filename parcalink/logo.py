"""ParçaLink logosu (vektör, kodla çizilir): lacivert zemin üzerinde iç içe iki zincir halkası."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen, QPixmap

LACIVERT = "#0f2742"
LACIVERT2 = "#1d4e89"
TURUNCU = "#ff7a1a"


def ciz(boyut=256, zemin=True):
    pm = QPixmap(boyut, boyut)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = boyut / 256.0
    if zemin:
        g = QLinearGradient(0, 0, boyut, boyut)
        g.setColorAt(0, QColor(LACIVERT2))
        g.setColorAt(1, QColor(LACIVERT))
        p.setBrush(QBrush(g))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(0, 0, boyut, boyut), 56 * s, 56 * s)
    kalin = 26 * s

    def halka(renk, cx):
        p.setPen(QPen(QColor(renk), kalin, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF((cx - 52) * s, 98 * s, 104 * s, 60 * s), 30 * s, 30 * s)

    halka(TURUNCU, 98)
    halka("#ffffff", 158)
    # iç içe görünüm: üst kesişimde turuncu halka beyazın üstünden geçer
    p.save()
    p.setClipRect(QRectF(128 * s, 70 * s, 44 * s, 56 * s))
    halka(TURUNCU, 98)
    p.restore()
    p.end()
    return pm
