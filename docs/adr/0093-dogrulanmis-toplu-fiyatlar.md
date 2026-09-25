# ADR-0093: 1000 adet fiyatı, doğrulandığı yerde dağıtıcının kademesinden

## Durum

Kabul edildi.

## Bağlam

Tablo donanımı 1000 adet kademesinde fiyatlıyor. Bir ürünün 1000 adet
fiyatı, tek adet parça fiyatlarının raporun kendi 1'den 100'e indirim
oranıyla (0,69 ile 0,80) ve varsayılan bir 0,9 ile çarpılmasıyla
bulunuyordu. Parça başına gerçek bir toplu fiyat yoktu.

Proje sahibi her parçanın 1000 adet fiyatını istedi. Dağıtıcı sayfaları
bu ortamdan kapalı olduğu için değerler ayrıca, yalnız dağıtıcının ya
da üreticinin kendi kademe tablosundan derlendi.

## Karar

`bom.toml`'da bir parça, doğrulanmış bir toplu fiyatı varsa `volume`
tablosunu taşıyor: fiyat, kademe, satıcı, adres, tarih. 1000 adet
sütununda o parça bu fiyatla giriyor; doğrulanmamış parçalar ve "diğer"
kalemi (güç, koruma, bağlantı, kutu) eskisi gibi raporun oranıyla.

Doğrulananlar (25 Eylül 2026):

| Parça | Satıcı | Kademe | USD |
|---|---|---|---|
| STM32G0B1MET6 | DigiKey | 500+ (1000 yok) | 3,83132 |
| ATECC608B-MAHDA-S | Mouser | 1000+ | 0,819 |
| DWM3000TR13 | LCSC | 10+ (daha yüksek kademe yok) | 22,5844 |
| ESP32-S3-WROOM-1-N8 | LCSC | 1300+ (1000 yok) | 3,1542 |
| BNO085 | Mouser | 1000+ | 8,81 |
| TCAN1051HGVDRQ1 | Mouser | 1000+ | 1,19 |
| Inventek W24P-U | DigiKey | 500+ (1000 yok) | 1,4375 |

Bekleyenler: E28-2G4M12S, E28-2G4M27S, STM32G031K8T6, ILI9341 ekran
(gerçek ILI9341 ilanı bulunamadı), bütün dış antenler ve anten kablosu.

## Sonuçlar

Raporun oranı toplu alımı olduğundan iyimser gösteriyordu. 1000 adette:

| Ürün | Önce | Şimdi |
|---|---|---|
| Şehir içi ve kırsal yayın birimi | 2479,75 | 2492,40 |
| Kritik bölge (tünel) yayın birimi | 1091,19 | 1668,40 |
| Yaya alıcısı | 2141,87 | 2670,42 |
| Kara aracı alıcısı | 4890,92 | 5359,55 |

En büyük fark DWM3000: LCSC'nin en yüksek yayımlanmış kademesi 22,58
USD; oran onu 10,3 USD'ye indiriyordu. Tünel satırının CAPEX'i bu yüzden
artıyor. 100 adet sütunu hâlâ raporun oranı; bazı ürünlerde 1000 adet
fiyatı 100 adetten yüksek görünüyor, bu da oranın iyimserliğinin izi.
