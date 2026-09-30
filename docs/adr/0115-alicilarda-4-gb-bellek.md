# ADR-0115: Alıcılarda 4 GB bellek, araç alıcısında AT32F403A

## Durum

Kabul edildi (proje sahibinin isteği, 30 Eylül 2026).

## Bağlam

Alıcı yüksekliğini haritadan alıyor (ADR-0088). Türkiye'yi Copernicus
30 m dosyalarından 113 parça kaplıyor (Natural Earth 1:10m ülke sınırı
ile Copernicus'un parça listesi karşılaştırıldı; sınırdaki parçalar
dahil). Bir parça 3600 × 3600 yükseklik. Yayımlandığı hâliyle (4 baytlık
sayılar, sıkıştırılmış) Ankara'nın dört parçası 38-41 MB, 113 parça
yaklaşık 4,5 GB. Yükseklik 2 baytla (10 cm adımlı) saklanırsa,
sıkıştırmadan, 113 × 3600 × 3600 × 2 bayt = yaklaşık 2,9 GB. Alıcıların
işlemcilerindeki bellek buna yetmiyor: yaya alıcısındaki ESP32-S3
modülünde 8 MB, araç alıcısındaki STM32G0B1'de 512 KB.

## Karar

- İki alıcıya da Zetta ZDEMMC04GA, 4 GB eMMC 5.1. JLCPCB C3010207,
  1000 adette 2,6462 $ (456+ kademesi; 1064+ kademesi 2,5699 $). Stok
  bugün sıfır; stok parça seçiminde ölçüt değil. Veri sayfasına göre
  (Zetta eMMC5.1 datasheet, rev 1.2): kullanıcı alanı 3.909.091.328 bayt
  (3728 MB), yani 2 baytlık Türkiye dosyası (2,9 GB) sığıyor, 4 baytlık
  hâli sığmıyor; besleme 3,3 V (VCC 2,7-3,6 V, VCCQ 1,7-1,95 ya da
  2,7-3,6 V); çalışma sıcaklığı -25 ile 85 °C; 153 bilyeli FBGA,
  11,5 × 13 × 1,0 mm; eMMC 5.1, v4.5-v5.0 ile geriye uyumlu; veri yolu
  1, 4 ya da 8 bit.
- Yaya alıcısında eMMC, ESP32-S3'ün SD/MMC arayüzüne bağlanır (ESP-IDF
  SDMMC Host Driver: iki yuva, her biri SD kart, SDIO aygıtı ya da eMMC
  yongası için 1, 4 ya da 8 hat).
- Araç alıcısının işlemcisi STM32G0B1MET6 yerine Artery AT32F403ARGT7.
  STM32G0B1'de SD/MMC arayüzü yok; eMMC'nin de SPI kipi yok. AT32F403A'da
  iki SD/SDIO/MMC arayüzü (MultiMediaCard 4.2, 1, 4 ya da 8 bit) ve iki
  CAN 2.0A/B denetleyicisi var (AT32F403A veri sayfası). JLCPCB C528440,
  960+ adette 1,3028 $; STM32G0B1 DigiKey'de 500+ adette 3,8313 $'dı.

Yeni alıcı fiyatları (1 / 100 / 1000 adet): yaya 3.542,82 / 2.937,37 /
2.614,66 TL, kara aracı 4.694,58 / 4.096,17 / 3.416,26 TL. Araç alıcısında
işlemci değişikliği belleğin fiyatını neredeyse karşılıyor: 1000 adette
yalnızca 5,70 TL daha pahalı.

## Seçenekler

| Seçenek | Ne sığar | 1000 adet |
|---|---|---|
| Zetta ZDEMMC04GA eMMC (seçilen) | bütün Türkiye, 2 baytla | 2,6462 $ |
| Creat Storage World CSNP4GCR01-BOW SD NAND, SPI ile | 512 MB: yolların yükseklikleri, birkaç il | 2,0468 $ (960+) |
| XMC XM25QH128CHIQT08Q SPI flash | 16 MB: yolların yükseklikleri | 0,3314 $ |

Araçta işlemciyi değiştirmeden SPI SD NAND da olabilirdi; bütün Türkiye
sığmadığı için işlemci değişti.

## Sonuçlar

- Tablonun maliyet satırları değişmiyor: alıcılar kuruluma sayılmıyor.
- Sitenin Sistem ve Maliyet sayfaları, sunumun 7. ve 15. slaytları ve
  başvuru formunun bütçe alanı yeni fiyatlarla güncellendi.
- AT32F403A'nın arayüzü MultiMediaCard 4.2'ye göre; Zetta'nın veri
  sayfası geriye uyumluluğu v4.5'e kadar yazıyor. Temel okuma ve yazma
  (1 ya da 4 bit, 26 MHz'e kadar) iki tarafta da tanımlı, ama bu ikilinin
  birlikte denendiği yayımlanmış bir kaynak bulunamadı: pilot kartta
  denenecek.
- eMMC'nin alt sıcaklık sınırı -25 °C; alıcıların öteki yongaları -40 °C'ye
  kadar çalışıyor (AT32F403A -40 ile 105 °C, ATGM336H-5NR32 -40 ile 85 °C).
- eMMC 153 bilyeli BGA kılıfta. İki katlı kartta yollanıp
  yollanamayacağı kart tasarımında görülecek; dört kat gerekirse kart
  fiyatı artar, bu fiyata dahil değil.
