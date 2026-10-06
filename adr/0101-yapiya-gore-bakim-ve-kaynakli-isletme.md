# ADR-0101: bakım ziyareti yapıya göre; işletme bedelleri kaynaklı

## Durum

Kabul edildi (proje sahibinin isteği, 27 Eylül 2026: dağıtım direği kirası
araştırılsın, kırsal bakım ziyareti bulunsun, geri kalanlar varsayım
denmeden kaynaklarıyla açıklansın). ADR-0100'deki tek bakım ziyareti
bedelinin (2200 TL) yerine geçiyor.

## Bakım ziyareti yapıya göre

ADR-0100 bakım ziyaretini her yerde günde sekiz birimden fiyatlıyordu.
Montaj ise kırsalda ve tünelde günde dört birimden fiyatlanıyordu; ziyaret
aynı ekip ve aynı araç olduğu için bu tutarsızdı. Artık:

- `operating.crew_day_tl` = 17570 TL: sepetli araç 2000 x 8 x 0,7 = 11200,
  usta 3170, yardımcı 3200 (ADR-0100'deki kaynaklar).
- Her yapının `mounting.<yapı>.per_crew_day` değeri, ekibin o yapıda günde
  uğradığı birim sayısı. Bir ziyaret, ekip gününün bu sayıya bölünmüşü.
  Harcırah da gün başına ödendiği için aynı sayıya bölünüyor.
- Çatıda sepetli araç yok: `mounting.rooftop.crew_day_tl` = 6370 TL.

| Yapı | Günde | Ziyaret | Dayanağı |
|---|---|---|---|
| Aydınlatma direği | 8 | 2196 TL | Dicle Elektrik, Suriçi, 25 Haziran 2026: 11 ekip bir hafta sonunda 207 direkte 414 armatür; iki günün 12'şer saati sayılırsa ekip başına sekiz saatte 12,5 armatür. 8 bunun altında. |
| Kırsal dağıtım direği | 4 | 4392 TL | Direk başına bir saat iş (üstteki satır), sekiz saatin ikisi merkeze gidiş dönüş, sahalar arası yarım saat: (8 - 2) / (1 + 0,5) = 4. Yol süreleri bu projenin tahmini. |
| Tünel askısı | 4 | 4392 TL | Karayolları'nın şerit kapatmasına bağlı iş; kapatmaya giden süre kırsaldaki yol gibi sayıldı. |
| Çatı | 4 | 1592 TL | İzin ve anahtar için yönetici bulmak; araçsız ekip günü 6370 TL. |
| 25 m direk | 4 | 4392 TL | Kırsaldaki direkle aynı sayı. |

## Kaynaklanan diğer bedeller

- **Elektrik:** 3,20 yerine 5,62 TL/kWh. Ticarethane, alçak gerilim, tek
  zamanlı, vergiler dahil 4,78 TL/kWh (Ocak 2026, forelektrik.com) ve
  4 Nisan 2026 zammı, alçak gerilim kamu ve özel hizmetler %17,5 (Milliyet
  Uzmanpara): 4,78 x 1,175. Birim aydınlatma direğinin genel aydınlatma
  hattından bedava beslenemez; Genel Aydınlatma Yönetmeliği bağlantı
  noktasından genel aydınlatma dışında bir amaca enerji verilmesine izin
  vermiyor.
- **Güneş seti:** 2330 yerine 2090 TL, parça parça Akakçe'den (Eylül 2026):
  panel 518,72, akü 524,40, 10 A PWM denetleyici 276,67, ABS braket seti
  421,01, IP65 buat 147,41, 5 m solar kablo 200 (metresi 25-40 TL, Power
  Enerji). Toplam 2088,21.
- **Şebeke dışı ek ziyaret:** 0,2/yıl, akünün 5 yıllık ömründen (GİB
  amortisman listesi 3.14.7).
- **Ekip:** 2 kişi, ekip gününe fiyatlanan usta ve yardımcı; sepetli aracın
  operatörü kiraya dahil.
- **Merkezî sistem:** 240000 yerine 237000 TL/yıl. Bir yazılımcının haftada
  bir günü, net medyan 95000 TL (Yazılımcı Maaşları 2026 anketi, 1223
  kişi): 228000; iki sanal sunucu, aylık 374,90 TL (Karekod, 25 Eylül
  2026): 8998. Haftada bir gün ve bin birime yayılması işletme kararı.

## Kaynağı bulunamayanlar

- **Dağıtım direği kirası:** dağıtım şirketlerinin direğe cihaz için
  yayımladığı bir bedel yok. Ulaştırma Bakanlığı'nın geçiş hakkı usul ve
  esasları, Türk Telekom'un bağlantı ve nakil ücretleri ve Genel
  Aydınlatma Yönetmeliği direk başına bir bedel yazmıyor. Karşılaştırma
  için bulunanlar: dağıtım şirketleri 2015'ten beri EPDK izniyle direkte
  reklam alanı kiralıyor (en küçük afiş ayda 4700 TL, Tr724, 2019); İBB
  2025 tarifesi small cell için yıllık 24500 TL, BEDAŞ/AYEDAŞ aydınlatma
  direğindeki kabinet için yer seçim belgesi ücretinin iki katı.
  **Karar (proje sahibi, 28 Eylül 2026): kira sıfır**, kamu protokolüyle;
  birimlerin AUS gibi hazır kamu yapılarına dahil edilebilmesi
  öngörülüyor. Dipnotlarda (site, sunum) belirtiliyor. Çatı kirası
  (1200 TL/yıl, bina sahibine) varsayım olarak kaldı; kırsalda bir çatı var.
- **25 m direk (85000 TL):** 25 m için yayımlanmış bir fiyat bulunamadı
  (yayımlanan aydınlatma direği fiyatları 10 m'ye kadar; projektör direği
  üreticileri teklifle satıyor). Kırsal satırda bir tane var.
- **Yükseklikler** (aydınlatma direği 12 m, dağıtım direği 10 m) ve
  **yılda 0,2 arıza ziyareti** kaynaksız kaldı.

## Sonuç

| Satır | Önce | Sonra |
|---|---|---|
| Şehir içi OPEX | 1928 TL/km²/yıl | 1936 TL/km²/yıl |
| Kırsal CAPEX | 1317 TL/km² | 1287 TL/km² |
| Kırsal OPEX | 352 TL/km²/yıl | 458 TL/km²/yıl |
| Tünel OPEX | 14599 TL/km/yıl | 22126 TL/km/yıl |

Doğruluk ve kullanılabilirlik değişmedi. Kırsal ve tünel OPEX'i arttı,
çünkü oradaki ziyaret artık montajla aynı hızda, günde dört birimden
fiyatlanıyor. Kırsal satırda varsayıma dayanan pay %78,5'ten %56,6'ya indi;
kalanı 25 m direk ve kira. Kira sıfırlandıktan sonra kırsal OPEX 458'den
312 TL/km²/yıl'a indi (bkz. aşağı).

## Kira sıfır (28 Eylül 2026)

`mounting.distribution_pole.rent_tl_per_year` 1200'den 0'a indi,
dayanağı "tasarım kararı: kamu protokolü". Kırsal OPEX yılda 52800 TL
azaldı: 165665'ten 112865 TL'ye, 458'den 312 TL/km²/yıl'a. Protokol
olmazsa direk başına 1200 TL kırsal OPEX'i yaklaşık %47 artırır.

Sitede ve sunumda alan hücreleri "≈ 148,94 milyon" oldu; dipnot 4
okyanuslar dahil tüm yüzeyi (yaklaşık 510,06 milyon km², NASA) ve karanın
payını (yaklaşık %29) veriyor. YERKON CAPEX dipnotu OPEX'i de açıklıyor ve
OPEX hücrelerine de bağlı.
