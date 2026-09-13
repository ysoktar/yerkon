# 0008. Saha verisi bir kez önbelleğe getirilir, sonra çevrimdışı okunur

## Durum
Kabul edildi.

## Bağlam
Projenin gerçek zemine ve gerçek binalara ihtiyacı var; üçü de farklı
davranan üç kaynaktan. GeoTIFF birinin indirdiği bir dosyadır. Bir yükseklik
servisi ağ üzerinden koordinat sorgularını cevaplar. OpenStreetMap ise kendi
hız sınırları olan başka bir ağ servisi üzerinden öznitelik sorgularını
cevaplar.

Bunlardan herhangi birini bir benzetim koşumunun içinden çağırmak, sonuçları
uzak bir servisin ayakta olmasına, hız sınırlayıcısına ve o gün ne
döndürdüğüne bağımlı kılardı. Bir Monte Carlo koşumu on binlerce zemin
sorgusu yapar; bunu hiçbir kamu servisi hoş görmez ve hiçbir denetçi
yeniden üretemez.

Ayrıca bu geliştirme ortamı üçünü de engelliyor, dolayısıyla koşum anında
onları çağıran hiçbir şey burada test edilemez.

## Karar
Getirmek ve okumak farklı zamanlarda yapılan farklı işlemlerdir.

Ağa dokunan tek şey `yerkon fetch`'tir. Bir sınır kutusu için yüksekliği ve
öznitelikleri çeker ve bir önbellek klasörüne düz dosyalar olarak yazar.
Birden çok kaynağa erişilebildiği yerde onları birlikte kullanır: bir
rasterden ya da bir servisten yükseklik, OpenStreetMap'ten öznitelikler,
tek bir sahada birleştirilmiş.

Geri kalan her şey önbelleği okur ve hiç soket açmaz. Dolu bir önbelleğe
karşı bir koşum belirlenimli, çevrimdışı ve aynı önbelleğe sahip herkes
tarafından yeniden üretilebilirdir.

Bir önbellek, her parçanın nereden, ne zaman ve hangi çözünürlükte geldiğini
kaydeden bir manifest taşır; böylece tablodaki bir sayı, bir veri sayfası
değerinin izlenebildiği gibi bir kaynağa kadar izlenebilir.

## Sonuçlar
Benzetim, bir servisin ayakta olmasına sessizce bağımlı olamaz.

Saha verisi işlenebilen, paylaşılabilen ve denetlenebilen bir eser hâline
gelir; bir menzil değerini yalnızca ifade edilmiş değil denetlenebilir
kılan da budur.

Bedeli bir adımdır: yeni bir alan için ilk koşumdan önce birinin getirmeyi
çalıştırması gerekir. Yapay arazi getirme gerektirmez, dolayısıyla
varsayılan yol tek bir komut olarak kalır.

Getirme, düşmek yerine kabiliyet kaybetmek zorundadır. Yüksekliği olan ve
binası olmayan bir saha elde tutmaya değer; manifest neyin eksik olduğunu
kaydeder, böylece model olmayan binaları sessizce açık arazi saymaz.
