# Tablodaki her değer nasıl hesaplanıyor

Bu belge, `output/yerkon_rows.csv` içindeki her hücrenin hangi kodun hangi
çıktısı olduğunu anlatır. Senaryo parametrelerinin dökümü için
[SCENARIOS.md](SCENARIOS.md), kanıt sınıfları için [EVIDENCE.md](EVIDENCE.md).

## Zincirin tamamı

```
senaryo tanımı            yerkon/scenarios.py
  anchor konumları    ->  yerkon/scenarios.py  (urban_grid_layout, roadside_layout,
                                                mast_layout, tunnel_layout)
  bağlantı menzili    ->  yerkon/link_budget.py (üretici referans mesafesi + derating)
  test yörüngesi      ->  yerkon/path.py
  menzil hata modeli  ->  yerkon/ranging_error.py
        |
        v
Monte Carlo             yerkon/simulate.py     (simulate_path_fixes)
  her yörünge noktası için:
    menzil içindeki anchor'lardan en yakın 8'ini seç
    her tekrar için:
      gerçek menzil + hata örneği -> ölçülen menzil
      her anchor için teslim edildi mi (Bernoulli)
      3B en küçük kareler ile [x, y, z] çöz
        |
        v
Kalman filtresi         yerkon/fusion.py       (run_filter)     <- tablo buradan
  sürüş izi boyunca 10 Hz:
    IMU ivmesiyle yayılım
    5 Hz menzil güncellemeleri (4 sigma kapısı)
    tekerlek hızı, IMU pusulası, harita yüksekliği güncellemeleri
        |
        v
metrikler               yerkon/metrics.py (tek-atım), yerkon/scenarios.py (filtreli)
        |
        v
satır biçimlendirme     yerkon/table.py
```

Tablodaki doğruluk değerleri filtre çıktısından gelir. Tek-atım zinciri
geometriyi ve radyonun tek başına ne yapabildiğini ölçmek için korunur ve
JSON çıktısında ayrıca raporlanır.

Her senaryoda 24 yörünge noktası × 300 tekrar = 7200 konum denemesi
yapılır. Seed sabittir (42), yani aynı komut her zaman aynı sayıları verir.

## Sütun sütun

### HPE P50 ve HPE P95 [m]

**Filtrelenmiş** yatay hatanın 50. ve 95. yüzdelikleri. Alıcı, menzil
ölçümlerini IMU, tekerlek odometrisi ve harita kısıtıyla bir Kalman
filtresinde birleştirir; raporun tarif ettiği alıcı bu. Filtrenin kendisi
ve neyin ortalamayla yok olmadığı [FUSION.md](FUSION.md) içinde.

Tek-atım (filtresiz) karşılığı JSON çıktısında `single_epoch_hpe_*`
alanlarında duruyor.

Yatay hata, kestirim ile gerçek konum arasındaki x-y düzlemi mesafesidir:
`sqrt((x̂-x)² + (ŷ-y)²)`. Kod: `yerkon/geometry.py::error_horizontal`,
yüzdelikler `yerkon/metrics.py::compute_accuracy_metrics`.

Yalnızca başarılı fix'ler sayılır. Başarısız denemeler doğruluk
ortalamasına girmez, kullanılabilirlik sütununa girer.

### VPE P95 [m]

Filtrelenmiş dikey hatanın 95. yüzdeliği: `|ẑ - z|`.

Bu sütun **haritayı ölçüyor.** Karasal geometri yüksekliği çözemediği için
dikey sonucu belirleyen şey, aracın ölçülmüş bir yol yüzeyinin üstünde
olduğunun bilinmesi. Harita belirsizliği 0,2 m'den 2,0 m'ye çıkarıldığında
VPE P95 0,45 m'den 4,36 m'ye çıkarken HPE hiç değişmiyor
([FUSION.md](FUSION.md#harita-doğruluğu-doğrudan-dikey-sonuca-geçiyor)).

Yükseklik ayrı bir geçişte değil, x ve y ile birlikte çözülür
(`yerkon/simulate.py::solve_position_3d` tek-atım için,
`yerkon/fusion.py` filtre için). Önce 2B çözüp sonra yüksekliği eklemek,
dikey hatayı yapay olarak küçültürdü.

### Kullanılabilirlik

`geçerli fix sayısı / denenen fix sayısı`, yüzde olarak.

Bir deneme üç şekilde başarısız olabilir ve üçü ayrı ayrı sayılır
(`yerkon/metrics.py::compute_reliability_metrics`):

| Başarısızlık | Anlamı | Çözümü |
|---|---|---|
| `coverage_gap_rate` | Menzil içinde 4'ten az anchor var | Daha çok anchor ya da daha uzun menzil |
| `dropout_rate` | Paket kaybı 4'ün altına düşürdü | Bağlantı katmanı ya da daha çok anchor |
| `solver_failure_rate` | Çözücü yakınsayamadı | Geometri |

Paket kaybı **her anchor için ayrı ayrı** uygulanır. TWR her anchor ile
ayrı bir alışveriş olduğundan kaybolan bir alışveriş bir ölçümü götürür,
tüm konumu değil. Fix ancak teslim edilen ölçüm sayısı dördün altına
düştüğünde başarısız olur.

Bu ayrım yalnızca anchor sayısının sınıra yakın olduğu yerde önemlidir.
Şehir içi ve kırsalda alıcı sekiz ölçüm alır ve dördünü birden
kaybetmediği sürece konum üretir; ikisinde de 7200 denemenin tamamı
başarılı. Tünelde beş ölçüm vardır ve ikisinin kaybı fix'i bitirir, bu da
kullanılabilirliği %99,3'e indirir.

Kapsama boşluğu dört senaryoda da sıfır: test yörüngesi boyunca her
noktada dörtten fazla anchor menzilde. Bu, kapsama probleminin genel
olarak yok olduğu anlamına gelmez, yalnızca test edilen yörünge boyunca
görülmediği anlamına gelir.

%100,0 değeri yalnızca modellenen kayıp altındaki radyo bağlantısı
kullanılabilirliğidir. Kanal doluluğu, girişim, düğüm arızası ve alıcı
açılış süresi modellenmedi; GNSS satırlarındaki hizmet kullanılabilirliği
yüzdeleriyle aynı ölçüt gibi okunmamalıdır.

### Alan [km²]

Doğruluk rakamının geçerli sayıldığı alan. Her senaryoda en az 1 km².

- Şehir içi: 1 km × 1 km hücre = 1,00 km².
- Kırsal: 42 km koridor × 24 m taşıt yolu genişliği = 1,01 km².
- Tünel: 50 km tünel × 20 m genişlik = 1,00 km².

Kırsalda kapsamanın taşıt yolu ile sınırlanması bilinçli bir seçim. Sistem
yoldan yüzlerce metre uzakta da sinyal veriyor, ama dikey geometri yoldan
uzaklaştıkça hızla bozulur. Geniş bir şeridi kapsama alanı ilan edip
doğruluğu onun üzerinden bildirmek, iyi ve kötü bölgeleri tek bir sayıda
ortalayıp ikisini de yanlış anlatırdı.

### CAPEX [TL/km²]

`(anchor sayısı × birim fiyat) / alan`.

Birim fiyatlar raporun kendi 100 adetlik toplu alım tablosundan:
şehir içi 1366,07 TL, kırsal 1082,68 TL, kritik bölge 1634,44 TL.
Yalnızca bileşen maliyeti; montaj, sertifikasyon, altyapı, enerji ve
işçilik dahil değil.

Koridor senaryolarında km başına maliyet de hesaplanır ve JSON çıktısında
`capex_per_km_tl` alanında bulunur. İnce bir kurdele biçimindeki bir
kurulumu km² üzerinden fiyatlamak yanıltıcıdır: tünel 1363123 TL/km²
görünürken 27230 TL/km'dir.

### OPEX

Her satırda "-". Gerekçe [README](../README.md#üretilen-satırlar) içinde.

## Dikey hata neden yatay hatadan kötü

Bu, sonuçların en çok soru doğuran kısmı, o yüzden mekanizmayı ayrı
yazıyorum.

Menzil ölçümünden konum çözerken, bir eksenin ne kadar iyi kestirilebildiği
o eksende anchor'ların sunduğu **açısal çeşitliliğe** bağlıdır. Ölçüt
DOP'tur (dilution of precision): kabaca

```
eksendeki hata ≈ DOP × menzil ölçüm hatası
```

Yatay eksende anchor'lar alıcının çevresine dağılmıştır, açısal çeşitlilik
yüksektir, HDOP küçüktür. Dikey eksende ise karasal bir kurulumda her
anchor alıcıya göre neredeyse ufuk hizasındadır:

| Bakış | Yükseklik farkı | Yatay mesafe | Bakış açısı |
|---|---|---|---|
| Yol kenarı ünitesi, 100 m | 4,5 m | 100 m | 2,58° |
| Yol kenarı ünitesi, 250 m | 4,5 m | 250 m | 1,03° |
| Yol kenarı ünitesi, 500 m | 4,5 m | 500 m | 0,52° |
| Kule, 600 m | 38,5 m | 600 m | 3,67° |
| Kule, 1500 m | 38,5 m | 1500 m | 1,47° |
| Bina çatısı, 150 m | 33,5 m | 150 m | 12,59° |
| Bina çatısı, 400 m | 33,5 m | 400 m | 4,79° |
| Tünel tavanı, 75 m | 2,8 m | 75 m | 2,14° |
| GNSS uydusu | yok | yok | ≈ 45° |

Bir uydu alıcının 45 derece üstünden bakar; menzil hatasının önemli bir
bileşeni doğrudan dikey eksene düşer. Bir yol levhası 1 dereceden bakar;
menzil hatasının neredeyse tamamı yatay eksene düşer ve dikey eksen için
geriye çok az bilgi kalır. Aradaki fark, ölçülen VDOP değerlerinde
görünür:

| Senaryo | HDOP | VDOP | VDOP/HDOP |
|---|---|---|---|
| Şehir içi (150 m ızgara) | 0,73 | 2,37 | 3,2× |
| Kırsal (750 m nokta aralığı) | 8,54 | 15,29 | 1,8× |
| Tünel (60 m düğüm aralığı) | 3,16 | 13,49 | 4,3× |

Ölçülen dikey hatalar bu çarpanlarla tutarlı. Şehir içi kalibreli
senaryoda menzil hatasının standart sapması 2,40 m ve medyan VDOP 2,79,
yani `2,79 × 2,40 ≈ 6,7 m` beklenir. Ölçülen tek atım VPE P50 4,56 m.

Bunu iyileştirmenin üç yolu var ve üçü de maliyetli:

1. **Anchor'ları sıklaştırmak.** Yakın anchor daha dik açı demek. Şehir
   içinde ızgarayı 250 m'den 150 m'ye sıkıştırmak VDOP'u 4,12'den 2,29'a
   indiriyor, birim sayısını 25'ten 49'a çıkarıyor.
2. **Daha yükseğe monte etmek.** 6 m'lik levha yerine 35 m'lik çatı,
   aynı mesafede beş kat dik açı verir.
3. **Dikey serbestliği dışarıdan vermek.** Yol yüksekliği haritadan
   biliniyorsa dikey eksen çözülmek zorunda değildir. Raporun harita
   kısıtlı füzyon mimarisi tam olarak bunu yapar. Bu simülasyon o katmanı
   modellemez ve çıplak geometrik sonucu raporlar.

## Bağlantı menzili nereden geliyor

Menzil değerleri `yerkon/link_budget.py` içinde, her biri raporun adıyla
verdiği modülün yayımlanmış değerine bağlı olarak tutulur.

| Senaryo | Modül | Yayımlanmış referans | Modellenen | Oran |
|---|---|---|---|---|
| Şehir içi | SX1280/SX1281 @ 12,5 dBm | 3,0 km | 400 m | %13 |
| Kırsal | E28-2G4M27S @ 27 dBm | 8,0 km | 3000 m | %37,5 |
| Tünel | DWM3000 | yok | 150 m | yok |

Referans mesafeler açık arazide, 5 dBi anten, 2,5 m yükseklik ve 1 kbps
hava hızında ölçülmüştür. Menzil ölçümü çok daha geniş bantta çalışır ve
ne kentsel kanyon ne de yol kenarı açık arazidir; derating oranları bu
farkı karşılar ve bu projenin yargısıdır.

Menzil, düğüm aralığını da belirler. Bir doğru boyunca S aralıklı düğümler
ve R menzil ile alıcı yaklaşık `2R/S` düğüm duyar; 3B fix dört ölçüm
istediğinden `S ≤ R/2` olmalıdır (`link_budget.minimum_spacing_for_fix`).
Tünelde bu, raporun öngördüğü 150 m aralığı eliyor ve 60 m'ye indiriyor.

## Alıcı kaç anchor ile ölçüm yapıyor

Fix başına en yakın 8 anchor. TWR her anchor için hava süresi harcar;
rapor da alıcıyı "konum için yeterli sayıda Yayın Birimi ile konuşacak"
diye tarif eder, menzildeki hepsiyle değil.

Bunun bedeli ve kazancı ölçüldü. Şehir içinde menzildeki 20 anchor'ın
hepsini kullanmak VDOP'u 2,37'den 2,02'ye indirir, ama bağlantıların
%54'ünü SX1280 ölçümlerinin kapsadığı 250 m'nin dışına taşır. En yakın 8
ile bu oran %6'ya düşer. Daha az ölçümle biraz daha kötü geometri, buna
karşılık sonucun çok daha büyük bölümünün ölçülmüş veriye dayanması.

## Menzil kısıtı neden var

`simulate_path_fixes` yalnızca `max_range_m` içindeki anchor'ları fix'e
katar. Bu, alanlar büyüdüğünde şart oldu: 50 km'lik bir tünelde 334
düğümün tamamını her fix'e katmak, 40 km ötedeki bir düğümün duyulduğunu
varsaymak olurdu. O düğümler hem gerçekte duyulmaz hem de simülasyonda
gerçek kurulumun sahip olmadığı bir geometri üretir.

Menzil içinde 4'ten az anchor kalırsa deneme kapsama boşluğu sayılır.
Yeterli anchor varsa geometri kötü olsa bile çözüm yapılır. İkincisi
bilinçli: neredeyse eş düzlemli anchor'lar arasındaki bir alıcı gerçekte
de konum üretir, sadece kötü bir konum. Çözmeyi reddetmek o hatayı
doğruluk sütunundan çıkarıp kullanılabilirlik sütununa taşırdı ve tam da
incelenen dikey zayıflığı gizlerdi.
