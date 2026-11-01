# ParçaLink

Windows masaüstü programı (.exe). Parça kodu yazılır, program o parçanın hangi araçlara uyduğunu gösterir
(marka, model, kasa, motor kodu, yıllar).

Durum: **ilk sürüm (0.1), deneme.**

## Nasıl çalışır
- OEM kodu yazılır → Claude internette arar → bulunan motor kodları `veri/Arac_Listesi.xlsx` ile eşleşir →
  tabloda marka, model, kasa, hacim, motor kodu, beygir, yakıt, şanzıman, yıllar, güven derecesi ve kaynak.
- "Caddy motor triger" gibi yazılırsa OEM kodları listelenir; bir koda çift tıklayınca uyan araçlar aranır.
- Sonuçlar 30 gün bilgisayarda saklanır (tekrar aramak ücretsiz ve anında); "İnternetten yenile" yeniden arar.
- Tablo "Tümünü kopyala" ile Excel'e / WhatsApp'a yapıştırılabilir.

## Exe'yi indirme
GitHub'da **Actions → ParçaLink exe** → en son başarılı çalıştırma → **Artifacts → ParcaLink-exe** (zip içinde
`ParcaLink.exe`). Masaüstüne koyup çift tıklayın. İlk açılışta **Ayarlar**'dan Anthropic API anahtarını girin
(anahtar sadece o bilgisayarda, `%APPDATA%\ParcaLink` içinde saklanır).

## Geliştirme
```
pip install -r requirements.txt
python main.py
python -m pytest -q tests
```

- Kararlar ve açık sorular: `docs/plan.md`
- Claude ile çalışma kuralları: `CLAUDE.md`

Bu depoya şifre, API anahtarı veya gizli bilgi konmaz.
