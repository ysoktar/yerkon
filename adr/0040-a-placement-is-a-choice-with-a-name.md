# ADR-0040: yerleştirme, adı olan bir seçimdir

## Durum

Kabul edildi.

## Bağlam

Direkleri nereye koyacağı `AnchorRun.anchors()` içinde, bir `if` ile
gömülüydü: saha genişse kaydırmalı kare ızgara, değilse çizgi. Tek bir
yöntem, adı yok, alternatifi yok, kendi başına sınanamıyor.

Oysa verici yerleştirme eski ve adları olan bir problem. Kapsama tarafı
Maximal Covering Location Problem'dir (Church ve ReVelle, 1974); tam
çözümü NP-zordur ve planlama araçlarının gerçekte koşturduğu şey
açgözlü seçimdir. Kafes tarafında bir düzlemi eş dairelerle örtmenin en
incesi üçgen kafestir (Kershner, 1939) — hücresel planlamanın altıgen
üzerine çizilmesinin sebebi budur.

Ve bu proje bir haberleşme ağı değil. Bir konumlandırma ağında dört
direk bir sıra hâlindeyse, ne kadar gür gelirlerse gelsinler alıcıya
enine yönde neredeyse hiçbir şey vermezler. Bunun ölçüsünün adı var:
seyreltme (dilution of precision). Kapsama bunu görmez.

## Karar

**Tek bir dikiş: `place(plan, ground)`.** Bütün arayüz bu. Bir yöntem
eklemek bir işlev ve `METHODS` içinde bir addır; hiçbir çağıran
değişmez, görüntüleyicinin açılır listesi motordan gelen bir dizgidir.
`AnchorRun.anchors()` artık ince bir uyarlayıcı: bir koşuyu `Plan` ve
`Ground`'a çevirir ve sonucu adlandırır.

**Sekiz yöntem, dört aile.** Kafesler (kare, altıgen, koridor, çevre),
aramalar (kapsama, geometri, k-örtme) ve elle. Birer tane verip geçmemek
kasıtlı: bir yöntemin ne yaptığı ancak yanında bir başkası varken
görülür.

**Seyreltme iki bilinmeyen için hesaplanır**, bir GNSS alıcısının
çözdüğü üç ya da dört için değil. İki yollu menzil ölçümü doğrudan
mesafe ölçer, dolayısıyla durumda saat kayması yoktur (ADR-0010) ve
geometri matrisinde saat sütunu olmaz; düşey ise yoldan gözlenebilir
değildir (ADR-0011). Yani satırlar yatay birim vektörlerdir ve HDOP
`sqrt(trace((GᵀG)⁻¹))`.

**Aramanın puanı sıralı bir çifttir:** önce sahanın kaç direk-görüşü
eksik olduğu, sonra yeterli olan yerlerde geometrinin ne kadar iyi
olduğu. Harmanlanmadı, çünkü ikisi aynı birimde değil ve aralarındaki
herhangi bir ağırlık kimsenin savunamayacağı bir sayı olurdu. Eksiği
hücre değil *görüş* saymak, aramanın başlamasını sağlayan şey: seyreltme
üç direk bir hücreye erişene kadar tanımsızdır, dolayısıyla yalnız
seyreltmeye bakan bir puan ilk iki seçimi aynı bulur ve arama
başlamadan durur. Bunu yaşayarak öğrendim; ilk iki denemede arama sıfır
direk yerleştirdi.

**Arama bir çıtada durur, bütçede değil.** Sürekli bir nitelik puanında
bir direk daha her zaman biraz iyileştirir, dolayısıyla çıtası olmayan
bir arama kendisine verilen bütçeyi döndürür — bu projenin diğer
aramaları için zaten kararlaştırılmış kural (ADR-0015, ADR-0023).
Varsayılan çıta HDOP 2; GNSS pratiğinin "iyi geometri" dediği yer.

**Yerleştirme önerir, benzetim yargılar.** Yöntemler adayları link
bütçesi yerine bir *erişim dairesine* karşı puanlar; birkaç yüz aday
üzerinde tam bir bütçe koşturmak dakikalar sürerdi ve cevabın yine
gerçek şey tarafından denetlenmesi gerekirdi. Buradaki hiçbir şey
yayımlanan bir sayıya karar vermez: `yerkon table` düzeni her satırla
aynı bütçe, arazi ve kestiriciden geçirir (ADR-0001).

## Sonuçlar

**Kafeslerin farkı ölçüldü.** Her biri kendi örtme sınırında — kare için
`s = r√2`, üçgen için `s = r√3`, çünkü hücrenin köşelerine en uzak nokta
çevrel yarıçaptır — 12 km'lik bir sahanın içinde: kare 100 direk, altıgen
**72**. Kenar etkilerinden arınmak için kapsama içeriden okundu.

**Ve asıl bulgu.** Aynı zeminde, aynı erişimle, aynı adaylardan on direk
seçmek:

| on direk şuna göre seçilince | ortalama HDOP | konum alınamayan hücre |
|---|---|---|
| en çok zemin örtsün | 15,27 | %74 |
| geometri iyi olsun | 10,77 | %49 |

Gerçek Kızılay üzerinde daha da keskin. Şehir içi erişim 3825 m, saha
2970 m — yani **tek bir direk bütün sahayı örtüyor**. Kapsamaya göre
seçen arama bu yüzden tam olarak bir direk koyuyor ve hiçbir yerde konum
alınamıyor; geometriye göre seçen üç direk koyuyor ve her yerde
alınıyor. Doğru ölçütü seçmenin bedeli bir satırın tamamı.

**Bir davranış değişti.** Kaydırmalı bir satırın son direği artık
sahanın kenarını geçemiyor, çünkü hiçbir şey ölçülenin dışında durmaz
(ADR-0037). Görüntüleyicinin şehir içi sekmesi 49 yerine 46 direk
gösteriyor. Raporun satırları etkilenmiyor: onları `scenarios.py`
yerleştirir.

**`design_of`, `reach_of` ve `_lowest_unit` sahneden duruma taşındı.**
Yalnızca durumu okuyorlar ve arayan yöntemlerin, erişim halkasının
çizildiği aynı mesafeye ihtiyacı var; bir sayıyı iki yerde hesaplamak,
bir resmin ve bir koşunun hangisinin yerleşim olduğunu söyleyecek hiçbir
şey olmadan anlaşmazlığa düşmesinin yoludur.

## Sonraki adımlar

Yol kenarındaki yapılara yerleştiren yöntemler (`Ground.furniture` zaten
onları bekliyor ve bir sınama onları kullanıyor) getirilmiş yol verisi
gerektiriyor; o veri gelene kadar arayüzde gri duracaklar. Presetler,
sinyal renklendirmesi ve alıcı güzergâhları da ayrı adımlar.
