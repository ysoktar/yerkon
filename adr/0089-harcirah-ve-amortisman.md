# ADR-0089: harcırah ve amortisman resmî kaynaklardan

## Durum

Kabul edildi.

## Bağlam

İşletme maliyetinde iki kalem varsayımdı: bir yayın biriminin kaç yılda
yenilendiği (8 yıl) ve bakım ziyaretinin bedeli (1800 TL; ekip, araç,
trafik). Proje sahibi harcırah ve amortisman değerlerinin resmî
kaynaklardan kullanılmasını istedi. Değerler resmî kurum ve üretici
kaynaklarından derlendi (7567 sayılı Kanun H Cetveli, GİB amortisman
listesi).

## Karar

**Amortisman (GİB amortisman listesi).** Yenileme kalemi her parçayı
kendi faydalı ömrüne bölüyor:

| Parça | Liste satırı | Ömür |
|---|---|---|
| Yayın birimi (telsiz sistemi) | 3.49.4 | 10 yıl |
| Akü | 3.14.7 | 5 yıl |
| Panel, denetleyici, tutucu, kablo | 45.1.9 (güneş enerjisi santrali; tek panel satırı yok) | 10 yıl |

Konum belirleme satırı (3.49.8, 5 yıl) uydu ile konum belirleyen
cihazlar için; yayın birimi uyduya dayanmıyor, bu yüzden telsiz satırı
alındı. Şebeke dışı ek ziyaret, akünün beş yıllık ömrüne uyarak yılda
0,25'ten 0,2'ye indi.

**Harcırah (7567 sayılı Kanun, H Cetveli).** Şehir dışına giden bakım
ekibinin her ziyaretine kişi başı 850 TL gündelik ekleniyor (B-e, 5-15.
derece). Özel sektörde vergiden istisna kısım GVK 24/2'ye göre aynı
aylık seviyesindeki devlet memurunun gündeliği; saha teknisyeni için en
yakın seviye 5-15. derece varsayıldı. Ekip iki kişi (varsayım).
Konaklama yok: iki saha da günübirlik uzaklıkta.

Ekip Ankara merkezde. Şehir içi (Kızılay) şehir dışı değil; kırsal
(Polatlı, yaklaşık 80 km) ve tünel (Kızılcahamam, yaklaşık 70 km) şehir
dışı sayıldı (`<satır>.crew_travels`).

**Doğrulanmayanlar.** Günübirlik görevde gündeliğin tamamı mı bir kısmı
mı ödendiği; büyükşehir içindeki bir ilçenin Harcırah Kanunu'nda görev
yeri dışı sayılıp sayılmadığı. İkisinde de maliyet açısından ihtiyatlı
taraf alındı (tam gündelik, şehir dışı).

## Sonuçlar

| Satır | OPEX önce (TL/yıl) | OPEX şimdi | Fark |
|---|---|---|---|
| Şehir içi | 17484 | 17035 | birim ömrü 10 yıl |
| Kırsal | 128919 | 156665 | harcırah +33320 |
| Tünel | 6714 | 9528 | harcırah +3060 |

- Harcırah kırsal ve tünelde işletmeyi artırıyor. Onu kaldıran şey
  yerel ekip: Polatlı'da dağıtım şirketinin kendi ekipleri, tünelde
  Karayolları'nın bakım ekibi. Ziyaret o ekiplere verilirse harcırah
  kalemi sıfırlanır.
- CAPEX değişmiyor.
