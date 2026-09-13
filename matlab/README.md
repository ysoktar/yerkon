# MATLAB ölçümleri

`src/yerkon/defaults.toml` içindeki iki figür tahmin edilmek yerine
ölçülebilir. Bunlardan biri burada.

## Çalıştırmak

MATLAB'ı aç, bu klasöre `cd` yap ve:

```matlab
yerkon_clock_residual
```

`out/clock_residual.csv` dosyasını yazar. Onu geri getir ve:

```powershell
yerkon calibrate matlab\out\clock_residual.csv
```

bu komut, yerine geçtiği figürün üzerine yapıştırılacak `defaults.toml`
girdisini, taşıdığı çarpanla birlikte yazdırır.

Yalnızca temel MATLAB. Araç kutusu yok, kurulacak bir şey yok.

## `yerkon_clock_residual.m` neyi ölçer

`clock.crystal.residual_ppm`. Bu betik çalıştırılmadan önce 0,5 varsayımıydı
ve modeldeki en az desteklenen sayıydı; şimdi `defaults.toml` içinde bir
MEASUREMENT olarak 0,0793 duruyor (ADR-0018). SX1280 üzerinde tek yönlü iki
yollu menzil ölçümünün hiç çalışıp çalışmadığına o karar verir: bu düzende artık saat kayması on altı
milisaniyelik bir yanıt gecikmesiyle çarpılır, yani 0,5 ppm 1,20 m eder
ve milyonda on parça, düzeltilmediğinde, 24,1 m eder.

Yöntem, gerçek bir alıcının kullandığı yöntemdir. Yukarı cıvıltıyı
cıvıltısızlaştırmak `offset − mu*tau` konumunda bir vuru verir; aşağı
cıvıltıyı cıvıltısızlaştırmak `offset + mu*tau` verir. Bunların
**toplamı**, zamanlaması sönmüş hâlde frekans kaymasının iki katıdır.
Tepe alınmadan önce izgeler önsöz boyunca biriktirilir, çünkü göz
kestirimleri döngüseldir ve onları aritmetik olarak ortalamak yanlıştır;
sonra bir parabolik aradeğerleme 1587 Hz'lik gözün altına iner — ki o göz
tek başına 0,65 ppm'dir ve olmasa cevabı boğardı.

Sinyal–gürültü oranını **ilinti sonrasında** +5'ten +40 dB'ye tarar,
çünkü link bütçesi orada yaşar: SX1280'in −20 dB'lik bant içi eşiğindeki
bir bağlantı, 30,1 dB'lik yayma kazancından sonra +10 dB'de oturur
(ADR-0017).

Dışarıda bıraktıkları: evre gürültüsü, çok yolluluk ve alışveriş
sırasındaki sürüklenme. Cevabı bir taban olarak oku, figürün kendisi
olarak değil.

## Burada olmayan ve nedeni

Diğer figür `radio.sx1280.implementation_floor_m`; Stuart Robinson'ın
parça üzerinde ölçtüğü 2,94 m. Dalga biçimi benzetilerek ölçülemez.

1625 kHz'de bir yonga 615 ns eder; bu da 184 m uçuş demektir. Bir ilinti
tepesini aradeğerlemek bunun belki onda birine iner, yani bir cıvıltı
benzetimi parçanın yaklaşık 18 m'ye kadar menzil ölçtüğünü söyler. Parça
ölçülebilir biçimde 2,94 m'ye kadar menzil ölçer. Demek ki zamanlaması
simge ilintisinden hiç gelmiyor: SX1280'in içinde bir yongadan çok daha
ince çalışan ve Semtech'in belgelemediği bir düzenekten geliyor.

18 m üreten bir betik, zaten anlaşılmış bir sebeple bir ölçümle
çelişirdi; bu da betiğin hiç olmamasından kötüdür. O figürün bir
benzetime değil, tezgâh üzerinde parçaya ihtiyacı var.
