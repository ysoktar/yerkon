# ADR-0045: bir güzergâh da bir seçimdir

## Durum

Kabul edildi.

## Bağlam

Yolculuk sekme başına tek şekildi: koridorda düz çizgi, alanda çevre
turu. Bütün alıcılar aynı yolu izliyordu; aralarındaki tek fark nereden
başladıkları ve ne hızla gittikleriydi.

Bu bir düzenleme, bir seçim değil. Ve tablonun bildirdiği bir şeye
sessizce karar veriyor: yalnızca doğuya giden bir güzergâh, enine
geometrisi hiç değişmeyen bir güzergâhtır — bir koridorda bu, yeterli
*görünen* bir yerleşim ile yeterli *olan* arasındaki farktır (ADR-0011).

ADR-0040 direkler için aynı şeyi söylemişti: yerleştirme adı olan bir
seçimdir. Güzergâh da öyle.

## Karar

**Aynı dikiş.** Bütün arayüz `trace(trip, course)`; yerel metrede bir
merkez çizgi döndürür. Güzergâh eklemek bir işlev ve bir addır; hiçbir
çağıran değişmez, görüntüleyicinin listesi motordan gelen bir dizgidir.

**Yedi şekil, ve hepsi bu alanın kendi adlandırdıkları.**

| Güzergâh | Nedir |
|---|---|
| Düz çizgi | Koridorun kendisi. |
| Gidiş-dönüş | Bir etüt aracının bir koridoru gerçekte sürdüğü şekil. Her nokta bir kez her yöne bakarak gözleniyor, yani direklerin hangi tarafta olduğuna bağlı bir sapma ortalamaya karışmak yerine ortaya çıkıyor. |
| Çevre turu | Kenardan dolaş, ortadan geç. Eskiden alanın tek şekliydi. |
| Sekiz çizme | Ataletsel ve GNSS alıcılarının denemede sürüldüğü desen: kendini kesiyor, yani araç her yöne giriyor. Tek yöne dönen bir çevrim, dönüş yönüne bağlı bir hatayı gizleyebilir. |
| Tarama (biçerdöver) | Boustrophedon: uçlarda dönen paralel geçişler. Bir alanı kenarından değil içinden örnekleyen standart etüt deseni. |
| Rastgele duraklar | Random waypoint; Johnson ve Maltz (1996), mobil ağların o gün bu gün kullandığı hareketlilik modeli. Tohumlu. |
| Gerçek yol | Getirmenin gerçekten getirdiği yol geometrisi. Tek ölçüm olan güzergâh; ötekiler birinin süreceği desenler. |

**Rastgele durakların kusuru yazılı.** Düzgün dağılımla çekilen duraklar
aracı sahanın ortasına kenarlarından çok daha sık koyar — Yoon, Liu ve
Noble, *Random waypoint considered harmful* (2003). Aynı makalenin
bildirdiği hız sönümü burada yok, çünkü hız modelden değil alıcıdan
geliyor. Birincisi gerçek ve bu güzergâh ortayı fazla örnekliyor; bir
sınama bunu ölçüyor, çünkü bir modelin yapmadığı şeyi adıyla söylemek bu
projenin karakteri.

**Alıcı başına.** Şehrin içini tarayan bir etüt aracı ile çevre yolunu
dönen bir kamyonet aynı direklere farklı sorular soruyor.

**Direklerin yeri bir alıcının güzergâhıyla oynamaz.** Direklerin
dizildiği omurga sahanın bir olgusu; bir alıcıya hangi deseni sürmesi
söylendiğinin değil. Bu yüzden `road()` omurga için güzergâhsız
çağrılıyor.

**Güzergâh belirtmeyen bir alıcı, eskiden sürdüğü yolu sürer** — nokta
nokta. Boş ad varsayılan, ki bu var olmadan önce kaydedilmiş bir
düzenleme olduğu gibi yüklensin (ADR-0043).

**Zeminin taşıyamadığı güzergâh gri gösteriliyor, gizlenmiyor.** Gerçek
yol, getirmenin henüz getirmediği bir geometri istiyor (ADR-0036).

## Sonuçlar

Kızılay'da dört güzergâh dört ayrı iz veriyor: düz çizgi `y` sıfırda
kalıyor, tarama 294..1078 bandını süpürüyor, sekiz 913..2640'a çıkıyor,
rastgele duraklar 1272..2549 arasında geziyor.

**Bir sınamayı kendim yakaladım.** İlk yazdığım "varsayılan eskisi gibi
sürüyor" sınaması, varsayılanı *yeni* `circuit` ile karşılaştırıyordu —
yani yeni kodun kendisiyle anlaştığını kanıtlıyordu, başka bir şey
değil. Eski iki şekil hâlâ `scenarios` içinde duruyor; karşılaştırma
artık onlara karşı. Ve bunu yazarken bir kayma buldum: adım
hesabım 147 yerine 148,5 veriyordu. Düzeltildi; üç satır da **nokta
nokta aynı**.

Bir de sekiz, verilen genişliğin yalnızca yarısını kullanıyordu:
`sin(t)cos(t)`, `sin(2t)/2` eder.

## Sonraki adımlar

Yol kenarı donanımı ve gerçek yol güzergâhı aynı şeyi bekliyor:
Overture'ın `transportation` katmanı (ADR-0038 binaları aynı yoldan
getirdi). O geldiğinde hem `road` güzergâhı hem de ADR-0040'ın levha ve
trafik ışığı yerleşimleri açılır.
