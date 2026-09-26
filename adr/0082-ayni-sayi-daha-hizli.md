# ADR-0082: aynı sayılar, daha kısa sürede

## Durum

Kabul edildi.

## Bağlam

Test takımı 50 dakika sürüyordu. En yavaş testler bir tabloyu ya da bir
satırı baştan koşturuyordu. Bir kırsal simülasyonun profili zamanın
nereye gittiğini gösterdi: bağlantı bütçesinin arazi hesabında, profil
noktaları üzerinde dönen Python döngüleri.

- `bullington_db` (ITU-R P.526 kırınımı) her profil noktası için ayrı bir
  fonksiyon çağrısı yapıyordu.
- `obstruction_between` en kötü noktayı ve doğrudan ışının kesilip
  kesilmediğini yine nokta nokta arıyordu.
- `Road.length_m` her çağrıda bütün yolu yeniden ölçüyordu; bir yolculuk
  bunu binlerce kez soruyor.
- `Road._ground_point` bir noktayı bulmak için yolu baştan yürüyordu.
- Profil bir çiftler listesi olarak üretiliyor, diziye, sonra yine çiftlere
  ve yine diziye çevriliyordu.
- `tallest_at_many` binası olmayan hücreler için de tek tek soruyordu.

## Karar

**Aynı aritmetik, aynı sırada, diziler üzerinde.** Her satır yerini
aldığı skaler ifadenin işlemlerini aynı sırayla yapıyor. IEEE 754 çift
duyarlıkta dört işlem ve karekök doğru yuvarlanıyor, numpy'da da
Python'da da. Bu yüzden sonuç son bitine kadar aynı. Toplamlar
`np.cumsum` ile, yani döngünün eklediği sırayla birikiyor; `np.sum`
kullanılmadı, çünkü o ikili toplama yapıyor ve son biti değiştirebilir.
En küçük değerin yeri `np.argmin` ile bulunuyor; o da döngü gibi ilk
en küçüğü döndürüyor.

**Yol bir kez ölçülüyor.** Uzunluk ve bölüm tablosu yolun üzerinde
önbellekte duruyor (`cached_property`). Bölüm, döngünün topladığı sırayla
toplanmış bitiş mesafeleri üzerinde ikiye bölerek aranıyor, böylece
döngünün durduğu bölüm bulunuyor.

**Profil bir kez dizi oluyor.** `_profile_arrays` kesirleri ve
yükseklikleri dizi olarak veriyor. `Obstruction` bu diziyi
`profile_array` olarak taşıyor; eşitlik ve yazdırma bu alanı görmüyor,
bağlantı bütçesi varsa onu, yoksa çiftleri kullanıyor.

**Binası olmayan hücreler tek adımda eleniyor.** Bina dizininin yanında
dolu hücrelerin yoğun bir ızgarası duruyor; yalnız dolu hücrelere düşen
noktalar tek tek soruluyor.

**Taramanın hücreleri taramadan ayrı.** `sweep_axes` bir kapsama
taramasının gezeceği hücreleri, bağlantı bütçesini koşturmadan veriyor.
Arazi ağının taramayı kapsadığını soran test artık bunu soruyor.

## Doğrulama

- Üç satırın kısaltılmış yolculukları, bir kapsama taraması, yerleşim
  aramasının erişim satırları ve üç yüz gerçek bağlantı için bir önceki
  kodun çıktısı kaydedildi; yeni kodun çıktısı `np.array_equal` ile
  aynı.
- `tests/test_exact_rewrites.py` eski döngüleri olduğu gibi saklıyor ve
  yeni kodu onlara `==` ile bağlıyor: rastgele profiller, Kızılay'ın
  gerçek zemini, yolların her noktası ve bölüm birleşim yerleri. Bir
  toplamanın parantezini değiştirmek (matematikte aynı, yuvarlamada
  farklı) bu testi kırıyor; bu denendi.

## Sonuç

Bir kırsal simülasyon 9,8 s'den 4,0 s'ye indi. Hiçbir yayımlanmış sayı
değişmedi, değişemez de: değişseydi yukarıdaki test kırılırdı.

Test tarafında üç düzenleme daha yapıldı: tünel ile şehri karşılaştıran
üç test aynı iki koşuyu paylaşıyor; iki kez koşunca aynı tabloyu veren
test kaba okumayla koşuyor; gölgesiz bir satırın her çekilişte aynı
olduğunu gösteren test bir dakikalık yolculuk kullanıyor.
