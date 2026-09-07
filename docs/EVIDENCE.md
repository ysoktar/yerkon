# Kanıt sınıfları ve sınırlar

Karşılaştırma tablosu çok farklı ağırlıkta sayıları aynı yazı tipiyle yan
yana koyuyor: gerçek bir ölçümden türetilmiş bir değer, sunumdan
kopyalanmış bir fiyat ve bu projenin seçtiği bir parametre. Hepsine eşit
güvenmek yanlış olur. Bu yüzden her parametre ve her sonuç bir
`EvidenceRecord` taşır (`yerkon/evidence.py`).

## Sınıflar

| Sınıf | Anlamı | Nerede kullanılıyor |
|---|---|---|
| `PUBLISHED_EXPERIMENT` | Birisi ölçmüş ve yayımlamış | Robinson'un altı SX1280 gözlemi |
| `HARDWARE_CALIBRATED_MODEL` | Hata dağılımı gerçek ölçümden çekilen model | Şehir içi ve kırsal satırlar |
| `DESIGN_DOCUMENT` | Sunumdan alınmış: fiyat, düğüm sayısı, hedef doğruluk | Birim fiyatlar, tünel düğüm aralığı, UWB hedefi |
| `SIMULATED_MONTE_CARLO` | Kalibre edilmemiş bir modelden üretilmiş simülasyon | Tünel satırı |
| `ENGINEERING_ASSUMPTION` | Kaynak vermediği için bu projenin seçtiği değer | Menziller, NLOS oranları, montaj yükseklikleri, aralıklar |

Bir tasarım hedefi bir ölçüm değildir. Sunum DWM3000 için ±10 cm sınıfı
doğruluk hedefliyor; bu hedefi bir dağılıma çevirip simüle etmek, o
doğruluğun ölçüldüğü anlamına gelmez. Tünel satırı bu yüzden
`SIMULATED_MONTE_CARLO` etiketli, `HARDWARE_CALIBRATED_MODEL` değil.

## SX1280 hata modeli

Kaynak: Stuart Robinson'un kişisel mühendislik blogunda yayımladığı
SX1280 menzil ölçüm testi.
<https://stuartsprojects.github.io/2019/04/26/Semtech-SX1280-2-4Ghz-LoRa-ranging-tranceivers.html>

Sunum kendi "1 m altı görüş hattı" iddiası için de aynı kaynağı gösteriyor.

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

- **Menzil bağımlılığı.** Hata 50 m'de ve 1.500 m'de aynı dağılımdan
  çekiliyor. Gerçekte uzak bağlantılar daha kötü olacaktır.
- **0-250 m dışı geçerlilik.** Kaynağın kapsadığı aralık bu. Kırsal
  senaryodaki bağlantıların %83'ü, şehir içindekilerin %54'ü bu aralığın
  dışında. Bu oranlar `links_beyond_calibrated_envelope` alanında
  raporlanıyor; gizlenmiyor ama giderilmiyor da.
- **Ortam koşulu.** Bant genişliği, yayılım faktörü, sıcaklık, anten
  yönelimi, LOS/NLOS durumu koşullanmıyor.
- **İstatistiksel güç.** Altı nokta, tek kurulum, tek ortam. Hobi
  düzeyinde bir test; üretici spesifikasyonu değil, bu projenin ölçümü
  değil.

Kalibreli varyant bu altı hatanın ortalamasını çıkarır. Bu, sunumun kendi
mimarisinde yer alan modül başına menzil ofseti kalibrasyonunu modeller:
sabit bir ofset tam olarak böyle bir kalibrasyonun sildiği şeydir.
Kalibrasyon donanımı sessizleştirmez, sadece ortalamayı sıfırlar; kalan
2,94 m'lik saçılma iki varyantta da aynıdır ve bir test bunu doğrular.

## DWM3000 hata modeli

Kalibreli DWM3000 ölçümü bu projeye ulaşmadı. Model, sunumun kendi
belirttiği ±10 cm sınıfı hedefe parametrelenmiş bir Gauss dağılımı ve
bağlantıların %10'una uygulanan 0,3 m'lik bir NLOS sapmasıdır.

Bu, ölçülmüş bir hata modeli değil, bir hedefin dağılım biçiminde ifade
edilmiş halidir. Tünel satırının sonuçları "bu hedef tutarsa şu geometri
şunu verir" cümlesinin sayısal karşılığıdır, "ölçtük, bu çıktı" değil.

## Sunumdan alınan değerler

| Değer | Kullanım |
|---|---|
| Şehir içi yayın birimi: 1.366,07 TL | Şehir içi CAPEX |
| Kırsal yayın birimi (E28-2G4M27S): 1.082,68 TL | Kırsal CAPEX |
| Kritik bölge yayın birimi (DWM3000): 1.634,44 TL | Tünel CAPEX |
| 2 km koridora 10-15 yayın düğümü | Tünel düğüm aralığı (150 m) |
| DWM3000 için ±10 cm sınıfı hedef | UWB hata modeli σ |
| Montaj sınıfları (direk, cephe, çatı) | Şehir içi montaj yükseklikleri |
| TWR tercihi (saat senkronizasyonu gerektirmemek için) | DS-TWR kullanımı |

Fiyatlar 100 adetlik toplu alım kademesinden ve yalnızca bileşen
maliyetidir. Montaj, sertifikasyon, altyapı, enerji beslemesi, backhaul ve
işçilik dahil değildir. Gerçek CAPEX daha yüksek olacaktır ve fark, bu
projenin sunumdan kestirebileceği bir büyüklük değildir.

## Bu projenin varsayımları

Aşağıdakiler için kaynak yok; hepsi bu projenin seçimi ve hepsi sonucu
doğrudan etkiliyor.

| Varsayım | Değer | Etkisi |
|---|---|---|
| Şehir içi bağlantı menzili | 400 m | Izgara aralığını belirler |
| Kırsal bağlantı menzili | 1.500 m | Kaç anchor'ın fix'e katıldığını belirler |
| Tünel bağlantı menzili | 400 m | 150 m aralığın yeterliliğini belirler |
| Şehir içi ızgara aralığı | 150 m | VDOP ve CAPEX'i belirler |
| Levha aralığı | 200 m | Kırsal VDOP ve CAPEX'i belirler |
| Kule aralığı | 2,5 km | Levha araları arasındaki dikey geometriyi kurtarır |
| Montaj yükseklikleri | 6 m levha, 35-45 m kule, 8/20/35 m şehir | Bakış açılarını belirler |
| NLOS oranları | %35 şehir, %15 kırsal, %10 tünel | Hata kuyruğunu belirler |
| Paket kaybı | %2 / %1 / %3 | Kullanılabilirlik sütununu belirler |
| Kapsama genişliği tanımı | Kırsalda taşıt yolu | Alan ve CAPEX/km² sütunlarını belirler |

Tünel bağlantı menzili özellikle dikkat ister. 400 m, açık havadaki
DWM3000 rakamlarının üstündedir; gerekçesi tünel kesitinin dalga kılavuzu
etkisidir. Bu etki gerçektir ama bu proje onu ölçmedi. Gerçek menzil daha
kısaysa sunumun kendi 150 m'lik düğüm aralığı bir fix için yeterli anchor
bırakmaz ve tünel satırının kullanılabilirliği düşer.

## Modellenmeyen katmanlar

Sonuçlar tek atımlık konum hatasıdır. Aşağıdakiler modellenmedi ve
hepsi gerçek sistemin lehine çalışır:

- **Kalman filtresi veya benzeri izleme.** Ardışık fix'ler bağımsız
  varsayıldı; gerçekte hareket modeli hatayı bastırır.
- **Harita kısıtı.** Yol yüksekliği biliniyorsa dikey eksen çözülmek
  zorunda değildir. Sunumun füzyon mimarisi bunu öngörüyor; dikey hata
  rakamları bu katman olmadan geçerlidir.
- **Ataletsel ölçüm birimi desteği.** Sunum IMU füzyonundan söz ediyor.
- **NLOS tespiti ve dışlama.** NLOS sapması eklendi, ayıklanmadı.

Buna karşılık aşağıdakiler de modellenmedi ve gerçek sistemin aleyhine
çalışır:

- **Menzile bağlı hata büyümesi.** Uzun bağlantılar kısa bağlantılarla
  aynı hata dağılımını kullanıyor.
- **Anchor konum belirsizliği.** Anchor koordinatları kusursuz biliniyor
  varsayıldı; gerçekte kurulum ölçümünün kendi hatası vardır.
- **Saat sürüklenmesi ve sıcaklık etkisi.**
- **Kanal doluluğu ve çakışma.** Paket kaybı sabit bir olasılık olarak
  modellendi, trafik yüküne bağlı değil.
