# Tablodaki her değer nasıl hesaplanıyor

Bu belge, `output/yerkon_rows.csv` içindeki her hücrenin hangi kodun hangi
çıktısı olduğunu anlatır. Senaryo parametrelerinin dökümü için
[SCENARIOS.md](SCENARIOS.md), kanıt sınıfları için [EVIDENCE.md](EVIDENCE.md).

## Zincirin tamamı

```
senaryo tanımı            yerkon/scenarios.py
  anchor konumları    ->  yerkon/scenarios.py  (urban_grid_layout, roadside_layout,
                                                mast_layout, tunnel_layout)
  test yörüngesi      ->  yerkon/path.py
  menzil hata modeli  ->  yerkon/ranging_error.py
        |
        v
Monte Carlo             yerkon/simulate.py     (simulate_path_fixes)
  her yörünge noktası için:
    menzil içindeki anchor'ları seç
    her tekrar için:
      gerçek menzil + hata örneği -> ölçülen menzil
      teslim edildi mi (Bernoulli)
      3B en küçük kareler ile [x, y, z] çöz
        |
        v
metrikler               yerkon/metrics.py
        |
        v
satır biçimlendirme     yerkon/table.py
```

Her senaryoda 24 yörünge noktası × 300 tekrar = 7.200 konum denemesi
yapılır. Seed sabittir (42), yani aynı komut her zaman aynı sayıları verir.

## Sütun sütun

### HPE P50 ve HPE P95 [m]

Başarılı fix'lerin yatay hatasının 50. ve 95. yüzdelikleri.

Yatay hata, kestirim ile gerçek konum arasındaki x-y düzlemi mesafesidir:
`sqrt((x̂-x)² + (ŷ-y)²)`. Kod: `yerkon/geometry.py::error_horizontal`,
yüzdelikler `yerkon/metrics.py::compute_accuracy_metrics`.

Yalnızca başarılı fix'ler sayılır. Başarısız denemeler doğruluk
ortalamasına girmez, kullanılabilirlik sütununa girer.

### VPE P95 [m]

Başarılı fix'lerin dikey hatasının 95. yüzdeliği: `|ẑ - z|`.

Yükseklik ayrı bir geçişte değil, x ve y ile birlikte tek bir doğrusal
olmayan sistemde çözülür (`yerkon/simulate.py::solve_position_3d`). Önce
2B çözüp sonra yüksekliği eklemek, dikey hatayı yapay olarak küçültürdü.

### Kullanılabilirlik

`geçerli fix sayısı / denenen fix sayısı`, yüzde olarak.

Bir deneme üç şekilde başarısız olabilir ve üçü ayrı ayrı sayılır
(`yerkon/metrics.py::compute_reliability_metrics`):

| Başarısızlık | Anlamı | Çözümü |
|---|---|---|
| `coverage_gap_rate` | Menzil içinde 4'ten az anchor var | Daha çok anchor ya da daha uzun menzil |
| `dropout_rate` | Paket kaybı; Bernoulli denemesi | Bağlantı katmanı |
| `solver_failure_rate` | Çözücü yakınsayamadı | Geometri |

Dört senaryoda da kapsama boşluğu sıfır çıkıyor; kullanılabilirlik
tamamen varsayılan paket kaybı oranından geliyor (%2-3). Bu, kurulum
yoğunluklarının test yörüngesi boyunca yeterli olduğu anlamına gelir,
kapsama probleminin genel olarak yok olduğu anlamına gelmez.

### Alan [km²]

Doğruluk rakamının geçerli sayıldığı alan. Her senaryoda en az 1 km².

- Şehir içi: 1 km × 1 km hücre = 1,00 km².
- Kırsal: 42 km koridor × 24 m taşıt yolu genişliği = 1,01 km².
- Tünel: 50 km tünel × 20 m genişlik = 1,00 km².

Kırsalda kapsamanın taşıt yolu ile sınırlanması bilinçli bir seçim. Sistem
yoldan 1 km uzakta da sinyal veriyor, ama orada dikey geometri çöküyor
(VDOP 5,5'ten 37'ye çıkıyor). Geniş bir şeridi kapsama alanı ilan edip
doğruluğu onun üzerinden bildirmek, iyi ve kötü bölgeleri tek bir sayıda
ortalayıp ikisini de yanlış anlatırdı. Düşüş eğrisi
[SCENARIOS.md](SCENARIOS.md#yoldan-uzaklaştıkça-ne-oluyor) içinde.

### CAPEX [TL/km²]

`(anchor sayısı × birim fiyat) / alan`.

Birim fiyatlar sunumun kendi 100 adetlik toplu alım tablosundan:
şehir içi 1.366,07 TL, kırsal 1.082,68 TL, kritik bölge 1.634,44 TL.
Yalnızca bileşen maliyeti; montaj, sertifikasyon, altyapı, enerji ve
işçilik dahil değil.

Koridor senaryolarında km başına maliyet de hesaplanır ve JSON çıktısında
`capex_per_km_tl` alanında bulunur. İnce bir kurdele biçimindeki bir
kurulumu km² üzerinden fiyatlamak yanıltıcıdır: tünel 545.903 TL/km²
görünürken 10.918 TL/km'dir.

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
| Yol levhası, 100 m | 4,5 m | 100 m | 2,58° |
| Yol levhası, 250 m | 4,5 m | 250 m | 1,03° |
| Kule, 750 m | 38,5 m | 750 m | 2,94° |
| Kule, 1500 m | 38,5 m | 1500 m | 1,47° |
| Bina çatısı, 150 m | 33,5 m | 150 m | 12,59° |
| Bina çatısı, 400 m | 33,5 m | 400 m | 4,79° |
| Tünel tavanı, 100 m | 2,8 m | 100 m | 1,60° |
| GNSS uydusu | — | — | ≈ 45° |

Bir uydu alıcının 45 derece üstünden bakar; menzil hatasının önemli bir
bileşeni doğrudan dikey eksene düşer. Bir yol levhası 1 dereceden bakar;
menzil hatasının neredeyse tamamı yatay eksene düşer ve dikey eksen için
geriye çok az bilgi kalır. Aradaki fark, ölçülen VDOP değerlerinde
görünür:

| Senaryo | HDOP | VDOP | VDOP/HDOP |
|---|---|---|---|
| Şehir içi (150 m ızgara) | 0,45 | 2,02 | 4,5× |
| Kırsal (200 m levha aralığı) | 2,70 | 6,28 | 2,3× |
| Tünel (150 m düğüm aralığı) | 7,90 | 31,85 | 4,0× |

Ölçülen dikey hatalar bu çarpanlarla tutarlı. Şehir içi kalibreli
senaryoda menzil hatasının standart sapması 3,02 m, medyan VDOP 2,02;
`2,02 × 3,02 ≈ 6,1 m` beklenir, ölçülen VPE P50 5,49 m.

Bunu iyileştirmenin üç yolu var ve üçü de maliyetli:

1. **Anchor'ları sıklaştırmak.** Yakın anchor daha dik açı demek. Şehir
   içinde ızgarayı 250 m'den 150 m'ye sıkıştırmak VDOP'u 3,98'den 2,00'a
   indiriyor, birim sayısını 25'ten 49'a çıkarıyor.
2. **Daha yükseğe monte etmek.** 6 m'lik levha yerine 35 m'lik çatı,
   aynı mesafede beş kat dik açı verir.
3. **Dikey serbestliği dışarıdan vermek.** Yol yüksekliği haritadan
   biliniyorsa dikey eksen çözülmek zorunda değildir. Sunumun harita
   kısıtlı füzyon mimarisi tam olarak bunu yapar. Bu simülasyon o katmanı
   modellemez ve çıplak geometrik sonucu raporlar.

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
