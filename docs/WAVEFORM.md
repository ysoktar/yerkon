# Dalga formu simülasyonu: menzil hatası nereden geliyor

Projedeki en zayıf kanıt menzil hata modeliydi. SX1280 için altı yayımlanmış
nokta, DWM3000 için ise raporun kendi hedefine (±10 cm) parametrelenmiş bir
Gauss vardı. İkisi de, fiziğin büyük ölçüde belirlediği bir büyüklük
hakkında varsayımdı.

`matlab/yerkon_ranging_sim.m` bunu doğrudan türetiyor: dalga formunu
üretiyor, kümelenmiş çok yolluluk kanalından geçiriyor, gürültü ekliyor,
varış zamanı kestirimi yapıyor. Aşağıdaki sonuçlar 7 vaka × 4 SNR × 3
mesafe × 300 deneme = vaka başına 3.600 denemeden geliyor (R2026a, 2026-09-07).

## Ne çıktı

| Kaynak | Sapma | σ | Not |
|---|---|---|---|
| **Robinson SX1280** (gerçek donanım) | +2,83 m | **2,94 m** | 6 nokta, 0-250 m, tek kurulum |
| MATLAB SX1280 406 kHz LOS | +0,41 m | **2,68 m** | 3.600 deneme |
| MATLAB SX1280 1,6 MHz LOS | +0,01 m | **0,68 m** | 3.600 deneme |
| MATLAB SX1280 1,6 MHz NLOS | +2,31 m | 16,59 m | ağır kuyruk |
| **Rapor hedefi DWM3000** | 0 m | **0,10 m** | tasarım hedefi, ölçüm değil |
| MATLAB UWB LOS | −0,45 m | **0,15 m** | hedefe yakın |
| MATLAB UWB tünel | −0,38 m | **0,45 m** | hedefin 4,5 katı |
| MATLAB UWB NLOS | +0,97 m | 1,64 m | |

## Aynı koşuyu tekrarlayınca ne kadar oynuyor

Aynı vaka kümesi iki kez çalıştırıldı: bir kez seri, bir kez `parfor` ile.
İşçiler kendi rastgele sayılarını çektiği için ikinci koşu birinciyi
bit düzeyinde tekrarlamaz, dolayısıyla bu ikisi bağımsız iki örneklem.
Aradaki fark, tek bir koşunun sayısına ne kadar güvenilebileceğini söylüyor:

| Vaka | σ (seri) | σ (parfor) | Fark |
|---|---|---|---|
| uwb_los | 0,155 m | 0,155 m | %0,1 |
| sx1280_1600k_los | 0,681 m | 0,668 m | %1,9 |
| uwb_nlos | 1,639 m | 1,608 m | %1,8 |
| sx1280_406k_nlos | 2,731 m | 2,667 m | %2,3 |
| sx1280_406k_los | 2,682 m | 2,590 m | %3,4 |
| sx1280_1600k_nlos | 16,613 m | 15,265 m | %8,1 |
| **uwb_tunnel** | **0,452 m** | **0,384 m** | **%15,1** |

Açık görüş hattı vakaları %3'ün altında oynuyor, yani bu sayılar üçüncü
haneye kadar okunabilir. Ağır kuyruklu vakalar oynuyor: tünel σ'sı iki koşu
arasında %15 fark ediyor, çünkü σ'yı birkaç büyük aykırı değer belirliyor ve
3.600 deneme onları istikrarlı örneklemeye yetmiyor.

Bunun pratik sonucu: **tünel satırının menzil hatası ±%15 belirsizlikle
okunmalı.** Şehir içi ve kırsal satırlar için böyle bir uyarı gerekmiyor.

## Robinson'ın verisi 406 kHz'e oturuyor

Robinson'ın ölçtüğü saçılma (2,94 m) ile 406 kHz simülasyonu (2,68 m)
neredeyse aynı. 1,6 MHz simülasyonu ise 0,68 m veriyor, yani dört kat daha
iyi.

İki okuma mümkün ve veriler ikisini ayıramıyor:

1. **Robinson dar bantta ölçtü.** Blog yazısı kullandığı menzil bant
   genişliğini vermiyor. Eğer 406 kHz civarındaysa, ölçtüğü şey fiziğin o
   bant genişliğinde izin verdiği sınıra zaten yakın ve ortada uygulama
   kaybı yok.
2. **Uygulama kaybı var.** Robinson 1,6 MHz'de ölçtüyse, gerçek donanım
   fiziğin izin verdiğinden 4,3 kat kötü demektir; aradaki fark anten, saat
   ve yonganın menzil bloğundan gelir.

Hangisi doğru olursa olsun sonuç aynı yere çıkıyor: **menzil bant
genişliği, raporun belirtmediği ama her şeyi belirleyen parametre.**

## Bant genişliği: en geniş en iyi değil

Önceki sürümde "mümkün olan en geniş bant seçilsin" yazmıştım. Bu yanlıştı.
Ölçünce optimum ortada çıkıyor.

Link bütçesi tarafı doğru. Yoğunluk sınırı yasal gücü bant genişliğiyle
birlikte artırdığı için geniş bant menzilden hiçbir şey götürmüyor
([regulatory.py](../yerkon/regulatory.py)). Temiz kanalda da bant
genişliğini iki katına çıkarmak menzil hatasını gerçekten yarıya indiriyor:

| Bant | LOS σ | NLOS σ | NLOS'ta hataların %10 m üstü |
|---|---|---|---|
| 203 kHz | 4,59 m | 4,45 m | %5 |
| 406 kHz | 2,46 m | 2,32 m | %0 |
| 812 kHz | 1,21 m | 7,21 m | %5 |
| 1625 kHz | 0,59 m | 18,02 m | %28 |

LOS sütunu beklendiği gibi, her katlamada yarıya iniyor. NLOS sütunu tersine
dönüyor, ve sebebi bir hata değil, fizik.

Geniş bant çok yolluluğu ayırıyor. Dar bantta yansımalar tek bir geniş
korelasyon tepesinde birleşiyor, tepe noktası ağırlıklı bir ortalama oluyor,
yani hata sapmalı ama sınırlı kalıyor. Geniş bantta yollar ayrı ayrı tepeler
olarak çözülüyor ve tepe dedektörü en güçlüsünü seçiyor. Doğrudan yolun
zayıfladığı bir kanalda en güçlüsü bir yansıma oluyor, ve hata artık bir
ortalama değil, o yansımanın gerçek fazla gecikmesi. Dağılım bunu
gösteriyor: 1625 kHz'de medyan hata 0,00 m ve hataların yarısı 1 m'nin
altında, ama %28'i 10 m'yi aşıyor. Dağılım iki modlu.

## Ön kenar kestirimi bu parçada kullanılamıyor

Bunun bilinen çözümü ön kenar kestirimi, yani tepeden geriye doğru arayıp
ilk varışı bulmak. DW serisi parçaların yaptığı bu. SX1280 için denedim ve
çalışmıyor:

| Yapılandırma | Sabit ofset | Kalibrasyon sonrası σ |
|---|---|---|
| 1625 kHz, tepe | +0,00 m | 18,02 m |
| 1625 kHz, ön kenar | −114 m | 29,60 m |
| 812 kHz, ön kenar | −256 m | 57,10 m |

Sebep ölçülebilir bir büyüklük. Geriye arama, korelasyon ana lobunun
yaklaşık yarısı kadar erken tetikleniyor, ve ana lob genişliği 1/B:

- UWB, 499,2 MHz, yarım lob yaklaşık 0,3 m, önemsiz
- SX1280, 1,625 MHz, yarım lob yaklaşık 90 m

Ölçülen ofset bu büyüklükte. Sabit kısmı kalibrasyonla gider ama geriye
kalan saçılma tepe dedektörünkinden kötü, çünkü geri arama mesafesi SNR ve
kanalla değişiyor. UWB'nin çok yolluluk bağışıklığı bant genişliğinden
değil, bant genişliğinin ön kenar kestirimini mümkün kılmasından geliyor.
SX1280 o eşiğin çok altında kalıyor.

## O zaman hangi bant

Kararı menzil hatası değil konum hatası versin. Senaryoların kendisiyle
ölçüldüğünde, HPE P50 olarak:

| Bant | Şehir içi (%35 engelli) | Kırsal (%15 engelli) |
|---|---|---|
| 203 kHz | 2,82 m | 21,46 m |
| 406 kHz | **1,64 m** | 13,98 m |
| 812 kHz | 2,35 m | **8,43 m** |
| 1625 kHz | 5,01 m | 15,70 m |

İkisi de U biçimli, ve optimum ortam açıldıkça genişliyor. Şehir içinde
406 kHz, kırsalda 812 kHz. Tablo bu iki değerle üretiliyor.

Bunun rapor açısından anlamı iyi. 406 kHz zaten Semtech'in ranging modunun
ve Robinson'ın ölçümlerinin kullandığı ayar, yani şehir içi için raporun
örtük tercihi doğru. Değiştirilmesi gereken tek şey kırsal, ve orada da bir
katlama.

Bu sonuç iki varsayıma dayanıyor: engellenen link oranları (%35 ve %15) ve
NLOS kanalının sertliği. İkisi de bu projenin seçimi. Optimum bant genişliği
bu sayılara bağlı, o yüzden saha ölçümü geldiğinde bu tablo yeniden
çalıştırılmalı.

## Tünel: rapor hedefi tutmuyor

Rapor DWM3000 için ±10 cm sınıfı doğruluk öngörüyor. Simülasyon açık görüş
hattında 0,15 m veriyor, yani hedef temiz koşullarda kabaca doğru. Ama
**tünel kanalında 0,45 m** çıkıyor, hedefin 4,5 katı.

Fark radyodan değil ortamdan geliyor: tünel kesiti sinyali duvarlardan
yansıtarak taşıyor, geciken bileşenler doğrudan yolla karışıyor ve ön kenar
kestirimi bozuluyor. UWB'nin 500 MHz bandı bunların çoğunu ayırabiliyor,
hepsini değil.

Tünel satırı artık bu modelden üretiliyor (`WAVEFORM_SIMULATION` kanıt
sınıfı), raporun hedefinden değil.

## Geri alınan bir bulgu

Daha önce "tünelde sensör füzyonu bir iyileştirme değil, çalışma şartı"
diye raporlamıştım: odometri ve pusula kapatıldığında yatay P95'in 0,56
m'den 295 m'ye çıktığını ölçmüştüm.

**Bu bir artefaktmış.** İki sebebi vardı:

1. Menzil hata modeli raporun hedefine göre σ = 0,096 m alınmıştı. Aykırı
   değer kapısı bu σ'ya göre ölçekleniyor, yani dört σ 0,38 m ediyor. Üstüne
   eklenen 0,30 m'lik NLOS sapması kapının hemen dibinde kalıyor, ölçümler
   reddediliyor ve filtre kör kalıyordu.
2. MATLAB modeline geçince NLOS iki kez sayılıyordu: dalga formu
   simülasyonu kanalı zaten içeriyor, senaryo bir kez daha ekliyordu.

İkisi de düzeltildi. Gerçekçi menzil hatasıyla (σ = 0,36 m) tünelde radyo
tek başına ıraksamıyor:

| Yapılandırma | HPE P50/P95 | VPE P50/P95 |
|---|---|---|
| Tam (menzil, odometri, pusula, harita) | 0,43 / 1,45 m | 0,25 / 0,69 m |
| Radyo tek başına (filtreli) | 0,55 / 2,55 m | 1,45 / 6,70 m |

Yardımcı sensörler hâlâ işe yarıyor. Esas katkıları dikeyde: VPE P95 6,70
m'den 0,69 m'ye iniyor, yani onda birine. Yatayda kazanç %43.

## Bu simülasyonun kapsamadıkları

- **Anten ve RF ön uç.** Anten faz merkezi kayması ve grup gecikmesi gerçek
  sistemde sabit ofsete katkı verir; burada yok.
- **Yonga üreticisinin kestirici algoritması.** Ne Qorvo'nun LDE'si ne
  Semtech'in menzil bloğu; ikisi de kapalı. Buradaki kestirici bir referans
  uygulaması.
- **Kanal parametreleri.** IEEE 802.15.4a modellerinin biçimini izliyor ama
  hiçbirini birebir üretmiyor; bu projenin sayıları.
- **Saat kararlılığı ve sıcaklık.**

Bu yüzden sonuçlar **fiziğin izin verdiği alt sınır** olarak okunmalı.
Gerçek donanım bundan iyi olamaz, kötü olabilir. Robinson'ın verisiyle
karşılaştırma da tam olarak bunu gösteriyor.
