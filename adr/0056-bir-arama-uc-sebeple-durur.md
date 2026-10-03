# ADR-0056: bir arama üç sebeple durur, ikisi sonuç değildir

## Durum

Kabul edildi.

## Bağlam

Bir arama üç sebeple duruyor:

1. çıtasını tutturdu,
2. bütçesi doldu,
3. eklenecek aday kalmadı.

Yalnızca birincisi bir sonuç. Dışarıdan üçü de aynı görünüyordu: kart
"27 direk · menzil 3,82 km" yazıyor, bitmiş bir iş gibi duruyor.

Kızılay'da bu ciddi. Ölçülen menzil 478 m, saha 2970 × 2940 m, ve
adaylar yalnızca 232 monte edilebilir yapı. HDOP ≤ 2 çıtası orada hiç
karşılanamıyor, çünkü 552 hücrenin 8'ine 478 m içinde hiçbir yapı yok.
Arama bütçesi ne kadarsa o kadar direk koyup duruyor, ve koyduğu sayı
birinin "demek bu kadar direk gerekiyormuş" diye okuyacağı bir sayı
olarak kalıyor. ADR-0023'ün uyardığı şey buydu.

## Karar

**`bar_of(plan, ground, spots)`**, `yerkon.layout` içinde, saf bir
işlev. Bir düzenlemenin yöntemine sorulan şeyi tutturup tutturmadığını
söylüyor.

`place` dokunulmadı. Her yöntemin paylaştığı tek imza kalıyor (ADR-0040)
ve elle düzenlenmiş bir dizilişe de aynı soru sorulabiliyor.

**Kafes yöntemleri hiçbir şey döndürmüyor.** Bir aralık bir hedef
değildir; ızgaraya "tutturdu" demek yöntemin hiç ileri sürmediği bir
iddiayı uydurmak olurdu.

**Üç çıta, üç ölçü:** `greedy-dop` için seyreltme, `k-cover` için
erişimdeki en az direk, örtme araması için örtülen hücre payı.

**İki başarısızlık ayrı ayrı söyleniyor.** `greedy-dop` çıtasını iki
türlü kaçırır: sahanın bir kısmında hiç konum alınamıyordur, ya da her
yerde alınıyordur ve geometri yalnızca kötüdür. İlki bir kapsama
sorunu, ikincisi bir yerleştirme sorunu, ve kart hangisi olduğunu
yazıyor.

**Nerede durduğu da yazılıyor.** Bütçesi dolan bir arama daha büyük bir
bütçeyle çıtayı tutturabilir; adayı kalmayan tutturamaz. Kart hangisi
olduğunu söylüyor, çünkü kişinin bir sonra uzanacağı düğme buna bağlı.

**Çıta ayakta duranlara soruluyor**, yerleştirilenlere değil. Elle üç
direk silmek bir dizilişi çıtanın altına düşürebilir ve kart o zaman
tutturduğunu söylemeyi bırakır.

**Ve yerleştirmeyle birlikte taşınıyor.** İkinci kez sormak ikinci bir
`Plan` ve `Ground` kurmak demek, ve iki tanesi hiçbir zaman tam olarak
aynı çift olmuyor. Sahne bunu bir kez yaptı ve çizdiği altmış direğin
elli ikisini tanıdı (ADR-0049).

## Yazarken çıkan hata

Çıtayı `_seen_and_dilution` ile ölçmüştüm. O işlev, tam hücre
merkezinde duran bir direği saymıyor: ona giden birim vektör tanımsız ve
seyreltme aritmetiği ona muhtaç. "Erişimde kaç direk var" sorusu içinse
o direk apaçık onlardan biri.

Sonuç: aramanın az önce tamamlandığını ilan ettiği bir `k-cover`
dizilişi, hücre merkezine denk düşen her aday yüzünden bir direk eksik
görünüyordu, ve kart bitmiş bir aramayı bitmemiş ilan ediyordu. Çıta
artık yöntemin kendi saydığı gibi sayıyor. Bir sınama bunu çiviliyor.

## Sonuçlar

Kızılay'da, tarayıcıda:

| yöntem | kart ne diyor |
|---|---|
| Kare ızgara | (çıta yok) |
| En çok zemin örten | 27 direk · *çıta tutturulamadı: 8 hücreye hiçbir direk erişmiyor · eklenecek aday kalmadı* |
| En iyi geometri | 60 direk · *çıta tutturulamadı: sahanın bir kısmında konum alınamıyor, 252 görüş eksik · bütçe doldu, 60 direk kondu* |
| Her noktaya yeter direk | 60 direk · *çıta tutturulamadı: bir yerde erişimde 0 direk var, istenen 4 · bütçe doldu* |

Üçü de aynı sebeple kaçırıyor: o 8 hücreye 478 m içinde hiçbir yapı
yok. Modellenmiş zeminde `k-cover` k=1 ve örtme araması çıtalarını
tutturuyor, yani "tutturuldu" dalı da yaşıyor.

İngilizcesi ayrı cümleler, ikisi de tarayıcıda yürünmüş durumda.
