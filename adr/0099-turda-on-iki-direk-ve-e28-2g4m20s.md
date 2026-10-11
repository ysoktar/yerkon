# ADR-0099: şehir içi ve kırsalda turda 12 direk; direk ve araçta E28-2G4M20S

## Durum

Kabul edildi (proje sahibinin kararı, 27 Eylül 2026). Şehir içi ve
kırsal için ADR-0085'in "turda sekiz direk" kararının yerine geçiyor;
tünel sekizde kalıyor. ADR-0094'ün modül seçiminin yerine geçiyor;
anten ve frekans atlama belgesi kararı geçerli.

## Bağlam

- **Tur boyu.** ADR-0085 sekizi ızgara, düz çizgi tur ve daire binalarla
  seçmişti. Gerçek yollarda, aramanın direkleri ve gerçek ayak izleriyle
  on iki öne geçti (ADR-0098): HPE P95 şehir içinde 0,86 m, kırsalda
  1,13 m daha iyi; bedeli HPE P50'de 0,17-0,25 m ve saniyede 1,87 yerine
  1,25 konum.
- **Modül.** Frekans atlama belgesiyle sınır 20 dBm e.i.r.p. (ADR-0094).
  5 dBi anten ve 0,3 dB besleme kaybıyla modülde 15,3 dBm yetiyor.
  E28-2G4M27S (27 dBm) bunu fazlasıyla veriyordu; E28-2G4M20S (20 dBm)
  de veriyor. Model iki modülde aynı bağlantıyı hesaplıyor: düz zeminde
  10 m direkten 1,5 m'deki araca bağlantı 8,1 km'ye kadar kuruluyor,
  5 m hassasiyet 6,0 km'de bitiyor.

## Karar

- `urban.anchors_per_round` ve `rural.anchors_per_round` = 12.
- Direk birimi (`amplified-anchor`) ve kara aracı alıcısı E28-2G4M20S
  taşıyor (`hardware.E28_2G4M20S`, `radios()["e28"]`). Simülatörün
  "e28" modülü de bu. E28-2G4M27S tanımı, 20 dBm'den fazlasına izin veren
  kurallar için duruyor.
- Fiyat: JLCPCB C411311, 1+ 5,9566 USD, 10+ 5,8105 USD (27 Eylül 2026).
  JLCPCB'nin tablosu 10+ kademesinde bitiyor ve LCSC'nin sayfası
  kaldırılmış; 1000 adet için 10+ fiyatı kullanılıyor, gerçek 1000 adet
  fiyatı daha düşük olabilir.

## Sonuç

- **Birim fiyatları** (TL):

| | 1 adet | 100 adet | 1000 adet |
|---|---|---|---|
| Direk birimi, E28-2G4M27S ile | 1868,34 | 1305,32 | 1493,43 |
| **Direk birimi, E28-2G4M20S ile** | 1733,44 | 1211,07 | 1365,12 |
| Kara aracı alıcısı, E28-2G4M27S ile | 4517,05 | 3474,84 | 3739,45 |
| **Kara aracı alıcısı, E28-2G4M20S ile** | 4382,14 | 3371,06 | 3611,14 |

- **Yayımlanan satırlar:**

| | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan km² | CAPEX/km² | OPEX/km²/yıl |
|---|---|---|---|---|---|---|---|
| Şehir içi, önce (8, 27S) | 2,03 | 9,80 | 3,96 | %96,37 | 8,14 | 9205 | 1771 |
| **Şehir içi, şimdi (12, 20S)** | 2,28 | 8,94 | 3,92 | %96,64 | 8,14 | 8905 | 1742 |
| Kırsal, önce (8, 27S) | 1,97 | 8,58 | 4,96 | %94,21 | 361,83 | 1322 | 333 |
| **Kırsal, şimdi (12, 20S)** | 2,14 | 7,45 | 4,93 | %96,26 | 361,83 | 1305 | 331 |

Tutarlar TL. Şehir içinde km² başına CAPEX %3, kırsalda %1 düştü.

- **Yonga siparişte doğrulanmalı.** EBYTE'ın güncel E28-2G4M20S sayfası
  yongayı SX1281 diye veriyor ve özelliklerde ölçümü sayıyor; eski
  kullanım kılavuzu SX1280 diyor. SX1281'de ölçüm motoru yok. Paketteki
  1280 ya da 1281 yazısına bakılmalı (`bom.toml`).
- **LBT kartın yazılımında.** SPI modülde hazır bir LBT yok. EBYTE'ın
  20S sayfasındaki LBT bağlantısı E22 serisini anlatan bir yazıya
  gidiyor. Semtech'e göre CAD tam bir taşıyıcı algılama değil; LBT,
  ExpressLRS'teki gibi anlık RSSI ile yapılmalı (EN 300 328 V2.2.2,
  4.3.1.7.2.2).

## Kaynaklar

- EBYTE, E28-2G4M20S ürün sayfası (Çince): SX1281, 20 dBm, 6 km.
- EBYTE, E28-2G4M20S kullanım kılavuzu v1.30: SX1280, uçuş süresi.
- EBYTE, E22 serisi LoRa modüllerinin işlevleri (LBT).
- JLCPCB, E28-2G4M20S (C411311), 27 Eylül 2026.
- Semtech, AN1200.85 v2.0 (Nisan 2024), giriş.
- ETSI EN 300 328 V2.2.2 (2019-07), 4.3.1.7.2.2.
- ExpressLRS, çekme isteği 1243.
