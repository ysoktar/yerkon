# ADR-0060: çıta tutmak çalıştığı anlamına gelmez

## Durum

Kabul edildi. ADR-0056'nın arama çubuğunu genişletir.

## Bağlam

Gölbaşı'nda `greedy-coverage` üç direk koydu, çubuğu tutturdu, ve
hizmet alanı 0,00 km² çıktı. Kart "çıta tutturuldu" yazıyordu.

Yöntem bozuk değil. `greedy-coverage` Maximal Covering Location
Problem'in açgözlüsü ve sorduğu şey bir paketin varması: **bir** direk.
Bir konum ise **dört** direk istiyor (`ENOUGH_TO_BE_SERVED`, ADR-0047).
Menzilin sahayı tek diskle örttüğü bir yerde ilk direk bütün hücreleri
kapsıyor, `covered.all()` doğru oluyor, arama duruyor, ve hiçbir
hücrede dört direk yok.

Bunu bir fikstürde yeniden ürettim. 3 km'lik kare saha, 3 km menzil:

| yöntem | direk | çubuk | tuttu | dört direğin eriştiği pay |
|---|---|---|---|---|
| greedy-coverage | 1 | kapsanan pay 1,00/1,00 | evet | **0,00** |
| greedy-dop | 4 | HDOP 1,47/2,00 | evet | 1,00 |
| k-cover | 4 | erişimde 4/4 | evet | 1,00 |

Üçü de "çıta tutturuldu" diyordu.

## Karar

**Yöntem değişmiyor, çubuk ne hizmet verdiğini taşıyor.**

`greedy-coverage`'ı dörde çevirmek onu `k-cover` yapardı ve iki yöntemi
karşılaştırma imkânını yok ederdi; modül bu yöntemi tam da farkı
ölçülebilsin diye tutuyor (ADR-0040). Değişen, çubuğun tek bir sayı daha
taşıması:

```python
served_share: float = 0.0
```

Aramanın kendi hücrelerinde `ENOUGH_TO_BE_SERVED` direğin eriştiği pay,
çubuk neyin üzerineyse olsun. Üç arama için de aynı biçimde sayılıyor,
yani üçü aynı ölçüyle okunuyor.

**Kart bunu her zaman yazıyor**, çıta tutmuş olsun olmasın:

```
çıta tutturuldu · ama hiçbir yerde dört direk yok: bu düzenleme konum vermez
çıta tutturulamadı: ... · bütçe doldu, 60 direk kondu · dört direğin eriştiği pay %12
```

**Sıfıra yuvarlanan bir pay rakamla değil kelimeyle yazılıyor.** Kızılay'da
`greedy-coverage` kendi hücrelerinin %0,36'sına hizmet veriyor ve "%0"
bir yuvarlama gibi okunurdu.

## Sonuçlar

Tarayıcıda yürüdüm. 1,5 km'lik saha, 6 km menzil, `greedy-coverage`: tek
direk, çubuk tuttu, ve kart

> çıta tutturuldu · ama hiçbir yerde dört direk yok: bu düzenleme konum
> vermez

diyor. Bildirilen durumun kendisi.

Yayımlanan tablo oynamadı: üç satır da kafes yöntemi kullanıyor ve
kafesler çubuk taşımıyor.

## Yapılmayanlar

**Pay aramanın kaba alanında sayılıyor, yayımlanan alanda değil.**
Aramanın puanladığı hücreler bir öneri, ve yayımlanan alan `coverage()`
ile gerçek bütçe ve zemin üzerinde ölçülüyor. İki sayı yakın ama aynı
değil, ve kart hangisi olduğunu yazmıyor.

**`greedy-coverage` hâlâ işe yaramaz bir düzenleme üretebiliyor.** Kart
artık bunu söylüyor, ama arama yine de duruyor. Bir konum veremeyen bir
düzenlemeyi hiç önermemek başka bir karar ve bu yöntemin ne olduğuyla
çelişiyor.
