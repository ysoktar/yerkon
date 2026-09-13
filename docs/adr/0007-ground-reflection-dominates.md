# 0007. Zemin yansıması, ve erişmek ile ölçmek arasındaki fark

## Durum
Kabul edildi. Bu deponun kendi `rf.py`'sinin ilk sürümünü düzeltir.

## Bağlam
İlk link bütçesi serbest uzay kaybı artı bıçak sırtı kırınımı
kullanıyordu. Dolayısıyla düz zemin üzerinde serbest uzayın ötesinde hiç
kayıp bildirmiyor ve stok donanımın 10 km'ye 50 dB'den fazla payla
eriştiği sonucuna varıyordu.

Bu, bu projedeki her geometri için yanlıştır. Zeminden birkaç metre
yukarıdaki bir telsizin ikinci bir yolu vardır: yüzeyden seken ışın.
Kırılma mesafesinin — `4 * h1 * h2 / dalgaboyu` — ötesinde ikisi karşıt
fazda varır ve kayıp mesafenin karesiyle değil dördüncü kuvvetiyle büyür.

Önceki modele karşı 10 km'de ölçülmüş hâliyle:

| Montaj | Kırılma noktası | Eksik gösterim |
|---|---|---|
| Yol levhası, 3 m | 196 m | 34,1 dB |
| Levha portalı, 6 m | 392 m | 28,1 dB |
| Pano, 10 m | 654 m | 23,7 dB |
| Uzun direk, 25 m | 1634 m | 15,7 dB |
| Kule, 35 m | 2288 m | 12,8 dB |

## Karar
Yol kaybı, iki ışınlı çift eğimli modeldir; artı arazi yola yükseldiğinde
kırınım, artı engel kaybı. İkisi ayrı etkilerdir: yansıma kusursuz düz
zemin üzerinde de olur, kırınım bir engele ihtiyaç duyar.

Bütçe artık **kullanılabilir menzili** bağlantının kapanıp kapanmadığından
ayrı bildiriyor ve yerleşim araması birincisini kullanıyor.

## Sonuçlar
Manşet iddia değişiyor. Bağlantılar hâlâ kapanıyor, çünkü yayılı bir dalga
formu gürültü tabanının 30 dB altında bile çözülmeye devam ediyor. Çöken
şey, sinyal-gürültü oranını izleyen zamanlama hassasiyeti.

Kullanılabilir menzil — ölçüm hatasının bir hedefin altında kaldığı mesafe:

| Montaj | sigma 3 m | sigma 5 m | sigma 10 m |
|---|---|---|---|
| Yol levhası, 3 m | 1,5 km | 1,9 km | 2,6 km |
| Levha portalı, 6 m | 2,3 km | 2,9 km | 3,9 km |
| Pano, 10 m | 3,1 km | 4,0 km | 5,3 km |
| Aydınlatma direği, 12 m | 3,4 km | 4,4 km | 6,0 km |
| Uzun direk, 25 m | 4,9 km | 6,4 km | 9,0 km |
| Kule, 35 m | 5,8 km | 7,5 km | 10,7 km |

Yani 5–10 km gereksinimi yalnızca yüksek yapılarla ve yalnızca uzak uçta
birkaç metrelik ölçüm hatası kabul edilebilirse karşılanıyor. 25 m'lik bir
direk 6,4 km'de 5 m'ye ölçüyor. Mevcut yol donanımına monte edilen hiçbir
şey işe yarar bir hassasiyette 5 km'ye erişmiyor.

Kapanma mesafesini menzil diye bildirmek, direk kapsamasını iki ila beş
kat; tablodaki her maliyet değerinin paydası olan hizmet alanını da bunun
karesi kadar olduğundan fazla gösterirdi.
