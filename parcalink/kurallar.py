"""OEM kodunun biçiminden ipucu: marka grubu, araç tipi, motor ailesi.

Bunlar sadece İPUCU'dur (kesin uyum değil). Tablo Claude'un bilgisinden hazırlandı; kullanıcı ETKA ile
kontrol edip düzeltebilir. Yeni satır eklemek için sözlüğe yazmak yeterli.
"""
import re

# VW grubu: ilk 3 hane araç tipi (parçanın ilk tasarlandığı araç).
VAG_ARAC = {
    "1H0": "VW Golf III / Vento", "1J0": "VW Golf IV / Bora", "1J1": "VW Golf IV / Bora", "1K0": "VW Golf V / Jetta V",
    "1K1": "VW Golf V", "5K0": "VW Golf VI", "5G0": "VW Golf VII", "5G1": "VW Golf VII", "5H0": "VW Golf VIII",
    "3B0": "VW Passat B5", "3C0": "VW Passat B6", "3AA": "VW Passat B7", "3G0": "VW Passat B8",
    "6N0": "VW Polo III", "6Q0": "VW Polo IV", "6R0": "VW Polo V", "6C0": "VW Polo V (6C)", "2G0": "VW Polo VI",
    "1T0": "VW Touran", "5T0": "VW Touran II", "5N0": "VW Tiguan", "5NA": "VW Tiguan II",
    "2K0": "VW Caddy III", "2K5": "VW Caddy", "7E0": "VW Transporter T5", "7H0": "VW Transporter T5",
    "7D0": "VW Transporter T4", "2E0": "VW Crafter (2006–2016)", "2D0": "VW LT", "7L0": "VW Touareg",
    "7P0": "VW Touareg II", "5C6": "VW Jetta VI", "5C0": "VW Beetle (5C)", "1C0": "VW Beetle (9C)",
    "7N0": "VW Sharan II", "7M0": "VW Sharan", "3H0": "VW Arteon", "2H0": "VW Amarok",
    "1Z0": "Skoda Octavia II", "5E0": "Skoda Octavia III", "1U0": "Skoda Octavia I", "5J0": "Skoda Fabia II / Roomster",
    "6V0": "Skoda Fabia III", "6Y0": "Skoda Fabia I", "3T0": "Skoda Superb II", "3V0": "Skoda Superb III",
    "5L0": "Skoda Yeti", "565": "Skoda Kodiaq", "57A": "Skoda Karoq", "60U": "Skoda Rapid",
    "1M0": "Seat Leon I / Toledo II", "1P0": "Seat Leon II", "5F0": "Seat Leon III", "6J0": "Seat Ibiza IV",
    "6F0": "Seat Ibiza V / Arona", "6L0": "Seat Ibiza III", "6K0": "Seat Ibiza II", "5P0": "Seat Altea / Toledo III",
    "8L0": "Audi A3 (8L)", "8P0": "Audi A3 (8P)", "8V0": "Audi A3 (8V)", "8Y0": "Audi A3 (8Y)",
    "8D0": "Audi A4 B5", "8E0": "Audi A4 B6/B7", "8K0": "Audi A4 B8", "8W0": "Audi A4 B9", "8T0": "Audi A5 (8T)",
    "4B0": "Audi A6 C5", "4F0": "Audi A6 C6", "4G0": "Audi A6 C7", "4K0": "Audi A6 C8", "4H0": "Audi A8 (4H)",
    "8X0": "Audi A1 (8X)", "8U0": "Audi Q3 (8U)", "8R0": "Audi Q5 (8R)", "4L0": "Audi Q7 (4L)", "4M0": "Audi Q7 (4M)",
    "8J0": "Audi TT (8J)", "8S0": "Audi TT (FV)", "81A": "Audi Q2",
}

# VW grubu motor parçaları: ilk 3 hane motor ailesi.
VAG_MOTOR = {
    "038": "1.4 / 1.9 / 2.0 TDI (pompa enjektör, EA188)", "045": "1.4 TDI 3 silindir (EA188)",
    "03L": "1.6 / 2.0 TDI common rail (EA189)", "04L": "1.6 / 2.0 TDI (EA288)", "04B": "1.4 / 1.6 TDI (EA288 küçük)",
    "03G": "2.0 TDI pompa enjektör", "059": "2.7 / 3.0 V6 TDI", "03C": "1.2 / 1.4 TSI (EA111)",
    "04E": "1.0 / 1.2 / 1.4 / 1.5 TSI (EA211)", "04C": "1.0 3 silindir (EA211)", "036": "1.4 / 1.6 benzinli (EA111)",
    "06A": "1.6 / 1.8 / 2.0 benzinli (EA113)", "06J": "1.8 / 2.0 TSI (EA888 2. nesil)",
    "06K": "1.8 / 2.0 TSI (EA888 3. nesil)", "06H": "1.8 / 2.0 TFSI (EA888)", "06F": "2.0 FSI / TFSI (EA113)",
    "07K": "2.5 R5 benzinli", "022": "VR6 / V5", "070": "2.5 R5 TDI", "076": "2.5 TDI (Crafter)",
}


def kod_normal(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def oem_gibi_mi(metin):
    """Tek kelime, harf+rakam karışık, 7–15 karakter -> OEM kodu say."""
    t = (metin or "").strip()
    n = kod_normal(t)
    if not (7 <= len(n) <= 15) or not any(c.isdigit() for c in n):
        return False
    # "Caddy motor triger" gibi kelime içeren yazılar OEM değil; "04L 129 766 N" gibi aralıklı kod OEM
    return not any(re.fullmatch(r"[A-Za-zÇĞİÖŞÜçğıöşü]{4,}", w) for w in t.split())


def ipucu(kod):
    """{'marka_grubu':..., 'arac':..., 'motor_ailesi':...}"""
    n = kod_normal(kod)
    out = {"marka_grubu": "", "arac": "", "motor_ailesi": ""}
    if re.fullmatch(r"A\d{10}(\d{2})?", n):
        out["marka_grubu"] = "Mercedes-Benz"
        kasa = n[1:4]
        out["arac"] = f"Mercedes kasa {kasa} (ör. W{kasa}) – parçanın ilk tasarlandığı kasa"
    elif re.fullmatch(r"[0-9A-Z]{3}\d{6}[A-Z]{0,3}", n) or re.fullmatch(r"[0-9A-Z]{3}\d{3}\d{3}[A-Z]{0,3}", n):
        out["marka_grubu"] = "Volkswagen grubu (VW, Audi, Seat, Skoda, Cupra, Porsche)"
        bas = n[:3]
        out["arac"] = VAG_ARAC.get(bas, "")
        out["motor_ailesi"] = VAG_MOTOR.get(bas, "")
    return out
