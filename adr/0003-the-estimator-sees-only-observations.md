# 0003. Kestirici yalnızca gözlemleri görür

## Durum
Kabul edildi. Önceki kod tabanındaki bir kusuru düzeltir.

## Bağlam
Önceki süzgeç, alıcının gerçek yüksekliğini ve gerçek yanal konumunu alıp
üzerine gürültü ekliyor ve bunları "harita" ölçümleri olarak geri
besliyordu. Ayrıca gerçek yörüngeden okunan ivmelerle ilerliyordu. "Yalnız
telsiz" karşılaştırması bile yanal harita desteğini almaya ve o ivmeleri
kullanmaya devam ediyordu.

İkisi de bildirilen hassasiyeti anlamsız kılar: süzgece cevap söylenmişti ve
ayrıştırma, kaldırdığını iddia ettiği desteği kaldırmıyordu.

## Karar
Kestirici tek bir argüman alır: bir Observation dizisi. Bir Observation,
ölçülmüş bir değer, onu üreten şeyin ölçülmüş konumu, bir zaman damgası ve
bir varyans taşır. Gerçek, kestirici paketinin içinden erişilebilir değildir
ve bir test, paketin dünya paketini import etmediğini savlar.

Kullanıldığı yerde harita desteği, alıcının yörüngesinden bağımsız kurulmuş,
kendi hatası olan bir Map nesnesinden gelir. Bir harita yanlış olabilir ve
bir harita eşleme başarısızlığı bir imkânsızlık değil, modellenmiş bir
olaydır.

Ayrıştırmalar gözlemlerin kullanımını değil üretimini kapatır. Odometriyi
kapatmak, hiçbir odometri gözleminin var olmaması demektir.

## Sonuçlar
Düşey hassasiyet artık telsiz geometrisi hakkında bir ifadedir — karşılaştırma
tablosunun sorduğu da budur. Önceki kod tabanının bildirdiğinden kötüdür ve
dürüsttür.
