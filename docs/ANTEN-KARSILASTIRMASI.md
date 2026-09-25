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
| O1 | 2,13 | 5,63 | 3,61 | %66,55 | 5,96 | 857 | 3048 | 82674 | 17382 | 13864 | 2915 | 256498 |
| O2 | 2,09 | 5,73 | 3,70 | %69,02 | 6,38 | 844 | 3105 | 82362 | 17351 | 12903 | 2718 | 255875 |
| O3 | 2,07 | 5,67 | 3,65 | %68,33 | 7,18 | 2842 | 3105 | 132309 | 22346 | 18436 | 3114 | 355767 |
| **O4** | 2,06 | 5,60 | 3,72 | %69,33 | 7,82 | 2593 | 5344 | 126087 | 21724 | 16124 | 2778 | 343323 |
| O5 | 1,87 | 5,51 | 3,73 | %83,78 | 8,28 | 1060 | 3252 | 87762 | 17891 | 10604 | 2162 | 266673 |
| O6 | 1,87 | 5,43 | 3,75 | %85,47 | 8,59 | 1048 | 3309 | 87450 | 17860 | 10176 | 2078 | 266050 |
| O7 | 1,82 | 4,99 | 3,79 | %85,00 | 8,97 | 2797 | 5547 | 131174 | 22232 | 14624 | 2479 | 353498 |

## Kırsal (Polatlı, 3000 m, 49 direk)

| | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan | Direk birimi | Araç alıcısı | CAPEX | OPEX/yıl | CAPEX/km² | OPEX/km²/yıl | 10 yıl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| O1 | 1,91 | 5,42 | 4,76 | %49,13 | 209,00 | 857 | 3048 | 381561 | 124026 | 1826 | 593 | 1621818 |
| O2 | 1,90 | 5,21 | 4,76 | %52,97 | 222,83 | 844 | 3105 | 380950 | 123965 | 1710 | 556 | 1620596 |
| O3 | 1,91 | 5,27 | 4,75 | %52,31 | 253,42 | 2842 | 3105 | 478845 | 133754 | 1890 | 528 | 1816386 |
| **O4** | 1,85 | 4,93 | 4,72 | %57,74 | 285,83 | 2593 | 5344 | 466650 | 132535 | 1633 | 464 | 1791995 |
| O5 | 1,80 | 4,63 | 4,70 | %64,93 | 290,50 | 1060 | 3252 | 391533 | 125023 | 1348 | 430 | 1641762 |
| O6 | 1,76 | 4,61 | 4,70 | %66,58 | 306,00 | 1048 | 3309 | 390922 | 124962 | 1278 | 408 | 1640539 |
| O7 | 1,72 | 4,53 | 4,72 | %68,36 | 367,58 | 2797 | 5547 | 476621 | 133532 | 1297 | 363 | 1811938 |

Tutarlar TL. Direk birimi ve araç alıcısı 1000 adetlik birim fiyat.
Alanın birimi km².

## Fiyatlar

1000 adet fiyatları dağıtıcının kademesinden, kademesi doğrulanan her
parçada (ADR-0093): E28-2G4M12S ve E28-2G4M27S (LCSC 100+, daha yüksek
kademe yok), STM32G031K8T6, STM32G0B1MET6, ATECC608B, DWM3000,
ESP32-S3, BNO085, TCAN1051, ILI9341 ekran, W24P-U ve 5 dBi çubuk anten
(Alibaba, 500-49999 adet, 1,18 USD).

Doğrulanamayanlar hâlâ tek adet perakende fiyatından raporun indirim
oranıyla taşınıyor: TP-Link TL-ANT2412D (50,66 USD), L-com HGV-2409U
(58,95 USD) ve LMR-200 kablo (9,50 USD). Bunların yayımlanmış bir 1000
adet kademesi bulunamadı; O3, O4 ve O7 bu yüzden en belirsiz satırlar.

Hüzme genişlikleri veri sayfalarından: HGV-2409U 15°, 5 dBi çubuk anten
54° (FT-RF RU-245805). TL-ANT2412D için veri sayfası 12° diyor; model
kazançtan türetilen 6,5°'yi kullanıyor (aynı sınıftaki TreLink
TLOD-2400-12V'nin veri sayfası 7°).

**TP-Link TL-ANT2412D üretimden kalkmış.** O4 ve O7 bu anteni kullanıyor.

**Belgelendirme:** BTK'ya ayrı başvuru ya da ücret yok. Laboratuvar
testleri (EN 300 328, EN 301 489-1/-17, EN 62368-1) teklifle; piyasa
göstergesi, teklif değil, üçü birlikte yaklaşık 7000-16500 €, bir
kerelik. Bin direkli bir ağda direk başına 7-16,5 €; tabloya
eklenmedi.

## Ne gösteriyor

1. **En iyisi O6: uyarlamalı FHSS belgesi ve iki uçta 5 dBi çubuk
   anten.** Şehir içinde en yüksek kullanılabilirlik (%85,47) ve km²
   başına en düşük CAPEX (10176 TL) ile OPEX (2078 TL); kırsalda %66,58 ve
   km² başına 1278 TL. Direk birimi 1048 TL.
2. **Belge alınmazsa şehir içinde O2** (5 dBi çubuk): bugünkü 12/8 dBi
   antenlerle (O4) aynı kullanılabilirlik, km² başına %20 daha ucuz.
   Kırsalda O4 daha iyi (%57,74'e %52,97), km² başına da daha ucuz.
3. **Kırsalda en yüksek sonuç O7** (%68,36), ama O6'dan yalnız 1,8 puan
   iyi ve pahalı, üretimden kalkmış bir antene dayanıyor.
4. **5 dBi çubuk anten doğrulanmış fiyatla baskılı antenden bile ucuz**
   (1,18'e 1,44 USD); O1'in O2'ye bir üstünlüğü kalmadı.
5. **O3 (direkte 8 dBi) mantıksız:** 12 dBi'den pahalı, sonucu daha kötü.

## Açık kalanlar

- **1000 adetlik fiyatlar** (bütün parçalar ve antenler).
- **Test ücretleri** (EN 300 328, EN 301 489-1/-17, EN 62368-1).
- **Cevap veren direğin de kanal kontrolü yapması gerekip gerekmediği**
  (standardın ilgili maddesi); gerekirse tur biraz daha uzar.
- **Şehir içinde kanalın dolu bulunma oranı** (-70 dBm/MHz eşiği):
  sahada SDR kaydıyla ölçülmeli (ADR-0083).
- **5 dBi çubuk anten iç ortam tipi.** Direkte su geçirmez bir sürüm ya
  da muhafaza gerekir; fiyatı biraz artar.
