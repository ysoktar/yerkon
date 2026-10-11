# ADR-0083: paket kaybı, bir SDR kaydından ölçülür

## Durum

Kabul edildi.

## Bağlam

Şehir içi satır, 2,4 GHz bandındaki başka trafik yüzünden mesafe ölçüm
alışverişlerinin %15'inin kaybolduğunu varsayıyor
(`site.urban_packet_loss`); kırsal satır %5 (`ranging.packet_loss`).
İkisi de varsayım. Şehir içi kullanılabilirliği en çok oynatan
sayılardan biri bu.

SDR++ ve SDRangel iki yaygın, ücretsiz SDR programı. Simülasyonun içinde
çalışamazlar: simülasyon Python, onlar birer masaüstü programı ve
yaptıkları işi (radyo sinyalini almak, göstermek, çözmek) simülasyonun
bir karşılığı yok. Yapabildikleri, sahadaki bandı kaydetmek. Kayıt da
tam olarak bu varsayımın yerine konabilecek şey.

## Karar

`yerkon calibrate` artık iki kayıt biçimini okuyor ve MATLAB
ölçümlerinde olduğu gibi `defaults.toml` girdisini yazıyor
(`src/yerkon/spectrum.py`):

- **SDR++**: kaydedicinin temel bant WAV dosyası. İki kanal, I ve Q;
  8, 16 ya da 32 bit tamsayı ya da 32 bit kayan nokta. Merkez frekansı
  dosyada yok, varsayılan dosya adında (`..._2440000000Hz_...`).
- **SDRangel**: dosya çıkışının `.sdriq` dosyası. 32 baytlık başlık
  (örnekleme hızı, merkez frekansı, başlangıç zamanı, örnek boyu, dolgu,
  ilk 28 baytın CRC-32'si), sonra 16 bit ya da (24 bit örnek boyunda)
  32 bit I ve Q.

İki biçim de programların kendi kaynak kodundan okundu (SDR++
`core/src/utils/wav.cpp` ve `misc_modules/recorder`; SDRangel
`sdrbase/dsp/filerecord.{h,cpp}` ve `dsptypes.h`); tahmin edilmedi.
Başlığın sağlama toplamı tutmayan bir `.sdriq` okunmuyor.

**Ne ölçülüyor.** Kayıt 0,5 ms'lik bloklara bölünüyor; her bloğun
yalnızca yayın biriminin kanalı içindeki gücü (SX1280 için 1625 kHz)
alınıyor, böylece yan kanaldaki trafik sayılmıyor. Kanalın sessiz
seviyesi blok güçlerinin onuncu yüzdeliği. Bu seviyenin eşik kadar
(varsayılan 3 dB) üstündeki blok dolu. Bir alışveriş, üst üste geldiği
bloklardan biri doluysa kayboluyor. Sonuç, alışveriş uzunluğundaki
pencerelerin dolu bir bloğa değen payı: rastgele bir anda başlayan bir
alışverişin kaybolma olasılığı. Alışveriş uzunluğu modelin kendi değeri
(SF10, 1625 kHz, tek yönlü TWR: 31,8 ms).

**Neyi bilmiyor.** Gelen sinyalin ne kadar güçlü olduğunu. Payı büyük
bir bağlantı zayıf bir girişimi fark etmez, kapsama kenarındaki bir
bağlantı kırılır. Eşik bunun yerine duruyor; varsayılan 3 dB, kanalda
gürültü kadar güçlü herhangi bir şeyi kayıp sayıyor, yani kapsama
kenarı durumu, kötümser taraf. `--threshold-db` ile değiştirilebilir.

## Kullanım

1. Pilot sahada, yayın biriminin duracağı yerde, en az 2 MHz örnekleme
   hızıyla ve yayın biriminin kanalına ayarlı olarak birkaç dakika
   kaydedin. RTL-SDR bu bandı göremez; HackRF, PlutoSDR, LimeSDR ya da
   benzeri gerekir. SDR++'ta kaydedicinin "baseband" kipi; SDRangel'de
   dosya çıkışı.
2. `yerkon calibrate kayit.wav` ya da `yerkon calibrate kayit.sdriq`.
   Kırsal için `--key ranging.packet_loss`. Kanal kaydın merkezinde
   değilse `--offset-hz`.
3. Yazdırılan girdiyi `defaults.toml`'a yapıştırın; kaynağı ve notu
   ölçümün kendisini anlatıyor.

## Sonuçlar

- Paket kaybı, ölçüldüğü yerde artık bir varsayım olmak zorunda değil.
- Bir SDR kalibre edilmiş bir güç ölçer değil. Bu ölçüm göreli (kanalın
  kendi sessiz seviyesine göre) ve bu yüzden güç kalibrasyonu
  gerektirmiyor; TS EN 300 328 uygunluğu gibi mutlak güç soruları için
  kullanılamaz.
- Testler, bilinen uzunlukta ve aralıkta patlamalar içeren yapay
  kayıtları iki biçimde de yazıp sonucu doğrudan sayımla karşılaştırıyor;
  kanal süzgeci kaldırıldığında yan kanal testi kırılıyor.
