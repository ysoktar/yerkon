# ADR-0047: aramanın çıtası bir sayının üç kopyasıydı

## Durum

Kabul edildi.

## Bağlam

ADR-0046'nın sonunda açık bir soru bırakmıştım: geometriye göre seçen
arama Kızılay'da dört direk koyuyor ve hizmet alanı 8,92 km²'den
**0,08 km²**'ye düşüyordu. Sebebini "arama üç görüş hedefliyor, alan
sütunu dört sayıyor" diye yazmıştım. Doğruydu — ama üç ayrı hatanın
yalnızca birincisiydi.

## Karar

**Bir: üç bir aritmetik özelliği, dört bir gereksinim.**

`dilution_at` iki bilinmeyenli bir matris çeviriyor — x ve y, çünkü iki
yollu menzil ölçümü saat sütunu bırakmıyor (ADR-0010) ve düşey yoldan
gözlenemiyor (ADR-0011). Üç menzil, o matrisin anlamlı olduğu ilk sayı.
Bu, altındaki aritmetiğin bir özelliği.

Bir *yerleşimin* ihtiyacı ise dört, ve bunu proje zaten iki yerde
**reddederek** söylüyor: `coverage()` ve `siting.Requirement`, ikisi de
"fewer than four ranges cannot place a point" diye yükseliyor. Alan
sütunu `area_reached_by(4)`.

Arama birincisini ikincisi yerine kullanıyordu — yani kendi
kestiricisinin konum üretemeyeceği bir sayıda "bitti" diyordu. İki sabit
oldu: `FEWEST_FOR_A_FIX = 3` ve `ENOUGH_TO_BE_SERVED = 4`.

**İki: aynı sayı üçüncü bir yerde de yazılıydı, ve o kazanıyordu.**

`AnchorRun.cover_k` 3 diyordu, `layout.Plan.cover_k` 4. Bir koşu kendi
değerini `place`'e taşıdığı için görüntüleyicinin kopyası sessizce
kazanıyordu. Sonuç: şehir içi k-cover üçe örtüyor, sütun dört sayıyor,
hizmet alanı **iki sahada da 0,00 km²**.

**Üç: arama, kodun kendisinin "bir iddia değil" dediği rakama karar
verdiriyordu.**

`reach_of`'un kendi belgesi şöyle: *"düz arazi rakamı, halka olarak
çizilir… halka bir sezgidir, bir iddia değil."* Bir halka için doğru, bir
karar için yanlış — ve aramalar onu sert bir kenar gibi kullanıyordu.

Ölçtüm. Kızılay'da halka **3825 m** diyor; gerçek link bütçesini gerçek
arazi üzerinde örneklediğimde kapanan en uzak link **1937 m**, ve
1 km'den sonra linklerin yarısı kapanmıyor. Arada 5231 bina var.

Aramalar artık **üzerinde durdukları zeminde ölçülmüş** bir menzil
alıyor: sahanın ortasından iki yüz ışın, gerçek bütçeden geçiyor, ve
cevap ondan dokuzunun hâlâ kapandığı son bandın dış kenarı. Ölçülüyor,
bir kuralla indirgenmiyor — önemli olan sayı bütçenin *bu* binaların ve
*bu* rölyefin üzerinde ne yaptığı, ve bütçe zaten orada.

| | halka | zeminde ölçülen |
|---|---|---|
| Kızılay | 3825 m | **478 m** |
| Gölbaşı, şehir içi | 3825 m | 1434 m |
| Polatlı | 5521 m | 1380 m |
| modellenmiş, az rölyefli | 5521 m | 3450 m |

Son satır denetim: üzerinde duran bir şey olmayınca ölçülen rakam açık
arazi rakamına geri yaklaşıyor.

Halka açık arazi rakamını koruyor ve ne olduğunu söylemeye devam ediyor.
Bir kafes diski hiç okumaz, dolayısıyla yalnızca aramalar değişiyor
(`layout.SEARCHES`). Maliyeti bir kez 80 ms, sonrası hatırlanıyor.

## Sonuçlar

Dört yerde denendi.

| | önce | sonra |
|---|---|---|
| Kızılay, greedy-dop | 0,08 km² | **8,60** |
| Kızılay, k-cover | 0,00 | **8,56** |
| Kızılay, greedy-coverage | 0,00 | **8,68** |
| Gölbaşı şehir, greedy-dop | 1,88 | **41,24** (23 direk) |
| Gölbaşı şehir, k-cover | 0,00 | **19,12** |
| Gölbaşı kırsal, greedy-coverage | 9,25 | **92,25** |
| Polatlı, k-cover | 61,75 | 64,25 |

Kızılay'da ızgara 36 direkle 8,92 km² veriyor; üç arama da aynı zemini
veriyor. Gölbaşı şehir içinde arama **23 direkle 41,24 km²** veriyor,
ızgaranın 36 direkle verdiği 29,64'ten iyi — aramanın var olma sebebi
tam olarak bu.

**Sınamaları yazmak sınamaların zayıflığını buldu.** İlk yazdığım üçün
ikisi, test ettikleri sabiti okuyordu; hatayı kasten geri koyunca
geçmeye devam ettiler — hatayı yakalamak yerine onunla birlikte
kaydılar. Artık `coverage()`'ın kendi reddine ve düz yazılmış bir dörde
bağlılar, ve davranış sınaması **erişimin sahadan büyük olduğu** zeminde
koşuyor, ki hata o koşulda ısırıyor. Üçü de hata geri konunca düşüyor.

## Kapatmadığım iki şey

**`greedy-coverage` hâlâ işe yaramaz bir yerleşim üretebiliyor.**
Gölbaşı şehir içinde üç direk koyup 0,00 km² hizmet veriyor. Bu bir hata
değil, MCLP'nin tanımı: "en az bir direğin eriştiği zemini büyüt" diye
puanlıyor ve konumlandırmayı hiç sormuyor. ADR-0040 zaten bunu söylemek
için var ve düzeltmek bulguyu silmek olurdu. Ama arayüzde seçilebilen ve
işe yaramaz bir sonuç veren bir seçenek olarak duruyor.

**Arama çıtasına ulaşamadığında bunu söylemiyor.** Kızılay'da 478 m'lik
bir diskle HDOP ≤ 2 çıtası hiç karşılanmıyor; arama bütçesi bitene ya da
adayları tükenene kadar gidiyor (232 direkte duruyor, ki bu tam olarak
sahadaki monte edilebilir yapı sayısı). Çıtayı karşılayıp duran bir arama
ile karşılayamayıp bütçesini döndüren bir arama dışarıdan aynı görünüyor
— ADR-0023'ün tam olarak uyardığı şey. Bunu söylemek ayrı bir iş.
