# ADR-0048: kol bir şey söylüyordu, saha başkaydı

## Durum

Kabul edildi.

## Bağlam

Saha boyu ve eni sürgüleri 500'er metre adımla hareket ediyordu. Ama bir
getirme yuvarlak bir sayıyla gelmiyor: Kızılay 2970 × 2940 m, Polatlı
22800 × 19860.

Sonuç: sayfa açıldığında **sürgü 2500'de, kutu 2970'te, motor 2970'te**.
Tarayıcı, ızgaraya düşmeyen değeri aşağı yuvarlıyor ve kol yalan
söylüyor. Aradaki bir değer — 2340, 1730 — hiç seçilemiyor.

Bu, bu projede daha önce iki kez yakalanmış hatanın aynısı: **bir kolun
iki yarısı farklı şey söylüyor.** Bir keresinde gri bir sürgünün yanında
canlı bir sayı kutusu vardı (ADR-0036); bu sefer sınırlanmış bir
sürgünün yanında her sayıyı kabul eden bir kutu.

## Karar

**Adım 10 m.** Sürgü her değeri tutabilir, kol her zaman gerçeği
gösterir. Getirilen zeminin tam boyu — ne çıkarsa — seçilebilir.

Alternatifleri reddettim: kaba adımı tutup yalnızca uç değeri
erişilebilir kılmak aradaki değerleri yalnızca kutudan girilebilir
bırakırdı, ve sahayı adıma yuvarlamak getirilen zeminin 470 metresini
kullanılmadan bırakırdı.

**Tavan kolun iki yarısına da konuyor.** `capSlidersToTheGround` yalnızca
sürgüye `max` yazıyordu; artık `knobInputs(key)` ile ikisine birden.

**Ölçülen zeminden büyük bir sayı yazılınca kutu yürürlükteki değere
döner.** Zaten dönüyordu — `fillControls` onu tazeliyor — ama sebebi
söylenmiyordu, ve açıklamasız geri sıçrayan bir kutu, sayfanın tuşu
kaçırdığı gibi okunuyor. Artık kolların yanında bir satır neyin
istendiğini, neyin tutulduğunu ve niçin söylüyor (ADR-0037: saha
getirilen zeminden büyük olamaz).

**O satır durum çubuğunda değil.** Önce oraya koymuştum ve bir saniye
sonra süpürmenin kendi mesajı üzerine yazdı. Durum çubuğu şu an ne
olduğu için; bu, sorunun cevabı.

## Sonuçlar

Tarayıcıda, Kızılay üzerinde:

| | sürgü | kutu | motor |
|---|---|---|---|
| açılışta | ~~2500~~ **2970** | 2970 | 2970 |
| 2340'a sürüklendi | 2340 | 2340 | 2340 |
| kutuya 9000 yazıldı | 2970 | 2970 | 2970 |

Üçüncü satırda kolların yanındaki not: *"9,00 km istendi, 2,97 km
tutuldu: saha getirilen zeminden büyük olamaz."* Bir sonraki geçerli
düzenlemede kendiliğinden kalkıyor.

En sürgüsü de aynı: 1730 m tam olarak tutuluyor, 0 koridor veriyor
(30 → 20 → 5 direk). Modellenmiş zeminde ölçüm olmadığı için tavan
40 km'ye açılıyor ve 31240 gibi bir sayı tam tutuluyor.

Sınamalar iki hatayı da, kasten geri konduklarında yakalıyor.

**Sevk edilen dört sahanın ölçüleri ona bölünüyor** — 2970, 2940, 22800,
19860 — ve bir sınama bunu çiviliyor, çünkü adım bunu varsayıyor. Bir
gün ona bölünmeyen bir ızgara gelirse sınama düşecek ve adım yeniden
düşünülecek; sessizce yuvarlanmayacak.
