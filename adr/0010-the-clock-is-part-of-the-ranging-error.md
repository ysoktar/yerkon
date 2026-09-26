# 0010. Saat, ölçüm hatasının parçasıdır ve ne kadarına alışveriş karar verir

## Durum
Kabul edildi.

## Bağlam
Link bütçesi, bir dalga formunun bir varışı ne kadar hassas
zamanlayabileceğine bir sınır verir. Zamanlamayı taşıyan alışveriş hakkında
hiçbir şey söylemez ve bu raporun adını verdiği donanımda hatanın çoğunun
geldiği yer alışveriştir.

SF10'da bir çerçeve yaklaşık on altı milisaniye sürer. Tek yönlü çift yönlü
ölçümde yakın telsiz gidiş dönüşü kendi saatiyle ölçer ve uzak telsizin
saatiyle ölçülmüş bir yanıt gecikmesini çıkarır; dolayısıyla iki saat
arasındaki fark o bütün gecikmeyi çarpar. Milyonda on parçada bu seksen
nanosaniye, yani yirmi dört metre eder — parça üzerinde gerçekten ölçülmüş
tek ölçüm hatasının sekiz katı.

Yayımlanmış ölçümlerin yirmi dört metrelik bir hata göstermemesi başlı
başına bir kanıttır. Her eşevreli alıcının zaten çözmek için yaptığı
düzeltmenin ölçüm işini de yaptığını söyler.

## Karar
Bir menzil ölçümünün hatası, dalga formu sınırı ile saat teriminin kareli
toplamıdır; altına da parçanın ölçülmüş tabanı uygulanır. Saat terimi üç
şeyden gelir: alışveriş şeması, çerçevenin ima ettiği yanıt gecikmesi ve
saat kaymasının alıcının frekans kayması kestiriminden ne kadarının sağ
kaldığı.

Tek yönlü ölçüm yanıt gecikmesini çarpar. Çift yönlü ölçüm bunu birinci
mertebeden götürür ve onun yerine uçuş süresini çarpar; o da yüzlerce kat
daha kısadır ama mesafeyle büyür.

Hava süresi telsizin kendi sembolleriyle, işlem kazancının alındığı önsözün
üzerinden sayılır; böylece bir telsize aynı anda ucuz bir çerçeve ve cömert
bir kazanç verilemez.

## Sonuçlar
Hangi şemanın kullanılacağı, kalan kayma varsayımken telsiz başına bir
cevaptı; ölçüldüğünde tek bir cevap oldu.

Milyonda yarım parça varsayıldığında SX1280'in tek yönlü saat terimi,
metrelerle ölçülen bir dalga formu sınırına karşı bir metreydi, yani tek
yönlü orada hiçbir şeye mal olmuyordu; darbeli telsizinki ise on
santimetrelik bir tabana karşı on santimetreydi, yani çift yönlü fazladan
çerçevesini hak ediyordu.

Ölçülmüş hâliyle kalan 0,0793 ppm (ADR-0018). Darbeli telsizin tek yönlü
terimi 1,6 cm'ye düşüyor, tabanı onu bütün yutuyor ve fazladan çerçeve iki
telsizde de hiçbir şey satın almıyor. İkisi de artık tek yönlü. Tünel
satırında bu, üçte bir az hava süresi, doksan beşinci yüzdelikte 1,00
yerine 0,72 m ve bir buçuk katı sabitleme demek.

Yavaş telsizde bir frekans kayması kestirimi isteğe bağlı değildir. Modele
onsuz ne olduğu sorulabilir ve cevap, ölçümün çalışmayı bırakmasıdır.

Hava süresi artık çalışmanın harcayabileceği bir niceliktir. SX1280'de altı
direğe karşı bir tur çeyrek saniye sürer; bu sürede saatte yüz kilometre
giden bir araç yedi metreye yakın yol alır — yanındaki ölçüm hatasının iki
katından fazla. Dolayısıyla kestirici bir turu eşzamanlı sayamaz ve buna
sonradan keşfedilmek yerine burada karar verilir.

Milyonda yarım parçalık kalan kayma modeldeki en az desteklenen sayıdır ve
ölçülmeye değer ilk şeydir.
