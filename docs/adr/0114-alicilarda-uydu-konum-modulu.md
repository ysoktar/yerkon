# ADR-0114: Alıcılarda uydu konum modülü

## Durum

Kabul edildi (proje sahibinin isteği, 29 Eylül 2026).

## Bağlam

YERKON uydu kesildiğinde yerdeki birimlerle devam eden bir yedek katman.
Alıcı uydu varken uydudan da konum almalı; malzeme listesinde bunu
yapacak bir parça yoktu.

## Karar

Yaya ve kara aracı alıcısına:

- Quectel L76KB-A58 uydu konum modülü: GPS, GLONASS, BeiDou, QZSS
  (Galileo yok). JLCPCB C2916234, 1000 adette 2,6803 $.
- Abracon PRO-OB-430 kart üstü yama anten, 1575 ve 1602 MHz, yani GPS ve
  GLONASS bantlarının ikisi de. JLCPCB C3284500, 1000 adette 0,5946 $.

İkisi birlikte 1000 adette yaklaşık 159 TL. Yeni alıcı fiyatları (1 / 100
/ 1000 adet): yaya 3.431,40 / 2.839,01 / 2.543,60 TL, kara aracı
4.801,44 / 4.246,93 / 3.467,69 TL.

## Seçenekler

Aynı kademe tablosunda (JLCPCB, 29 Eylül 2026):

| Modül | Uydu sistemleri | 1000 adet | Stok |
|---|---|---|---|
| Quectel L76KB-A58 (seçilen) | GPS, GLONASS, BeiDou, QZSS | 2,68 $ | 2.246 |
| ZHONGKEWEI ATGM336H-5N31 | GPS, BeiDou | 1,81 $ | 10.875 |
| ZHONGKEWEI ATGM336H-5N11 | GPS, GLONASS, BeiDou, Galileo, QZSS | 2,20 $ | 0 |
| u-blox MAX-M10S-00B | GPS, GLONASS, BeiDou, Galileo, QZSS | 10,51 $ (10+) | 686 |

Araç kutusu gökyüzünü görmeyen bir yere konacaksa kablolu dış anten
gerekir; örnek BAT WIRELESS BWGPSZWX46-38JL1000 (aktif, SMA, 1575,42 MHz),
1000 adette 1,45 $.

## Sonuçlar

Tablonun maliyet satırları değişmiyor: alıcılar kuruluma sayılmıyor.
Sitenin Sistem ve Maliyet sayfaları, sunumun 15. slaytı ve başvuru
formunun bütçe alanı yeni fiyatlarla güncellendi.
