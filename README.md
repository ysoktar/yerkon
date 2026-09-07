# YERKON karşılaştırma tablosu simülasyonu

Bu depo tek bir iş yapar: YERKON raporunda tarif edilen şehir içi, kırsal
ve kritik bölge kurulumlarını simüle eder ve karşılaştırma tablosuna
girecek dört satırı üretir. Sayılar varsayılmaz, hesaplanır; her girdinin
nereden geldiği çıktıya iliştirilir.

```bash
python run.py
```

Çıktı `output/yerkon_rows.csv`: sadece dört satır.

## Üretilen satırlar

| Sistem | Teknoloji | Ortam | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan | CAPEX |
|---|---|---|---|---|---|---|---|---|
| YERKON (Şehir İçi - Kalibreli)¹ | Karasal PNT (SX1280/LoRa TWR) | Dış | 2,31 m | 4,82 m | 1,07 m | %100,0 | 1,00 km² | ≈ 66.937 TL/km² |
| YERKON (Şehir İçi - Ham)² | Karasal PNT (SX1280/LoRa TWR) | Dış | 3,02 m | 6,34 m | 1,05 m | %100,0 | 1,00 km² | ≈ 66.937 TL/km² |
| YERKON (Kırsal)³ | Karasal PNT (E28-SX1280 TWR) | Dış | 5,45 m | 25,47 m | 0,98 m | %100,0 | 1,01 km² | ≈ 200.854 TL/km² |
| YERKON (Kritik Bölge/Tünel)⁴ | Karasal PNT (UWB/DWM3000 TWR) | İç + dış | 0,15 m | 0,56 m | 0,63 m | ≈ %99,3 | 1,00 km² | ≈ 1.363.123 TL/km² |

Doğruluk değerleri **filtrelenmiş** sonuçtan geliyor: menzil ölçümleri
BNO085 IMU, tekerlek odometrisi ve harita kısıtıyla bir Kalman filtresinde
birleştirildi, çünkü raporun tarif ettiği alıcı bu. Radyo-tek sonuç da
hesaplanıyor ve JSON çıktısında duruyor. Ayrıntı:
[docs/FUSION.md](docs/FUSION.md).

**VPE sütunu haritayı ölçüyor, radyoyu değil.** Karasal geometri yüksekliği
çözemiyor; çözen şey aracın ölçülmüş bir yol yüzeyinin üstünde olduğunun
bilinmesi. Harita belirsizliği 0,5 m alındı ve VPE bununla doğrusal
ölçekleniyor (σ 2 m olsaydı VPE P95 4,36 m olurdu). Rapora yazılırken bu
belirtilmeli.

Dipnotlar:

1. 1 km × 1 km şehir hücresi, 150 m aralıklı 49 yayın birimi (8/20/35 m
   montaj yüksekliği). Modül başına menzil ofseti kalibrasyonu uygulanmış.
   HPE P50 = 2,31 m, raporun kendi `<2 m` hedefinin biraz üstünde.
2. Aynı kurulum, kalibrasyon adımı atlanmış. Tek fark bu; birim sayısı,
   geometri ve maliyet birebir aynı.
3. 42 km karayolu koridoru. 500 m'de bir, yolun iki tarafında karşılıklı
   AUS/yol kenarı noktası (6 m) ve 2,5 km'de bir kule (35-45 m); toplam
   187 birim. Kapsama, iki hat arasındaki 24 m genişliğindeki taşıt yolu.
4. 50 km tünel/metro ağı, **60 m** aralıklı 834 UWB düğümü. Raporun
   öngördüğü 150 m aralık DWM3000'in gerçek menziliyle konum çözümü
   üretmiyor; aşağıya bakınız.

OPEX her satırda "-". Rapor yıllık işletme maliyeti vermiyor ve
karşılaştırma tablosu, yayımlanmış işletme maliyeti olmayan diğer
sistemler için zaten "-" kullanıyor.

Şehir içi ve kırsalda kullanılabilirlik yuvarlama sonucu değil: 7.200
denemenin 7.200'ünde konum çözümü üretildi. Bu, **yalnızca modellenen
kayıp altındaki radyo bağlantısı kullanılabilirliğidir**. Kanal doluluğu,
girişim, düğüm arızası, alıcı açılış süresi gibi sebepler modellenmedi;
gerçek hizmet kullanılabilirliği bunlardan dolayı daha düşük olacaktır.
GNSS satırlarındaki yüzdelerle aynı ölçüt gibi okunmamalıdır.

## Kaç anchor gerekiyor, kaç tane var

3B konum çözümü en az dört mesafe ölçümü ister. Menzil düzeltmesinden
sonra düğüm sayısının her senaryoda artması gerekmedi, çünkü şehir içi ve
kırsal zaten bu sınırın çok üstündeydi:

| Senaryo | Menzilde duyulan | Fix'te kullanılan | Gereken |
|---|---|---|---|
| Şehir içi | 20 | 8 | 4 |
| Kırsal | 26 | 8 | 4 |
| Tünel | 5 | 5 | 4 |

Sadece tünel sınıra yakındı, ve düğüm sayısı orada zaten 334'ten **834'e**
çıktı (150 m → 60 m aralık). Şehir içinde ve kırsalda anchor eklemek
kullanılabilirliği değil, yalnızca geometriyi iyileştirirdi; onun bedeli
ve kazancı [docs/SCENARIOS.md](docs/SCENARIOS.md) içindeki aralık
tablolarında.

Kırsalda düğüm sayısı 439'dan 187'ye **düştü**, çünkü rapor Grup 2 için
"az sayıda yüksek kapsamalı nokta" istiyor ve 187 birim de dört anchor
sınırının altı kat üstünde kalıyor.

Tünelin sınıra yakınlığı ölçülebilir bir sonuç doğuruyor. Paket kaybı
artık her anchor için ayrı ayrı uygulanıyor; TWR her anchor ile ayrı bir
alışveriş olduğu için kaybolan bir alışveriş tüm konumu değil bir ölçümü
götürür. Şehir içi ve kırsalda sekiz ölçümden birini kaybetmek fix'i
etkilemez. Tünelde beş ölçümden ikisini kaybetmek fix'i bitirir, ve
kullanılabilirliğin %99,3'te kalmasının sebebi budur.

## Menzil değerleri nereden geliyor

Bağlantı menzili bu çalışmanın döndüğü eksen: kaç anchor'ın duyulduğunu,
o da geometriyi, o da dikey hatayı belirler. Uydurulmuş bir menzil sayısı
sessizce sonucu da uydurur. Bu yüzden her menzil, raporun adıyla verdiği
modülün yayımlanmış değerinden başlar ve oradan modellenen menzile geçiş
yazılı olarak kaydedilir (`yerkon/link_budget.py`).

| Senaryo | Modül | Yayımlanmış referans mesafe | Modellenen menzil | Oran |
|---|---|---|---|---|
| Şehir içi | SX1280/SX1281 @ 12,5 dBm | 3,0 km | 400 m | %13 |
| Kırsal | E28-2G4M27S @ 27 dBm | 8,0 km | 3.000 m | %37,5 |
| Tünel | DWM3000 | yayımlanmış üst sınır yok | 150 m | — |

Üretici referans mesafeleri **açık arazide, 5 dBi anten, 2,5 m yükseklik
ve en düşük hava hızında (1 kbps)** ölçülmüştür. Bir kurulum bu üç koşulun
hiçbirini karşılamaz: menzil ölçümü 1 kbps'ten çok daha geniş bantta
çalışır, ve ne kentsel kanyon ne de yol kenarı açık arazidir. Derating
oranları bu projenin mühendislik yargısıdır, ölçüm değildir.

Qorvo DWM3000 için üst sınır yayımlamıyor. Ticari modüller için bildirilen
pratik değerler ~50-100 m; selefi DWM1000 için 300 m ilan edilmiş, harici
antenli DW3000 kartlarında açık görüşte 500 m gösterilmiştir. 150 m, tünel
kesitinin sinyali dalga kılavuzu gibi taşıması gerekçesiyle bu bandın üst
yarısından seçilmiştir.

## En önemli bulgu: tünel düğüm aralığı

Rapor pilot için "bir ulaşım koridoruna 10-15 yayın düğümü" öngörüyor; 2 km
koridorda bu ~150 m aralık demek. DWM3000'in gerçekçi menzilinde bu aralık
**konum çözümü üretmiyor**:

| Düğüm aralığı | Menzildeki düğüm (en az) | HDOP | VDOP | TL/km |
|---|---|---|---|---|
| 150 m (raporun öngördüğü) | 2 | çözüm yok | çözüm yok | 10.885 |
| 100 m | 2 | çözüm yok | çözüm yok | 16.344 |
| 75 m (teorik tavan) | 4 | 3,83 | 15,02 | 21.771 |
| **60 m (kullanılan)** | **5** | **3,10** | **14,14** | **27.230** |
| 50 m | 5 | 2,61 | 11,04 | 32.689 |

3B konum çözümü en az dört mesafe ölçümü ister. 150 m aralıkta alıcı bir
veya iki düğüm duyar. Tavan `2R/4 = 75 m`; 60 m, beşinci düğümü menzilde
tutmak için pay bırakır. Bedeli, tünel CAPEX'inin 2,5 katına çıkmasıdır
(10.885 → 27.230 TL/km).

Bu, simülasyonun rapora geri verdiği tek somut tasarım düzeltmesidir.

## Sonuçlar nasıl okunmalı

**Yatay doğruluk hedefe yakın.** Şehir içi HPE P50 = 2,31 m, raporun kendi
"ideal senaryolarda <2 m" hedefinin biraz üstünde. Tünelde 15 cm.

**Radyo tek başına yüksekliği çözemiyor; harita çözüyor.** Karasal bir
sistemde her anchor alıcıya göre neredeyse aynı yükseklikte durur. Alıcıdan
6 m'lik bir yol kenarı ünitesine 250 m mesafede bakış açısı 1,03 derece,
500 m'de 0,52 derecedir; GNSS uydusunda aynı açı 45 derece civarındadır.
Harita kısıtı kaldırıldığında dikey hata şehir içinde 1,07 m'den 12,70 m'ye,
kırsalda 31 m'ye çıkıyor. Ayrıntı:
[docs/METHOD.md](docs/METHOD.md#dikey-hata-neden-yatay-hatadan-kötü).

**Tünelde sensör füzyonu bir iyileştirme değil, çalışma şartı.** Koridor
geometrisi eksen boyunca neredeyse hiçbir bilgi vermiyor: odometri ve
pusula kapatıldığında filtre sürükleniyor ve yatay P95 0,56 m'den 295 m'ye
çıkıyor.

**Açık alanda odometri yatayda küçük bir zarar veriyor.** %2'lik tekerlek
ölçek sapması 13,9 m/s'de 0,28 m/s'lik hız sapması demek; şehir içinde
radyo geometrisi zaten iyi olduğu için odometri bilgi yerine sapma ekliyor
(HPE P50 1,76 → 2,19 m). Kırsalda tersi, geometri zayıf olduğu için fayda
sağlıyor (P95 25,54 → 21,65 m).

**Kalibrasyon bedava ve fark yaratıyor.** Robinson'un yayımladığı SX1280
verisinde 2,83 m sabit sapma var. Sabit sapma tüm anchor'lara aynı anda
bindiği için ne geometri ne de filtreleme onu kaldırabiliyor: modül başına
ofset kalibrasyonu yatay hatayı 3,02 m'den 2,31 m'ye düşürüyor. Dikeyde
fark kapanıyor, çünkü orada belirleyici olan harita kısıtı. Raporun
mimarisi bu adımı zaten öngörüyor.

**Kırsalda "az sayıda yüksek kapsamalı nokta" bedelini doğrulukta ödüyor.**
Rapor Grup 2 için bunu açıkça istiyor. 500 m aralıklı 187 birim, 200 m
aralıklı 439 birime göre km başına 2,3 kat ucuz; karşılığında VDOP 6,80'den
11,56'ya çıkıyor. Tablo [docs/SCENARIOS.md](docs/SCENARIOS.md) içinde.

**CAPEX/km² koridor kurulumlarını haksız gösteriyor.** Bir tünel ya da yol
şeridi ince bir kurdeledir. Koridorlar için km başına maliyet daha
anlamlıdır: kırsal 4.821 TL/km, tünel 27.230 TL/km.

## Kurulum ve çalıştırma

```bash
pip install -r requirements.txt     # numpy, scipy
python run.py                       # output/yerkon_rows.csv

python run.py --details             # + tüm metrikler (JSON)
python run.py --image               # + tablo görseli (matplotlib gerekir)
python run.py --repeats 1000        # daha çok Monte Carlo tekrarı
```

Aynı seed aynı sayıları verir. Varsayılan seed 42, varsayılan tekrar sayısı
örnek başına 300.

Testler:

```bash
pip install pytest && python -m pytest -q
```

## Depo yapısı

```
run.py                  tek giriş noktası
yerkon/
  evidence.py           bir sayının nereden geldiğini taşıyan kayıt
  link_budget.py        yayımlanmış menzil değerleri ve derating gerekçeleri
  geometry.py           3B menzil geometrisi, HDOP/VDOP, geometri kalitesi
  ranging_error.py      SX1280 (ölçüme dayalı) ve DWM3000 (yapılandırılmış) hata modelleri
  receiver.py           raporun üç alıcısı: IMU, odometri, harita kısıtı
  path.py               tek-atım yörüngeleri ve zaman-serili sürüş izleri
  simulate.py           menzil kısıtlı Monte Carlo konum çözümü
  fusion.py             IMU + odometri + pusula + harita Kalman filtresi
  metrics.py            doğruluk, güvenilirlik, maliyet
  scenarios.py          dört kurulum senaryosunun tanımı
  table.py              satır biçimlendirme ve CSV
  render.py             PNG görsel (opsiyonel)
docs/
  METHOD.md             her tablo değerinin nasıl hesaplandığı
  SCENARIOS.md          her senaryonun tam parametre dökümü
  FUSION.md             alıcı modeli, Kalman filtresi, duyarlılık analizleri
  EVIDENCE.md           kanıt sınıfları ve sınırlar
```

## Sınırlar

Kısa liste; tamamı [docs/EVIDENCE.md](docs/EVIDENCE.md) içinde.

- SX1280 hata modeli altı yayımlanmış ölçüm noktasından geliyor ve yalnızca
  0-250 m aralığını kapsıyor. Şehir içinde bağlantıların %6'sı, kırsalda
  %72'si bu aralığın dışında; oran çıktıda raporlanıyor.
- DWM3000 için kalibreli veri yok. Tünel satırı bir tasarım hedefinin
  simülasyonu, bir ölçümün değil.
- Menzil derating oranları, NLOS oranları, montaj yükseklikleri ve düğüm
  aralıkları bu projenin varsayımları.
- CAPEX yalnızca ana bileşen maliyeti. PCB ve dizgi, pasifler, kablolama,
  mekanik işleme, test, sertifikasyon, vergi, kargo, saha kurulumu ve
  işçilik dahil değil.
- Kullanılabilirlik yalnızca modellenen paket kaybını içerir. Kanal
  doluluğu, girişim, düğüm arızası ve alıcı açılış süresi modellenmedi.
- VPE sütunu harita doğruluğuyla doğrusal ölçekleniyor; radyonun dikey
  performansını değil, haritanınkini ölçüyor.
- Menzil hatasının ne kadarının ortalamayla yok olmayan sabit ofset olduğu
  ölçülemedi. Varsayılan %50 alındı; %0 ile %100 arasında şehir içi hata
  iki, kırsal dört katına çıkıyor.
- Manyetik bozulma, tekerlek kayması, yanal harita eşleme ve kanal
  doluluğu modellenmedi.
