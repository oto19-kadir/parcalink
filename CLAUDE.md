# ParçaLink – Claude için çalışma kuralları

Sahibi: Kadir Demirkoparan (Oto19 Kartal). Bu depo sadece **ParçaLink** masaüstü programıdır.

## Projeleri karıştırma (KESİN)
- "ParçaLink" = sadece bu depo (`oto19-kadir/parcalink`).
- "Kartal" = `oto19-kadir/oto19kartal` (oto19kartal.com sitesi). "Düğme" = `oto19-kadir/otodugmemarket` (otodugmemarket.com).
- ParçaLink işi Kartal'a veya Düğme'ye yazılmaz, onlardan dosya taşınmaz. Başka projeden veri gerekirse önce kullanıcıya sorulur.

## Ne yapıyor
- Kullanıcı parça kodunu (OEM / stok / tedarikçi kodu – netleşecek) yazar; program uyumlu araçları listeler.
- Windows'ta masaüstünden çift tıklayınca açılan tek .exe; kurulum gerektirmemesi hedef.
- Exe, GitHub Actions'ın Windows makinesinde üretilir (Claude'un ortamı Linux).

## Kurallar
1. **Uydurma uyumluluk yok:** Hangi parçanın hangi araca uyduğu bilgisi sadece kullanıcının verdiği veya onayladığı kaynaktan gelir. Claude kendi bilgisinden uyumluluk yazmaz; tahmini veri varsa "doğrulanmamış" diye işaretlenir.
2. **Gizli bilgiler:** Şifre, API anahtarı, Client Secret ASLA istenmez, sohbete, koda veya depoya yazılmaz.
3. **Kopyalama:** Başka sitelerin veya katalogların verisi izinsiz toplu kopyalanmaz.
4. **Yazım:** Programda görünen metinler düzgün Türkçe, tam cümle.
5. Her iş bitince commit edilip GitHub'a gönderilir; `docs/plan.md` güncellenir.
