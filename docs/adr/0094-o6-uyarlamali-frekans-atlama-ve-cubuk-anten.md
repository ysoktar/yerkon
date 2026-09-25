# ADR-0094: şehir içi ve kırsal O6 ile: uyarlamalı frekans atlama belgesi, 27 dBm modül ve 5 dBi çubuk anten

## Durum

Kabul edildi (proje sahibinin kararı, 25 Eylül 2026). ADR-0091'in
direk ve araç antenlerinin yerini alıyor; ADR-0091'in duyarlılık kararı
geçerli. ADR-0092'deki kural artık tabloda kullanılıyor.

## Bağlam

Yedi anten ve belge seçeneği tam çözünürlükte koşuldu ve 1000 adet
fiyatıyla fiyatlandı (`docs/ANTEN-KARSILASTIRMASI.md`). O6 şehir içinde
en yüksek kullanılabilirliği ve km² başına en düşük maliyeti verdi,
kırsalda da O7'nin 1,8 puan gerisinde, ondan ucuz kaldı. Proje sahibi
O6'yı seçti.

## Karar

Şehir içi ve kırsal satırlar:

- **Kural:** `TR-FHSS`, uyarlamalı frekans atlama (dinle, sonra konuş).
  20 dBm e.i.r.p., yoğunluk sınırı yok. Her kanal kullanımından sonra en
  az %5 sessizlik; ölçüm turu bu yüzden 1,05 kat uzuyor
  (`SpectrumRule.idle_after_occupancy`, `channel_share`).
- **Direk birimi:** E28-2G4M27S (27 dBm), kutunun konnektörüne takılı
  5 dBi çubuk anten, STM32G031, ATECC608B. Kablo yok. 1000 adette
  1062,80 TL.
- **Kara aracı alıcısı:** aynı modül ve aynı anten. 1000 adette
  3308,82 TL.
- **Yaya alıcısı:** değişmedi: E28-2G4M12S ve baskılı anten. Pil
  cihazı, bağlantısı kısa. Belgelendirme testine o da giriyor, çünkü
  aynı kanallarda ölçüm yapıyor.
- **Tünel:** değişmedi (UWB, `TR`).

Satırların kuralı, modülleri ve antenleri tek yerde:
`scenarios.ROW_REGIONS`, `ROW_RADIOS`, `ROW_ANTENNAS`. Simülatörün
sekmeleri aynı tablolardan okuyor. Sayfanın bölge menüsüne "Türkiye,
frekans atlamalı belgeli" eklendi.

Malzeme listesinde `amplified-anchor` artık şehir içi ve kırsal yayın
birimi. `sx1280-anchor`, belgesiz yayın birimi (E28-2G4M12S ve aynı
çubuk anten, O2): tablonun hiçbir satırı onu kullanmıyor, simülatörde
modül seçilince fiyatı o.

## Sonuç (25 Eylül koşusu)

| | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan | CAPEX/km² | OPEX/km²/yıl |
|---|---|---|---|---|---|---|---|
| Şehir içi, önce (O4) | 2,06 | 5,60 | 3,72 | %69,33 | 7,82 | 16124 | 2778 |
| **Şehir içi, O6** | 1,87 | 5,43 | 3,75 | %85,47 | 8,59 | 10220 | 2083 |
| Kırsal, önce (O4) | 1,85 | 4,93 | 4,72 | %57,74 | 285,83 | 1633 | 464 |
| **Kırsal, O6** | 1,76 | 4,61 | 4,70 | %66,58 | 306,00 | 1280 | 409 |

Tutarlar TL, alan km². Şehir içinde km² başına CAPEX %37, kırsalda %22
düştü; kullanılabilirlik şehir içinde 16,1, kırsalda 8,8 puan arttı.

Seçenek tablosunda O6'nın direk birimi 1048 TL görünüyordu. O hesap
belgesiz kartın "diğer" kalemini kullanıyordu; yükselteçli kart
raporun kırsal satırından ayrıştırıldığı için "diğer" kalemi yaklaşık
0,3 USD farklı. Tablodaki km² başına tutarlar bu yüzden seçenek
tablosundakinden biraz yüksek (şehir içi 10176 yerine 10220).

## Sonuçlar

- **Belgelendirme gerekiyor.** EN 300 328 (uyarlamalı FHSS), EN 301 489-1
  ve -17, EN 62368-1. BTK'ya ayrı başvuru ya da ücret yok. Laboratuvar
  teklifi yok; piyasa göstergesi üçü birlikte yaklaşık 7000-16500 €, bir
  kerelik. Tabloya eklenmedi.
- **Kanal dolu çıkarsa bekleme modelde yok.** Şehir içinde Wi-Fi
  -70 dBm/MHz eşiğini sık aşarsa paket kaybı artar. Sahada SDR kaydıyla
  ölçülmeli (ADR-0083).
- **Çubuk anten iç ortam tipiydi;** aşağıdaki ek dış ortam antenine
  geçişi anlatıyor.

## Ek: dış ortam anteni (25 Eylül 2026)

İlk fiyatlanan çubuk anten (FT-RF RU-245805) üreticiye göre iç ortam
anteni ve bir IP koruma sınıfı yok. Direkte ve araç tavanında dış ortam
anteni gerekiyor. Proje sahibi Taoglas GW.22.5151'i seçti: 2,4 GHz,
5 dBi, RP-SMA(M), IP67 ve UV'ye dayanıklı.

- **Fiyat:** Mouser 1000 adet kademesi 10,07 USD; tek adet 11,51 USD
  (Westward Sales). Direk birimi 1000 adette 1493,43 TL, kara aracı
  alıcısı 3739,45 TL.
- **Hüzme:** üretici dikey hüzme genişliği vermiyor. Model, veri sayfası
  hüzme vermeyen her antende olduğu gibi McDonald yaklaşımını kullanıyor:
  5 dBi için 35,3°. Önceki antenin veri sayfası 54° diyordu; daha dar
  hüzme direğin dibinde daha ihtiyatlı.
- **Sonuç:**

| | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan | CAPEX/km² | OPEX/km²/yıl |
|---|---|---|---|---|---|---|---|
| Şehir içi | 1,85 | 5,47 | 3,75 | %85,67 | 8,59 | 11477 | 2209 |
| Kırsal | 1,76 | 4,65 | 4,71 | %66,47 | 305,75 | 1350 | 416 |

Doğruluk ve kullanılabilirlik neredeyse aynı; km² başına CAPEX şehir
içinde %12, kırsalda %5 arttı.
