# ADR-0073: tünel satırı uzunluğa bölünür

## Durum

Kabul edildi.

## Bağlam

Tablonun CAPEX sütunu kilometrekare başına kurulum maliyetini veriyor.
Üç YERKON satırının ikisi için bu doğru: şehir içi ve kırsal birer
alana hizmet ediyor.

Tünel etmiyor. 12 m genişliğinde 2 km'lik bir tünel **0,02 km²**
kaplıyor, yani bir kilometrekarenin ellide biri. Aynı toplam sermaye bu
kadar küçük bir paydaya bölününce sütunda milyonlarla ölçülen bir sayı
çıkıyordu — GPS'in 683,80'inin yanında dört bin kat. O sayı tünelin
pahalı olduğunu söylemiyordu; paydanın küçük olduğunu söylüyordu.

Site bunu zaten biliyordu. "Tabloyu okurken üç uyarı" başlığının ilk
maddesi tam olarak bunu anlatıyor ve okuyucuya "kilometre başına
maliyetle karşılaştırılmalı" diyordu. Ama tablo o dönüşümü yapmıyor,
okuyucudan yapmasını istiyordu. Bir tablonun işi okura ödev vermek
değil.

Makine de hazırdı: `Costing.capex_tl_per_route_km` ve
`Deployed.serves_a_corridor` aylardır duruyordu, ikisi de tam bu iş
için yazılmıştı, ve tablo ikisini de kullanmıyordu.

## Karar

**Bir koridor kendi uzunluğuna bölünür.** Tünel satırının iki maliyet
hücresi artık güzergâh kilometresi başına. Hangi paydanın kullanıldığını
satırın kendisi taşıyor (`Row.costed_by`), ve bunu senaryonun
`serves_a_corridor` değeri belirliyor — sayıların şekline bakıp tahmin
edilmiyor.

**Hücre kendi birimini yazıyor.** Sütun başlığı TL/km² diyor, o iki
hücre `/km` ile bitiyor. Sütun başlığını değiştirmek üç satırın ikisi
için yanlış olurdu; hücreyi işaretlemek yalnızca farklı olanı
işaretliyor.

**Alan adları yalan söylemiyor.** `Row.capex_tl_per_km2` artık
`capex_tl_per_unit`, çünkü tünel satırında km² değil. `Costing`
tarafındaki `capex_tl_per_km2` olduğu gibi kaldı: orada gerçekten
kilometrekare.

**Bir dipnot ne yapıldığını söylüyor.** Tablonun altında, diğerleri
gibi: neden bölündüğü, neyle bölündüğü, ve diğer satırlarla aynı ölçü
olmadığı.

**Maliyet grafiğinde tünel yok.** Kilometre başına bir sayıyla
kilometrekare başına bir sayı aynı eksene konmaz. Çizim onu atlıyor ve
altyazısı neden atladığını söylüyor.

## Sonuçlar

Tünelin CAPEX'i milyonlar mertebesinden, şehir içi satırınkiyle aynı
mertebeye indi. Aynı donanım, aynı sermaye; değişen tek şey neye
bölündüğü ve bunun yazılı olması.

Yayımlanan kayıt artık `costed_by` taşıyor. Bunu taşımayan eski bir
kayıt okunduğunda her satır alan kabul ediliyor, ki o kayıtlar
yazıldığında öyleydi.

Üç sınama tutuyor: tünel satırı uzunluğa bölünmüş ve hücreleri `/km`
ile işaretli, diğer ikisi değil; dipnot iki dilde tabloda; ve maliyet
çizimi kendi ekseninde olmayanı atlıyor.

## Yapılmayanlar

**Alan sütunu 0,02 km² olarak kalıyor.** Tünelin kapladığı yer o, ve
sütun alanı soruyor. Maliyet neye bölündüyse o ayrı bir sorudur.

**Şehir içi ve kırsal değişmedi.** İkisi de alana hizmet ediyor ve
ikisinin de güzergâh kilometresi bir test yolculuğunun uzunluğu,
hizmetin bir boyutu değil — `serves_a_corridor`'ın notu bunu zaten
söylüyordu.

**Rapor ve sunum değişmedi.** Tablonun bu hâli siteden alınıp rapora
taşınırsa, oradaki sütun başlığının da bunu söylemesi gerekir.
