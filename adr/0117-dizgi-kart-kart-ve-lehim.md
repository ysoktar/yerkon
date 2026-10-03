# ADR-0117: Dizgi kart kart sayılır, lehim eklenir

## Durum

Kabul edildi (proje sahibinin isteği, 30 Eylül 2026).

## Bağlam

Dizgi satırı her ürün için aynıydı: 150 SMD lehim noktası. Gerçek sayı
kartlar arasında çok farklı; yaya ve araç alıcılarında yalnız eMMC'nin
153 bilyesi var. Delikli parçalar (şebeke beslemesi HLK-5M12, varistör,
vidalı klemensler, araç alıcısındaki ekran modülünün başlığı) ve pil ile
güneş paneli kabloları hiç sayılmıyordu.

## Karar

- Her ürünün SMD lehim noktası, parçalarının kılıfından sayılır (bir
  QFN'nin alt pedi de bir nokta): yayın birimi 125, kritik bölge yayın
  birimi 133, yaya alıcısı 428, kara aracı alıcısı 409. Pasifler satırı
  (25 iki uçlu parça, LED, düğme) 56 nokta.
- JLCPCB'nin fiyatları (Economic PCBA, 30 Eylül 2026): kurulum 8,18 $,
  şablon 1,53 $, genişletilmiş parça başına 3,07 $ (on parça varsayıldı),
  SMD nokta başına 0,0016 $; delikli parça ve kablo lehimi nokta başına 0,0164 $ (siparişte
  10.000 noktaya kadar), 0,015 $ (10.001-30.000).
- Lehim noktaları (delikli parçalar ve kablolar): yayın birimlerinde 10 (HLK-5M12 4, varistör 2,
  iki klemens 4), yaya alıcısında 4 (pil ve panel kabloları), araç
  alıcısında 18 (ekran başlığı 14, iki klemens 4).
- Kartın kutuya takılması işçiliktir, bu fiyata dahil değil.

## Sonuçlar

Yeni 1000 adet fiyatları: yayın birimi 1.397,25 TL (önce 1.391,17),
kritik bölge yayın birimi 1.387,41 TL (1.380,70), yaya alıcısı 2.697,22 TL
(2.672,21), kara aracı alıcısı 3.169,03 TL (3.135,50).

Tablonun maliyet sütunları yeni fiyatlarla yeniden hesaplandı; simülasyon
yeniden koşulmadı, çünkü konum sonuçları fiyattan etkilenmiyor: şehir içi
CAPEX 9.097 TL/km² (9.083), OPEX 1.944 (1.943); kırsal 1.141 (1.140) ve
330; tünel 154.974 TL/km (154.803) ve 32.413 (32.396); Tüm Türkiye
1.300 TL/km² (1.299) ve 362. Direk boyu ve tünel aralığı notlarındaki
maliyetler aynı oranla güncellendi (şehir içinde bütün birimler aynı
direkte olduğu için oran tam; kırsalda karışık direklerde yuvarlama
içinde).
