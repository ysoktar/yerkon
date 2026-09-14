# ADR-0037: çalışma, ölçümün bittiği yerde biter

## Durum

Kabul edildi.

## Bağlam

`Site.height_at`, ızgarasının dışında hata yükseltmek yerine kenara
kırpar. Sınıra değip geçen bir link yolu için bu doğrudur: sert bir
başarısızlık, en yakın bilinen zeminden daha yararsız olurdu.

Bir yerleşim için yanlıştır. Kenarın ötesinde kırpma, sınır satırını bir
düzleme doğru uzatır ve düzlem, bu modelin çizebileceği en elverişli
zemindir: her yansıma iki-ışın teriminin varsaydığı ayna açısıyla gelir
ve hiçbir şey hiçbir şeyi engelleyemez (ADR-0021). Orada duran bir direk,
kimsenin ölçmediği bir sayının üzerinde duruyordur.

Ve tam olarak bu oluyordu. Hazır gelen satırlar, altlarındaki ızgaradan
büyük:

| satır | istenen | ölçülen | dışarıdaki direkler |
|---|---|---|---|
| Şehir içi | 3000 × 3000 m | 2970 × 2940 m | 46'nın 10'u |
| Kırsal | 20000 × 20000 m | 22800 × 19860 m | 33'ün 5'i |

Kırsal satırdaki beş direk, y = 20000'de, ölçülen zeminin 140 m
ötesindeydi — ve turun uzak kolunu taşıyan sıra onlardı.

Fark, indirmenin kendi yuvarlamasından geliyor: kizilay 3005 m'lik bir
kutu için istendi ve 30 m aralıkla 0..2970'i kapsayan bir ızgara geldi;
polatli 20015 m için istendi ve 60 m aralıkla 0..19860 geldi. Kutu değil,
elde olan ızgara belirleyicidir.

Görüntüleyicide aynı delik daha büyüktü. 3 km'lik bir kutu indirip
sahanın boyunu 20 km'ye çekmek, direkleri ölçülen zeminin on yedi
kilometre ötesine, bir düzleme koyuyordu ve hiçbir şey itiraz etmiyordu.

## Karar

**Bir saha, kendisi için indirilen zeminden büyük olamaz.** Kural tek bir
işlevde: `fits_on(site, length_m, width_m)`, istenen boyu ve eni ölçülen
ızgaranın içine getirir. Modellenmiş zeminin kenarı yoktur, dokunulmaz.
Sıfır en bir alan değil bir çizgidir, sıfır kalır.

Kuralı üç yer okur: raporun şehir içi ve kırsal satırları, ve
görüntüleyicinin `ViewState.within_site()`'ı.

**Satırlar kare değil dikdörtgen olur.** Ölçülen zemin dikdörtgendir.
Kareye zorlamak kırsal satırda x yönünde ölçülmüş 2800 m'yi çöpe atıyor
ve üç direk daha kaybettiriyordu. Her yön kendi ölçüsüyle sınırlanır.

**Zemini seçmek de onay panelinden geçer.** Daha küçük bir yer seçmek
boyu, eni ve direk dizilerini içeri çeker; bu, birinin görmesi gereken
bir değişikliktir (ADR-0009). Aynı kural en sürgüsü için de geçerli oldu;
eskiden o sürgü panelsiz uygulanıyordu.

**Sürgüler ölçülen zeminin ötesini sunmaz.** Motor zaten reddediyor ve
panel söylüyor, ama 3 km'lik bir indirme üzerinde kırk kilometreye kadar
giden bir sürgü, reddi göstermek yerine davet eder.

**Tünel bağlanmaz.** Bir tünel tepenin içinden geçer, üzerinden değil:
tabanı iki portal arasındaki çizgidir ve `Sloping` y'yi hiç okumaz.
Uzunluğu zaten portalların okunduğu yerde dağın genişliğine karşı
denetleniyor. Direklerin ±4 m'lik yanal kayması tünelin kendi genişliği,
yüzeyde bir taşma değil.

## Sonuçlar

**Tablo kımıldadı ve bu, değişikliğin bulgusudur.**

| | önce | sonra |
|---|---|---|
| Şehir içi HPE P50 | 1,62 m | 1,79 m |
| Şehir içi kullanılabilirlik | %99,41 | %97,62 |
| Şehir içi direk | 46 | 36 |
| Şehir içi alan | 10,68 km² | 7,87 km² |
| Kırsal HPE P50 | 2,69 m | 3,13 m |
| Kırsal kullanılabilirlik | **%89,50** | **%72,64** |
| Kırsal direk | 33 | 28 |
| Kırsal alan | 654,00 km² | 427,50 km² |
| Ağırlıklı HPE P50 | 1,93 m | 2,08 m |
| Ağırlıklı kullanılabilirlik | %93,44 | %82,67 |

Tünel satırı kımıldamadı; zaten dağının içindeydi.

Kırsal kullanılabilirlikteki on yedi puan tek bir yerden geliyor:
ölçülen zeminin 140 m ötesinde duran mast sırası, turun uzak kolunu
besleyen sıraydı. O sıra bir düzlemin üzerinde duruyordu ve düzlem
üzerinde her link kapanır. Yani %89,50'nin bir kısmı, hiç ölçülmemiş
elverişli zeminin ürünüydü.

**Bunun bir sonraki adımı bıraktığı yer.** `_anchors_over` ızgarayı
`arange` ile serer, yani sahanın kendi uzak kenarı aralığın tam katı
değilse boş kalır: 19860 m'yi 4000 m aralıkla döşemek son 3860 m'yi
direksiz bırakıyor. Eskiden 20000, 4000'e tam bölündüğü için bu
görünmüyordu. Kırsal düşüşün büyük kısmı buradan geliyor ve bu bir
yerleşim düzeni sorusudur — sessizce değiştirmek yerine söyleniyor.
Daha küçük zemine göre yeniden yerleştirmek `yerkon solve`'un işi
(ADR-0023).

**Bir bulguyu da götürdü.** "Tur başına sekiz yerine on iki direk
yoklamak 5,5 puan eder ve hiç sermayeye mal olmaz", bu projenin en
sevdiği sonuçlardan biriydi. Yalnızca ölçülmüş zemin üzerinde iki tohumda
şöyle: 6'da %65,50/%65,47, 8'de %73,41/%69,94, 10'da %69,23/%74,75, 12'de
%72,64/%72,19, 16'da %74,33/%72,51. Altı açıkça az; sekizin üstünde
sıralama tohumla dönüyor ve komşu değerler arasındaki fark tohumlar
arasındaki kadar. Beş buçuk puan, kısmen ölçülmemiş zeminin ürünüymüş.

Bunu bir sınama yakaladı ve sınamayı zayıflatmak yerine iddiası
değiştirildi: artık kazananı değil, sekiz ile on arasındaki sıralamanın
tohumla döndüğünü sabitliyor. `rural.anchors_per_round` on ikide duruyor,
çünkü tek bir tohuma bakarak değiştirmek bu projenin zaten bir kez
yaptığı hata. Onu çözecek olan daha çok tohumla `yerkon solve`.

**Genelleşen ders.** Kırpan bir arayüz, çağıranın ne yaptığını bilmeden
kırpar. `height_at`'in kırpması bir link yolu için doğru, bir yerleşim
için sessizce yanlıştı; ve sessizce yanlış olan bir şey, hata
yükseltmediği için kimsenin fark etmediği şeydir. Bir sınama artık her
satırın her direğinin ölçülen ızgaranın içinde olduğunu söylüyor.
