# Senaryo dökümü

Dört senaryonun her parametresi, kaynağı ve sonucu. Kod:
`yerkon/scenarios.py`, menzil değerleri `yerkon/link_budget.py`.

Kaynak sütunundaki etiketler:

- **Rapor**: YERKON raporundan alınmış değer.
- **Üretici**: modül üreticisinin yayımladığı değer.
- **Ölçüm**: yayımlanmış donanım ölçümünden geliyor.
- **Varsayım**: bu projenin seçimi; hiçbir kaynak bu değeri vermiyor.

Ortak parametreler: alıcı fix başına en yakın **8** anchor ile mesafe
ölçümü yapar (tünelde menzilde yalnız 5 olduğu için 5). Her senaryonun bir
de zaman-serili sürüş izi vardır; tablodaki doğruluk değerleri o iz boyunca
çalışan Kalman filtresinden gelir ([FUSION.md](FUSION.md)). Aşağıdaki
"tek-atım" sonuçlar filtresiz, yalnız radyo geometrisini gösterir. TWR her anchor için hava süresi harcar ve rapor alıcıyı "yeterli
sayıda yayın birimi ile konuşacak" diye tarif eder, menzildeki hepsiyle
değil. Sekiz, 3B fix için gereken dördün üstünde yedek bırakır ve
bağlantıları SX1280 ölçümlerinin kapsadığı mesafe aralığına yaklaştırır.

---

## 1. Şehir içi

Tabloda bir satır var, kalibreli olan. Aşağıdaki sütunlardan ikincisi aynı
kurulumun menzil ofseti kalibrasyonu atlanmış hâli. Birim sayısı, geometri
ve maliyet birebir aynı, tek fark o adım.

Kalibrasyonsuz kurulum tabloya ayrı bir satır olarak konmadı.
Karşılaştırma tablosundaki diğer sistemlerin hiçbiri kendisinin kasten
kalibre edilmemiş bir sürümünü satır olarak vermiyor, dolayısıyla o satır
sistemleri değil bir kurulum hatasını karşılaştırırdı. Buradaki
karşılaştırma o adımın ne kazandırdığını gösteriyor ve tabloyu
şişirmiyor.

| Parametre | Değer | Kaynak |
|---|---|---|
| Kapsama alanı | 1 km × 1 km = 1,00 km² | Varsayım (≥ 1 km² koşulu) |
| Anchor sayısı | 36 | Türetilmiş (ızgara) |
| Izgara aralığı | 175 m | Süpürmeyle seçildi ([CONFIGURATION.md](CONFIGURATION.md)) |
| Montaj yükseklikleri | 8 m direk, 20 m cephe, 35 m çatı (±0,75 m sapma) | Rapor (montaj sınıfları), Varsayım (dağılım) |
| Bağlantı menzili | 400 m = 3,0 km referansın %13'ü | Üretici + Varsayım (derating) |
| Menzil bant genişliği | 406 kHz | Süpürmeyle seçildi |
| Menzil hata modeli | SX1280, MATLAB dalga formu simülasyonu | Simülasyon |
| Menzil hatası σ | 2,40 m | Türetilmiş |
| Engellenen link oranı | %35 (sert NLOS) | Varsayım |
| Paket kaybı | %2 | Varsayım |
| Birim fiyat | 1366,07 TL | Rapor |
| Test yörüngesi | Hücreyi çapraz kesen doğru, 24 nokta, z = 1,5 m | Varsayım |

Raporun Grup 1 montaj listesi (baz istasyonları, trafik levhaları ve
lambaları, reklam panoları, yol kenarı ışıklandırmaları) 150 m'lik bir
ızgarayı destekler: şehir içi aydınlatma direkleri 25-40 m, kavşak
sinyalizasyonu 100-200 m aralıkla zaten mevcuttur.

Montaj yükseklikleri komşu anchor'lar arasında değişir. Tek yükseklikte bir
ızgara eş düzlemlidir ve dikey ekseni hiç çözemez.

### Ölçülen geometri ve sonuç

| | Kalibreli (tablo satırı) | Kalibrasyonsuz |
|---|---|---|
| Düğüm sayısı, aralık | 36, 175 m | 36, 175 m |
| Menzil bant genişliği | 406 kHz | 406 kHz |
| Menzil hatası σ | 2,40 m | 2,40 m |
| Menzilde duyulan / kullanılan (en az) | 15 / 8 (5) | 15 / 8 (5) |
| Medyan / en uzun bağlantı | 202 m / 392 m | 202 m / 392 m |
| Kanıt zarfı dışındaki bağlantı | %0,0 | %0,0 |
| HDOP / VDOP (medyan) | 0,73 / 2,79 | 0,73 / 2,79 |
| En kötü VDOP | 10,53 | 10,53 |
| Tek atım HPE P50 / P95 | 1,44 m / 3,69 m | 2,04 m / 4,98 m |
| Tek atım VPE P50 / P95 | 4,56 m / 29,82 m | 18,38 m / 48,56 m |
| Filtreli HPE P50 / P95 | **1,64 m / 3,40 m** | **2,15 m / 4,82 m** |
| Filtreli VPE P50 / P95 | **0,44 m / 1,00 m** | **0,43 m / 1,04 m** |
| Kullanılabilirlik | %100,0 | %100,0 |
| CAPEX | 49179 TL/km² | 49179 TL/km² |

Sürüş izi: 50 km/h'de, 2,5 derece/s dönüşle hücre içinde kalan bir
yay üzerinde 180 saniye, ±1,2 m şerit değişimiyle. Dönüş kasıtlı: hep düz
giden bir alıcı IMU pusula hatasını hiç sınamaz.

Kalibrasyonun etkisi filtre sonrasında da sürüyor. Sabit ofset tüm
anchor'lara aynı anda bindiği için ne geometri ne de filtreleme onu
kaldırabiliyor; dikeyde ise fark kapanıyor, çünkü orada belirleyici olan
harita kısıtı.

Kalibrasyon yatay hatayı %18, dikey hatayı %29 iyileştiriyor. Sabit sapma
dikey eksende daha çok büyütülür, çünkü o eksenin DOP'u daha yüksektir.

### Izgara aralığı ne satın alıyor

Aynı hücre, farklı ızgara aralıklarıyla (400 m menzil, en yakın 8 anchor):

| Aralık | Birim | HDOP | VDOP | Medyan bağlantı | CAPEX TL/km² |
|---|---|---|---|---|---|
| 100 m | 121 | 0,75 | 1,57 | 112 m | 165294 |
| 150 m | 49 | 0,73 | 2,29 | 181 m | 66937 |
| 175 m (kullanılan) | **36** | **0,73** | **2,79** | **202 m** | **49179** |
| 200 m | 36 | 0,73 | 3,03 | 225 m | 49179 |
| 250 m | 25 | 0,78 | 4,12 | 248 m | 34152 |
| 300 m | 16 | 1,02 | 5,58 | 241 m | 21857 |

Sıklaştırmak neredeyse yalnızca dikey doğruluk satın alıyor: HDOP 100 ile
250 m arasında sabit kalırken VDOP 2,6 kat değişiyor. Sebebi, en yakın 8
anchor kuralının yatay dağılımı zaten koruması, dikey açının ise doğrudan
mesafeye bağlı olmasıdır.

---

## 2. Kırsal

Rapor Grup 2 için "az sayıda yüksek kapsamalı nokta" istiyor ve montaj
noktası olarak AUS/yol kenarı üniteleri ile baz istasyonu sahalarını
sayıyor. Yerleşim buna göre kuruldu.

| Parametre | Değer | Kaynak |
|---|---|---|
| Koridor uzunluğu | 42 km | Varsayım (≥ 1 km² koşulu) |
| Kapsama | İki hat arası 24 m taşıt yolu = 1,01 km² | Varsayım |
| Yol kenarı anchor'ı | 500 m'de bir, iki yanda karşılıklı, 6 m (±0,5 m) | Rapor (AUS/RSU noktaları), Varsayım (aralık) |
| Kule anchor'ı | 2,5 km'de bir, 35-45 m, yoldan 30 m açıkta | Rapor (baz istasyonu sahaları), Varsayım (aralık) |
| Toplam anchor | 170 yol kenarı + 17 kule = 187 | Türetilmiş |
| Bağlantı menzili | 3000 m = 8,0 km referansın %37,5'i | Üretici + Varsayım (derating) |
| Menzil hata modeli | SX1280, Robinson bootstrap, kalibreli | Ölçüm |
| Menzil hatası σ | 3,05 m | Türetilmiş |
| NLOS oranı ve sapması | %15, 2,0 m | Varsayım |
| Paket kaybı | %1 | Varsayım |
| Birim fiyat | 1082,68 TL | Rapor |
| Test yörüngesi | Taşıt yolunda zikzak (±10,8 m), 24 nokta | Varsayım |

E28-2G4M27S modülü BOM'a göre SX1280 tabanlıdır. Yükselteç link bütçesini
değiştirir, menzil ölçüm hatası mekanizmasını değil; bu yüzden aynı hata
modeli kullanıldı. Yine de bağlantıların %72'si Robinson verisinin
kapsadığı 0-250 m aralığının dışında kalıyor. Bu bir çıkarsamadır ve JSON
çıktısında `links_beyond_calibrated_envelope` alanında raporlanır.

### Ölçülen geometri ve sonuç

| | Değer |
|---|---|
| Düğüm sayısı, levha aralığı | 131, 750 m |
| Menzil bant genişliği | 812 kHz |
| Menzil hatası σ | 3,98 m |
| Menzilde duyulan / kullanılan (en az) | 18 / 8 (8) |
| Medyan / en uzun bağlantı | 620 m / 1750 m |
| Kanıt zarfı dışındaki bağlantı | %0,0 |
| HDOP / VDOP (medyan) | 8,54 / 15,29 |
| En kötü VDOP | 40,21 |
| Tek atım HPE P50 / P95 | 5,91 m / 35,24 m |
| Tek atım VPE P50 / P95 | 6,56 m / 30,40 m |
| Filtreli HPE P50 / P95 | **2,55 m / 3,86 m** |
| Filtreli VPE P50 / P95 | **0,35 m / 1,00 m** |
| Kullanılabilirlik | %100,0 |
| CAPEX | 140705 TL/km², 3377 TL/km |

Sürüş izi: 110 km/h'de koridor boyunca 180 saniye (5,5 km), ±3 m şerit
değişimiyle.

Kırsalın yatay hatası yol boyunca değil, yola dik yönde. Anchor'lar yol
boyunca 42 km'ye yayılırken yola dik yönde 60 m'lik bir şeritte kalıyor,
dolayısıyla menzil ölçümü yol boyunca konuma dik yöndekinden dokuz kat
duyarlı. Yanal harita kısıtı bunu kapatıyor ve HPE P95'i 26,49 m'den
3,86 m'ye indiriyor. Ayrıntısı README'de.

### Nokta sıklığı ne satın alıyor

42 km koridor, kuleler 2,5 km'de bir sabit:

| Yol kenarı aralığı | Birim | HDOP | VDOP | Medyan bağlantı | TL/km | TL/km² |
|---|---|---|---|---|---|---|
| 1000 m | 103 | 12,12 | 16,01 | 838 m | 2655 | 110631 |
| 750 m (kullanılan) | **131** | **8,54** | **15,29** | **620 m** | **3377** | **140705** |
| 500 m | 187 | 5,84 | 11,56 | 458 m | 4821 | 200854 |
| 300 m | 299 | 4,68 | 9,48 | 274 m | 7708 | 321152 |
| 200 m | 439 | 2,95 | 6,80 | 196 m | 11317 | 471524 |

Raporun "az sayıda nokta" tercihi burada ölçülebilir hale geliyor. 200 m
aralık VDOP'u 6,80'e indiriyor ama km başına maliyeti 3,4 katına çıkarıyor.
Seçilen 750 m, rapor metnine sadık kalan ve dört anchor'ı her noktada menzilde
tutan seçim.

### Kuleler ne yapıyor

Kuleler yol kenarı ünitelerinden 30-40 m daha yüksektir ve dikey geometriye
tek anlamlı katkıyı onlar yapar. Ama en yakın 8 anchor kuralında kuleler
çoğu zaman seçilmez: yol kenarı noktaları 500 m'de bir, kuleler 2,5 km'de
birdir, yani en yakın kule medyan 600 m uzaktadır.

Sekiz yuvadan birini en yakın kuleye ayıran bir seçim kuralı denendi:
VDOP 11,56'dan 10,50'ye iniyor, HDOP değişmiyor. %9'luk kazanç modeli
karmaşıklaştırmayı hak etmedi, ama gerçek bir alıcı yazılımında geometriye
duyarlı anchor seçimi bedelsiz bir iyileştirmedir.

Kazancın küçük kalmasının sebebi yine açı: 600 m mesafedeki 40 m'lik bir
kule 3,67 derecelik bir bakış açısı verir, 250 m'deki 6 m'lik bir yol
kenarı ünitesi 1,03 derece. İkisi de dik değildir.

---

## 3. Kritik bölge (tünel)

| Parametre | Değer | Kaynak |
|---|---|---|
| Tünel uzunluğu | 50 km | Varsayım (≥ 1 km² koşulu) |
| Tünel genişliği | 20 m | Varsayım |
| Kapsama alanı | 50 km × 20 m = 1,00 km² | Türetilmiş |
| Düğüm aralığı | 60 m | Türetilmiş (bağlantı menzilinden) |
| Anchor sayısı | 834 | Türetilmiş |
| Montaj | Duvar (1,2-1,3 m) ve tavan (4,3-4,4 m), dört adımlı döngü | Varsayım |
| Bağlantı menzili | 150 m | Varsayım (yayımlanmış üst sınır yok) |
| Menzil hata modeli | DWM3000, MATLAB dalga formu simülasyonu | Simülasyon |
| Menzil hatası σ | 0,35 m | Türetilmiş |
| Paket kaybı | %3 | Varsayım |
| Birim fiyat | 1634,44 TL | Rapor |
| Test yörüngesi | Tünel boyunca doğru, 24 nokta | Varsayım |

### Düğüm aralığı neden raporun öngördüğünden küçük

Rapor pilot için 2 km koridora 10-15 düğüm öngörüyor, yani ~150 m aralık.
Bir doğru boyunca S aralıklı düğümler ve R menzil ile alıcı yaklaşık `2R/S`
düğüm duyar. 3B fix dört ölçüm ister, dolayısıyla `S ≤ 2R/4 = R/2`.
R = 150 m için tavan 75 m'dir (`link_budget.minimum_spacing_for_fix`).

| Düğüm aralığı | Menzildeki düğüm (en az) | HDOP | VDOP | TL/km | Toplam TL |
|---|---|---|---|---|---|
| 150 m | 2 | çözüm yok | çözüm yok | 10885 | 544269 |
| 100 m | 2 | çözüm yok | çözüm yok | 16344 | 817220 |
| 75 m | 4 | 3,83 | 15,02 | 21771 | 1088537 |
| **60 m (kullanılan)** | **5** | **3,10** | **14,14** | **27230** | **1361489** |
| 50 m | 5 | 2,61 | 11,04 | 32689 | 1634440 |

60 m, tavanın altında kalıp beşinci düğümü menzilde tutar. Bu, raporun
pilot yoğunluğunu yaklaşık 2,5 katına çıkarır.

Bu sonuç tek bir varsayıma, 150 m'lik bağlantı menziline dayanıyor. Gerçek
menzil 300 m ise raporun 150 m aralığı çalışır; 75 m ise 30 m aralık
gerekir. DWM3000 için üretici bir üst sınır yayımlamadığından bu belirsizlik
giderilemedi ve sonuç bu koşula bağlı olarak okunmalıdır.

### Montaj deseni

Desen dört adımlıdır, iki değil. İki adımlı bir desen (bir duvar, bir tavan)
tüm anchor'ları iki paralel doğru üzerine yerleştirir ve 3B'de iki paralel
doğru her zaman eş düzlemlidir; dikey eksen kaç anchor eklenirse eklensin
çözülemez. Bir test bunu koruma altına alıyor
(`test_two_parallel_lines_of_anchors_are_coplanar`).

### Ölçülen geometri ve sonuç

| | Değer |
|---|---|
| Düğüm sayısı, aralık | 834, 60 m |
| Menzil hatası σ | 0,35 m |
| Menzilde duyulan / kullanılan (en az) | 5 / 5 (5) |
| Medyan / en uzun bağlantı | 75 m / 149 m |
| HDOP / VDOP (medyan) | 3,16 / 13,49 |
| En kötü VDOP | 21,84 |
| Tek atım HPE P50 / P95 | 0,24 m / 2,70 m |
| Tek atım VPE P50 / P95 | 1,04 m / 5,46 m |
| Filtreli HPE P50 / P95 | **0,43 m / 1,45 m** |
| Filtreli VPE P50 / P95 | **0,25 m / 0,69 m** |
| Kullanılabilirlik | %99,3 |
| CAPEX | 1363123 TL/km², 27262 TL/km |

Sürüş izi: 80 km/h'de tünel boyunca 180 saniye (4 km), ±1,5 m şerit
değişimiyle.

Yardımcı sensörler tünelde de en çok dikeyde işe yarıyor. Odometri, pusula
ve harita kapatıldığında yatay P95 1,45 m'den 2,55 m'ye, dikey P95 ise
0,69 m'den 6,70 m'ye çıkıyor.

Burada daha önce "tünel, sensör füzyonunun zorunlu olduğu tek senaryo,
onlarsız yatay P95 295 m'ye çıkıyor" diye bir bulgu yazmıştım. O bir
artefaktmış ve geri alındı. Sebebi
[WAVEFORM.md](WAVEFORM.md#geri-alınan-bir-bulgu) içinde: menzil hatası
raporun hedefine göre alındığı için aykırı değer kapısı fazla dar
kalıyordu, ve NLOS iki kez sayılıyordu.

DOP değerleri dört senaryonun ortasında, sonuçlar ise açık ara en iyisi.
Bu bir çelişki değil. UWB'nin menzil hatası σ = 0,35 m, SX1280'in 2,40
m'sinin yedide biri. Kötü geometri küçük bir hatayı büyütüyor ve yine de
küçük kalıyor.


---

## Dört anchor sınırına yakınlık

3B konum çözümü en az dört mesafe ölçümü ister. Senaryolar bu sınıra çok
farklı mesafelerde duruyor ve fark kullanılabilirlik sütununda görünüyor.

| Senaryo | Menzilde | Kullanılan | Sınıra pay | Kullanılabilirlik |
|---|---|---|---|---|
| Şehir içi | 20 | 8 | 4 ölçüm | %100,0 |
| Kırsal | 26 | 8 | 4 ölçüm | %100,0 |
| Tünel | 5 | 5 | 1 ölçüm | %99,3 |

Paket kaybı her anchor için ayrı ayrı uygulanır. TWR her anchor ile ayrı
bir alışveriştir, dolayısıyla kaybolan bir alışveriş bir ölçümü götürür,
tüm konumu değil. Sekiz ölçümü olan bir alıcı dördünü birden kaybetmedikçe
konum üretir; beş ölçümü olan bir alıcı ikisini kaybettiğinde üretemez.

Tünelde beş anchor'ın hepsinin kullanılmasının sebebi menzilde daha
fazlasının olmaması. Bu, düğüm aralığını 60 m'nin altına indirmek için ek
bir gerekçedir: 50 m aralıkta alıcı yedi anchor duyar ve iki kayba
dayanabilir, ama tünel CAPEX'i 32689 TL/km'ye çıkar.

Şehir içi ve kırsalda %100,0 değeri 7200 denemenin tamamında çözüm
üretildiği anlamına gelir. Yalnızca modellenen paket kaybı altındaki
radyo bağlantısı kullanılabilirliğidir; kanal doluluğu, girişim, düğüm
arızası ve alıcı açılış süresi modellenmedi.
