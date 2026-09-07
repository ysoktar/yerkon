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

## Çalıştırma sırası

### 1. Ortam kontrolü

```matlab
cd matlab
yerkon_env_check
```

Çıktının tamamını gönder. Hangi toolbox'ların olduğunu bilmek, elle
yazdığım kanal modelini MathWorks'ün kendi modelleriyle değiştirip
değiştiremeyeceğimizi belirler.

### 2. Kısa deneme

```matlab
yerkon_ranging_sim('Trials', 20)
```

Birkaç dakika sürer. Amaç script'in senin sürümünde hatasız çalıştığını
görmek. Ekran çıktısını gönder.

### 3. Tam koşu

```matlab
yerkon_ranging_sim('Trials', 300)
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

## Bilinen sınırlar

- **Kanal parametreleri bu projenin.** IEEE 802.15.4a modellerinin biçimini
  izliyor ama hiçbirini birebir üretmiyor. Communications Toolbox varsa
  standart modelle değiştirebiliriz; ortam kontrolü çıktısı bunu
  söyleyecek.
- **Kestirici referans uygulaması.** Ne Qorvo'nun LDE algoritması ne de
  Semtech'in ranging bloğu; ikisi de kapalı.
- **Anten ve RF ön uç modellenmedi.** Anten faz merkezi kayması ve grup
  gecikmesi gerçek sistemde sabit ofsete katkı verir.

## Algoritma doğrulaması

MATLAB burada çalıştırılamadığı için algoritma Python'a port edilip test
edildi ve üç hata bu sayede yakalandı: korelasyon referans gecikmesi
yanlıştı, dar bant vakalarında yayılım gecikmesi korelasyon tepesinden
kısa olduğu için ölçüm dejenere oluyordu, ve tek bir kestirici iki radyo
için de kullanılıyordu. Düzeltilmiş hali burada. Yine de MATLAB
sözdiziminin senin sürümünde çalıştığı doğrulanmadı; 2. adımın amacı bu.
