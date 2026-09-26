# 0018. Tahmin olmayı bırakan ilk değer

## Durum
Kabul edildi.

## Bağlam
`clock.crystal.residual_ppm` 0,5'ti; 2,4 GHz'de milyonda yarım parça 1,2
kHz'lik bir artık eder ve bu, sinyale zaten kilitlenmek zorunda kalmış bir
alıcı için sıradan göründüğü için seçilmişti. Modeldeki en az desteklenen
sayıydı ve SX1280'de tek yönlü çift yönlü ölçümün hiç çalışıp
çalışmadığına karar veren oydu.

`matlab/yerkon_clock_residual.m` onu ölçtü. Sekiz önsöz sembolü, üç yüz
deneme, 2, 5, 10 ve 20 ppm'lik kristal kaymaları, bağlantıların gerçekten
kapandığı sinyal-gürültü aralığında.

## Karar
Varsayılan 0,0793 ppm; `MEASUREMENT` kaynağıyla ve geldiği koşumla
birlikte. Bu, aralık üzerindeki en kötü karesel ortalama artıktır — en
iyisi değil, ortalaması da değil — çünkü yalnızca bir bağlantının güçlü
ucunda geçerli olan bir değer uzak uçta çöker.

## Sonuçlar
Tahminden altı kat iyi; ve tahmin doğru yönde ihtiyatlıymış.

Ölçüm, tahminin söyleyemediği şeyi de söylüyor: onu neyin sınırladığını.
Artık sinyalle zar zor iyileşiyor: otuz desibel fazlası iki kat satın
alıyor, gürültüyle sınırlı bir kestirici otuz kat alırdı. Hiç gürültü
olmadan koşulduğunda aynı kestirici, yalnızca tepenin FFT gözleri arasında
nereye düştüğüne bağlı olarak 0,0164 ile 0,0643 ppm veriyor — ölçülen
platoyla dört ondalık basamağa kadar uyuşuyor. Taban, kanal değil parabolik
tepe aradeğerleyicisi.

Bu ayrım sayının kendisinden daha önemli. Sistematik bir hata tekrarlanan
alışverişlerde ortalamayla azalmaz, dolayısıyla hiçbir ölçüm miktarı onu
kaldırmaz; ve daha ince bir aradeğerleyici onu düşürürdü. Değer, bir
kristalin değil bir kestiricinin özelliğidir.

Bir tasarım kararı değişti. Varsayılan artıkta darbeli telsizin tek yönlü
saat terimi on santimetrelik bir tabana karşı on santimetreydi, yani çift
yönlü ölçüm üçüncü çerçevesini hak ediyordu. Ölçülmüş hâliyle o terim 1,6
cm ve taban onu yutuyor. Tünel yerleşimi artık tek yönlü: üçte bir az hava
süresi, doksan beşinci yüzdelikte 1,00 yerine 0,72 m ve bir buçuk katı
sabitleme. Bir test eski değeri tutuyor ve eski sonucun ondan hâlâ çıktığını
denetliyor; böylece cevabın model değiştiği için değil bir sayı değiştiği
için değiştiği açık oluyor.

Otuz üç değerin otuz ikisi hâlâ varsayım. Birine kaynak bulmak böyle
görünüyor ve `defaults.toml`'daki sıralama sıradakinin hangisi olduğunu
söylüyor.

Ölçümün kapsamadıkları: faz gürültüsü, çok yolluluk ve alışveriş sırasında
sürüklenme. Bu bir tabandır. Kalan risk, gerçek bir parçanın onun epey
üstünde durmasıdır ve bu bir benzetim değil bir tezgâh gerektirir.
