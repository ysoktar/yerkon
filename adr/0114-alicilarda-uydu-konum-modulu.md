# ADR-0114: Alıcılarda uydu konum modülü

## Durum

Kabul edildi (proje sahibinin isteği, 29 Eylül 2026).

## Bağlam

YERKON uydu kesildiğinde yerdeki birimlerle devam eden bir yedek katman.
Alıcı uydu varken uydudan da konum almalı; malzeme listesinde bunu
yapacak bir parça yoktu.

## Karar

Yaya ve kara aracı alıcısına:

- ZHONGKEWEI ATGM336H-5NR32 uydu konum modülü: GPS, GLONASS, BeiDou,
  QZSS (kullanım kılavuzunun modül tablosu; içindeki AT6558R yongası
  Galileo'yu da alabiliyor, modülün listesinde yok). JLCPCB C5117921,
  1000 adette 1,501 $.
- Abracon PRO-OB-430 kart üstü yama anten, 1575 ve 1602 MHz, yani GPS ve
  GLONASS bantlarının ikisi de. JLCPCB C3284500, 1000 adette 0,5946 $.

İkisi birlikte 1000 adette yaklaşık 102 TL. Yeni alıcı fiyatları (1 / 100
/ 1000 adet): yaya 3.333,75 / 2.775,35 / 2.486,48 TL, kara aracı
4.703,79 / 4.183,27 / 3.410,56 TL.

İlk seçilen Quectel L76KB-A58'di (aynı sistemler, 1000 adette 2,6803 $).
Aynı gün, stok durumuna bakılmadan yeniden arandığında ATGM336H-5NR32
aynı sistemleri daha ucuza verdiği için onun yerine geçti. Stok parça
seçiminde ölçüt değil.

## Seçenekler

Aynı kademe tablosunda (JLCPCB, 29 Eylül 2026):

| Modül | Uydu sistemleri | 1000 adet | Stok |
|---|---|---|---|
| ZHONGKEWEI ATGM336H-5NR32 (seçilen) | GPS, GLONASS, BeiDou, QZSS | 1,50 $ | 1.197 |
| Quectel L76KB-A58 | GPS, GLONASS, BeiDou, QZSS | 2,68 $ | 2.246 |
| ZHONGKEWEI ATGM336H-5N31 | GPS, BeiDou | 1,81 $ | 10.875 |
| ZHONGKEWEI ATGM336H-5N11 | GPS, GLONASS, BeiDou, Galileo, QZSS (JLCPCB'nin listesi) | 2,20 $ | 0 |
| u-blox MAX-M10S-00B | GPS, GLONASS, BeiDou, Galileo, QZSS | 10,51 $ (10+) | 686 |

Araç kutusu gökyüzünü görmeyen bir yere konacaksa kablolu dış anten
gerekir; örnek BAT WIRELESS BWGPSZWX46-38JL1000 (aktif, SMA, 1575,42 MHz),
1000 adette 1,45 $.

## Sonuçlar

Tablonun maliyet satırları değişmiyor: alıcılar kuruluma sayılmıyor.
Sitenin Sistem ve Maliyet sayfaları, sunumun 15. slaytı ve başvuru
formunun bütçe alanı yeni fiyatlarla güncellendi.
