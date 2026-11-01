# Doğruluk denemesi 1 (1 Kasım 2026)

Yöntem: her OEM kodu sadece kod + marka grubu ("VW" / "Mercedes", kodun biçiminden) ile internette arandı;
bulunan motor kodları araç listesiyle (veri/Arac_Listesi.xlsx) eşleştirildi; sonuç kullanıcının cevap anahtarıyla
karşılaştırıldı. (Bir ara turda sorgulara cevap anahtarından araç adları yazılmıştı; o tur geçersiz sayıldı.)

| OEM kodu | Parça (bulunan) | Kullanıcının cevabı | Bulunan araçlar | Araç | Motor kodu |
|---|---|---|---|---|---|
| 04L129766N | Emme manifoldu / intercooler (1.6–2.0 TDI) | Golf 7, Passat, A3, Leon, Kodiaq; CXXA CLHA DDYA CUNA CUPA DBGA DFGA CRKB CKFV | Golf, A3, Leon, Kodiaq (+ Octavia, Jetta, Arteon, Tiguan); CLHA, DBGA, CRBC, CXXB | 4/5 (Passat yok) | 2/9 |
| 2E0857186 | "Blende" (trim/kapak) | Crafter 06-16, Sprinter W906 06-16 | Araç bulunamadı | 0/2 | – |
| 04B145749K | Intercooler 1.4 TDI | Polo 5, A1, Ibiza, Toledo, Rapid, Fabia | Polo V, A1, Ibiza, Toledo, Fabia, Rapid; CUSA CUSB CUTA | 6/6 | (cevapta yok) |
| A9064640318 | Direksiyon açı sensörü / spiral | Crafter 06-16, Sprinter W906 06-16 | Sprinter W906 | 1/2 (Crafter yok) | – |
| 1J0820045F | Kalorifer kontrol paneli | Golf 4, Bora 98> | Golf IV, Jetta IV/Bora 1998–2006 (+ Passat?) | 2/2 | – |
| 5E0820951C | Orta torpido havalandırma ızgarası | Octavia 18-21 | Octavia III 2013–2021 | 1/1 (yıllar geniş) | – |
| 038906461 | Hava akış (MAF) sensörü, 1.9 TDI | Golf 4, Bora, A3, Polo; 1.4/1.9 TDI ALH AGR AMF | Golf, Jetta/Bora, Beetle 1998–2003 (C ekiyle); B ekinde BEW (yanlış dönem) | 2/4 | 0/3 |

**Toplam:** araç (model) 16/22 doğru bulundu (%73); motor kodu 2/12 (%17). Parçanın ne olduğu 7 kodun 6'sında net.

## Bulgular
1. Model düzeyinde iyi, **motor kodu ve yıl düzeyinde zayıf.** "1.6 mı 2.0 mı, hangi motor kodu" sorusuna internet araması tek başına yetmiyor.
2. **Kodun sonundaki harf önemli:** 038906461, 038906461B ve 038906461C farklı dönemler. Program eki ayırmalı.
3. **Kodun başı aracı söylüyor:** VW grubunda ilk 3 hane araç tipidir (2E0 = Crafter, 5E0 = Octavia III, 1J0 = Golf 4/Bora, 5G0 = Golf 7); Mercedes'te ortadaki 3 hane kasa (A906… = W906 Sprinter). Bu kural, internette bulunamayan kodlarda (2E0857186) ipucu verir.
4. Bulunan "fazla" araçlar (Octavia, Jetta, Arteon, Tiguan, Passat, Beetle) yanlış olmayabilir; cevap anahtarında olmayabilirler. Kontrol edilmeli.

## Sonuç
İnternet + yapay zekâ + araç listesi, "bu parça hangi modellere uyar" için işe yarar ama ticari satış için motor
kodu doğruluğu yetersiz. Önerilen: lisanslı katalog verisi (ör. TecDoc) + yapay zekâ (doğal dil araması:
"Caddy motor triger") + kod biçimi kuralları; internet araması yedek kaynak olarak, kaynak göstererek.
