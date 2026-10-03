# ADR-0041: bir fotoğraf veri değildir

## Durum

Kabul edildi.

## Bağlam

Görüntüleyici zemini tek bir zeytin yeşiliyle çiziyordu. Yükseklik
gerçekti, binalar gerçekti, ama bakan kişi Kızılay'a mı yoksa
Kızılcahamam'a mı baktığını ekrandan söyleyemiyordu — iki tepe, iki
renk, aynı renk.

Karşılaştırma noktası olarak `gazebo_terrain_generator` gösterildi. O
aracın diğerlerinden ayrıldığı yer tam da bu: ürettiği `mesh/aerial.png`
bir uydu dokusudur ve araziye giydirilir.

Buradaki soru "bir resim indirilir mi" değil, **bir resmin bu projede ne
olduğu**. Bu depodaki her sayı bir veri sayfasına, yayımlanmış bir
ölçüme ya da yazılı bir varsayıma kadar izlenebilir (ADR-0001). Bir
uydu görüntüsü bunların hiçbiri değil.

## Karar

**Fotoğraf çizilir, okunmaz.** `Site.aerial` benzetimin hiçbir yerinde
okunmaz: link bütçesi bir tarlanın ne renk olduğunu umursamaz, engel
binalardan gelir (ADR-0038), zemin yükseklik ızgarasından. Bu, kodda
açıkça yazılı — çünkü veriye benzeyen bir resim, veri gibi okunmaya
davet eder. Kaybolursa yayımlanan hiçbir sayı değişmez.

**Hazır bir karo adresi yok.** Her sağlayıcının kendi koşulları var ve
çoğu anahtar istiyor; kutuya bir adres koymak, bu projeyi koşturan
kişinin adına başkasının koşullarını kabul etmek olurdu. Adres `yerkon
fetch --imagery` ile ya da sayfadaki kutuyla verilir; verilmezse
fotoğraf inmez ve zemin eskisi gibi düz renk çizilir.

**Eksik bir karo delik, hiç karo gelmemesi hatadır.** Bir kare yüzünden
bütün şehrin görüntüsünü kaybetmek kimsenin istediği şey değil ve gri
bir kare ekranda zaten belli olur. Ama hiçbirinin gelmemesi yanlış
adres, eksik anahtar ya da yanlış ağ demektir; bunu söylemek, hiçliğin
fotoğrafını uzatmaktan iyidir.

**Tel üzerinden resim gider, renk değil.** Ağ düğümü başına üç bayt renk
ve yirmi iki bin düğüm, her kamera sürüklemesinde çeyrek megabayt eder
— tarayıcının bir kez önbelleğe aldığı tek bir PNG'nin bir kez
söylediği şeyi söylemek için. Sahne fotoğrafın *adresini* taşır; sayfa
onu bir kez indirip piksellerini okur.

**Fotoğraf kendi sınırlarını taşır.** Bir getirme kutu ister, tam karo
alır; resim sahanın her kenarından taşar. Kırpmak çözünürlüğü boşuna
atmak, taşmayı yok saymak ise resmi yarım sokak kaydırmak olurdu. Sayfa
gerçek köşeleri öğrenir.

**Karo başına tek renk, dörtgen başına tek renk.** Bu boyayıcı düz
çokgen dolduruyor; dört bin dörtgenin her birine ayrı dönüşümle resim
dilimi çizmek başka bir boyayıcı demek. Bedeli göründüğünden az: ağ
kameranın baktığı yere göre inceliyor (`ground`, scene.py), dolayısıyla
bir sokağın üstündeki dörtgenler metrelerce ve fotoğraf, bakılan
mesafenin çözünürlüğünde geliyor.

**Resmin dışı gri değil, yok.** `Aerial.sample` kenara yapışır, çünkü
sınırı sıyıran bir link yoluna en yakın bilinen zemini vermek doğrudur.
Boyayıcının örnekleyicisi ise resmin dışında `null` döner ve zemin
eskisi gibi zeytin çizilir: fotoğrafı olmayan zemin, fotoğrafı olmayan
zemin gibi görünmeli; yapışmak kenar satırını kırlara yayardı.

## Sonuçlar

Kızılay'ın zemini, 3328 × 3584 pikselde, piksel başına **0,92 m**
(yakınlık 17). Resim sahanın dışına batıda 42 m, güneyde 196 m taşıyor;
sayfa bu köşeleri olduğu gibi alıyor.

Sayfanın örnekleyicisi ile motorun `Site.colours_at`'ı, saha metreleri
içinde rastgele yirmi noktada **yirmi yirmi** aynı pikseli veriyor —
yani resim ters değil, taşma kadar kaymış değil, satırı sütunu
karışmamış. Bunu tarayıcıda gerçek PNG üzerinden ölçtüm; örnekleyici bu
yüzden `draw.js` içinde ve dışarı açık.

Sınamalar gerçek bir sokete karşı koşuyor. Bu kum havuzundan bütün karo
sunucuları kapalı (ADR-0021), bu yüzden kaydedilmiş bir yük uydurup
yolun yarısını sınamak yerine `127.0.0.1` üzerinde bir karo sunucusu
ayağa kalkıyor: adres şablonu, iş parçacıkları, disk önbelleği, dikiş ve
bildirdiği sınırlar gerçekten koşuyor. Eksik olan yalnızca internet, ve
içinde hata olan kısım internet değil.

**Bir sızıntı temizlendi.** `site/places/probe`, ADR-0039 ile birlikte
yanlışlıkla işlenmiş bir sınama kalıntısıydı: yükseklik kaynağı `fake`,
getirilme zamanı `now`. Zemin listesinde dört gerçek getirmenin yanında
gerçekmiş gibi duruyordu; silindi.

## Sonraki adımlar

Yol kenarı donanımı, presetler, sinyal renklendirmesi ve alıcı
güzergâhları — ADR-0040'ın bıraktığı yerden.
