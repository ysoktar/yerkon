# ADR-0062: bir yolun kaç metrede bir okunduğu zeminin özelliği

## Durum

Kabul edildi. ADR-0053'ün açık bıraktığı maddeyi kapatır.

## Bağlam

ADR-0053 kırınımı bütün profil üzerinden hesaplamaya başladı ve
"Yapılmayanlar" bölümüne şunu yazdı: profil 64 örnekle okunuyor, 1,2
km'de aralık ~19 m, daha sık örneklemek cevabı değiştirir ve ne yönde
ölçülmedi.

Ölçtüm. Her satırdan altmış bağlantı, örnek sayısı ikiye katlanarak:

| satır | ortanca mesafe | 64 örnek | 1024 örnek | fark |
|---|---|---|---|---|
| Kızılay | 989 m | 39,50 dB | 40,32 dB | +0,83 |
| Polatlı | 6884 m | 31,28 dB | 37,60 dB | **+6,32** |
| tünel | 405 m | 0,00 dB | 0,00 dB | 0,00 |

Yön tek. Bullington'ın kurgusu örnekler üzerinden bir maksimum alıyor,
yani hiç alınmamış bir örnek cevabı düşüremez, ancak yükseltebilir.
Eksik örnekleme yalnızca eksik okur.

Ve büyük fark kırsalda, çünkü **sabit bir örnek sayısı aralığı
bağlantının boyuna bağlıyor**. 64 örnek 989 m'de 15,5 m aralık demek,
6884 m'de 107,6 m. İkincisi, hücreleri 30 m olan bir Copernicus
ızgarasının üzerinde: veride duran bilgi atılıyordu.

Bir örnek sayısı bir zemin modelinin özelliği değil. Bir aralık öyle.

## Karar

**`Terrain.profile_spacing_m`**, metre cinsinden, 32 örnek tabanı ve
2048 tavanıyla. Sıfır, çağıranın istediği sabit sayıyı bırakıyor, yani
ayrımdan önceki davranış (ADR-0035).

**Varsayılan 10 m.** 30 m'lik hücrenin içine üç örnek düşürüyor ve
yakınsamanın 0,3 dB altında kalıyor. Yirmi yedi metre 6,32 dB'lik
farkın yalnızca üçte ikisini kapatıyordu.

**Profil tek geçişte okunuyor.** Bir engel sorgusunun %84'ü profili
okumaktı ve bunun neredeyse tamamı aritmetik değil çağrı giderleriydi.
Her zemin türü artık bütün bir çizgiyi birden cevaplıyor (`along`),
raster ve binalar dahil. Cevap birebir aynı, bir sınama bunu her zemin
türü için çiviliyor.

## Sonuçlar

Kırsal engel sorgusu 25,9 ms'den 2,75 ms'ye indi, 9,4 kat.

| | 64 sabit | 10 m aralık |
|---|---|---|
| şehir HPE P95 | 8,78 m | **8,19 m** |
| şehir kullanılabilirlik | %80,08 | **%79,88** |
| şehir alan | 6,84 km² | **6,68 km²** |
| kırsal HPE P95 | 31,77 m | **22,72 m** |
| kırsal kullanılabilirlik | %51,80 | **%41,83** |
| kırsal alan | 175,67 km² | **143,75 km²** |
| ağırlıklı HPE P95 | 14,28 m | **13,44 m** |
| tablo süresi | 4 dk 46 sn | **15 dk 33 sn** |

Kırsal satır on puan kullanılabilirlik ve otuz iki km² alan kaybetti.
Kaybı kabul etmenin sebebi yönü: eski varsayılan kırınımı eksik
okuduğu için kapsamayı *fazla* gösteriyordu, yani sistemi kayırıyordu.
Yayımlanan bir tablo bilerek kayırdığı bir sayı taşıyamaz.

P95'in 31,77'den 22,72'ye *iyileşmesi* bir çelişki değil, aynı mekanizma:
düşen bağlantılar en kötüleri, düşünce kuyruk kısalıyor. Kullanılabilirlik
ve alan sütunları ne olduğunu söylüyor.

Süre üç buçuk kat arttı ve vektörleştirme olmasaydı altı kat artacaktı
(27 dk 17 sn ölçüldü). İkisi de geri alınabilir: `site.profile_spacing_m`
sıfır, `site.shadow_draws` bir.

## Aynı iddia üçüncü kez ölçüldü

`test_how_long_a_rural_round_runs...` tur uzunluğunun ne kadar değdiğini
tutuyor ve bu karar onu üçüncü kez oynattı:

| model | on direk kaç tohumda kazanıyor | ortalama | yayılım | oran |
|---|---|---|---|---|
| tek gölge genişliği | 5/8 | +0,0080 | 0,0200 | 0,4 |
| yola göre ayrılmış (ADR-0061) | 8/8 | +0,0227 | 0,0069 | 3,3 |
| ve profil on metrede bir | 7/8 | +0,0088 | 0,0055 | 1,6 |

Sınama üç kez yeniden yazıldı çünkü her seferinde *boyu* çiviliyordu.
Üçünde de duran şey şekli: etki artı yönde ve tohumdan tohuma saçılımla
aynı mertebede, yani tek bir koşu ikisinden hiçbirine karar veremiyor.
Sınama artık bunu çiviliyor, bir bandla: etki saçılımın beşte biriyle
beş katı arasında. Bandın dışına çıkmak bir bulgu, bozuk bir sınama
değil.

## Yapılmayanlar

**On metre bir yakınsama noktası, bir çözünürlük değil.** Yüzey 30 m'lik
bir ızgaranın iki doğrusal ara değeri, ve on metrede örneklemek o
yüzeyin maksimumunu daha iyi buluyor. Gerçek zeminin 10 m'de ne yaptığı
başka bir soru ve bu veri onu cevaplamıyor.

**Tavan 2048 bağlayıcı.** 20 km'lik bir bağlantı 9,8 m yerine 9,3 m
aralıkla okunuyor, ki fark yok; ama 40 km'lik bir bağlantı 19,5 m'ye
düşerdi. Bu projenin satırlarında böyle bir bağlantı yok.

**Süre hâlâ profilde değil.** Vektörleştirmeden sonra 15 dk 33 sn'nin
çoğu benzetimin geri kalanı. Daha hızlı bir tablo istemek başka bir işin
konusu.
