# ADR-0109: TDoA'nın saat bedeli kaynaklı: bir atomik saatin tek adet fiyatı

## Durum

Kabul edildi (proje sahibinin kararı, 28 Eylül 2026).

## Bağlam

Sistem sayfası ve sunumun 5. slaytı, TDoA'da milyarda bir saniyenin
altında senkronizasyonun birim başına "yaklaşık 100000 liralık" atomik
saat ve IEEE 1588 PTP altyapısı istediğini söylüyordu. Bu sayı ilk
sunumdan geliyordu ve bir kaynağı yoktu.

## Karar

- Sayı, çip ölçekli bir atomik saatin (Microchip SA65) tek adet
  fiyatıyla değişti: yaklaşık 5500 USD (Analog IC Tips, Bill Schweber,
  28 Eylül 2021). Sitenin kuruyla (48,44 TL) yaklaşık 266400 lira.
- Proje sahibinin isteğiyle toplu fiyat (250 adet ve üstünde yarısı)
  kullanılmadı.
- Sayı yalnız saatin bedeli; PTP altyapısı fiyatlanmadı. Şekildeki
  etiket bu yüzden "birim başına atomik saat, TDoA".

## Sonuç

Sayı kaynaklı ve Kaynaklar sayfasında. Fiyat 2021'in; bugünkü fiyat
satıcıdan doğrulanamadı (Mouser ve Microchip Direct sayfaları
açılmadı).
