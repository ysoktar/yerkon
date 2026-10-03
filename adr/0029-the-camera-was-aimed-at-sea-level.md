# ADR-0029: kamera deniz seviyesine nişanlanmıştı

## Durum

Kabul edildi.

## Bağlam

3B sahne boştu. Yavaş değil, yanlış değil — boş; indirilmiş zemin
üzerinde duran her kipte. Yanındaki panel kusursuz çalışıyordu: kırk
dokuz direk, 3,82 km erişim, arazi tarif edilmiş. Resim hiçbir şey
göstermiyordu.

Her hareket çalışıyordu. Sürüklemek kamerayı döndürüyor, tekerlek
yakınlaştırıyor, tuşlar yürütüyordu ve her biri pikselleri
değiştiriyordu — çünkü başka türlü aydınlatılmış boş bir ekran da bir
değişikliktir. Kameranın *hareket ettiğini* sınamak, onun *bir şeye
nişanlandığını* sınamak değildir ve hatanın tamamı bu farktır.

Çerçeveleme `orbit.target = [corridor / 2, width / 2, 0]` koyuyordu.

Engebe beş kat abartılı çizilir, böylece silik bir dalgalanma değil
engebe olarak okunur. Ankara'nın zemini deniz seviyesinden 700 ile 1900 m
yukarıdadır. Kızılay yaklaşık 1150 m'dedir; bu da görüş uzayında 5750
birim eder — ve kamera 6000 birim uzaktan sıfıra nişanlanmıştı; yani var
olan her şeyin neredeyse bütün görüş uzaklığı kadar altındaki bir
noktaya bakıyordu.

Modellenmiş arazinin ortalaması sıfırdır. Bu, senaryolar gerçek
Ankara'ya taşınana kadar (ADR-0021) durumu tamamen gizledi; sonra her
satırın her varsayılan görünümü boş çıktı.

## Karar

Başlangıç noktasına değil sahneye çerçevele: x ve y'de direklerin ortası,
z'de ise ortalama zemin yüksekliği çarpı düşey abartı. Bunu
`frameEverything` yapar, ilk çerçeveleme onu çağırır ve `F` onu yeniden
çağırır.

## Sonuçlar

Çiziyor.

Ders, sınamaların neyi denetlediğiyle ilgili. Kameranın bir kez
çerçevelendiğini ve her tazelemede çerçevelenmediğini sınayan bir sınama
vardı; yakınlaştırmanın tekerleği izlediğini sınayan bir sınama;
sürüklemenin zemini izlediğini sınayan bir sınama — hepsi geçiyordu,
hepsi mekanizmaya dairdi, hiçbiri sonucun görünür olup olmadığına dair
değildi. Bir ekran görüntüsü bunu ilk koşuda yakalardı; ne kadar okunsa
yakalanmazdı.

Bu yüzden çerçevelemenin artık hesaba katması gereken iki şeyi adıyla
anan bir sınaması var — zemin yüksekliği ve çizildiği abartı — ve onu
bulan alışkanlık, tutulmaya değer olan: sayfayı aç ve bak.
