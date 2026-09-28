# ADR-0103: kartın geri kalanı parça parça; direk boyları ve fiyatları kaynaklı

## Durum

Kabul edildi (proje sahibinin isteği, 28 Eylül 2026: sunumda olmayan
parçaların fiyatı bulunsun, bütün direklerin boyu ve fiyatı bulunsun,
yükseklikler küme olarak simülasyonda denensin, maliyet sayfası
okunur olsun).

## Kartın geri kalanı

Raporun "diğer" satırı (güç dönüşümü, koruma, bağlantı, kutu) raporun
toplamından ana parçalar çıkarılarak bulunuyordu. Artık parça parça
yazılı ve fiyatı ona göre hesaplanıyor; raporun kalanı karşılaştırma için
yanında duruyor.

| Parça | Görevi | 1 adet | Toplu | Kaynak |
|---|---|---|---|---|
| HLK-5M12 | 230 V'tan 12 V, 5 W | 2,84 $ | 1,59 $ (1000) | LCSC C209908 |
| TPS563200 | 12 V'tan 3,3 V | 1,03 $ | 0,67 $ (1000) | LCSC C97253 |
| SMBJ18A | aşırı gerilim koruması | 0,15 $ | 0,10 $ (500) | LCSC C151256 |
| 10D471K | varistör | 0,12 $ | 0,07 $ (500) | LCSC C316609 |
| SMD1206P050TF | sigorta, 500 mA | 0,10 $ | 0,06 $ (500) | LCSC C106264 |
| SS34 | ters kutup diyodu | 0,04 $ | 0,03 $ (600) | LCSC C8678 |
| 2 x KF301 | klemens | 0,20 $ | 0,13 $ (1000) | LCSC C474881 |
| IPEX-SMA | anten kablosu | 1,05 $ | 0,54 $ (1000) | LCSC C403729 |
| Gainta G203 | IP65 kutu, 115x65x40 | 4,99 € | yayımlanmamış | gainta.com |
| Pasifler | 25 parça | 0,79 $ | 0,44 $ (1000) | LCSC |
| Baskılı devre | iki kat | 0,40 $ | yayımlanmamış | JLCPCB, 5 kart 2 $ |
| Dizgi | 150 lehim noktası | 8,32 $ | 0,64 $ (100) | JLCPCB yardım sayfası |

Tünel biriminde anten kablosu yok. Yaya alıcısında LiPo pil (YDL,
4,27 $), şarj ve koruma (TP4056, DW01A, FS8205), USB-C, 3,3 V
düzenleyici ve el tipi kutu (Gainta G517, 1,86 €); araç alıcısında 80 V'a
dayanan düşürücü (XL7015), SMBJ33A, klemensler, USB-C, anten kablosu ve
kutu (Gainta G212, 5,98 €) var. Euro 4 Eylül 2026 kuruyla (1,1622 $)
çevrildi.

1000 adette yayın birimi 1365,12'den 1288,87 TL'ye, tünel birimi
1691,48'den 1595,56 TL'ye indi. Tek adet fiyatı yükseldi, çünkü dizginin
kurulum bedeli beş kartlık bir siparişe bölünüyor.

## Direk boyları ve fiyatları

- Aydınlatma direği: TEDAŞ'ın LED'li yol aydınlatma usul ve esasları
  (Ağustos 2022, Ek-1), yol sınıfına göre 6, 8, 10, 12, 14 m. Fiyatlar
  (Pana, Eylül 2026): 6 m 6500, 8 m 9750, 10 m 14750, 12 m 18250, 14 m
  24750, 15 m 27500 TL.
- Dağıtım direği: TEDAŞ-MLZ/99-34, 9,3-25 m. İletkene en az 2,5 m (orta
  gerilim) Elektrik Kuvvetli Akım Tesisleri Yönetmeliği'nden. Gömülme
  derinliği için kaynak bulunamadı; değer varsayım olarak kaldı.
- 25 m direk: 20 m galvaniz direk 120000 TL, 30 m 475000 TL (Pana). 25 m
  için modelin kuralı (bedel yüksekliğin karesiyle artar) 187500 TL
  veriyor; montajla 191890 TL. Eski 85000 TL, 20 m'nin fiyatının bile
  altındaydı.

Yükseklikler kümenin değerlerinde koşuldu:

| Aydınlatma direği | HPE P95 | Kullanılabilirlik | Alan km² | CAPEX TL/km² |
|---|---|---|---|---|
| 8 m | 9,19 | %94,94 | 7,34 | 10010 |
| 10 m | 9,04 | %96,30 | 7,90 | 9296 |
| 12 m | 8,94 | %96,64 | 8,14 | 9022 |
| 14 m | 8,74 | %96,82 | 8,24 | 8916 |

| Dağıtım direğinde birim | HPE P95 | Kullanılabilirlik | Alan km² |
|---|---|---|---|
| 6 m | 7,99 | %94,29 | 337,67 |
| 8 m | 7,64 | %95,27 | 352,67 |
| 10 m | 7,45 | %96,26 | 361,83 |

Hangi değerin kullanılacağı proje sahibinin kararına bırakıldı; model
şimdilik 12 m ve 10 m ile kalıyor.

## Sayfalar

- Sonuçlar sayfasındaki "Şehir içi neden bu kadar ucuz" bölümü kaldırıldı;
  şehir içi satırı km² başına en pahalısı. Yerine Maliyet sayfasında
  "Yayın birimleri" bölümü var: bir birimin her yapıdaki kurulum ve
  işletme bedeli ve satırların km² başına neden farklı olduğu (yoğunluk).
- "Her varsayım" tablosu "Her sayının dayanağı" oldu: konu gruplarına
  ayrılmış, numaralı bir liste; her sayı değeri, türü, nasıl hesaplandığı
  ve kaynağıyla.
- Mevzuat sayfasına direk boyları ve iletken mesafesi (TEDAŞ, EKATY) ile
  kamu yapısında yer kullanımı (3194 sayılı Kanun Ek 9/7, Genel Aydınlatma
  Yönetmeliği) eklendi.

## Yeniden yayım (28 Eylül 2026)

25 m direk gerçek fiyatına çıkınca kırsal yerleşim araması onu bıraktı:
52 birim (46 dağıtım direği, 4 aydınlatma direği, 2 çatı). Eski yerleşim
yeni fiyatlarla yaklaşık 1568 TL/km² tutardı; yenisi 1107 TL/km².
Doğruluk biraz düştü: HPE P95 7,45'ten 8,02 m'ye, kullanılabilirlik
%96,26'dan %94,85'e; ikisi de 10 m hedefinin içinde.

| Satır | HPE P50 | P95 | VPE P95 | Kullanılabilirlik | Alan | CAPEX | OPEX |
|---|---|---|---|---|---|---|---|
| Şehir içi | 2,28 | 8,94 | 3,92 | %96,64 | 8,14 km² | 8844 TL/km² | 1919 |
| Kırsal | 2,16 | 8,02 | 4,95 | %94,85 | 354,83 km² | 1107 TL/km² | 329 |
| Tünel | 0,58 | 2,43 | 3,31 | %94,32 | güzergâh | 106855 TL/km | 21963 |
