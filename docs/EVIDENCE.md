# Kanıt sınıfları ve sınırlar

Karşılaştırma tablosu çok farklı ağırlıkta sayıları aynı yazı tipiyle yan
yana koyuyor: gerçek bir ölçümden türetilmiş bir değer, rapordan
kopyalanmış bir fiyat ve bu projenin seçtiği bir parametre. Hepsine eşit
güvenmek yanlış olur. Bu yüzden her parametre ve her sonuç bir
`EvidenceRecord` taşır (`yerkon/evidence.py`).

## Sınıflar

| Sınıf | Anlamı | Nerede kullanılıyor |
|---|---|---|
| `PUBLISHED_EXPERIMENT` | Birisi ölçmüş ve yayımlamış | Robinson'un altı SX1280 gözlemi |
| `HARDWARE_CALIBRATED_MODEL` | Hata dağılımı gerçek ölçümden çekilen model | Şehir içi ve kırsal satırlar |
| `DESIGN_DOCUMENT` | Rapordan alınmış: fiyat, düğüm sayısı, hedef doğruluk | Birim fiyatlar, tünel düğüm aralığı, UWB hedefi |
| `SIMULATED_MONTE_CARLO` | Kalibre edilmemiş bir modelden üretilmiş simülasyon | Tünel satırı |
| `ENGINEERING_ASSUMPTION` | Kaynak vermediği için bu projenin seçtiği değer | Menziller, NLOS oranları, montaj yükseklikleri, aralıklar, harita doğruluğu |
| `OFFICIAL_SPECIFICATION` | Üretici, adı geçen parça için belirtiyor | BNO085 pusula doğruluğu (3,5° dinamik) |

Bir tasarım hedefi bir ölçüm değildir. Rapor DWM3000 için ±10 cm sınıfı
doğruluk hedefliyor; bu hedefi bir dağılıma çevirip simüle etmek, o
doğruluğun ölçüldüğü anlamına gelmez. Tünel satırı bu yüzden
`SIMULATED_MONTE_CARLO` etiketli, `HARDWARE_CALIBRATED_MODEL` değil.

## SX1280 hata modeli

Kaynak: Stuart Robinson'un kişisel mühendislik blogunda yayımladığı
SX1280 menzil ölçüm testi.
<https://stuartsprojects.github.io/2019/04/26/Semtech-SX1280-2-4Ghz-LoRa-ranging-tranceivers.html>

Rapor kendi "1 m altı görüş hattı" iddiası için de aynı kaynağı gösteriyor.

| Gerçek menzil | Gösterilen | Hata |
|---|---|---|
| 0 m | 4,4 m | +4,4 m |
| 50 m | 57,6 m | +7,6 m |
| 100 m | 103,0 m | +3,0 m |
| 150 m | 148,0 m | −2,0 m |
| 200 m | 201,0 m | +1,0 m |
| 250 m | 253,0 m | +3,0 m |

Ortalama sapma +2,83 m, kalan standart sapma 2,94 m.

Model, bu altı hatadan yerine koyarak örnekleme yapar (bootstrap).
Parametrik bir dağılım uydurulmadı, menzile bağlı bir regresyon
kurulmadı. Altı tekrarsız nokta ne bir dağılım şekli iddiasını ne de bir
menzil bağımlılığı iddiasını taşıyabilir.

### Bu modelin taşımadıkları

- **Menzil bağımlılığı.** Hata 50 m'de ve 1.000 m'de aynı dağılımdan
  çekiliyor. Gerçekte uzak bağlantılar daha kötü olacaktır.
- **0-250 m dışı geçerlilik.** Kaynağın kapsadığı aralık bu. Kırsal
  senaryodaki bağlantıların %72'si, şehir içindekilerin %6'sı bu aralığın
  dışında. Bu oranlar `links_beyond_calibrated_envelope` alanında
  raporlanıyor; gizlenmiyor ama giderilmiyor da. Şehir içindeki oranın
  düşük olması, alıcının menzildeki her anchor yerine en yakın sekiziyle
  ölçüm yapmasından geliyor.
- **Ortam koşulu.** Bant genişliği, yayılım faktörü, sıcaklık, anten
  yönelimi, LOS/NLOS durumu koşullanmıyor.
- **İstatistiksel güç.** Altı nokta, tek kurulum, tek ortam. Hobi
  düzeyinde bir test; üretici spesifikasyonu değil, bu projenin ölçümü
  değil.

Kalibreli varyant bu altı hatanın ortalamasını çıkarır. Bu, raporun kendi
mimarisinde yer alan modül başına menzil ofseti kalibrasyonunu modeller:
sabit bir ofset tam olarak böyle bir kalibrasyonun sildiği şeydir.
Kalibrasyon donanımı sessizleştirmez, sadece ortalamayı sıfırlar; kalan
2,94 m'lik saçılma iki varyantta da aynıdır ve bir test bunu doğrular.

## DWM3000 hata modeli

Kalibreli DWM3000 ölçümü bu projeye ulaşmadı. Model, raporun kendi
belirttiği ±10 cm sınıfı hedefe parametrelenmiş bir Gauss dağılımı ve
bağlantıların %10'una uygulanan 0,3 m'lik bir NLOS sapmasıdır.

Bu, ölçülmüş bir hata modeli değil, bir hedefin dağılım biçiminde ifade
edilmiş halidir. Tünel satırının sonuçları "bu hedef tutarsa şu geometri
şunu verir" cümlesinin sayısal karşılığıdır, "ölçtük, bu çıktı" değil.

## Rapordan alınan değerler

| Değer | Kullanım |
|---|---|
| Şehir içi yayın birimi: 1.366,07 TL | Şehir içi CAPEX |
| Kırsal yayın birimi (E28-2G4M27S): 1.082,68 TL | Kırsal CAPEX |
| Kritik bölge yayın birimi (DWM3000): 1.634,44 TL | Tünel CAPEX |
| 2 km koridora 10-15 yayın düğümü | Tünel düğüm aralığı için başlangıç noktası; bkz. aşağıdaki not |
| DWM3000 için ±10 cm sınıfı hedef | UWB hata modeli σ |
| Montaj sınıfları (direk, cephe, çatı) | Şehir içi montaj yükseklikleri |
| TWR tercihi (saat senkronizasyonu gerektirmemek için) | DS-TWR kullanımı |
| "Yeterli sayıda Yayın Birimi ile konuşacak" | Fix başına 8 anchor |
| İdeal senaryolarda <2 m HPE P50 hedefi | Şehir içi sonucun karşılaştırıldığı ölçüt |

Raporun tünel düğüm yoğunluğu bu simülasyonda doğrudan kullanılamadı.
10-15 düğüm/2 km, ~150 m aralık demektir; DWM3000'in modellenen 150 m
menzilinde bu aralık bir fix için gereken dört anchor'ı menzilde
bırakmıyor. Aralık 60 m'ye indirildi ve gerekçesi
[SCENARIOS.md](SCENARIOS.md#düğüm-aralığı-neden-raporun-öngördüğünden-küçük)
içinde.

Fiyatlar 100 adetlik toplu alım kademesinden ve yalnızca bileşen
maliyetidir. Montaj, sertifikasyon, altyapı, enerji beslemesi, backhaul ve
işçilik dahil değildir. Gerçek CAPEX daha yüksek olacaktır ve fark, bu
projenin rapordan kestirebileceği bir büyüklük değildir.

## Bu projenin varsayımları

Aşağıdakiler için kaynak yok; hepsi bu projenin seçimi ve hepsi sonucu
doğrudan etkiliyor.

| Varsayım | Değer | Etkisi |
|---|---|---|
| Şehir içi menzil derating | 3,0 km referansın %13'ü = 400 m | Izgara aralığını belirler |
| Kırsal menzil derating | 8,0 km referansın %37,5'i = 3.000 m | Kaç anchor'ın duyulduğunu belirler |
| Tünel bağlantı menzili | 150 m (yayımlanmış üst sınır yok) | Düğüm aralığını ve tünel CAPEX'ini belirler |
| Fix başına anchor sayısı | 8 (en yakınlar) | DOP ile çıkarsama oranı arasındaki dengeyi belirler |
| Şehir içi ızgara aralığı | 150 m | VDOP ve CAPEX'i belirler |
| Yol kenarı nokta aralığı | 500 m | Kırsal VDOP ve CAPEX'i belirler |
| Kule aralığı | 2,5 km | Kuleleri her noktada menzilde tutar |
| Montaj yükseklikleri | 6 m yol kenarı, 35-45 m kule, 8/20/35 m şehir | Bakış açılarını belirler |
| NLOS oranları | %35 şehir, %15 kırsal, %10 tünel | Hata kuyruğunu belirler |
| Paket kaybı | %2 / %1 / %3 | Kullanılabilirlik sütununu belirler |
| Kapsama genişliği tanımı | Kırsalda taşıt yolu | Alan ve CAPEX/km² sütunlarını belirler |

### Menzil derating oranları

Üretici referans mesafeleri gerçek ve yayımlanmıştır; onlardan modellenen
menzile geçişteki oran değildir. Referans mesafeler açık arazide, 5 dBi
anten, 2,5 m yükseklik ve 1 kbps hava hızında ölçülür. Bir kurulum bu üç
koşulun hiçbirini karşılamaz, ama "ne kadar düşürmeli" sorusunun ölçülmüş
bir cevabı bu projede yok. %13 ve %37,5 mühendislik yargısıdır.

Stuart Robinson'un aynı yonga ile 40 km ve 85 km menzil ölçümü yayımlamış
olması bu oranları geçersiz kılmaz: o ölçümler balondan yere, temiz
Fresnel bölgesiyle yapılmıştır ve yol kenarındaki bir bağlantıya
aktarılamaz.

### Tünel bağlantı menzili

Bu, çalışmadaki tek en sonuç belirleyici varsayım. Qorvo DWM3000 için bir
üst sınır yayımlamıyor. Bildirilen pratik değerler ticari modüller için
~50-100 m; selefi DWM1000 için 300 m ilan edilmiş, harici antenli DW3000
kartlarında açık görüşte 500 m gösterilmiştir. 150 m, tünel kesitinin
sinyali dalga kılavuzu gibi taşıması gerekçesiyle bu bandın üst yarısından
seçildi.

Sonuç doğrudan buna bağlı: 150 m menzilde raporun kendi 150 m'lik düğüm
aralığı bir fix için yeterli anchor bırakmaz ve aralık 60 m'ye inmek
zorunda kalır, tünel CAPEX'i 2,5 katına çıkar. Gerçek menzil 300 m ise
raporun aralığı çalışır ve bu düzeltme gereksizdir; 75 m ise 30 m aralık
gerekir ve maliyet iki katına daha çıkar.

## Alıcı ve füzyon varsayımları

Tablodaki doğruluk artık filtrelenmiş sonuçtan geliyor, dolayısıyla filtre
ve sensör varsayımları da sonucu doğrudan belirliyor. Tamamı
[FUSION.md](FUSION.md) içinde; en etkili ikisi:

| Varsayım | Değer | Etkisi |
|---|---|---|
| Menzil hatasının kalıcı sapma oranı | %50 | %0 ile %100 arasında şehir içi hata iki, kırsal dört katına çıkıyor |
| Harita yükseklik belirsizliği | 0,5 m | VPE bununla doğrusal ölçekleniyor; VPE sütunu haritayı ölçüyor |

BNO085'in 3,5 derecelik dinamik pusula hatası üreticinin yayımladığı
değerdir. Onunla birlikte kullanılan ivme gürültüsü ve sapması, odometri
ölçek hatası ve harita doğruluğu bu projenin figürleridir.

## Modellenmeyen katmanlar

Aşağıdakiler hâlâ modellenmedi:

- **Manyetik bozulma.** Tünelde ve şehir kanyonunda pusula, demir ve akım
  kaynaklı bozulmadan 3,5 derecelik spesifikasyonun ötesinde etkilenir.
  Gerçek sistemin aleyhine.
- **Tekerlek kayması.** Frenleme ve virajda odometri yolu yanlış sayar.
  Aleyhine.
- **Yanal harita eşleme.** Yalnızca yükseklik kısıtı uygulandı; aracın
  şeritte olduğu bilgisi kullanılsa yatay hata da düşerdi. Lehine.
- **NLOS tespiti ve dışlama.** NLOS sapması eklendi, ayıklanmadı. Lehine.
- **Menzile bağlı hata büyümesi.** Uzak bağlantılar kısa bağlantılarla aynı
  hata dağılımını kullanıyor. Aleyhine.
- **Anchor konum belirsizliği.** Anchor koordinatları kusursuz biliniyor
  varsayıldı. Aleyhine.
- **Kanal doluluğu ve çakışma.** Paket kaybı sabit olasılık, trafik yüküne
  bağlı değil. Aleyhine.

Buna karşılık aşağıdakiler de modellenmedi ve gerçek sistemin aleyhine
çalışır:

- **Menzile bağlı hata büyümesi.** Uzun bağlantılar kısa bağlantılarla
  aynı hata dağılımını kullanıyor.
- **Anchor konum belirsizliği.** Anchor koordinatları kusursuz biliniyor
  varsayıldı; gerçekte kurulum ölçümünün kendi hatası vardır.
- **Saat sürüklenmesi ve sıcaklık etkisi.**
- **Kanal doluluğu ve çakışma.** Paket kaybı sabit bir olasılık olarak
  modellendi, trafik yüküne bağlı değil.
