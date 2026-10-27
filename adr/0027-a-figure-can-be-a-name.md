# ADR-0027: bir figür bir ad olabilir ve hiçbir şeyi değiştirmeyen seçenek bir yalandır

## Durum

Kabul edildi.

## Bağlam

`rural-hard-ground`, adlandırılmış dört yerleşim seçeneğinden biri
olarak hazır geliyordu. Notu, kırsal satırı Polatlı'nın 486 m'lik
engebesi yerine Gölbaşı'nın 907 m'lik engebesi üzerine oturttuğunu ve
kullanılabilirliğin yaklaşık %90'dan yaklaşık %45'e düştüğünü söylüyordu.

Zemin düzeltmelerinden sonra hazır gelen seçenekler kendi notlarına karşı
denetlenirken, bu seçeneğin **tam olarak varsayılanın sayılarını**
ürettiği görüldü — %89,50 kullanılabilirlik, ellinci yüzdelikte 2,69 m;
her basamağına kadar.

`site.rural_relief_m` değerini ayarlıyordu; bu ise hiç zemin
indirilmediğinde kullanılan *yedek* engebedir. Polatlı indirilmiştir ve
paketle birlikte gelir, dolayısıyla yedeğe hiç başvurulmaz ve seçenek
hiçbir şeyi değiştirmemiştir.

Hiçbir şey hata yükseltmedi. `options.write`, ayarlar dosyasının
tutmadığı bir figürü adlandıran bir seçeneği zaten reddeder — bu
denetim, tam olarak sessizce hiçbir şey yapmayan bir kaydedilmiş dosyayı
engellemek için vardır. Bu seçenek ise var olan, ama hazır gelen
yapılandırmada okunmayan bir figürü adlandırıyordu.

Daha iyisini yapamamasının sebebi, değiştirmesi gereken şeyin bir figür
olmamasıydı. Bir satırın hangi sahada durduğu `scenarios.py` içinde
`RURAL_SITE = "polatli"` olarak yaşıyordu ve `defaults.toml` yalnızca
sayı tutuyordu. Seçenek de en yakın sayıya uzandı.

Bu aynı zamanda görüntüleyicinin yeni indirme panelini yarım bağlı
bırakıyordu: biri sayfadan İzmir'i indirebilir, ona bakabilir ve bir
rapor satırını onun üzerine koymanın hiçbir yolu olmazdı.

## Karar

**Bir `Sourced` değer sayı olduğu gibi ad da olabilir.**
`Settings.number` bir adı, metnini istemesini söyleyen bir iletiyle
reddeder; `Settings.text` onu döndürür. Bir düzenleme, girdinin hâlihazırda
olduğu türe zorlanır; çünkü bir sayfa her şeyi metin olarak gönderir ve
bu olmadan bir aralık `"3000"` dizgisi olarak saklanır ve her yerde
`3000` ile eşit çıkmazdı.

`urban.site`, `rural.site` ve `tunnel.site` artık yanlarındaki aralıklar
gibi DESIGN figürleridir. `src/yerkon/site/places/` altındaki dizin
adlarını taşırlar; boş olması modellenmiş arazi demektir. `yerkon fetch`
neyi yazarsa — görüntüleyiciden yazdıkları dahil — birine girebilir.

`rural-hard-ground` artık `rural.site = "golbasi"` ayarlıyor ve
söylediğini yapıyor. Figürler panelinde bir ad, serbest metin kutusu
yerine gerçekten indirilmiş sahalardan oluşan bir seçici olarak
görünüyor; çünkü orada olmayan bir dizini yazmak bunun yapabileceği tek
hatadır.

## Sonuçlar

İndirme paneli baştan sona bağlı: sayfadan bir yer indir, sonra bir rapor
satırını ona yönlendir; tablo, ayrıştırma ve çözücü hepsi onun üzerinde
çalışır.

Üç sınama artık buraya getiren başarısızlığı sabitliyor: sahanın bir
figür olduğunu, seçeneğin başka bir zemine ulaştığını ve bir addan sayı
istemenin tahmin etmek yerine bunu söylediğini.

Daha geniş ders, ateşlenmeyen denetim hakkında. `options.write`, bir
seçeneğin adlandırdığı her anahtarın var olduğunu doğrular. Bu, anahtarın
uygulanacağı yapılandırmada *okunup okunmadığı* sorusuyla aynı değildir
ve bu proje o boşluğa artık iki kez yakalandı — bir kez burada, bir kez de
on altı yerleşim figürü görüntüleyiciye altlarında çizilecekleri bir grup
başlığı olmadan gönderildiğinde; oradaydılar, doğruydular ve
görünmezdiler. Varlığı denetlemek ucuzdur. Başvurulduğunu denetlemek
değildir ve bunu yakalayan tek şey, şeyi çalıştırıp iddiasıyla
karşılaştırmaktır.

Bunu bulan da o oldu: bir sınama değil, dört notu dört taze koşuya karşı
yeniden okumak.
