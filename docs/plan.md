# ParçaLink – plan (1 Kasım 2026)

## Hedef
Parça işini kolaylaştıran, ticari olarak satılabilecek Windows masaüstü programı (.exe), birkaç bilgisayarda çalışır.

İki arama yönü:
1. **OEM kodu → uyan araçlar.** OEM kodu yazılır (ör. 5G0959855), program parçanın uyduğu araçları getirir:
   marka, model, kasa, motor kodu, beygir, yakıt, şanzıman, yıllar. Liste tek tuşla kopyalanır.
2. **Araç + parça adı → OEM kodu.** "Caddy motor triger" gibi yazılır, program o aracın o parçasının OEM kodunu
   (kodlarını) getirir.

## Kullanıcının cevapları (1 Kasım 2026)
- Bilgi kaynağı: parça kodu internette bir arama motorunda aranacak.
- Araç ve motor kodu, Claude'un hazırladığı araç Excel'inden (Arac_Listesi.xlsx) bulunup eşleştirilecek.
- Yazılacak kod: OEM kodu.
- İnternet: veriyi doğru getirecekse internetle çalışabilir.
- Birkaç bilgisayar; ileride ticari satış düşünülüyor.
- Arkada bir yapay zekâ modeli çalışacak.
- Uyan araçlar kopyalanabilecek.
- **Sonuçta her zaman yıllar yazar** (marka, model, kasa, yıllar). **Motor parçasıysa** ek olarak motor kodu ve motor hacmi (1.6 / 2.0 vb.) yazar; aynı modelin hangi motoruna uyduğu ayrılır.
- **Web sitesi değil, masaüstü programı** (kendi penceresi olan .exe). Arka plandaki sunucu kullanıcıya görünmez; sadece anahtarları ve lisansı tutar.

## Nasıl çalışacak (önerilen yapı)
```
[ParçaLink.exe]  --(OEM kodu / "Caddy motor triger")-->  [ParçaLink sunucusu]
                                                            |-- arama motoru servisi (web sonuçları)
                                                            |-- yapay zekâ: sayfalardan araç ve kod bilgisini çıkarır
                                                            |-- araç listesiyle eşleştirme (motor kodu, yıllar)
[ParçaLink.exe]  <--(uyan araçlar + her birinin kaynağı + güven derecesi)--
```
- **Neden arada sunucu var:** Arama ve yapay zekâ servislerinin anahtarları (ücretli) exe'nin içine konursa
  programı alan herkes onları çıkarabilir. Anahtarlar sadece sunucuda durur; exe sunucuya sorar. Lisans
  (hangi bilgisayar kullanabilir) da sunucuda kontrol edilir.
- **Doğruluk:** İnternetteki bilgi her zaman doğru değildir, yapay zekâ da hata yapabilir. Bu yüzden her araç
  satırında **kaynağı** (hangi siteden geldiği) ve **güven derecesi** gösterilir; birden fazla bağımsız kaynakta
  geçen eşleşme "doğrulandı", tek kaynakta geçen "kontrol edin" diye işaretlenir. Program "kesin uyar" demez.
- **Önbellek:** Bir kez bulunan OEM kodu sunucuda saklanır; aynı kod tekrar arandığında hızlı ve ücretsiz gelir.

## Riskler ve dikkat
1. **Araç listesinin doğruluğu:** Arac_Listesi.xlsx'in bir kısmı Claude'un hafızasından, doğrulanmamış.
   Ticari satıştan önce kontrol edilmeli.
2. **Veri hakları:** Ticari satışta kullanılan verinin (araç listesi, arama sonuçlarından alınan bilgiler) izinli
   olması gerekir. Sitelerin içeriği toplu kopyalanıp satılamaz; sonuçlar kaynak gösterilerek, arama anında
   özetlenmeli. TecDoc gibi lisanslı kaynak en sağlam yol. Satış öncesi hukukçuya danışılmalı.
3. **Maliyet:** Arama servisi ve yapay zekâ arama başına ücretli. Önbellek maliyeti düşürür. Satış fiyatı buna göre
   belirlenir.

## Aşamalar
1. **Doğruluk denemesi (exe'den önce):** Kullanıcının uyumunu bildiği 10 gerçek OEM kodu ile sistem denenir;
   doğru, yanlış, eksik sayılır. Sonuç iyi değilse yöntem değişir. Bu aşamada exe yok, sadece deneme.
2. **Sunucu:** arama + yapay zekâ + araç listesi eşleştirmesi + önbellek.
3. **Masaüstü program (.exe):** arama kutusu, sonuç tablosu, kaynak ve güven derecesi, "Kopyala" tuşu.
   GitHub'ın Windows makinesinde derlenir.
4. **Ticari hazırlık:** lisans ve bilgisayar sınırı, güncelleme, kullanım sözleşmesi.

## Açık sorular
1. Doğruluk denemesi için (gelen: 5G0959855 – Golf 7, Passat B8, Tiguan 2; en az 9 kod daha, motor parçaları dahil) uyumunu kesin bildiğiniz **10 OEM kodu** ve uyan araçları.
2. Sunucu nerede olacak? (Kartal için alınacak hosting ayrı projedir; ParçaLink için ayrı karar.)
3. Arama servisi ve yapay zekâ hesapları kullanıcı adına açılacak; anahtarları sadece kullanıcı sunucuya girer.

## Yapılanlar
- 1 Kasım 2026: Depo açıldı (gizli), kurallar ve plan yazıldı.
- 1 Kasım 2026: Kullanıcı cevapları işlendi, yapı ve aşamalar yazıldı.
- 1 Kasım 2026: Doğruluk denemesi 1 (7 kod): model %73, motor kodu %17 – ayrıntı `docs/test-1.md`.
