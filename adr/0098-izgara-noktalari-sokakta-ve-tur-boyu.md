# ADR-0098: bina içine düşen ızgara noktaları en yakın sokakta; turda 8 ve 12 direk

## Durum

Kabul edildi (proje sahibinin kararı, 27 Eylül 2026): ızgara noktaları
sokağa taşınıyor. Tur boyu için iki değer de ölçüldü; seçim proje
sahibinin. Tablo sekizde kalıyor (ADR-0085). ADR-0097'nin yayımlanan
şehir içi satırının yerine geçiyor.

## Bağlam

Yerleşim araması ızgaranın noktalarını her zaman aday tutuyor, böylece
ızgaradan kötü bir cevap veremiyor (ADR-0081). Kızılay'da bu noktalardan
4'ü gerçek ayak izine göre bir binanın içinde kalıyordu (ADR-0097). Bir
aydınlatma direği bina içine dikilemez; model orada direğe binanın çatı
yüksekliğini de bedavaya veriyordu (ADR-0038).

## Karar

- **Bina içine düşen ızgara noktası en yakın sokağa taşınıyor.**
  Getirilen yol ağı beş metrede bir örnekleniyor; hiçbir binanın içinde
  olmayan ve satırın alanında kalan en yakın nokta seçiliyor
  (`placement._open_street_points`). Kızılay'da 4 nokta 17 ile 57 m
  arası taşındı. Direk türü, kavşak direği de, aynı kalıyor.
- **Şehir içi arama yeniden koşuldu** ("daha ucuz"): 19 direk; 16 yol
  kenarı, 2 ızgara noktası, 1 mevcut yapı. Hiçbiri bina içinde değil.

## Sonuç

- **Yayımlanan şehir içi satırı** (turda 8 direk):

| | Direk | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan km² | CAPEX/km² | OPEX/km²/yıl |
|---|---|---|---|---|---|---|---|---|
| Önce (ADR-0097, 4 direk bina içinde) | 21 | 2,03 | 9,84 | 4,00 | %96,86 | 8,32 | 9949 | 1915 |
| **Şimdi** | 19 | 2,03 | 9,80 | 3,96 | %96,37 | 8,14 | 9205 | 1771 |

Tutarlar TL. Km² başına CAPEX ve OPEX %7 düştü; kullanılabilirlik 0,5
puan, alan %2 azaldı. Kurulum 74925 TL, işletme yılda 14420 TL.

- **Turda 8 ve 12 direk,** tam çözünürlük, aynı direkler, yalnız
  `<satır>.anchors_per_round` değişiyor:

| Satır | Turda | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Tur süresi | Saniyede konum |
|---|---|---|---|---|---|---|---|
| Şehir içi | **8** | 2,03 | 9,80 | 3,96 | %96,37 | 534 ms | 1,87 |
| Şehir içi | 12 | 2,28 | 8,94 | 3,92 | %96,64 | 802 ms | 1,25 |
| Kırsal | **8** | 1,97 | 8,58 | 4,96 | %94,21 | 534 ms | 1,87 |
| Kırsal | 12 | 2,14 | 7,45 | 4,93 | %96,26 | 802 ms | 1,25 |

  Maliyet ikisinde aynı. On iki, HPE P95'i şehir içinde 0,86 m, kırsalda
  1,13 m iyileştiriyor, kullanılabilirliği 0,3 ve 2,1 puan artırıyor;
  bedeli HPE P50'de 0,17-0,25 m kötüleşme ve saniyede üçte bir daha az
  konum. ADR-0085'te sekiz öndeydi; o ölçüm ızgara, düz çizgi tur ve
  daire binalarla yapılmıştı.

## Kaynaklar

- Overture Maps Foundation, buildings ve transportation temaları, sürüm
  2026-08-19.0 (ayak izleri ve yol ağı).
