# Anten ve belgelendirme seçenekleri: fiyat ve performans

25 Eylül 2026 (fiyatlar ve uyarlamalı FHSS satırları güncellendi). Hepsi tam çözünürlükte (sekiz gölge çekilişi, 10 m
profil), SX1280'in resmî duyarlılığıyla (-118 dBm, ADR-0091), A
seçeneği (görüş dışı yanlılık yok), harita yükseklik kısıtı, yerel bakım
firması. Tünel UWB ile ölçüyor, hiçbir seçenek onu değiştirmiyor.

## Seçenekler

| | Direk anteni | Araç anteni | Türkiye kuralı | Telsiz modülü |
|---|---|---|---|---|
| O1 | baskılı W24P-U, 3,2 dBi | baskılı W24P-U, 3,2 dBi | 12,1 dBm (yoğunluk sınırı) | E28-2G4M12S |
| O2 | 5 dBi çubuk (AIR802 ANRD2405-SMA) | 5 dBi çubuk | 12,1 dBm | E28-2G4M12S |
| O3 | 8 dBi (L-com HGV-2409U) | 5 dBi çubuk | 12,1 dBm | E28-2G4M12S |
| **O4 (bugün)** | 12 dBi (TP-Link TL-ANT2412D) | 8 dBi (L-com HGV-2409U) | 12,1 dBm | E28-2G4M12S |
| O5 | baskılı, 3,2 dBi | baskılı, 3,2 dBi | **uyarlamalı FHSS belgesi: 20 dBm** | direk ve araçta E28-2G4M27S |
| O6 | 5 dBi çubuk | 5 dBi çubuk | uyarlamalı FHSS belgesi: 20 dBm | E28-2G4M27S |
| O7 | 12 dBi | 8 dBi | uyarlamalı FHSS belgesi: 20 dBm | E28-2G4M27S |

Yaya her seçenekte baskılı anteninde ve E28-2G4M12S'de kalıyor.

FHSS satırları **uyarlamalı** (dinle, sonra konuş) hâlde: EN 300 328'in
uyarlamasız kipi 5 ms'den uzun yayına izin vermiyor, bizim ölçüm paketimiz
SF10'da yaklaşık 15 ms. Uyarlamalı kipte her kanal kullanımından sonra en
az %5 sessizlik var; model turu bu kadar uzatıyor (ADR-0092). Kanalın dolu
bulunup beklenmesinin getirdiği ek kayıp modelde yok; şehir içinde Wi-Fi
yoğunluğuna bağlı, sahada ölçülmeli. FHSS
belgesi yoğunluk sınırını kaldırıyor, yalnız 20 dBm e.i.r.p. kalıyor;
bunu kullanmak için direk ve araç 27 dBm'lik modüle (E28-2G4M27S) geçiyor.

## Şehir içi (Kızılay, 600 m, 25 direk)

| | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan | Direk birimi | Araç alıcısı | CAPEX | OPEX/yıl | CAPEX/km² | OPEX/km²/yıl | 10 yıl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| O1 | 2,13 | 5,63 | 3,61 | %66,55 | 5,96 | 756 | 3064 | 80148 | 17130 | 13440 | 2873 | 251445 |
| O2 | 2,07 | 5,66 | 3,66 | %69,89 | 6,37 | 955 | 3364 | 85124 | 17627 | 13370 | 2769 | 261399 |
| O3 | 2,07 | 5,64 | 3,66 | %69,50 | 7,20 | 2741 | 3364 | 129782 | 22093 | 18017 | 3067 | 350714 |
| **O4** | 2,06 | 5,53 | 3,71 | %69,00 | 7,82 | 2492 | 5360 | 123560 | 21471 | 15801 | 2746 | 338270 |
| O5 | 1,87 | 5,51 | 3,73 | %83,78 | 8,28 | 887 | 3210 | 83416 | 17457 | 10078 | 2109 | 257982 |
| O6 | 1,85 | 5,47 | 3,75 | %85,67 | 8,59 | 1086 | 3510 | 88393 | 17954 | 10290 | 2090 | 267935 |
| O7 | 1,82 | 5,11 | 3,79 | %84,82 | 8,97 | 2623 | 5506 | 126829 | 21798 | 14139 | 2430 | 344807 |

## Kırsal (Polatlı, 3000 m, 49 direk)

| | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan | Direk birimi | Araç alıcısı | CAPEX | OPEX/yıl | CAPEX/km² | OPEX/km²/yıl | 10 yıl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| O1 | 1,91 | 5,42 | 4,76 | %49,13 | 209,00 | 756 | 3064 | 376609 | 123531 | 1802 | 591 | 1611914 |
| O2 | 1,88 | 5,23 | 4,75 | %52,74 | 222,67 | 955 | 3364 | 386364 | 124506 | 1735 | 559 | 1631423 |
| O3 | 1,91 | 5,17 | 4,76 | %52,46 | 253,75 | 2741 | 3364 | 473893 | 133259 | 1868 | 525 | 1806482 |
| **O4** | 1,84 | 5,01 | 4,73 | %57,75 | 285,83 | 2492 | 5360 | 461698 | 132039 | 1615 | 462 | 1782091 |
| O5 | 1,80 | 4,63 | 4,70 | %64,93 | 290,50 | 887 | 3210 | 383016 | 124171 | 1318 | 427 | 1624727 |
| O6 | 1,76 | 4,65 | 4,71 | %66,47 | 305,75 | 1086 | 3510 | 392770 | 125147 | 1285 | 409 | 1644235 |
| O7 | 1,71 | 4,48 | 4,70 | %68,40 | 367,58 | 2623 | 5506 | 468104 | 132680 | 1273 | 361 | 1794904 |

Tutarlar TL. Direk birimi ve araç alıcısı 1000 adetlik birim fiyat.
Alanın birimi km².

## Fiyatlar

1000 adet fiyatları, dağıtıcının kademesi doğrulanan parçalarda o
kademeden (ADR-0093): STM32G0B1MET6, ATECC608B, DWM3000, ESP32-S3,
BNO085, TCAN1051, W24P-U. Doğrulanmayanlar (E28-2G4M12S, E28-2G4M27S,
STM32G031K8T6, ekran, bütün dış antenler ve kablo) hâlâ tek adet
perakende fiyatından raporun indirim oranıyla taşınıyor; o satırlar
değişecek.

Kullanılan tek adet fiyatları: AIR802 ANRD2405-SMA 8,95 USD, L-com
HGV-2409U 58,95 USD, TP-Link TL-ANT2412D 50,66 USD, LMR-200 kablo
9,50 USD, E28-2G4M12S 4,39 USD, E28-2G4M27S 8,74 USD.

**TP-Link TL-ANT2412D üretimden kalkmış** (üretici "End of Life"
gösteriyor). O4 ve O7 bu anteni kullanıyor; seçilirse yerine eşdeğer bir
12 dBi dış ortam anteni bulunmalı.

**FHSS belgesinin bedeli tabloda yok.** BTK'ya ayrı bir başvuru ya da
ücret yok (5 Şubat 2021'den beri); bedel yalnız laboratuvar testleri
(EN 300 328, EN 301 489-1/-17, EN 62368-1) ve onların yayımlanmış bir
fiyatı bulunamadı.

## Ne gösteriyor

1. **Uyarlamalı FHSS belgesi hepsinden iyi.** Baskılı antenle bile (O5)
   şehir içi kullanılabilirlik %66,55'ten %83,78'e, kırsal %49,13'ten
   %64,93'e çıkıyor; şehir içinde km² başına CAPEX en düşük (10078 TL).
   Direk birimi yalnız 27 dBm'lik modül farkıyla pahalanıyor (756'dan
   887 TL'ye). Bedeli: dinle-sonra-konuş yazılımı ve laboratuvar testi.
2. **Belge olmadan en iyi fiyat/performans 5 dBi çubuk anten (O2).**
   Bugünkü 12/8 dBi antenlerle (O4) aynı şehir içi kullanılabilirliği
   km² başına %15 daha ucuza veriyor. Kırsalda O4 daha iyi (%57,75'e
   %52,74) ve km² başına daha ucuz, çünkü direk başına alanı büyütüyor.
3. **Kırsalda en yüksek sonuç O7** (uyarlamalı FHSS + 12/8 dBi): %68,40,
   km² başına en düşük CAPEX ve OPEX.
4. **O3 (direkte 8 dBi) mantıksız:** 12 dBi'den pahalı, sonucu daha kötü.

## Açık kalanlar

- **1000 adetlik fiyatlar** (bütün parçalar ve antenler).
- **Test ücretleri** (EN 300 328, EN 301 489-1/-17, EN 62368-1).
- **Cevap veren direğin de kanal kontrolü yapması gerekip gerekmediği**
  (standardın ilgili maddesi); gerekirse tur biraz daha uzar.
- **Şehir içinde kanalın dolu bulunma oranı** (-70 dBm/MHz eşiği):
  sahada SDR kaydıyla ölçülmeli (ADR-0083).
- **5 dBi çubuk anten iç ortam tipi.** Direkte su geçirmez bir sürüm ya
  da muhafaza gerekir; fiyatı biraz artar.
