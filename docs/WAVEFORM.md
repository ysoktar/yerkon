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

## Bant genişliği seçiminin sonuca etkisi

Bu bir **karşı-olgusal denemedir, tabloya girmez.** Aynı senaryo, tablonun
kendi ayarlarıyla (füzyonlu, 16 koşu, seed 42), yalnızca menzil hata modeli
değiştirilerek tekrar çalıştırıldı. İlk satır tablodaki satırın kendisidir,
yani karşılaştırmanın referansı tabloyla birebir aynı sayıdır:

| Senaryo | Menzil hata modeli | σ | HPE P50 | HPE P95 |
|---|---|---|---|---|
| Şehir içi | **Robinson (tablodaki satır)** | 3,04 m | **2,44 m** | **4,86 m** |
| Şehir içi | MATLAB 406 kHz | 2,69 m | 2,12 m | 4,31 m |
| Şehir içi | MATLAB 1,6 MHz | 0,71 m | 0,52 m | 1,07 m |
| Kırsal | **Robinson (tablodaki satır)** | 3,01 m | **7,77 m** | **36,84 m** |
| Kırsal | MATLAB 406 kHz | 2,68 m | 6,15 m | 30,92 m |
| Kırsal | MATLAB 1,6 MHz | 0,69 m | 1,67 m | 13,10 m |

1,6 MHz'e geçilseydi şehir içi yatay hata 2,44 m'den 0,52 m'ye, kırsal
7,77 m'den 1,67 m'ye inerdi. **Ek donanım yok, ek düğüm yok, sadece bir
konfigürasyon seçimi.**

Tablo yine de Robinson satırını kullanıyor. Sebebi: 1,6 MHz satırı bir
simülasyonun çıktısı, Robinson satırı ise açılmış bir donanımın ölçümü.
Rapor SX1280'i hangi menzil bandında çalıştıracağını söylemediği sürece,
tabloda duracak olan ölçülmüş sayıdır. Rapor bandı belirtirse tablo o
satıra geçebilir.

Bedeli var: daha geniş bant daha düşük alıcı hassasiyeti, yani daha kısa
menzil demek. Kırsalda bu, düğüm aralığını sıklaştırmayı gerektirebilir. Bu
ödünleşim bu projede ölçülmedi, çünkü menzil-bant genişliği ilişkisi için
elde kalibreli bir link bütçesi yok.

**Rapora öneri:** menzil bant genişliği açıkça belirtilsin ve mümkün olan en
geniş bant seçilsin.

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
   değer kapısı bu σ'ya göre ölçekleniyor, yani 4σ = 0,38 m. Üstüne
   eklenen 0,30 m'lik NLOS sapması kapının hemen dibinde kalıyor, ölçümler
   reddediliyor ve filtre kör kalıyordu.
2. MATLAB modeline geçince NLOS iki kez sayılıyordu: dalga formu
   simülasyonu kanalı zaten içeriyor, senaryo bir kez daha ekliyordu.

İkisi de düzeltildi. Gerçekçi menzil hatasıyla (σ = 0,49 m) tünelde
radyo-tek filtre **ıraksamıyor**:

| Yapılandırma | HPE P50/P95 | VPE P50/P95 |
|---|---|---|
| Tam (menzil+odo+pusula+harita) | 0,63 / 2,19 m | 0,33 / 0,70 m |
| Radyo-tek (filtreli) | 0,70 / 3,21 m | 1,07 / 7,40 m |

Yardımcı sensörler hâlâ işe yarıyor, ama esas katkı dikeyde: VPE P95 7,40
m'den 0,70 m'ye iniyor. Yatayda kazanç %32.

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
