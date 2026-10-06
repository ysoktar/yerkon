# ADR-0036: hiçbir şey yapmayan bir denetim, denetim değildir

## Durum

Kabul edildi.

## Bağlam

Ölçülmüş bir zemin seçmek, altındaki üç sürgüyü — tepe yüksekliği, tepe
aralığı, yüzey pürüzü — griye çeviriyordu; çünkü `ViewState.terrain` bir
saha adlandırılmışsa onları hiç okumaz.

Onları griye çeviren satır sürgüyü kilitliyordu. Her denetim iki girdidir:
sürgü ve yanındaki tam sayı (ADR-0034, çünkü adımı 500 olan bir sürgüye
4000 verilemez). Sayı kutusu canlı kalıyordu. Yani ölçülmüş bir zemine
kutuya yazarak 700 m rölyef verilebiliyordu; sayı kabul ediliyor, ekranda
görünüyor ve hiçbir şeyi değiştirmiyordu — çünkü zemin ölçülmüştü.

Gri bir sürgünün altında canlı görünen bir kutu, üç durumun en kötüsüdür:
kilidin sebebini gösterir ve sonra kilidi tutmaz.

Aynı üç değerin ikinci bir ölü hâli hiç fark edilmemişti. Bir tünel
tepenin *içinden* geçer: tabanı iki portal arasındaki düz çizgidir ve
`tunnel_ground` bu üçünü saha olsun olmasın hiç okumaz. Tünel satırında
zemini "Modellenmiş"e çevirdiğinde üçü de canlı ve siyah geri geliyordu;
oysa hiçbiri okunmuyordu.

Ve panelin tepesinde ayrı bir sorun vardı. Satır sekmeleri ile TR/EN
seçicisi panelin akışında duruyordu; panel ise kaydırılan kutunun ta
kendisi. Biri beşinci adımdaki yetmiş iki değerin içinde çalışırken
ikisi de ekranın yukarısında kalıyordu: satır değiştirmek ya da dili
değiştirmek için önce başa kadar geri kaydırmak gerekiyordu. Sonuç zaten
alta sabitlenmişti (ADR-0034); üst ucu sabitlemek atlanmıştı.

## Karar

**Ölü olan, iki yarısıyla birlikte kilitlenir ve bütün olarak grileşir.**
Kilit tek bir yerde, durumdan hesaplanır: `lockDeadKnobs`, hangi
denetimin okunmadığını sorar, her ikisini de kapatır, `label.knob`'a
`dead` sınıfını koyar ve sebebini altındaki nota yazar. Durumdan
hesaplandığı için yeniden yüklemede, satır değişiminde ve dil
değişiminde aynı şekilde tutar; en son hangi işleyicinin çalıştığına
bağlı değildir.

**Ölü olmanın iki sebebi ayrı ayrı söylenir.** Ölçülmüş zemin kendi
rölyefini getirir; bir tünel ise tepenin içinden geçer. Tünel satırında
ikisi de doğrudur ve okunmama sebebi tüneldir, o yüzden önce o söylenir.

**Engel kaybı kilitlenmez.** Ölçülmüş zemin bina ve ağaç getirmez —
OpenStreetMap binaları ayrıca indirilmediyse — dolayısıyla o değer
okunmaya devam eder. Kilit, okunmayanın listesi kadardır; bir adım
değil.

**Satırlar ve dil panele sabitlenir.** `#top`, sekmeleri ve arama
satırını taşır ve panelin üstüne yapışır. Kaydırılan bir şeyin onun
arkasına düşmemesi için panelin `scroll-padding-top` değeri başlığın
ölçülen yüksekliğinden gelir; yazılı bir sayıdan değil, çünkü başlık iki
satır metindir ve yüksekliği yazı tipiyle oynar.

## Sonuçlar

Değişmesi bir şey ifade etmeyen her denetim gri ve kilitli; ifade eden
her denetim siyah ve canlı. Tünel satırında üç değer artık zemin
seçiminden bağımsız olarak kilitli, ki bu bu değişiklikten önce hiç
doğru olmamıştı.

Satırlar ve dil, panel altı bin piksel kaydırılmışken bile tıklanabilir.

İki sınama bunları tutuyor: biri her denetimin iki yarısının aynı adı
taşıdığını (`id` ve `id-num`), ki yarım kilitlenen bir denetim doğru
görünür; diğeri sekmelerin ve dil seçicisinin `#top` içinde olduğunu ve
`#top`'un yapışkan olduğunu. İkisi de bozulduğunda düşüyor — denenerek
doğrulandı.

Genelleşen ders, ADR-0027'nin bıraktığı yerin aynısı: bir şeyin *var
olduğunu* denetlemek ucuz, *okunduğunu* denetlemek değil. Sürgü
kilitliydi; kutu vardı, doğruydu ve kilitli değildi. Bunu bulan da bir
sınama değil, sayfayı açıp kutuya bir sayı yazmaktı.
