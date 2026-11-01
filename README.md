# ParçaLink

Windows masaüstü programı (.exe). Parça kodu yazılır, program o parçanın hangi araçlara uyduğunu gösterir
(marka, model, kasa, motor kodu, yıllar).

Durum: **sürüm 0.2, deneme.** İnternet, ödeme veya API anahtarı gerekmez.

## Nasıl çalışır
- OEM kodu yazılır. **Kayıtlıysa** (yeşil) uyan araçlar kesin gelir: marka, model, kasa, hacim, motor kodu,
  beygir, yakıt, şanzıman, yıllar.
- **Kayıtlı değilse** (sarı) kodun başından tahmin gelir (ör. 2E0 = Crafter, 5E0 = Octavia III) ve o aracın Excel'deki
  motor seçenekleri listelenir. ETKA'dan kontrol edip **Kaydet / düzenle** ile kaydedilir.
- Kaydederken motor kodları yazılır (CLHA, CRBC…) → araçlar, hacim, beygir, yıllar `veri/Arac_Listesi.xlsx`'ten
  otomatik gelir; ya da model adıyla listelenip işaretlenir.
- "Caddy triger" gibi yazılınca kayıtlı parçalarda arar. "Google'da ara" kodu tarayıcıda aratır.
- Tablo "Tümünü kopyala" / Ctrl+C ile Excel'e veya WhatsApp'a yapıştırılır.
- Kayıtlar bilgisayarda `%APPDATA%\ParcaLink\parcalar.db` dosyasında; "Kayıtları Excel'e aktar" / "Excel'den kayıt al"
  ile başka bilgisayara taşınır.

## Exe'yi indirme
GitHub'da **Actions → ParçaLink exe** → en son başarılı çalıştırma → **Artifacts → ParcaLink-exe** (zip içinde
`ParcaLink.exe`). Masaüstüne koyup çift tıklayın.

## Geliştirme
```
pip install -r requirements.txt
python main.py
python -m pytest -q tests
```

- Kararlar ve açık sorular: `docs/plan.md`
- Claude ile çalışma kuralları: `CLAUDE.md`

Bu depoya şifre, API anahtarı veya gizli bilgi konmaz.
