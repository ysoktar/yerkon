# ADR-0102: doğrulanmış kademe fiyatı küçük adette taban

## Durum

Kabul edildi (proje sahibinin sorusu, 28 Eylül 2026: birim fiyat 1000
adet mi 100 adet mi?).

## Sorun

Sitede 100 adetlik fiyat 1000 adetlikten ucuz çıkıyordu (şehir içi ve
kırsal birim 1211,07 ile 1365,12 TL). 100 adet, eski raporun 1'den 100'e
indirimiyle tahmin ediliyordu. 1000 adet ise satıcıların doğrulanmış
kademe fiyatlarını kullanıyordu (ADR-0093) ve bu fiyatlar raporun
indiriminden pahalı. Ayrıca DWM3000 ile ESP32-S3'ün doğrulanmış 10 ve
1300 adetlik fiyatları, tek adet için yazılı fiyattan yüksekti. Bu yüzden
tünel birimi 1000 adette tek adetten pahalı görünüyordu.

## Karar

Bir parçanın doğrulanmış kademe fiyatı o kademeden büyük her adette
kullanılır. Daha küçük adette bu fiyat bir tabandır: bir parça az
alındığında çok alındığından ucuz olamaz. Kademesi doğrulanmayan parçalar
ve "diğer" satırı eskisi gibi raporun indirimiyle (1000 adette 100
adetlik fiyatın %90'ı) hesaplanır.

## Sonuç

1000 adet fiyatları, dolayısıyla maliyet tablosu, değişmedi. 1 ve 100
adet değişti; artık her üründe 1 > 100 > 1000.

| Ürün | 1 adet | 100 adet | 1000 adet |
|---|---|---|---|
| Şehir içi ve kırsal yayın birimi | 1733,44 | 1211,07'den 1417,55 | 1365,12 |
| Kritik bölge (tünel) yayın birimi | 1662,69'dan 1952,38 | 1212,43'ten 1744,09 | 1691,48 |
| Yaya alıcısı | 2987,03'ten 3282,63 | 2379,86'dan 2910,70 | 2724,32 |
| Kara aracı alıcısı | 4382,14'ten 4671,84 | 3371,06'dan 3970,85 | 3611,14 |

Sunum ve formdaki birim fiyatlar 1000 adetlik sayılara (1365-1691 TL)
çekilecek. Pilotun tek adet fiyatlarıyla ana bileşen tutarı 10 x 1733,44
+ 3282,63 + 4671,84 = 25288,87 ile 15 x 1952,38 + 3282,63 + 4671,84 =
37240,17 TL arası.
