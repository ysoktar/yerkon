# 0001. Tek motor, birçok ön yüz

## Durum
Kabul edildi.

## Bağlam
Önceki kod tabanı aynı fiziği koşmanın dört yolunu büyüttü: bir toplu tablo
üreteci, bir avuç gelişigüzel tarama betiği, bir MATLAB dalga formu
çalışması ve bir çalışma klasöründe tutulan bir yığın karşılaştırma parçası.
Belgelerdeki sayılar en son hangisi koştuysa ondan geliyordu ve ikisi,
hiçbir şey düşmeden birbiriyle çelişiyordu.

## Karar
Her sayıyı tek bir motor üretir. Bir tohum ve bir senaryo verildiğinde
belirlenimlidir ve yalnızca bir özet değil, tipli bir olay akışı yayar.

Geri kalan her şey o akışı tüketir:

- tablo üreteci onu yüzdeliklere ve maliyetlere indirger,
- 3B görüntüleyici onu yeniden oynatır,
- deneyler senaryo değiştirgelerini tarar ve birçok akışı indirger,
- gerileme testleri onun üzerinde savda bulunur.

Bir ön yüz fizik hesaplayamaz. Bir görüntüleyicinin bir bağlantının neden
düştüğünü göstermesi gerekiyorsa, sebebi olaya motor koyar.

## Sonuçlar
Görüntüleyici tablodan ayrı düşemez, çünkü ikisi de aynı koşumu okur. Bir ön
yüz eklemek fizik tarafında hiçbir şeye mal olmaz. Bedeli şudur: olay akışı
artık bir arayüzdür — alan eklemek ucuzdur, bir alanın anlamını değiştirmek
değildir.
