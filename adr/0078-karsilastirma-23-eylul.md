# ADR-0078: karşılaştırma tablosu 23 Eylül belgesine göre

## Durum

Kabul edildi.

## Bağlam

Diğer sistemlerin satırları için 23 Eylül 2026 tarihli bir araştırma
belgesi geldi. Belge YERKON satırlarını bilerek boş bırakıyor; diğer on
satırı yeniden kontrol ediyor ve birçok hücreyi değiştiriyor.

## Karar

**Uydu sistemlerinin alan paydası kara oldu.** Dünyanın bütün yüzeyi
(510064472 km²) yerine okyanuslar ve denizler çıkarılmış kara yüzeyi,
yaklaşık 148940000 km². YERKON karada kurulduğu için aynı payda. GPS,
Galileo, GLONASS ve BeiDou'nun maliyet hücreleri bu yüzden yaklaşık 3,4
kat büyüdü (GPS CAPEX 683,80 → 2341,76 TL/km²). Dipnot bunun hizmet
alanını karayla sınırlamadığını ve karada GNSS'nin kesin kullanılamadığı
tek bir alanın çıkarılamayacağını söylüyor.

**Tasarım eşikleri yerine gerçekleşen ölçümler.** Galileo Q2 2026
(1,41 / 2,40 m, %99,58), BeiDou iGMAS (1,52 / 2,64 m), QZSS FY2025
ikinci yarı (1,70 / 2,73 m, %99,996). Eşikler dipnotta duruyor.

**NavIC boş.** 29 Temmuz 2026 itibarıyla konum sağlayan üç uydu var,
bağımsız çözüm için dört gerekiyor.

**Karasal satırlarda karışmış testler ayrıldı.** TerraPoiNT'in yatayı
tek bir ION testinden; Locata'nın kullanılabilirliği ölçülmüş bir
günlük %100, öngörülen %99,9999 değil; eLoran'ın teorik üç daire alanı
kaldırıldı.

**Belgedeki binlik noktaları yazılmadı.** Sayılar sitenin kuralıyla:
virgül ondalık, binlik ayırıcı yok (148940000, 2341,76).

**"PNT" hiçbir satırda yok.** ADR-0066 YERKON satırlarından kaldırmıştı
ama TerraPoiNT, Locata ve eLoran'ın teknoloji hücreleri ile kaynakçadaki
Koreli derginin kısaltması hâlâ yazıyordu. Belge de "Karasal alternatif
PNT" diyordu. Teknoloji hücreleri "konumlandırma" diyor, dergi adıyla
yazılıyor, ve bir sınama sitenin hiçbir sayfasında bunu yakalıyor.

## Yapılmayanlar

**YERKON satırları bu kararın konusu değil.** Onlar koşudan geliyor ve
maliyetleri ayrı bir kararla (ADR-0079) yeniden kuruldu.

**Kaynaklar yeniden açılıp okunmadı.** Bu oturumun ağ politikası
kaynak sitelerine erişimi kapatıyor; değerler belgeden alındı, belgenin
kendi kontrolüne dayanıyor.
