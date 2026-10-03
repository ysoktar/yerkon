# ADR-0100: harcırah kanundan, montaj ve bakım kaynaklı bileşenlerden; harici anten gerekli

## Durum

Kabul edildi (proje sahibinin isteği, 27 Eylül 2026: harcırah kaynaklı
anlatılsın, varsayımlar azalsın, anten gerekli mi ölçülsün). ADR-0089'un
"doğrulanmayanlar" bölümünün ve ADR-0090'daki 1800 TL'lik ziyaret
bedelinin yerine geçiyor.

## Harcırah

- **Ne:** görev yeri dışına geçici görevle gönderilen çalışana yol
  gideriyle ödenen gündelik (6245 sayılı Harcırah Kanunu). Özel sektörde
  vergiden istisna kısım, aynı aylık seviyesindeki devlet memurunun
  gündeliği (193 sayılı Gelir Vergisi Kanunu, Madde 24/2).
- **Ne kadar:** 2026 H Cetveli, 5-15. derece, 850 TL/gün (7567 sayılı
  Kanun).
- **Nerede:** büyükşehirde görev yeri, çalışanın bağlı olduğu ilçenin
  belediye sınırı ve onun devamı olan yerleşim yerleri (Madde 3/g).
  ADR-0089'daki açık soru kapandı: Çankaya'daki bir ekip için Kızılay
  görev yeri, Polatlı ve Kızılcahamam görev yeri dışı.
- **Günübirlik:** öğle (13.00) ya da akşam (19.00) yemeği zamanlarından
  birini dışarıda geçirene 1/3, ikisini geçirene 2/3, geceyi geçirene
  tam gündelik (Madde 39). ADR-0089 tamamını almıştı; model artık 1/3
  alıyor (`operating.per_diem_share`): kişi başı 283,33 TL.
- Bugün üç satırda da sıfır: ekip kendi ilçesinde ya da bakım yerel
  firmada (ADR-0090). Mevzuat sayfasına kaynaklı bir "Harcırah" bölümü
  eklendi; maliyet sayfasındaki "per diem" satırı "Harcırah" oldu.

## Montaj ve bakım

Tek bir ekip günü iki kaynaktan hesaplanıyor:

- Sepetli araç: Ankara'da 20 m sepetli araç saati yaklaşık 2000 TL,
  günlük kiralamada %30 indirim (Ankara Sepetli Vinç Kiralama, fiyat
  rehberi): 2000 x 8 x 0,7 = 11200 TL.
- İşçilik: elektrik ustası aylık 80000-110000 TL, düz işçi günlük
  2500-3200 TL, büyükşehirde üst banda yakın (Yapı Arenası, 12 Ağustos
  2026). Usta 95000 / 30 = 3170 TL, yardımcı 3200 TL.
- Ekip günü: 17570 TL.

| Kalem | Önce | Şimdi | Hesap |
|---|---|---|---|
| Aydınlatma direğine montaj | 2450 | 2500 | 17570 / 8 + 300 malzeme |
| Dağıtım direğine montaj | 4600 | 4690 | 17570 / 4 + 300 |
| Çatıya montaj | 1800 | 1890 | 6370 / 4 + 300 (araç yok) |
| Tünel askısı | 6000 | 4690 | 17570 / 4 + 300 (şerit kapatmaya bağlı) |
| Bakım ziyareti | 1800 | 2200 | 17570 / 8 (ADR-0101 ile yapıya göre: kırsalda ve tünelde 17570 / 4) |

Tutarlar TL. Hâlâ bu projenin varsayımı olanlar: günde kaç birim (8 ya
da 4), birim başına 300 TL malzeme, dağıtım direği kirası (ayda 100 TL;
karşılaştırma için İBB 2025 tarifesi bir repeater ya da small cell için
yılda 24500 TL alıyor), 25 m direk (85000 TL), elektrik birim fiyatı,
merkezî sistem.

## Sonuç (27 Eylül koşusu)

| | CAPEX önce | CAPEX şimdi | OPEX önce | OPEX şimdi |
|---|---|---|---|---|
| Şehir içi, TL/km² | 8905 | 9022 | 1742 | 1928 |
| Kırsal, TL/km² | 1305 | 1317 | 331 | 352 |
| Tünel, TL/km | 130755 | 108485 | 13239 | 14599 |

Doğruluk ve kullanılabilirlik değişmedi.

## Anten: gerekli mi

Harici anten olmadan direk ve araç, modülün kart üstü PCB anteniyle
çalışır. EBYTE bu antenin kazancını vermiyor (E28-2G4M20S kullanım
kılavuzu v1.30, 9. bölüm); tüneldeki gibi ölçülene kadar 0 dBi alındı.
Aynı direkler, tam çözünürlük:

| | Anten | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan km² | CAPEX/km² | OPEX/km²/yıl |
|---|---|---|---|---|---|---|---|---|
| Şehir içi | **5 dBi** | 2,28 | 8,94 | 3,92 | %96,64 | 8,14 | 9022 | 1928 |
| Şehir içi | kart üstü | 2,37 | 9,01 | 3,97 | %94,18 | 6,56 | 9787 | 2253 |
| Kırsal | **5 dBi** | 2,14 | 7,45 | 4,93 | %96,26 | 361,83 | 1317 | 352 |
| Kırsal | kart üstü | 2,27 | 8,20 | 4,97 | %90,22 | 319,58 | 1414 | 391 |

- Birim 1000 adette 1365,12 TL'den 877,33 TL'ye iniyor, ama kapsanan
  alan şehir içinde %19, kırsalda %12 küçülüyor. Km² başına maliyet
  antensiz daha yüksek.
- Düz zeminde menzil yaklaşık %24 kısalıyor: 12 m direkten bağlantı
  8,8 km yerine 6,7 km, 5 m hassasiyet 6,6 km yerine 5,0 km.
- **Karar:** 5 dBi harici anten kalıyor.

## Kaynaklar

- 6245 sayılı Harcırah Kanunu, Madde 3/g ve 39.
- 193 sayılı Gelir Vergisi Kanunu, Madde 24/2.
- 7567 sayılı 2026 Merkezi Yönetim Bütçe Kanunu, H Cetveli.
- Ankara Sepetli Vinç Kiralama, fiyat rehberi (2026).
- Yapı Arenası, 2026 usta yevmiyeleri (12 Ağustos 2026).
- İBB Elektronik Sistemler Şube Müdürlüğü, 2025 ücret tarifesi.
- EBYTE, E28-2G4M20S kullanım kılavuzu v1.30.
