# Senaryo dökümü

Dört senaryonun her parametresi, kaynağı ve sonucu. Kod:
`yerkon/scenarios.py`, menzil değerleri `yerkon/link_budget.py`.

Kaynak sütunundaki etiketler:

- **Rapor**: YERKON raporundan alınmış değer.
- **Üretici**: modül üreticisinin yayımladığı değer.
- **Ölçüm**: yayımlanmış donanım ölçümünden geliyor.
- **Varsayım**: bu projenin seçimi; hiçbir kaynak bu değeri vermiyor.

Ortak parametre: alıcı fix başına en yakın **8** anchor ile mesafe ölçümü
yapar. TWR her anchor için hava süresi harcar ve rapor alıcıyı "yeterli
sayıda yayın birimi ile konuşacak" diye tarif eder, menzildeki hepsiyle
değil. Sekiz, 3B fix için gereken dördün üstünde yedek bırakır ve
bağlantıları SX1280 ölçümlerinin kapsadığı mesafe aralığına yaklaştırır.

---

## 1-2. Şehir İçi (Kalibreli ve Ham)

İki satır aynı kurulumdur. Tek fark menzil ofseti kalibrasyonunun
uygulanıp uygulanmadığıdır; birim sayısı, geometri ve maliyet birebir
aynıdır.

| Parametre | Değer | Kaynak |
|---|---|---|
| Kapsama alanı | 1 km × 1 km = 1,00 km² | Varsayım (≥ 1 km² koşulu) |
| Anchor sayısı | 49 | Türetilmiş (ızgara) |
| Izgara aralığı | 150 m | Varsayım (raporun "yüksek sayıda kısa menzilli" tarifi) |
| Montaj yükseklikleri | 8 m direk, 20 m cephe, 35 m çatı (±0,75 m sapma) | Rapor (montaj sınıfları), Varsayım (dağılım) |
| Bağlantı menzili | 400 m = 3,0 km referansın %13'ü | Üretici + Varsayım (derating) |
| Menzil hata modeli | SX1280, Robinson bootstrap | Ölçüm |
| Menzil hatası σ | 3,03 m | Türetilmiş |
| NLOS oranı ve sapması | %35, 1,5 m | Varsayım |
| Paket kaybı | %2 | Varsayım |
| Birim fiyat | 1.366,07 TL | Rapor |
| Test yörüngesi | Hücreyi çapraz kesen doğru, 24 nokta, z = 1,5 m | Varsayım |

Raporun Grup 1 montaj listesi (baz istasyonları, trafik levhaları ve
lambaları, reklam panoları, yol kenarı ışıklandırmaları) 150 m'lik bir
ızgarayı destekler: şehir içi aydınlatma direkleri 25-40 m, kavşak
sinyalizasyonu 100-200 m aralıkla zaten mevcuttur.

Montaj yükseklikleri komşu anchor'lar arasında değişir. Tek yükseklikte bir
ızgara eş düzlemlidir ve dikey ekseni hiç çözemez.

### Ölçülen geometri ve sonuç

| | Kalibreli | Ham |
|---|---|---|
| Fix başına kullanılan anchor | 8 | 8 |
| Medyan / en uzun bağlantı | 171 m / 377 m | 171 m / 377 m |
| 250 m'yi aşan bağlantı oranı | %6,3 | %6,3 |
| HDOP / VDOP (medyan) | 0,73 / 2,37 | 0,73 / 2,37 |
| En kötü VDOP | 6,54 | 6,54 |
| HPE P50 / P95 | 1,98 m / 4,05 m | 2,39 m / 5,63 m |
| VPE P50 / P95 | 6,55 m / 35,98 m | 19,91 m / 50,11 m |
| Kullanılabilirlik | %97,9 | %97,9 |
| CAPEX | 66.937 TL/km² | 66.937 TL/km² |

Kalibrasyon yatay hatayı %17, dikey hatayı %28 iyileştiriyor. Sabit sapma
dikey eksende daha çok büyütülür, çünkü o eksenin DOP'u daha yüksektir.

### Izgara aralığı ne satın alıyor

Aynı hücre, farklı ızgara aralıklarıyla (400 m menzil, en yakın 8 anchor):

| Aralık | Birim | HDOP | VDOP | Medyan bağlantı | CAPEX TL/km² |
|---|---|---|---|---|---|
| 100 m | 121 | 0,75 | 1,57 | 112 m | 165.294 |
| 150 m | 49 | 0,73 | 2,29 | 181 m | 66.937 |
| 200 m | 36 | 0,73 | 3,03 | 225 m | 49.179 |
| 250 m | 25 | 0,78 | 4,12 | 248 m | 34.152 |
| 300 m | 16 | 1,02 | 5,58 | 241 m | 21.857 |

Sıklaştırmak neredeyse yalnızca dikey doğruluk satın alıyor: HDOP 100 ile
250 m arasında sabit kalırken VDOP 2,6 kat değişiyor. Sebebi, en yakın 8
anchor kuralının yatay dağılımı zaten koruması, dikey açının ise doğrudan
mesafeye bağlı olmasıdır.

---

## 3. Kırsal

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
| Bağlantı menzili | 3.000 m = 8,0 km referansın %37,5'i | Üretici + Varsayım (derating) |
| Menzil hata modeli | SX1280, Robinson bootstrap, kalibreli | Ölçüm |
| Menzil hatası σ | 3,05 m | Türetilmiş |
| NLOS oranı ve sapması | %15, 2,0 m | Varsayım |
| Paket kaybı | %1 | Varsayım |
| Birim fiyat | 1.082,68 TL | Rapor |
| Test yörüngesi | Taşıt yolunda zikzak (±10,8 m), 24 nokta | Varsayım |

E28-2G4M27S modülü BOM'a göre SX1280 tabanlıdır. Yükselteç link bütçesini
değiştirir, menzil ölçüm hatası mekanizmasını değil; bu yüzden aynı hata
modeli kullanıldı. Yine de bağlantıların %72'si Robinson verisinin
kapsadığı 0-250 m aralığının dışında kalıyor. Bu bir çıkarsamadır ve JSON
çıktısında `links_beyond_calibrated_envelope` alanında raporlanır.

### Ölçülen geometri ve sonuç

| | Değer |
|---|---|
| Fix başına kullanılan anchor | 8 (menzilde 26) |
| Medyan / en uzun bağlantı | 458 m / 1.000 m |
| 250 m'yi aşan bağlantı oranı | %72,4 |
| HDOP / VDOP (medyan) | 5,84 / 11,56 |
| En kötü VDOP | 28,30 |
| HPE P50 / P95 | 7,02 m / 26,04 m |
| VPE P50 / P95 | 7,11 m / 29,94 m |
| Kullanılabilirlik | %98,8 |
| CAPEX | 200.854 TL/km², 4.821 TL/km |

### Nokta sıklığı ne satın alıyor

42 km koridor, kuleler 2,5 km'de bir sabit:

| Yol kenarı aralığı | Birim | HDOP | VDOP | Medyan bağlantı | TL/km | TL/km² |
|---|---|---|---|---|---|---|
| 1000 m | 103 | 12,12 | 16,01 | 838 m | 2.655 | 110.631 |
| **500 m (kullanılan)** | **187** | **5,84** | **11,56** | **458 m** | **4.821** | **200.854** |
| 300 m | 299 | 4,68 | 9,48 | 274 m | 7.708 | 321.152 |
| 200 m | 439 | 2,95 | 6,80 | 196 m | 11.317 | 471.524 |

Raporun "az sayıda nokta" tercihi burada ölçülebilir hale geliyor. 200 m
aralık VDOP'u 6,80'e indiriyor ama km başına maliyeti 2,3 katına çıkarıyor.
500 m, rapor metnine sadık kalan ve dört anchor'ı her noktada menzilde
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

## 4. Kritik Bölge (Tünel)

| Parametre | Değer | Kaynak |
|---|---|---|
| Tünel uzunluğu | 50 km | Varsayım (≥ 1 km² koşulu) |
| Tünel genişliği | 20 m | Varsayım |
| Kapsama alanı | 50 km × 20 m = 1,00 km² | Türetilmiş |
| Düğüm aralığı | 60 m | Türetilmiş (bağlantı menzilinden) |
| Anchor sayısı | 834 | Türetilmiş |
| Montaj | Duvar (1,2-1,3 m) ve tavan (4,3-4,4 m), dört adımlı döngü | Varsayım |
| Bağlantı menzili | 150 m | Varsayım (yayımlanmış üst sınır yok) |
| Menzil hata modeli | DWM3000, yapılandırılmış Gauss | Rapor hedefi |
| Menzil hatası σ | 0,096 m (NLOS dahil) | Türetilmiş |
| NLOS oranı ve sapması | %10, 0,3 m | Varsayım |
| Paket kaybı | %3 | Varsayım |
| Birim fiyat | 1.634,44 TL | Rapor |
| Test yörüngesi | Tünel boyunca doğru, 24 nokta | Varsayım |

### Düğüm aralığı neden raporun öngördüğünden küçük

Rapor pilot için 2 km koridora 10-15 düğüm öngörüyor, yani ~150 m aralık.
Bir doğru boyunca S aralıklı düğümler ve R menzil ile alıcı yaklaşık `2R/S`
düğüm duyar. 3B fix dört ölçüm ister, dolayısıyla `S ≤ 2R/4 = R/2`.
R = 150 m için tavan 75 m'dir (`link_budget.minimum_spacing_for_fix`).

| Düğüm aralığı | Menzildeki düğüm (en az) | HDOP | VDOP | TL/km | Toplam TL |
|---|---|---|---|---|---|
| 150 m | 2 | çözüm yok | çözüm yok | 10.885 | 544.269 |
| 100 m | 2 | çözüm yok | çözüm yok | 16.344 | 817.220 |
| 75 m | 4 | 3,83 | 15,02 | 21.771 | 1.088.537 |
| **60 m (kullanılan)** | **5** | **3,10** | **14,14** | **27.230** | **1.361.489** |
| 50 m | 5 | 2,61 | 11,04 | 32.689 | 1.634.440 |

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
| Fix başına kullanılan anchor | 5 |
| Medyan / en uzun bağlantı | 75 m / 149 m |
| HDOP / VDOP (medyan) | 3,16 / 13,49 |
| En kötü VDOP | 21,84 |
| HPE P50 / P95 | 0,11 m / 0,83 m |
| VPE P50 / P95 | 0,51 m / 3,83 m |
| Kullanılabilirlik | %97,0 |
| CAPEX | 1.363.123 TL/km², 27.230 TL/km |

DOP değerleri dört senaryonun ortasında, sonuçlar ise açık ara en iyisi.
Çelişki değil: UWB'nin menzil hatası σ = 0,096 m, SX1280'in 3,03 m'sinin
otuzda biri. Kötü geometri küçük bir hatayı büyütüyor ve yine de küçük
kalıyor.
