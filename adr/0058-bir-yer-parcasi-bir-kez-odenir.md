# ADR-0058: bir yer parçası bir kez ödenir

## Durum

Kabul edildi.

## Bağlam

Bütçe iki kaybı topluyordu. Biri yer yansıması: iki ışın modelinin
kopya ışını doğrudan ışını söndürüyor ve serbest uzaya göre fazladan
bir bedel çıkıyor. Diğeri kırınım: yola giren bir şey ışığı kesiyor ve
alan kenarın üzerinden dolaşarak geliyor. Satır şuydu:

```python
path_loss_db = spread_db + diffraction_db + clutter_loss_db
```

İki terim de aynı yer parçasının aynı bağlantıya yaptığı şeyi anlatıyor
ve toplandıklarında bağlantı tek bir yer parçası için iki kez ödüyor.

Fiziksel olarak da aynı anda olmuyorlar. İki ışının anlattığı sönümleme
için sönecek bir doğrudan ışın gerekiyor; bir sırt yolu kestiğinde
doğrudan ışın yok, gelen alan zaten kenarın üzerinden geldi. Bu yüzden
Tavsiye'nin kendi kurgusu kaybı serbest uzay artı kırınım olarak
kuruyor (ITU-R P.452, P.1812) ve üzerine bir yansıma terimi eklemiyor.

Rakam da söylüyordu. 20 m direkten 2 m alıcıya sekiz kilometre, ortada
25 m'lik bir sırt: yansıma 15,7 dB, kırınım 27,1 dB, ödenen 42,8 dB.
Yer, bir kere serbest uzayın üstüne 42,8 dB bindirebilecek kadar kötü
değil.

## Karar

**İki fazlalığın büyüğü ödenir, toplamı değil.**

```python
free_space_db = free_space_path_loss_db(distance_m, frequency_hz)
path_loss_db = (free_space_db
                + max(spread_db - free_space_db, diffraction_db)
                + obstruction.clutter_loss_db
                + obstruction.shadow_db)
```

Açık bir yolda yansıma terimi büyüktür ve kazanır. Kesilmiş bir yolda
kırınım kazanır. Sınırın yakınında hangisi kötüyse cevap odur.

İki ışın terimi serbest uzaya *göre* alınıyor, çünkü kırınım zaten
öyle ölçülüyor. Kırılma noktasının altında iki ışın serbest uzaydan az
olabiliyor; o zaman fazlalık eksi çıkıyor ve `max` kırınımı seçiyor.

## Sonuçlar

Aynı sekiz kilometre, aynı 20 m direk:

| yol | yansıma | kırınım | ödenen (önce) | ödenen (sonra) |
|---|---|---|---|---|
| düz ova | 15,7 dB | 6,1 dB | 21,8 dB | **15,7 dB** |
| 25 m sırt | 15,7 dB | 27,1 dB | 42,8 dB | **27,1 dB** |

Düz zeminin kendi eğriliği hâlâ sayılıyor, sadece karar vermiyor:
on kilometrede 5,99 dB okuyor ve aynı yolun yansıması 14,8 dB.

Yayımlanan tablo oynadı:

| satır | önce | sonra |
|---|---|---|
| şehir HPE P95 | 9,32 m | **9,61 m** |
| şehir kullanılabilirlik | %80,95 | **%81,23** |
| şehir alan | 6,26 km² | **6,32 km²** |
| kırsal HPE P95 | 23,74 m | **20,90 m** |
| kırsal alan | 162,25 km² | **163,08 km²** |
| ağırlıklı HPE P95 | 12,93 m | **13,31 m** |
| tünel | 3,03 m | 3,03 m |

Tünel oynamadı: bir tünelde kırınım da yansıma da portalların dışında
kalıyor ve içeride ikisi de sıfıra yakın.

Şehir satırının kötüleşmesi bir çelişki değil. Aynı satırda
kullanılabilirlik ve alan da arttı: çift sayım kalkınca kayıp düşüyor,
eskiden kapanmayan bağlantılar kapanıyor, ve kapananlar en kötüleri
olduğu için doğruca kuyruğa giriyorlar. Daha çok yerde konum alınıyor,
ve alınan konumların en kötü yüzde beşi biraz daha kötü.

## Üç sınama düştü, yerine ölçüm kondu

`test_relief_is_a_trade_rather_than_a_help` iki şey iddia ediyordu:
rölyef bazı bağlantıları tamamen kaybettiriyor, ve sağ kalanları
düzlükten *iyi* yapıyor. İkincisi toplama yapısının eseriymiş. Toplarken
rölyef büyük bir yansıma terimini küçük bir kırınımla takas ediyordu;
büyüğü alırken böyle bir takas yok.

3 km'den 10 km'ye bir koridor, dört tohumda on metrelik dalgalanma:

| zemin | kapanan | ortanca sigma |
|---|---|---|
| düz | 1,00 | 5,198 m |
| yumuşak, tohum 3 | 0,79 | 5,247 m |
| yumuşak, tohum 5 | 0,76 | 5,772 m |
| yumuşak, tohum 7 | 0,76 | 6,208 m |
| yumuşak, tohum 11 | 0,79 | 7,723 m |
| sarp (80 m), tohum 11 | 0,00 | yok |

Rölyef yansımayı gerçekten zayıflatıyor: 3 km'de düzlükte 5,3 dB olan
fazlalık 2,2 dB'ye iniyor. Ama bunu yapan tepeler yolun içinde duruyor
ve 16 ile 26 dB arası kırınım getiriyor, yani yansımanın hiç olmadığı
kadar. Büyüğü ödendiğinde rölyef düpedüz bir maliyet.

Sınama `test_relief_costs_more_than_the_reflection_it_weakens` olarak
yeniden yazıldı ve tek tohuma değil dört tohuma dayanıyor. Yansımanın
zayıfladığı iddiası kendi sınamasında duruyor
(`test_gentle_relief_helps_by_aiming_the_cancelling_ray_away`), orada
yansıma tek başına ölçülüyor ve etkilenmedi.

`test_closer_anchors_place_the_receiver_better` ikinci sınamaydı. Direk
aralığını 1000, 1500 ve 2000 m'de gezip hatanın adım adım büyüdüğünü
iddia ediyordu. Yeni yayılımda 1500 ve 2000 yer değiştirdi (2,89 m ve
2,62 m), ve sekiz tohumda ölçünce iddianın hiç doğru olmadığı çıktı:

| aralık | 1000 | 1500 | 2000 | 2500 | 3000 |
|---|---|---|---|---|---|
| ortanca hata | 2,01 m | 2,52 m | 5,45 m | yok | 6,87 m |

Sekiz tohumun hiçbirinde 2500 m'de konum alınmıyor ve sekizinde de
3000 m'de tekrar alınıyor. Sebebi zemin fikstürü: `ROLLING` tek bir tepe
dalga boyuna sahip, 3000 m. 3000 m aralık her direği tepenin aynı
noktasına koyuyor, 2500 m aralık beş ayrı noktasına dağıtıyor ve
bazıları çukur. Yani adım adım sıralama bir yayılım özelliği değil,
fikstürün rezonansı. Sınama artık geniş aralığı ölçüyor: bir kilometre
üç kilometreye karşı, sekiz tohumda sekiz kez kazanıyor.

`test_the_panel_shows_old_and_new_for_everything_that_moves` üçüncüsü.
Panelin her satırın iki yanını da yazdırdığını iddia ediyor ama bunu
`"5,52 km -> 1,66 km"` dizgisini arayarak yapıyordu, yani link
bütçesinin bir anlık görüntüsüydü. Sayılar artık panelden okunup
karşılaştırılıyor.

Tasarım paneli zaten oynadı. 3 m levha açık zeminde kırınım ödüyordu ve
o terim toplamdan çıkınca menzili uzadı; 25 m direğin yolu açık olduğu
için kırınımı zaten sıfırdı ve rakamı hiç oynamadı:

| yapı | yükseklik | önce | sonra |
|---|---|---|---|
| yol levhası | 3 m | 1,66 km | **1,91 km** |
| levha portalı | 6 m | 2,51 km | **2,70 km** |
| pano | 10 m | 3,47 km | **3,49 km** |
| aydınlatma direği | 12 m | 3,82 km | 3,82 km |
| amaca özel direk | 25 m | 5,52 km | 5,52 km |
| kule | 35 m | 6,53 km | 6,53 km |

Önceki sütun bu tablo için ayrıca ölçüldü, README'den alınmadı: 12 m
satırı README'de 3,83 yazıyordu ve iki yapının da verdiği 3,82. Eski
bir modelden kalmış, düzeltildi.

Yüksekliğin menzil satın aldığı sonucu değişmedi, alçak uçtaki fark
biraz kapandı: 25 m ile 3 m arası 3,3 kattan 2,9 kata indi.

## Yapılmayanlar

**Geçiş bölgesi sert.** Sırt tam Fresnel bölgesinin kenarındayken iki
terim birbirine yakın ve cevap birinden diğerine sıçrıyor. Gerçekte
kısmen kesilmiş bir yolda hem sönen bir doğrudan ışın hem kenardan
gelen alan var, ve toplamları bir güç toplamı. Bunu yapmak iki terimin
faz ilişkisini gerektiriyor; ne P.452 ne P.1812 bunu yapıyor.

**Gölgeleme ve örtü hâlâ ekleniyor.** İkisi de serbest uzayın üstüne
eklenen ayrı etkiler (ADR-0055) ve yer geometrisinin iki okuması
değiller, o yüzden `max` dışında kaldılar.
