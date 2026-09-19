# ADR-0057: sekiz bant bir ölçüm değildi

## Durum

Kabul edildi. ADR-0047'nin ölçüm kısmını değiştirir.

## Bağlam

ADR-0047, aramaların düz arazi rakamına karar verdirmesini bitirdi:
disk artık bu zeminde ölçülüyor. Ölçümün kendisine bakmamıştım.

`measured_reach_m` açık arazi menzilini **8 banda** bölüyor, 200 ışın
atıyor, ve geçen son bandın dış kenarını döndürüyordu. Üç şey bozuktu.

**Cevap sekiz değerden biri olabiliyordu.** Kızılay'da bant genişliği
478 m. Şehir zemini ile modellenmiş kırsal zemin birebir aynı sayıyı
verdi, ondalığına kadar: ikisi de aynı bantta kaldığı için. Bir kolun
çözünürlüğü ±478 m ise o kol bir ölçüm değil, bir kova.

**Hiç bant geçmezse taban dönüyordu.** `answer = reached or edges[1]`
satırı, hiçbir bandın çıtayı tutturamadığı durumda ilk bandın dış
kenarını cevap olarak veriyordu. Altı tohumun üçünde olan buydu:
bildirilen 478 m, ölçülen hiçbir şey. Ve sahadaki her arama yerini o
sayıya göre seçiyordu.

**Dış bantlar en az kanıtı alıyordu.** Işınlar merkezden rastgele açıyla
atılıp saha dışına düşenler eleniyordu, ve eleme oranı mesafeyle artıyor.
Yani çıtanın kırıldığı yer olan dış bantlar en az örneği alıyordu. 200
ışın 8 banda bölününce bant başına ~25 örnek düşüyor; %90 çıtası 25
örnekte 25/26 ile 193/220 arasındaki farkı ayırt edemiyor.

**Ve koridorlarda hiçbir ışın sahaya düşmüyordu.** Tünel satırının eni
sıfır, `0 <= y <= 0` yalnızca tam olarak y=0'ı kabul ediyor, rastgele
açı bunu neredeyse hiç tutturmuyor. Tünelin "ölçülen" menzili baştan
sona tabandı.

## Karar

**32 bant, bant başına 400 ışın.** Çözünürlük Kızılay'da 478 m'den
119,5 m'ye iniyor.

**Her bant aynı kanıtı alıyor.** Işınlar bandın kendi aralığından
çekiliyor ve saha dışına düşen yeniden çekiliyor, bir deneme tavanıyla.
Örneklenemeyen bir bant kanıt değildir: cevabı ne uzatır ne durdurur.

**Koridor kendi boyunca örnekleniyor.** Eni sıfırsa açı 0 ya da π.

**Hiç bant geçmezse bu söyleniyor.** `Reach(metres, measured)` döndü:
`measured` yanlışsa mesafe bir tavan, bir okuma değil. Gerçek menzil
onun altında ve bu örnekleme nerede olduğunu söyleyemiyor.

## Sonuçlar

| satır | önce | sonra |
|---|---|---|
| şehir (Kızılay) | 478,1 m | **239,1 m** ölçüldü |
| kırsal (Polatlı) | 690,1 m | **172,5 m** ölçüldü |
| tünel | 370 m, hiç ışın düşmemiş | **351,5 m** ölçüldü |

Kırsalın diski **dörtte birine** indi. Maliyet: şehirde 1,2 sn, kırsalda
0,8 sn, tünelde 4,0 sn, düzenleme başına bir kez ve önbellekli.

Yayımlanan tablo oynamadı: üç satır da kafes yöntemi kullanıyor ve
kafesler bu sayıyı hiç okumuyor.

**Kart artık hangi diski kullandığını yazıyor.** Yanındaki halka açık
arazi rakamı (3825 m), arama başka bir sayıyla yer seçiyor (239 m), ve
kart bugüne kadar yalnızca ilkini gösteriyordu. Ölçülemediğinde de
söylüyor: "{metres} m, ama ölçülemedi, gerçek menzil bunun altında".

Aynı mesafe iki farklı iddia olabiliyor, ve bir sınama bunu çiviliyor:
400 m rölyefte cevap 119,5 m *ölçüldü*, 900 m rölyefte aynı 119,5 m
*ölçülemedi*.

## Yapılmayanlar

**Çıta hâlâ sert bir %90.** Örneklenmiş bir oranla sert bir eşik her
zaman bir bıçak sırtı bırakır; kırsalın ilk bandı 40 ışında 0,875, 120'de
0,900, 400'de 0,935 veriyordu. 400 ışın eşiği gürültüden ayırıyor ama
kaldırmıyor.

**Dışa yürüyüş ilk düşen bandı cevap sayıyor.** Bir tepenin ardındaki
400 m, arkasındaki vadinin 600 m'sinden kötü olabilir; yürüyüş 400'de
durur. Bu, aramanın diski sert bir kenar olarak kullanmasıyla tutarlı,
ama monotonluk varsayımıdır ve ölçülmedi.
