# 0019. Ortalamayla kaybolmayan üç hata

## Durum
Kabul edildi.

## Bağlam
Modeldeki her hata gürültüydü. Bir menzil, gerçek mesafe artı bir normal
dağılımdan çekiliş olarak dönüyordu ve yeterince böylesi verilen bir süzgeç
gerçeğe yakınsar. Gerçek konumlandırma sistemleri böyle davranmaz ve sebebi,
en kötü hatalarının gürültü olmamasıdır.

## Karar
Üç ekleme; hepsi gürültü değil, yanlılık ya da kesinti.

**Fazladan yol uzunluğu.** Yolda bir şey durduğunda sinyal onun üzerinden
gider ve bir menzil ölçümü o daha uzun yolu zamanlar. Görüş hattının `h`
metre üzerindeki bir bıçak sırtı `h²/2 · (1/d₁ + 1/d₂)` ekler; uzun bir
bağlantıda yumuşak bir yükselti için santimetreler, kısa bir bağlantıda
enine bir sırt için on metre. Link bütçesinin zaten bildiği açıklıktan
hesaplanır ve her zaman pozitiftir.

**Direk etüt hatası.** Kestiriciye her direğin ölçülmüş konumu verilir ve
onu kesin sayar; dolayısıyla etütte yanlış olan ne varsa o direğin katkıda
bulunduğu her sabitlemeye girer. Bir koşumun başında direk başına bir kez
çekilir ve tutulur, çünkü bir etüt hatası bir ölçümün değil bir kurulumun
özelliğidir.

**Paket kaybı.** Link bütçesinin modellemediği her şey: paylaşımlı bandın
geri kalanından gelen girişim, bu çalışmanın benzetmediği trafikle
çakışmalar, iki ışınlı ortalamanın düzlediği sönümlemeler. Böyle kaybolan
bir alışveriş hiçbir şey üretmez — tam olarak hiç kapanmamış biri gibi. 2,4
GHz kablosuz ağlarla aynı banttır; şehir değerinin açık yoldakinin üç katı
ve tünelinkinin sıfır olmasının sebebi budur.

Hiçbiri gözlemin taşıdığı varyansı değiştirmez. Bir alıcı kendisine yalan
söylendiğini bilmez ve bir yanlılığı örtmek için şişirilmiş bir varyans,
bilen bir alıcıyı modellerdi.

## Sonuçlar
Tünel satırı yalnızca on beş santimetrelik bir etüt hatasıyla medyanda 0,24
m'den 1,76 m'ye gitti. Metre altı değeri kusursuz bilinen direklerin
üzerinde duruyormuş ve düşeyi gözlenemez bırakan geometri bir etüt hatasını
da yaklaşık onla büyütüyor.

O büyütme doğrusal ve doyuma ulaşmıyor: 0,05 m etüt hatası 0,68 m, 0,15 m
1,76 m, 0,30 m 3,14 m veriyor. **Direkleri ölçtüğünden daha iyi
konumlanamazsın** ve bir koridorda on katı kadar bile yaklaşamazsın.

Yol satırları zar zor oynadı ve bu, aynı bulgunun diğer tarafı. Yayılı bir
telsiz yaklaşık üç metreye ölçer ve onda bir metrelik etüt hatası onun
altında kaybolur. Taban her yerleşimde vardır ve yalnızca diğer her şeyin
ondan iyi olduğu yerde bağlar.

Dolayısıyla bir etüt şartnamesi donanım şartnamesinin yanına aittir; ve en
çok da tam olarak ona en az ihtiyacı varmış gibi görünen yerleşimde oraya
aittir.
