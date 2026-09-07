# MATLAB tarafı

Bu klasör, projedeki en zayıf kanıtı güçlendirmek için var: **menzil hata
modeli**. Şu an SX1280 için altı yayımlanmış nokta, DWM3000 için ise
raporun kendi hedefine parametrelenmiş bir Gauss dağılımı kullanılıyor.
İkisi de varsayım. Oysa bir alıcının sinyalin varış zamanını ne kadar
hassas ölçebileceğini büyük ölçüde fizik belirler: bant genişliği, çevredeki
çok yolluluk ve sinyal-gürültü oranı.

`yerkon_ranging_sim.m` bunu doğrudan simüle eder. Dalga formunu üretir,
kümelenmiş çok yolluluk kanalından geçirir, gürültü ekler, varış zamanı
kestirimi yapar ve menzil hatasını kaydeder. Çıktı, varsayılan bir dağılım
değil, radyonun parametrelerinden türetilmiş bir hata dağılımıdır.

**Hiçbir toolbox gerektirmez.** Saf MATLAB.

## Önce: bunlar MATLAB komutları, PowerShell komutu değil

Aşağıdaki komutlar **MATLAB'ın kendi komut penceresinde** çalışır.
PowerShell'de yazarsan `is not recognized as the name of a cmdlet` hatası
alırsın.

İki yol var.

**Yol A - MATLAB'ı aç, içinde çalıştır (önerilen).**

MATLAB'ı başlat, sonra MATLAB komut penceresinde:

```matlab
cd 'C:\Users\yavuz\git\yerkon\matlab'
yerkon_env_check
```

**Yol B - PowerShell'den tek satırda.**

MATLAB PATH'te ise, PowerShell'den:

```powershell
matlab -batch "cd('C:\Users\yavuz\git\yerkon\matlab'); yerkon_env_check"
```

PATH'te değilse tam yolla (sürüm numarası seninkine göre değişir):

```powershell
& "C:\Program Files\MATLAB\R2024b\bin\matlab.exe" -batch "cd('C:\Users\yavuz\git\yerkon\matlab'); yerkon_env_check"
```

`-batch` çıktıyı doğrudan PowerShell'e basar, dosyaya yönlendirmek için:

```powershell
matlab -batch "cd('C:\Users\yavuz\git\yerkon\matlab'); yerkon_env_check" | Tee-Object env_check.txt
```

## Çalıştırma sırası

### 1. Ortam kontrolü

MATLAB içinde:

```matlab
yerkon_env_check
```

Çıktının tamamını gönder. Hangi toolbox'ların olduğunu bilmek, elle
yazdığım kanal modelini MathWorks'ün kendi modelleriyle değiştirip
değiştiremeyeceğimizi belirler.

### 2. Kısa deneme

MATLAB içinde:

```matlab
yerkon_ranging_sim('Trials', 20)
```

PowerShell'den:

```powershell
matlab -batch "cd('C:\Users\yavuz\git\yerkon\matlab'); yerkon_ranging_sim('Trials', 20)"
```

Birkaç dakika sürer. Amaç script'in senin sürümünde hatasız çalıştığını
görmek. Ekran çıktısını gönder.

### 3. IMU karakterizasyonu

Sensor Fusion and Tracking Toolbox gerekiyor (sende var).

```matlab
yerkon_imu_char
```

Bir iki dakika sürer. Şunları gönder:

```
matlab/export/yerkon_imu_drift.csv
matlab/export/yerkon_imu_params.csv
```

Bu, füzyon filtresindeki en zayıf varsayımlardan birini düzeltiyor. Şu an
IMU ivme gürültüsü ve sapması benim seçtiğim sayılar (0,08 ve 0,03 m/s²) ve
menzil ölçümü gelmediği anlarda kestirimin ne kadar sürükleneceğini bunlar
belirliyor — tünelde sonucun tamamı bu. `imuSensor` gerçek bir MEMS
biriminin stokastik terimlerini taşıyor, sapma kararsızlığını benim
modelimdeki sabit ofset yerine rastgele yürüyüş olarak veriyor. Çıktı, aynen
filtrenin ihtiyaç duyduğu büyüklük: **kesinti süresine göre serbest ataletsel
sürüklenme.**

### 4. Tam koşu

MATLAB içinde:

```matlab
yerkon_ranging_sim('Trials', 300)
```

PowerShell'den:

```powershell
matlab -batch "cd('C:\Users\yavuz\git\yerkon\matlab'); yerkon_ranging_sim('Trials', 300)"
```

Uzun sürebilir (yarım saat mertebesinde olabilir). Bitince şu iki dosyayı
gönder:

```
matlab/export/yerkon_ranging_errors.csv
matlab/export/yerkon_ranging_summary.csv
```

Tek bir vakayı denemek istersen:

```matlab
yerkon_ranging_sim('Trials', 100, 'Cases', {'uwb_tunnel'})
```

## Simüle edilen vakalar

| Vaka | Radyo | Bant genişliği | Koşul | Kestirici |
|---|---|---|---|---|
| `uwb_los` | DWM3000 | 499,2 MHz | Görüş hattı | Ön kenar |
| `uwb_nlos` | DWM3000 | 499,2 MHz | Engelli | Ön kenar |
| `uwb_tunnel` | DWM3000 | 499,2 MHz | Tünel | Ön kenar |
| `sx1280_1600k_los` | SX1280 | 1,625 MHz | Görüş hattı | Tepe |
| `sx1280_1600k_nlos` | SX1280 | 1,625 MHz | Engelli | Tepe |
| `sx1280_406k_los` | SX1280 | 406 kHz | Görüş hattı | Tepe |
| `sx1280_406k_nlos` | SX1280 | 406 kHz | Engelli | Tepe |

Her vaka dört SNR (10-25 dB) ve üç mesafe için koşar.

Kestirici radyoya göre değişiyor, çünkü iki parça gerçekten farklı çalışır.
UWB'nin 500 MHz bandında yollar ayrışabilir, bu yüzden **ön kenar** araması
yapılır (DW serisi yongaların yaptığı da budur) ve yansımaya kilitlenmek
önlenir. SX1280'in 1,6 MHz bandında korelasyon tepesi yüzlerce metre
geniştir; yollar zaten ayrışmaz, aranacak daha erken bir varış yoktur.
Geriye sabit bir ofset kalır — Robinson'un verisindeki 2,83 m'lik sapmanın
kaynağı da budur ve modül başına kalibrasyonun sildiği şey odur.

## Sonuçlar ne olacak

`yerkon/matlab_import.py` bu CSV'leri okuyup hata modeline çeviriyor.
Kanıt sınıfı `WAVEFORM_SIMULATION`: raporun hedefinden türetilmiş bir
Gauss'tan güçlü (bant genişliği bağımlılığı ve LOS/NLOS farkı fizikten
çıkıyor, seçilmiyor), donanım ölçümünden zayıf (kanal parametreleri bu
projenin ve hiçbir anten açılmadı).

## Bu makinede doğrulanan ortam

R2026a, ve şunlar kurulu: Communications, DSP System, Parallel Computing,
Phased Array, Sensor Fusion and Tracking, Signal Processing, Simulink.

Navigation Toolbox ve Statistics and Machine Learning Toolbox yok, ama
gerekmiyor: `imuSensor`, `insfilterNonholonomic` ve `gpsSensor` Sensor
Fusion and Tracking ile geliyor, `prctile` yerine de elle yazılmış bir
yüzdelik fonksiyonu kullanılıyor. **Ek kurulum gerekmiyor.**

## Bilinen sınırlar

- **Kanal parametreleri bu projenin.** IEEE 802.15.4a modellerinin biçimini
  izliyor ama hiçbirini birebir üretmiyor. Communications Toolbox varsa
  standart modelle değiştirebiliriz; ortam kontrolü çıktısı bunu
  söyleyecek.
- **Kestirici referans uygulaması.** Ne Qorvo'nun LDE algoritması ne de
  Semtech'in ranging bloğu; ikisi de kapalı.
- **Anten ve RF ön uç modellenmedi.** Anten faz merkezi kayması ve grup
  gecikmesi gerçek sistemde sabit ofsete katkı verir.

## İlk koşudan çıkan düzeltmeler (2026-09-07)

Senin makinende çalışan ilk sürüm üç hata ortaya çıkardı. Üçü de sonuçlara
bakınca görünür oldu, hepsi düzeltildi.

**1. IMU sonucu yerçekimini ölçüyordu.** 1 saniyede 10,0 m/s hız hatası ve
5,10 m konum sürüklenmesi bildirdi. 10,0 m/s tam olarak *g*, ve 5,10 m de
`½·g·t²`'nin verdiği 4,90 m. `imuSensor` özgül kuvvet döndürür, yani
yerçekimine tepkiyi içerir; ben onu saf kinematik ivmeyle karşılaştırmıştım.
Artık referans, aynı hareketi gören **gürültüsüz bir ikinci `imuSensor`**;
fark alınca yerçekimi de, modelin kullandığı eksen düzeni de kendiliğinden
düşüyor. Düzeltilmiş sürüklenme santimetre mertebesinde olmalı, metre değil.

**2. UWB, dar bant SX1280'den kötü çıkıyordu.** 499,2 MHz'in 406 kHz'den
kötü zamanlama vermesi fiziksel olarak imkânsız: bin kat bant genişliği bin
kat zamanlama çözünürlüğü demek. Sebep, kanal modelinde görüş hattı için
baskın doğrudan yol olmamasıydı; erken bir yansıma şansa doğrudan yolu
geçebiliyor ve ön kenar dedektörü ona kilitleniyordu. Kanala **Rician K
faktörü** eklendi: görüş hattında doğrudan yol deterministik ve baskın
(12 dB), NLOS'ta zayıf (−6 dB), tünelde ortada (0 dB).

**3. SNR neredeyse hiçbir şeyi değiştirmiyordu.** 10 dB ile 25 dB arasında
sonuçlar aynı çıkıyordu, çünkü gürültü gücü tamponun **ortalamasına** göre
ölçekleniyordu ve tampon varış anının iki yanında çoğunlukla boş. İstenen
SNR uygulanmıyordu. Artık sinyal **tepe** gücüne göre referanslanıyor ve
SNR beklendiği gibi çalışıyor: 406 kHz görüş hattında standart sapma
5 dB'de 8,5 m iken 25 dB'de 0,80 m'ye iniyor.

Düzeltmelerden sonra beklenen sıralama (25 dB, görüş hattı, standart sapma):
UWB 499 MHz < SX1280 1,6 MHz < SX1280 406 kHz. Bant genişliği arttıkça hata
düşüyor, olması gerektiği gibi.

## Algoritma doğrulaması

MATLAB burada çalıştırılamadığı için algoritma Python'a port edilip test
edildi. İlk turda üç hata bu sayede yakalandı: korelasyon referans
gecikmesi yanlıştı, dar bant vakalarında yayılım gecikmesi korelasyon
tepesinden kısa olduğu için ölçüm dejenere oluyordu, ve tek bir kestirici
iki radyo için de kullanılıyordu.

Yukarıdaki üç düzeltme de aynı yöntemle, senin gönderdiğin sonuçlara
bakılıp Python portunda doğrulandıktan sonra uygulandı. MATLAB
sözdiziminin çalıştığı ilk koşuda teyit edildi.
