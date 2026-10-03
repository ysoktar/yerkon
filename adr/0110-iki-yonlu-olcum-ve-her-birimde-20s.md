# ADR-0110: Her ölçüm iki yönde kapanır; her birimde E28-2G4M20S

## Durum

Kabul edildi (proje sahibinin kararı, 29 Eylül 2026).

## Bağlam

İki yönlü mesafe ölçümünde (TWR) direk sorar, alıcı yanıtlar; ölçüm
ancak iki paket de karşıya ulaşırsa olur. Model yanıtın bağlantısını
yalnız yanıtlayanın gücü sorandan düşükse ayrıca hesaplıyordu ve o
zaman da engeli direğin ucundan ölçülmüş haliyle kullanıyordu. Yaya
alıcısında 12,5 dBm'lik E28-2G4M12S vardı, direk ve araçta 20 dBm'lik
E28-2G4M20S. Yayanın zayıf yanıtı direğe ulaşmasa da ölçüm sayılabiliyordu.

## Karar

- Her ölçümde yanıtın bağlantısı da hesaplanır. İkisinden biri
  kapanmazsa ölçüm yoktur; kapanırsa zayıf olanın sinyal gürültü oranı
  kullanılır. Yanıtın engeli, aynı yol ters yönden okunarak bulunur
  (`Obstruction.reversed()`): tepe ve yansıma noktaları yolun öbür
  ucuna göre yer değiştirir. Gölgeleme iki yönde aynıdır, çünkü aynı
  ortamdır.
- Yaya alıcısı da E28-2G4M20S taşır; gücü yazılımla ayarlanır. Böylece
  şehir içi, kırsal, araç ve yaya birimlerinin hepsinde tek bir 2,4 GHz
  modülü kalır. Tünel birimleri DWM3000 ile kalır.
- Yaya alıcısının fiyatı 1, 100 ve 1000 adette 3082,55, 2586,76 ve
  2309,77 TL'den 3158,59, 2661,96 ve 2384,97 TL'ye çıkar (LCSC ve
  JLCPCB kademe fiyatları, 25-28 Eylül 2026). Tablonun maliyetleri
  yalnız yayın birimlerini sayar, bu yüzden değişmez.

## Sonuç

Tablo iki yönlü modelle yeniden koşuldu (29 Eylül 2026, sekiz gölge
çekilişi, 10 m profil aralığı):

| Satır | HPE P50 [m] | HPE P95 [m] | VPE P95 [m] | Kullanılabilirlik |
|---|---|---|---|---|
| Şehir içi, önce | 2,28 | 8,94 | 3,92 | %96,64 |
| Şehir içi, sonra | 2,29 | 9,19 | 4,00 | %96,65 |
| Kırsal, önce | 2,16 | 8,16 | 4,96 | %94,52 |
| Kırsal, sonra | 2,16 | 8,15 | 4,96 | %94,58 |
| Tünel | 0,58 | 2,43 | 3,31 | %94,32 (değişmedi) |

CAPEX ve OPEX değişmedi. Şehir içinde P95'in 0,25 m artması, artık
yanıtı ulaşmayan uzak direklerin ölçüme girmemesinden geliyor. Tünel
değişmedi, çünkü orada her uç aynı DWM3000'ü aynı sınırda kullanıyor.

Yerel araç `tools/hardware.py` tünelde DWM3000 ile E28-2G4M20S'yi de
karşılaştırır. 20S'ye şehrin 15 m kabul sınırı verilir; tünelin 2 m
sınırı UWB'nin desimetre ölçümü için konmuştur ve LoRa ölçümlerinin
hepsini dışarıda bırakır. 2,4 GHz'te tünelin kılavuzlu kaybı 2,8-5 GHz'te
ölçülmüş modelin dışa uzatılmasıdır.
