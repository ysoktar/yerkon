# YERKON karşılaştırma tablosu simülasyonu

Bu depo tek bir iş yapar: YERKON raporunda tarif edilen şehir içi, kırsal
ve kritik bölge kurulumlarını simüle eder ve karşılaştırma tablosuna
girecek üç satırı üretir. Sayılar varsayılmaz, hesaplanır; her girdinin
nereden geldiği çıktıya iliştirilir.

```bash
python run.py
```

Çıktı `output/yerkon_rows.csv`: sadece üç satır.

## Üretilen satırlar

| Sistem | Teknoloji | Ortam | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan | CAPEX |
|---|---|---|---|---|---|---|---|---|
| YERKON (Şehir İçi)¹ | Karasal PNT (SX1280/LoRa TWR) | Dış | 1,64 m | 3,40 m | 1,00 m | %100,0 | 1,00 km² | ≈ 49179 TL/km² |
| YERKON (Kırsal)² | Karasal PNT (E28-SX1280 TWR) | Dış | 2,55 m | 3,86 m | 1,00 m | %100,0 | 1,01 km² | ≈ 140705 TL/km² |
| YERKON (Kritik Bölge/Tünel)³ | Karasal PNT (UWB/DWM3000 TWR) | İç + dış | 0,43 m | 1,28 m | 0,70 m | ≈ %99,3 | 1,00 km² | ≈ 1363123 TL/km² |

Doğruluk değerleri filtrelenmiş sonuçtan geliyor. Menzil ölçümleri BNO085
IMU, tekerlek odometrisi ve harita kısıtıyla bir Kalman filtresinde
birleştirildi, çünkü raporun tarif ettiği alıcı bu. Radyo tek başına sonuç
da hesaplanıyor ve JSON çıktısında duruyor. Ayrıntısı
[docs/FUSION.md](docs/FUSION.md) içinde.

VPE sütunu haritayı ölçüyor, radyoyu değil. Karasal geometri yüksekliği
çözemiyor. Çözen şey, aracın ölçülmüş bir yol yüzeyinin üstünde olduğunun
bilinmesi. Harita belirsizliği 0,5 m alındı ve VPE bununla doğrusal
ölçekleniyor, yani σ 2 m olsaydı VPE P95 dört katına çıkardı. Rapora
yazılırken bu belirtilmeli.

Dipnotlar:

1. 1 km × 1 km şehir hücresi, 175 m aralıklı 36 yayın birimi (8, 20 ve
   35 m montaj yüksekliği), 406 kHz menzil bandı. Modül başına menzil
   ofseti kalibrasyonu uygulanmış; atlanırsa ne olduğu aşağıda.
2. 42 km karayolu koridoru, 812 kHz menzil bandı. 750 m'de bir, yolun iki
   tarafında karşılıklı yol kenarı noktası (6 m) ve 2,5 km'de bir kule
   (35 ile 45 m arası), toplam 131 birim. Kapsanan alan, iki hat arasındaki
   24 m genişliğindeki taşıt yolu.
3. 50 km tünel ağı, 60 m aralıklı 834 UWB düğümü. Raporun öngördüğü 150 m
   aralık DWM3000'in gerçek menziliyle konum çözümü üretmiyor, aşağıya
   bakınız.

Aralık ve bant genişliği seçimlerinin nasıl yapıldığı
[docs/CONFIGURATION.md](docs/CONFIGURATION.md) içinde. Şehir içi ve kırsal
aralıkları bu süpürmede değişti, ve ikisi de aynı anda hem ucuzladı hem
doğrulaştı.

OPEX her satırda "-". Rapor yıllık işletme maliyeti vermiyor, ve
karşılaştırma tablosu yayımlanmış işletme maliyeti olmayan diğer sistemler
için zaten "-" kullanıyor.

Şehir içi ve kırsalda kullanılabilirlik yuvarlama sonucu değil. 7200
denemenin 7200'ünde konum çözümü üretildi. Bu yalnızca modellenen kayıp
altındaki radyo bağlantısı kullanılabilirliğidir. Kanal doluluğu, girişim,
düğüm arızası ve alıcı açılış süresi modellenmedi, dolayısıyla gerçek
hizmet kullanılabilirliği bunlardan dolayı daha düşük olacak. GNSS
satırlarındaki yüzdelerle aynı ölçüt gibi okunmamalı.

## Kaç anchor gerekiyor, kaç tane var

3B konum çözümü en az dört mesafe ölçümü ister. Menzil düzeltmesinden sonra
düğüm sayısının artması gerekmedi, çünkü şehir içi ve kırsal zaten bu
sınırın çok üstündeydi:

| Senaryo | Düğüm | Menzilde duyulan | Fix'te kullanılan | En kötü noktada | Gereken |
|---|---|---|---|---|---|
| Şehir içi | 36 | 15 | 8 | 5 | 4 |
| Kırsal | 131 | 18 | 8 | 8 | 4 |
| Tünel | 834 | 5 | 5 | 5 | 4 |

Şehir içi ve kırsalda alıcı kullanabileceğinden fazlasını duyuyor. Bir fix
en fazla sekiz anchor kullandığı için fazlası işe yaramıyor, ve bu iki
satırın aralığını açmayı mümkün kılan da bu.

Sadece tünel sınıra yakın. Düğüm sayısı orada 334'ten 834'e çıktı, çünkü
raporun öngördüğü 150 m aralık DWM3000'in gerçek menziliyle dört anchor
duyurmuyor. Gereken aralık 60 m, ve bedeli km başına 2,5 kat düğüm.

Tünelin sınıra yakınlığının ölçülebilir bir sonucu var. Paket kaybı her
anchor için ayrı uygulanıyor, çünkü TWR her anchor ile ayrı bir alışveriş.
Kaybolan bir alışveriş tüm konumu değil bir ölçümü götürüyor. Şehir içi ve
kırsalda sekiz ölçümden birini kaybetmek fix'i etkilemiyor. Tünelde beş
ölçümden ikisini kaybetmek fix'i bitiriyor, ve kullanılabilirliğin %99,3'te
kalmasının sebebi bu.

## Menzil bant genişliği: optimum ortada

Daha önce "en geniş bandı seç" diye yazmıştım. Ölçünce yanlış çıktı.

Geniş bant temiz kanalda menzil hatasını gerçekten yarıya indiriyor, ve
menzilden hiçbir şey götürmüyor, çünkü yasal güç yoğunluk sınırı yüzünden
bant genişliğiyle birlikte artıyor. Ama çok yolluluğu da ayırıyor. Yollar
ayrı tepeler olarak çözülünce tepe dedektörü en güçlüsünü seçiyor, ve
engelli bir kanalda en güçlüsü bir yansıma oluyor. 1625 kHz'de medyan hata
0,00 m, ama hataların %28'i 10 m'yi aşıyor.

Bunun bilinen çözümü ön kenar kestirimi, ve SX1280 kullanamıyor. Geriye
arama korelasyon ana lobunun yarısı kadar erken tetikleniyor, bu da UWB'de
0,3 m, SX1280'de 90 m ediyor. Ölçtüm, 114 m'lik bir ofset veriyor.

Kararı menzil hatası değil konum hatası veriyor. HPE P50 olarak:

| Bant | Şehir içi (%35 engelli) | Kırsal (%15 engelli) |
|---|---|---|
| 203 kHz | 2,82 m | 5,82 m |
| 406 kHz | **1,64 m** | 3,22 m |
| 812 kHz | 2,35 m | **2,55 m** |
| 1625 kHz | 5,01 m | 3,54 m |

İkisi de U biçimli, ve optimum ortam açıldıkça genişliyor. Tablo şehir
içini 406 kHz, kırsalı 812 kHz ile üretiyor.

Rapor için iyi haber: 406 kHz zaten Semtech'in ranging modunun ve
Robinson'ın ölçümlerinin ayarı, yani şehir içi tercihi doğruymuş.
Değiştirilmesi gereken tek şey kırsalda bir katlama. Ayrıntısı
[docs/WAVEFORM.md](docs/WAVEFORM.md) içinde.

## Maliyet: iki şebeke de gereğinden sıktı

Bir fix en fazla sekiz anchor kullanıyor. Alıcı sekizden fazlasını duyduğu
anda fazlası hiç kullanılmıyor, ve şebekeyi sıklaştırmak yalnızca en yakın
sekizinin yaydığı tabanı daraltıyor. Daha çok donanımla daha kötü geometri.

Şehir içi ızgara:

| Aralık | Düğüm | TL/km² | HPE P50 | HPE P95 |
|---|---|---|---|---|
| 125 m | 81 | 110652 | 2,17 m | 4,44 m |
| 150 m (eski) | 49 | 66937 | 1,95 m | 3,99 m |
| 175 m | 36 | **49179** | **1,64 m** | **3,40 m** |
| 225 m | 25 | 34152 | 1,97 m | 4,76 m |

Kırsal levha aralığı:

| Aralık | Düğüm | TL/km² | HPE P50 | HPE P95 |
|---|---|---|---|---|
| 500 m (eski) | 187 | 200854 | 2,88 m | 7,57 m |
| 750 m | 131 | **140705** | **2,55 m** | **3,86 m** |
| 1000 m | 103 | 110631 | 2,46 m | 11,07 m |

İkisinde de yeni aralık hem ucuz hem doğru, yani ödünleşim yok. Şehir içi
%27, kırsal %30 ucuzluyor. 225 m ve 1000 m daha da ucuz ama orada ödünleşim
başlıyor: 225 m yolun en kötü noktasında dört anchor bırakıyor, 1000 m
kırsal kuyruğu ikiye katlıyor. Gerekçeler
[docs/CONFIGURATION.md](docs/CONFIGURATION.md) içinde.

Daha büyük kaldıraç yol kaybı üstelinde. Dört anchor duyulması şartı
`aralık ≤ menzil/2` demek, ve menzil üstele çok duyarlı. Şehir içi için
seçtiğim 400 m, üstelin 3,8 olmasına denk geliyor, yani yoğun kanyonun ucu.
Üstel 3,5 çıkarsa aralık 354 m'ye kadar açılabilir. Birkaç noktada RSSI
ölçüp üsteli belirlemek, km² başına maliyetteki beş katlık belirsizliği
kapatır.

## Koridorda hata yolun karşısında, boyunca değil

Kırsal satırın yatay hatası uzun süre 7,81 m'de takılı kaldı, dikey hata
1,00 m iken. İki sütun aynı şeyi ölçmüyor, ve sebebi geometride.

Bir koridor bütün anchor'ları tek bir çizgi üzerine diziyor. Kırsal
düzende anchor'lar yol boyunca 42 km'ye yayılıyor ama yola dik yönde
sadece 60 m'lik bir şerit içinde duruyor. Sonuç, menzil ölçümünün iki
eksene duyarlılığında görünüyor. En yakın sekiz anchor için ortalama:

| Eksen | Menzil duyarlılığı |
|---|---|
| Yol boyunca (x) | 0,875 |
| Yola dik (y) | 0,097 |
| Düşey (z) | 0,108 |

Yani radyo, aracın yolun neresinde olduğunu iyi görüyor, hangi şeritte
olduğunu neredeyse hiç görmüyor. Filtrelenmiş hatanın bileşenleri de bunu
söylüyordu: yol boyunca P50 1,49 m, yola dik P50 7,40 m.

Çözüm, dikeyi zaten kurtaran şeyin aynısı. Yol yüzeyinin yüksekliğini
veren harita, taşıt yolunun nerede geçtiğini de veriyor. O kısıt filtreye
bağlandığında:

| Yanal harita kısıtı | HPE P50 | HPE P95 |
|---|---|---|
| Yok | 7,81 m | 26,49 m |
| σ 3,0 m (kullanılan) | **2,55 m** | **3,86 m** |
| σ 1,5 m | 1,66 m | 3,15 m |

Kuyruk yedide birine iniyor ve maliyet değişmiyor. σ 3,0 m seçildi çünkü
üç sigmada senaryonun modellediği 24 m'lik taşıt yolunu kapsıyor, yani
"hangi taşıt yolunda" diyor, "hangi şeritte" demiyor. Daha dar bir değer
şerit seviyesinde harita eşleştirme iddiası olurdu ve bunun için harita
yetmez.

Kısıt şehir içine uygulanmadı. Şehrin sokakları iki yöne birden gidiyor ve
test yörüngesi dönüyor, dolayısıyla sabitlenecek tek bir "yola dik" eksen
yok.

## Anchor konumları ne kadar iyi biliniyor

Her montaj noktası ölçülür, ve o ölçümden kalan hata çözüme doğrudan girer.
Menzil hatasından ayrı davranır: menzil hatası her ölçümde yeniden çekilir
ve ortalamayla küçülür, ölçüm hatası kurulum boyunca sabit kalır. Filtre
onu ortalayamaz.

Şehir içi ve kırsalda RTK her noktayı bağımsız sabitliyor. Tünelde gökyüzü
olmadığı için konum portalden travers ile taşınıyor, dolayısıyla hata
mesafenin kareköküyle büyüyor ve 50 km sonunda 11 cm oluyor.

Ölçülen sonuç: bu kalitede ölçüm hiçbir satırı belirlemiyor. Etki şehir
içinde %0,1, kırsalda %0,3, tünelde %0,7. Yani rapor yüksek hassasiyetli
ölçüm için ayrı bütçe ayırmak zorunda değil. Model tepkisiz olduğu için
değil: 2 m'lik bir ölçüm hatası verildiğinde tünel satırı 78 m'ye çıkıyor.
Ayrıntısı [docs/EVIDENCE.md](docs/EVIDENCE.md) içinde.

## Menzil değerleri nereden geliyor

Bağlantı menzili bu çalışmanın döndüğü eksen: kaç anchor'ın duyulduğunu,
o da geometriyi, o da dikey hatayı belirler. Uydurulmuş bir menzil sayısı
sessizce sonucu da uydurur. Bu yüzden her menzil, raporun adıyla verdiği
modülün yayımlanmış değerinden başlar ve oradan modellenen menzile geçiş
yazılı olarak kaydedilir (`yerkon/link_budget.py`).

| Senaryo | Modül | Yayımlanmış referans mesafe | Modellenen menzil | Oran |
|---|---|---|---|---|
| Şehir içi | SX1280/SX1281 @ 12,5 dBm | 3,0 km | 400 m | %13 |
| Kırsal | E28-2G4M27S @ 27 dBm | 8,0 km | 3000 m | %37,5 |
| Tünel | DWM3000 | yayımlanmış üst sınır yok | 150 m | yok |

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
| 150 m (raporun öngördüğü) | 2 | çözüm yok | çözüm yok | 10885 |
| 100 m | 2 | çözüm yok | çözüm yok | 16344 |
| 75 m (teorik tavan) | 4 | 3,83 | 15,02 | 21771 |
| 60 m (kullanılan) | **5** | **3,10** | **14,14** | **27262** |
| 50 m | 5 | 2,61 | 11,04 | 32689 |

3B konum çözümü en az dört mesafe ölçümü ister. 150 m aralıkta alıcı bir
veya iki düğüm duyar. Tavan `2R/4 = 75 m`; 60 m, beşinci düğümü menzilde
tutmak için pay bırakır. Bedeli, tünel CAPEX'inin 2,5 katına çıkması, yani
km başına 10885 TL yerine 27262 TL.

Bu, simülasyonun rapora geri verdiği en somut tasarım düzeltmesi. Diğer
ikisi, şehir içi ve kırsal aralıklarının ters yönde değişmesi: onlar
gereğinden sık kurulmuş.

## Sonuçlar nasıl okunmalı

**Yatay doğruluk hedefin altında.** Şehir içi HPE P50 1,64 m, raporun kendi
"ideal senaryolarda 2 m'nin altı" hedefinin içinde. Tünelde 43 cm.

**Radyo tek başına yüksekliği çözemiyor, harita çözüyor.** Karasal bir
sistemde her anchor alıcıya göre neredeyse aynı yükseklikte durur. Alıcıdan
6 m'lik bir yol kenarı ünitesine 250 m mesafede bakış açısı 1,03 derece,
500 m'de 0,52 derece. Aynı açı GNSS uydusunda 45 derece civarında. Harita
kısıtı kaldırıldığında dikey P95 şehir içinde 1,00 m'den 14,29 m'ye,
kırsalda 1,00 m'den 40,82 m'ye çıkıyor. Ayrıntısı
[docs/METHOD.md](docs/METHOD.md#dikey-hata-neden-yatay-hatadan-kötü)
içinde.

**Yardımcı sensörlerin katkısı her senaryoda dikeyde.** Odometri, pusula ve
harita kapatıldığında:

| Senaryo | HPE P95 (tam / radyo) | VPE P95 (tam / radyo) |
|---|---|---|
| Şehir içi | 3,40 / 3,60 m | 1,00 / 14,97 m |
| Kırsal | 3,86 / 3,65 m | 1,00 / 34,43 m |
| Tünel | 1,28 / 1,71 m | 0,70 / 5,69 m |

Dikeyde kazanç on beş ile otuz dört kat. Yatayda küçük ve kırsalda hafif
negatif: radyo tek başına P95 3,65 m, tam yapılandırmada 3,86 m. Sebebi
odometri, aşağıda. Daha önce
tünel için "füzyon olmadan filtre ıraksıyor" diye bir bulgu raporlamıştım.
O bir artefaktmış ve geri alındı, gerekçesi
[docs/WAVEFORM.md](docs/WAVEFORM.md#geri-alınan-bir-bulgu) içinde.

**Açık alanda odometri yatayda küçük bir zarar veriyor.** %2'lik tekerlek
ölçek sapması 13,9 m/s'de 0,28 m/s'lik hız sapması demek. Şehir içinde
radyo geometrisi zaten iyi olduğu için odometri bilgi yerine sapma ekliyor:
odometri kapalıyken P50 1,76 m, açıkken 1,64 m, yani burada fayda sağlıyor.
Kırsalda yanal harita kısıtı geometri boşluğunu zaten kapattığı için
odometri artık bilgi eklemiyor: kapalıyken P50 2,10 m, açıkken 2,55 m.
Kısıt eklenmeden önce tersiydi. Yardımcı sensörlerin faydası, kapattıkları
boşluk başka bir şeyle kapanınca kayboluyor.

**Kalibrasyon bedava ve fark yaratıyor.** Robinson'un yayımladığı SX1280
verisinde 2,83 m sabit sapma var. Sabit sapma tüm anchor'lara aynı anda
bindiği için ne geometri ne filtreleme onu kaldırabiliyor. Modül başına
ofset kalibrasyonu yatay P50'yi 2,15 m'den 1,64 m'ye, P95'i 4,82 m'den
3,40 m'ye düşürüyor. Dikeyde fark kapanıyor, çünkü orada belirleyici olan
harita kısıtı. Raporun mimarisi bu adımı zaten öngörüyor.

Kalibrasyonsuz kurulum tabloda ayrı bir satır değil. Karşılaştırma
tablosundaki diğer sistemlerin hiçbiri kendisinin kasten kalibre
edilmemiş bir sürümünü satır olarak vermiyor, dolayısıyla o satır
sistemleri değil bir kurulum hatasını karşılaştırırdı.
`urban_scenario(calibrated=False)` onu hâlâ üretiyor.

**CAPEX/km² koridor kurulumlarını haksız gösteriyor.** Bir tünel ya da yol
şeridi ince bir kurdele. Koridorlar için km başına maliyet daha anlamlı:
kırsal 3377 TL/km, tünel 27262 TL/km.

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

`output/` klasörü sürüm takibinde değil: her çalıştırmada yeniden üretilir,
bu yüzden takip edilseydi her `git pull` çakışırdı. Referans kopya
`docs/reference_output/` içinde duruyor.

MATLAB tarafı için [matlab/README.md](matlab/README.md). Oradaki komutlar
MATLAB'ın kendi komut penceresinde çalışır, PowerShell'de değil.

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
  matlab_import.py      MATLAB dalga formu simülasyonu çıktısını okur
  table.py              satır biçimlendirme ve CSV
  render.py             PNG görsel (opsiyonel)
matlab/
  yerkon_env_check.m    hangi MATLAB sürümü ve toolbox'lar var
  yerkon_ranging_sim.m  dalga formu + çok yolluluk seviyesinde menzil hatası
docs/
  METHOD.md             her tablo değerinin nasıl hesaplandığı
  SCENARIOS.md          her senaryonun tam parametre dökümü
  FUSION.md             alıcı modeli, Kalman filtresi, duyarlılık analizleri
  WAVEFORM.md           MATLAB dalga formu simülasyonu ve bulguları
  EVIDENCE.md           kanıt sınıfları ve sınırlar
matlab/README.md        MATLAB tarafının çalıştırma sırası ve sınırları
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
