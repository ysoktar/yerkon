# Senaryo dökümü

Dört senaryonun her parametresi, kaynağı ve sonucu. Kod:
`yerkon/scenarios.py`.

Kaynak sütunundaki etiketler:

- **Sunum**: YERKON sunumundan alınmış değer.
- **Ölçüm**: yayımlanmış donanım ölçümünden geliyor.
- **Varsayım**: bu projenin seçimi; sunum bu değeri vermiyor.

---

## 1-2. Şehir İçi (Kalibreli ve Ham)

İki satır aynı kurulumdur. Tek fark menzil ofseti kalibrasyonunun
uygulanıp uygulanmadığıdır; anchor sayısı, geometri ve maliyet birebir
aynıdır.

| Parametre | Değer | Kaynak |
|---|---|---|
| Kapsama alanı | 1 km × 1 km = 1,00 km² | Varsayım (≥ 1 km² koşulu) |
| Anchor sayısı | 49 | Türetilmiş (ızgara) |
| Izgara aralığı | 150 m | Varsayım |
| Montaj yükseklikleri | 8 m direk, 20 m cephe, 35 m çatı (±0,75 m sapma) | Sunum (montaj sınıfları), Varsayım (dağılım) |
| Bağlantı menzili | 400 m | Varsayım |
| Menzil hata modeli | SX1280, Robinson bootstrap | Ölçüm |
| Menzil hatası σ | 3,02 m | Türetilmiş |
| NLOS oranı ve sapması | %35, 1,5 m | Varsayım |
| Paket kaybı | %2 | Varsayım |
| Birim fiyat | 1.366,07 TL | Sunum |
| Test yörüngesi | Hücreyi çapraz kesen doğru, 24 nokta, z = 1,5 m | Varsayım |

Montaj yükseklikleri komşu anchor'lar arasında değişir. Tek yükseklikte
bir ızgara eş düzlemlidir ve dikey ekseni hiç çözemez; `coplanar()` bunu
yakalar ve bir test bu durumu koruma altına alır.

### Ölçülen geometri ve sonuç

| | Kalibreli | Ham |
|---|---|---|
| Menzil içindeki anchor (medyan / en az) | 20 / 8 | 20 / 8 |
| Medyan bağlantı mesafesi | 263 m | 263 m |
| HDOP / VDOP (medyan) | 0,45 / 2,02 | 0,45 / 2,02 |
| En kötü VDOP | 6,54 | 6,54 |
| Koşul sayısı (medyan) | 6,6 | 6,6 |
| HPE P50 / P95 | 1,26 m / 3,00 m | 1,52 m / 5,08 m |
| VPE P50 / P95 | 5,49 m / 30,89 m | 19,64 m / 50,68 m |
| 3B hata P95 | 30,96 m | 50,74 m |
| Kullanılabilirlik | %97,9 | %97,9 |
| CAPEX | 66.937 TL/km² | 66.937 TL/km² |

Kalibrasyon yatay hatayı yaklaşık %20, dikey hatayı %39 iyileştiriyor.
Sabit sapma dikey eksende daha çok büyütülür, çünkü o eksenin DOP'u daha
yüksektir.

### Izgara aralığı ne satın alıyor

Aynı hücre, farklı ızgara aralıklarıyla (1 km kenar, 400 m menzil):

| Aralık | Birim | Menzildeki anchor | HDOP | VDOP | CAPEX TL/km² |
|---|---|---|---|---|---|
| 100 m | 121 | 38 | 0,33 | 1,29 | 165.294 |
| 150 m | 49 | 16 | 0,52 | 2,00 | 66.937 |
| 200 m | 36 | 10 | 0,65 | 2,80 | 49.179 |
| 250 m | 25 | 8 | 0,76 | 3,98 | 34.152 |
| 300 m | 16 | 4 | 1,02 | 5,58 | 21.857 |

Sıklaştırmak esas olarak dikey doğruluk satın alıyor. 300 m'den 100 m'ye
inerken HDOP 3 kat, VDOP 4,3 kat iyileşiyor, maliyet 7,6 kat artıyor.
150 m, dikey hatayı kullanılabilir aralıkta tutan en ucuz noktaya yakın
olduğu için seçildi.

---

## 3. Kırsal

| Parametre | Değer | Kaynak |
|---|---|---|
| Koridor uzunluğu | 42 km | Varsayım (≥ 1 km² koşulu) |
| Kapsama | Levha hatları arası 24 m taşıt yolu = 1,01 km² | Varsayım |
| Levha anchor'ı | 200 m'de bir, yolun iki yanında karşılıklı, 6 m (±0,5 m) | Varsayım |
| Kule anchor'ı | 2,5 km'de bir, 35-45 m, yoldan 30 m açıkta | Varsayım |
| Toplam anchor | 422 levha + 17 kule = 439 | Türetilmiş |
| Bağlantı menzili | 1.500 m | Varsayım |
| Menzil hata modeli | SX1280, Robinson bootstrap, kalibreli | Ölçüm |
| Menzil hatası σ | 3,01 m | Türetilmiş |
| NLOS oranı ve sapması | %15, 2,0 m | Varsayım |
| Paket kaybı | %1 | Varsayım |
| Birim fiyat | 1.082,68 TL | Sunum |
| Test yörüngesi | Taşıt yolu üzerinde zikzak (±10,8 m), 24 nokta | Varsayım |

E28-2G4M27S modülü BOM'a göre SX1280 tabanlıdır. Yükselteç link bütçesini
değiştirir, menzil ölçüm hatası mekanizmasını değil; bu yüzden aynı hata
modeli kullanıldı. Yine de bağlantıların %83'ü Robinson verisinin
kapsadığı 0-250 m aralığının dışında kalıyor. Bu bir çıkarsamadır ve
JSON çıktısında `links_beyond_calibrated_envelope` alanında oran olarak
raporlanır.

### Ölçülen geometri ve sonuç

| | Değer |
|---|---|
| Menzil içindeki anchor (medyan / en az) | 31 / 20 |
| Medyan / en uzun bağlantı | 735 m / 1.491 m |
| HDOP / VDOP (medyan) | 2,70 / 6,28 |
| En kötü VDOP | 10,74 |
| Koşul sayısı (medyan) | 35,4 |
| HPE P50 / P95 | 4,04 m / 14,15 m |
| VPE P50 / P95 | 8,00 m / 24,18 m |
| Kullanılabilirlik | %98,8 |
| CAPEX | 471.524 TL/km², 11.317 TL/km |

### Levha sıklığı ne satın alıyor

42 km koridor, kuleler 2,5 km'de bir sabit:

| Levha aralığı | Birim | HDOP | VDOP | TL/km | TL/km² |
|---|---|---|---|---|---|
| 500 m | 187 | 7,57 | 9,66 | 4.821 | 200.854 |
| 300 m | 299 | 4,20 | 7,85 | 7.708 | 321.152 |
| 200 m | 439 | 2,64 | 5,74 | 11.317 | 471.524 |
| 150 m | 579 | 2,08 | 5,03 | 14.926 | 621.897 |
| 100 m | 859 | 1,31 | 3,33 | 22.143 | 922.641 |

Kuleler bu tabloda görünmeyen bir iş yapıyor: levhalar arasında kalan
bölgelerde tek dik açı kaynağı onlar. Kule aralığı 5 km olduğunda
menzil dışında kaldıkları bölgelerde VDOP 15'in üstüne çıkıyordu; 2,5
km'ye indirmek her noktada en az bir kuleyi menzilde tutuyor.

### Yoldan uzaklaştıkça ne oluyor

200 m levha aralığı, koridor boyunca ölçülen değerler:

| Yoldan uzaklık | Menzildeki anchor | HDOP | VDOP |
|---|---|---|---|
| 0 m (orta şerit) | 31 | 2,59 | 5,46 |
| 3,7 m (iç şerit) | 31 | 2,64 | 5,74 |
| 12 m (levha hattı) | 31 | 2,57 | 6,87 |
| 25 m | 31 | 2,13 | 8,79 |
| 50 m | 31 | 1,75 | 16,50 |
| 100 m | 31 | 1,10 | 18,73 |
| 250 m | 31 | 0,60 | 19,87 |
| 500 m | 29 | 0,46 | 23,44 |
| 1000 m | 23 | 0,54 | 36,69 |

Yatay doğruluk yoldan uzaklaştıkça **iyileşiyor**, çünkü anchor'lar
alıcının çevresine daha geniş bir açıyla yayılıyor. Dikey doğruluk ise
6,7 kat kötüleşiyor: taşıt yolundayken alıcı karşılıklı levha çiftlerinin
arasında kalır ve yakın anchor'lar dik açı sağlar; yoldan çıkınca tüm
anchor'lar aynı tarafta ve aynı yükseklikte toplanır.

Kapsama alanının taşıt yolu ile sınırlanmasının sebebi bu. Sistem 1 km
uzakta da fix üretiyor, ama oradaki dikey hata taşıt yolundakinin
katlarıdır ve ikisini tek bir P95'te ortalamak her ikisini de yanlış
anlatır.

---

## 4. Kritik Bölge (Tünel)

| Parametre | Değer | Kaynak |
|---|---|---|
| Tünel uzunluğu | 50 km | Varsayım (≥ 1 km² koşulu) |
| Tünel genişliği | 20 m | Varsayım |
| Kapsama alanı | 50 km × 20 m = 1,00 km² | Türetilmiş |
| Düğüm aralığı | 150 m | Sunum (2 km koridora 10-15 düğüm) |
| Anchor sayısı | 334 | Türetilmiş |
| Montaj | Duvar (1,2-1,3 m) ve tavan (4,3-4,4 m), dört adımlı döngü | Varsayım |
| Bağlantı menzili | 400 m | Varsayım |
| Menzil hata modeli | DWM3000, yapılandırılmış Gauss | Sunum hedefi |
| Menzil hatası σ | 0,095 m (NLOS dahil) | Türetilmiş |
| NLOS oranı ve sapması | %10, 0,3 m | Varsayım |
| Paket kaybı | %3 | Varsayım |
| Birim fiyat | 1.634,44 TL | Sunum |
| Test yörüngesi | Tünel boyunca doğru, 24 nokta | Varsayım |

Montaj deseni dört adımlıdır, iki değil. İki adımlı bir desen (bir duvar,
bir tavan) tüm anchor'ları iki paralel doğru üzerine yerleştirir ve 3B'de
iki paralel doğru her zaman eş düzlemlidir. Bu durumda dikey eksen kaç
anchor eklenirse eklensin çözülemez. Bir test bunu koruma altına alıyor
(`test_two_parallel_lines_of_anchors_are_coplanar`).

400 m bağlantı menzili, açık havadaki DWM3000 rakamlarının üstündedir.
Gerekçe, tünel kesitinin sinyali dalga kılavuzu gibi taşıması ve küresel
yayılıma göre daha az zayıflatmasıdır. Bu menzil olmadan sunumun kendi
150 m'lik düğüm aralığı, bir fix için gereken dört anchor'ı menzilde
tutmaya yetmezdi.

### Ölçülen geometri ve sonuç

| | Değer |
|---|---|
| Menzil içindeki anchor (medyan / en az) | 5 / 5 |
| Medyan / en uzun bağlantı | 200 m / 400 m |
| HDOP / VDOP (medyan) | 7,90 / 31,85 |
| En kötü VDOP | 55,40 |
| Koşul sayısı (medyan) | 78,7 |
| HPE P50 / P95 | 0,26 m / 1,89 m |
| VPE P50 / P95 | 1,37 m / 5,55 m |
| Kullanılabilirlik | %97,0 |
| CAPEX | 545.903 TL/km², 10.918 TL/km |

DOP değerleri dört senaryonun en kötüsü, sonuçlar ise en iyisi. Çelişki
değil: UWB'nin menzil hatası σ = 0,095 m, SX1280'in 3,0 m'sinin
otuzda biri. Kötü geometri küçük bir hatayı büyütüyor ve yine de küçük
kalıyor.

Yüksek DOP'un sebebi tünelin doğrusal olması. Anchor'lar tünel ekseni
boyunca dizildiği için eksen yönündeki çözünürlük zayıftır; bu, koridor
tipi her kurulumun yapısal özelliğidir ve düğüm sıklaştırarak azaltılır
ama yok edilemez.
