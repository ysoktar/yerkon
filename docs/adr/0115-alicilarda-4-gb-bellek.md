# ADR-0115: Alıcılarda 4 GB bellek, araç alıcısında AT32F403A

## Durum

Kabul edildi (proje sahibinin isteği, 30 Eylül 2026).

## Bağlam

Alıcı yüksekliğini haritadan alıyor (ADR-0088). Türkiye'nin Copernicus
30 m yükseklik dosyaları yayımlandığı hâliyle yaklaşık 4 GB tutuyor:
bir 1° × 1° parça 38-41 MB, Türkiye yaklaşık 100 parça (tahmin).
Yükseklik 4 yerine 2 baytla saklanırsa yaklaşık yarısı. Alıcıların
işlemcilerindeki bellek buna yetmiyor: yaya alıcısındaki ESP32-S3
modülünde 8 MB, araç alıcısındaki STM32G0B1'de 512 KB.

## Karar

- İki alıcıya da Zetta ZDEMMC04GA, 4 GB eMMC 5.1. JLCPCB C3010207,
  1000 adette 2,6462 $ (456+ kademesi; 1064+ kademesi 2,5699 $). Stok
  bugün sıfır; stok parça seçiminde ölçüt değil.
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
| Zetta ZDEMMC04GA eMMC (seçilen) | bütün Türkiye | 2,6462 $ |
| Creat Storage World CSNP4GCR01-BOW SD NAND, SPI ile | 512 MB: yolların yükseklikleri, birkaç il | 2,0468 $ (960+) |
| XMC XM25QH128CHIQT08Q SPI flash | 16 MB: yolların yükseklikleri | 0,3314 $ |

Araçta işlemciyi değiştirmeden SPI SD NAND da olabilirdi; bütün Türkiye
sığmadığı için işlemci değişti.

## Sonuçlar

- Tablonun maliyet satırları değişmiyor: alıcılar kuruluma sayılmıyor.
- Sitenin Sistem ve Maliyet sayfaları, sunumun 7. ve 15. slaytları ve
  başvuru formunun bütçe alanı yeni fiyatlarla güncellendi.
- eMMC 153 bilyeli BGA kılıfta. İki katlı kartta yollanıp
  yollanamayacağı kart tasarımında görülecek; dört kat gerekirse kart
  fiyatı artar, bu fiyata dahil değil.
