"""OEM kodunun biçiminden TAHMİN: araç tipi ve motor ailesi.

Bunlar sadece tahmindir (kesin uyum değil). Tablo Claude'un bilgisinden hazırlandı; kullanıcı ETKA ile kontrol edip
düzeltebilir. Yeni satır: "kod başı": ("açıklama", "Marka", "Excel'deki model adı", ilk yıl, son yıl)
"""
import re

# VW grubu: ilk 3 hane = parçanın ilk tasarlandığı araç tipi.
VAG_ARAC = {
    "1H0": ("VW Golf III / Vento", "Volkswagen", "Golf", 1991, 1998),
    "1J0": ("VW Golf IV / Bora", "Volkswagen", "Golf", 1997, 2005), "1J1": ("VW Golf IV / Bora", "Volkswagen", "Golf", 1997, 2005),
    "1K0": ("VW Golf V / Jetta V", "Volkswagen", "Golf", 2003, 2009), "1K1": ("VW Golf V", "Volkswagen", "Golf", 2003, 2009),
    "5K0": ("VW Golf VI", "Volkswagen", "Golf", 2008, 2013), "5G0": ("VW Golf VII", "Volkswagen", "Golf", 2012, 2020),
    "5G1": ("VW Golf VII", "Volkswagen", "Golf", 2012, 2020), "5H0": ("VW Golf VIII", "Volkswagen", "Golf", 2019, 2026),
    "3B0": ("VW Passat B5", "Volkswagen", "Passat", 1996, 2005), "3C0": ("VW Passat B6", "Volkswagen", "Passat", 2005, 2010),
    "3AA": ("VW Passat B7", "Volkswagen", "Passat", 2010, 2014), "3G0": ("VW Passat B8", "Volkswagen", "Passat", 2014, 2023),
    "6N0": ("VW Polo III", "Volkswagen", "Polo", 1994, 2001), "6Q0": ("VW Polo IV", "Volkswagen", "Polo", 2001, 2009),
    "6R0": ("VW Polo V", "Volkswagen", "Polo", 2009, 2017), "6C0": ("VW Polo V (6C)", "Volkswagen", "Polo", 2014, 2017),
    "2G0": ("VW Polo VI", "Volkswagen", "Polo", 2017, 2026),
    "1T0": ("VW Touran", "Volkswagen", "Touran", 2003, 2015), "5T0": ("VW Touran II", "Volkswagen", "Touran", 2015, 2025),
    "5N0": ("VW Tiguan", "Volkswagen", "Tiguan", 2007, 2016), "5NA": ("VW Tiguan II", "Volkswagen", "Tiguan", 2016, 2024),
    "2K0": ("VW Caddy III", "Volkswagen", "Caddy", 2004, 2015), "2K5": ("VW Caddy", "Volkswagen", "Caddy", 2004, 2020),
    "7E0": ("VW Transporter T5", "Volkswagen", "Transporter", 2003, 2015),
    "7H0": ("VW Transporter T5", "Volkswagen", "Transporter", 2003, 2015),
    "7D0": ("VW Transporter T4", "Volkswagen", "Transporter", 1990, 2003),
    "2E0": ("VW Crafter (2006–2016) / Mercedes Sprinter W906", "Volkswagen", "Crafter", 2006, 2016),
    "2D0": ("VW LT", "Volkswagen", "LT", 1996, 2006),
    "7L0": ("VW Touareg", "Volkswagen", "Touareg", 2002, 2010), "7P0": ("VW Touareg II", "Volkswagen", "Touareg", 2010, 2018),
    "5C6": ("VW Jetta VI", "Volkswagen", "Jetta", 2011, 2018), "5C0": ("VW Beetle (5C)", "Volkswagen", "Beetle", 2011, 2019),
    "1C0": ("VW Beetle (9C)", "Volkswagen", "Beetle", 1998, 2010),
    "7N0": ("VW Sharan II", "Volkswagen", "Sharan", 2010, 2022), "7M0": ("VW Sharan", "Volkswagen", "Sharan", 1995, 2010),
    "3H0": ("VW Arteon", "Volkswagen", "Arteon", 2017, 2024), "2H0": ("VW Amarok", "Volkswagen", "Amarok", 2010, 2022),
    "1U0": ("Skoda Octavia I", "Skoda", "Octavia", 1996, 2010), "1Z0": ("Skoda Octavia II", "Skoda", "Octavia", 2004, 2013),
    "5E0": ("Skoda Octavia III", "Skoda", "Octavia", 2012, 2020),
    "6Y0": ("Skoda Fabia I", "Skoda", "Fabia", 1999, 2007), "5J0": ("Skoda Fabia II / Roomster", "Skoda", "Fabia", 2007, 2014),
    "6V0": ("Skoda Fabia III", "Skoda", "Fabia", 2014, 2021),
    "3T0": ("Skoda Superb II", "Skoda", "Superb", 2008, 2015), "3V0": ("Skoda Superb III", "Skoda", "Superb", 2015, 2024),
    "5L0": ("Skoda Yeti", "Skoda", "Yeti", 2009, 2017), "565": ("Skoda Kodiaq", "Skoda", "Kodiaq", 2016, 2024),
    "57A": ("Skoda Karoq", "Skoda", "Karoq", 2017, 2026), "60U": ("Skoda Rapid", "Skoda", "Rapid", 2012, 2019),
    "1M0": ("Seat Leon I / Toledo II", "Seat", "Leon", 1999, 2005), "1P0": ("Seat Leon II", "Seat", "Leon", 2005, 2012),
    "5F0": ("Seat Leon III", "Seat", "Leon", 2012, 2020), "6K0": ("Seat Ibiza II", "Seat", "Ibiza", 1993, 2002),
    "6L0": ("Seat Ibiza III", "Seat", "Ibiza", 2002, 2009), "6J0": ("Seat Ibiza IV", "Seat", "Ibiza", 2008, 2017),
    "6F0": ("Seat Ibiza V / Arona", "Seat", "Ibiza", 2017, 2026), "5P0": ("Seat Altea / Toledo III", "Seat", "Altea", 2004, 2015),
    "8L0": ("Audi A3 (8L)", "Audi", "A3", 1996, 2003), "8P0": ("Audi A3 (8P)", "Audi", "A3", 2003, 2013),
    "8V0": ("Audi A3 (8V)", "Audi", "A3", 2012, 2020), "8Y0": ("Audi A3 (8Y)", "Audi", "A3", 2020, 2026),
    "8D0": ("Audi A4 B5", "Audi", "A4", 1994, 2001), "8E0": ("Audi A4 B6 / B7", "Audi", "A4", 2000, 2008),
    "8K0": ("Audi A4 B8", "Audi", "A4", 2007, 2015), "8W0": ("Audi A4 B9", "Audi", "A4", 2015, 2025),
    "8T0": ("Audi A5 (8T)", "Audi", "A5", 2007, 2016),
    "4B0": ("Audi A6 C5", "Audi", "A6", 1997, 2005), "4F0": ("Audi A6 C6", "Audi", "A6", 2004, 2011),
    "4G0": ("Audi A6 C7", "Audi", "A6", 2011, 2018), "4K0": ("Audi A6 C8", "Audi", "A6", 2018, 2025),
    "4H0": ("Audi A8 (4H)", "Audi", "A8", 2010, 2017), "8X0": ("Audi A1 (8X)", "Audi", "A1", 2010, 2018),
    "8U0": ("Audi Q3 (8U)", "Audi", "Q3", 2011, 2018), "8R0": ("Audi Q5 (8R)", "Audi", "Q5", 2008, 2017),
    "4L0": ("Audi Q7 (4L)", "Audi", "Q7", 2006, 2015), "4M0": ("Audi Q7 (4M)", "Audi", "Q7", 2015, 2026),
    "8J0": ("Audi TT (8J)", "Audi", "TT", 2006, 2014), "8S0": ("Audi TT (FV)", "Audi", "TT", 2014, 2023),
    "81A": ("Audi Q2", "Audi", "Q2", 2016, 2024),
}

# VW grubu motor parçaları: ilk 3 hane = motor ailesi (sadece açıklama).
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
    """7–15 karakter, rakam içeren ve kelime (4+ harf) içermeyen yazı OEM kodu sayılır."""
    t = (metin or "").strip()
    n = kod_normal(t)
    if not (7 <= len(n) <= 15) or not any(c.isdigit() for c in n):
        return False
    # "Caddy motor triger" gibi kelime içeren yazılar OEM değil; "04L 129 766 N" gibi aralıklı kod OEM
    return not any(re.fullmatch(r"[A-Za-zÇĞİÖŞÜçğıöşü]{4,}", w) for w in t.split())


def ipucu(kod):
    """{'marka_grubu', 'arac', 'motor_ailesi', 'excel': (marka, model, yil_bas, yil_bit) | None, 'kasa': str}"""
    n = kod_normal(kod)
    out = {"marka_grubu": "", "arac": "", "motor_ailesi": "", "excel": None, "kasa": ""}
    if re.fullmatch(r"A\d{10}(\d{2})?", n):
        out["marka_grubu"] = "Mercedes-Benz"
        out["kasa"] = n[1:4]
        out["arac"] = f"Mercedes kasa {n[1:4]} (W/C/S/X{n[1:4]})"
    elif re.fullmatch(r"[0-9A-Z]{3}\d{6}[A-Z]{0,3}", n):
        out["marka_grubu"] = "Volkswagen grubu"
        bas = n[:3]
        if bas in VAG_ARAC:
            etiket, marka, model, a, b = VAG_ARAC[bas]
            out["arac"], out["excel"] = etiket, (marka, model, a, b)
        out["motor_ailesi"] = VAG_MOTOR.get(bas, "")
    return out
