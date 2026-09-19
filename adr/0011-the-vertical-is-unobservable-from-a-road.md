# 0011. Düşey, bir yoldan gözlenemez ve cevap budur

## Durum
Kabul edildi.

## Bağlam
Direkler bir yolun kenarındaki yapılara konur. Katalog bir levha için üç
metreden amaca özel bir direk için yirmi beş metreye uzanır, yani bir
yerleşim yüksekliklerini yirmi iki metrelik bir aralıkta karıştırabilir.
Hizmet ettikleri bağlantılar ise kilometrelerce uzundur.

Dört bin metrelik bir taban çizgisine karşı yirmi iki metre yükseklik bir
yayılım değildir. Her menzil neredeyse tamamen yataydır, dolayısıyla bir
menzil ölçümünün düşey bileşeni ikinci mertebeden bir terimdir ve bir buçuk
metredeki bir alıcıyı direklerin üstündeki ayna görüntüsünden ayıracak
geometri neredeyse hiç yoktur.

Aritmetik bunu iki kez gösterir. Bir en küçük kareler çözümü yerleşmek
yerine direk düzleminin iki yanı arasında salınır ve yerleştiği yerde düşey
varyans yüzlerce metrekareye çıkar.

Direkler tek yükseklikteyken ve yükseklikler üç ile yirmi beş metre arasında
karıştırılmışken dört yüz çözüm üzerinden ölçüldüğünde düşey hata aşağı
yukarı aynı: iki durumda da medyanı yirmi beş metre civarı. Montaj
yüksekliklerini karıştırmak gözlenebilir bir düşey satın almıyor.

## Karar
Belirtildiği gibi yükseklik kısıtı yok. Düşey serbest bir değişken olarak
kalır ve hatası, geometrinin ürettiği büyüklükte bildirilir.

En küçük kareler çözümü sönümlüdür ve bir adım uyumu kötüleştirdiğinde
sönüm yükseltilir. Bu, alıcının nerede olduğu hakkında değil aritmetik
hakkında bir ifadedir: çözümün salınmak yerine düzlemin bir yanına
yerleşmesini sağlar ve düşey hatayı küçültmez.

Gözlenemez bir düşey bir kesinti değildir. Bir sabitleme, *yatay* bir eksen
belirsiz olduğunda — mesela direkler tek sıradayken — reddedilir, çünkü
böyle bir konum hiçbir anlam taşımaz. Büyük düşey hatası olan bir sabitleme
hâlâ bir şey ifade eder ve sabitleme olarak sayılır.

## Sonuçlar
VPE sütunu her yol senaryosunda, birkaç metrelik bir HPE'ye karşı onlarca
metre okuyacaktır. Bu, yol kenarı direklerinden oluşan karasal bir ağ
hakkında doğru bir ifadedir ve gerçek sistemlerin bir barometreye, bir yol
yüzeyi modeline ya da gerçekten yüksek bir yerdeki bir direğe uzanmalarının
sebebidir.

Bunların hiçbiri raporun malzeme listesinde yok, dolayısıyla hiçbiri
modellenmiyor. Sonradan biri eklenirse, bu ADR onun karşısında duran
gerekçedir.

Küçük bir VPE bildirmek, kestiriciye bulması istenen yüksekliği söylemeyi
gerektirirdi. Önceki kod tabanı bu türden bir şey yaptı ve hassasiyet
değerleri hiçbir şey hakkında ifadelerdi.
