# 0015. Yerleşim araması değiştirgeleri değil yapıları arar

## Durum
Kabul edildi.

## Bağlam
Listedeki son iş; geri kalan her şey kurulana kadar ertelendi. Bir eniyileyici
ancak eniyilediği şey kadar iyidir ve link bütçesi, alışveriş, kestirici ve
maliyetlendirme var olup test edilene kadar herhangi bir yerleşim
algoritması, kimsenin savunamayacağı bir sayıyı küçültüyor olurdu.

Sonra maliyetlendirme neyin eniyileneceğini söyledi. Telsizler, direk tabanlı
bir yerleşimin sermayesinin yaklaşık yüzde biri. Para biriktirmek için
modüller üzerinde arama yapmak, yanlış yüzde üzerinde arama yapmak olurdu.

## Karar
Arama, *her noktada hangi yapının kullanılacağı ve aralarının ne kadar
olacağı* üzerinedir; yalnızca koridorun taşıdığı söylenen yapılar
kullanılarak ve yalnızca hiçbiri yokken inşa edilerek. Her aday birinin
kurabileceği bir yerleşimdir: gerçek montajlarda gerçek direkler, tablonun
kullandığı link bütçesiyle puanlanmış ve aynı malzeme listesiyle
fiyatlandırılmış.

İki karıştırma biçimi aranır, çünkü zıt yönlere çekerler ve genel olarak
hiçbiri kazanmaz. Her noktada duran **en ucuz** yapıyı almak direk başına en
düşük fiyatı verir ve kısa olduğu için daha fazlasını gerektirir. **En uzun**
olanı almak her biri için daha pahalıdır ve daha azını gerektirir. Cevap
hangisi daha ucuza çıktıysa odur ve ikincisi yanında bildirilir.

Aralıklar seyrekten sıka doğru aranır ve arama gereksinimi karşılayan ilkinde
durur, çünkü daha sık olan daha pahalıdır ve asla daha az kapsamaz. İlk
yazılan sürüm sıktan seyreğe arıyordu ve işe yarayan, iki buçuk kat fazlaya
mal olan bir cevap döndürüyordu.

Alan taraması bir kez, kazanan üzerinde koşar. Projedeki en yavaş şeydir ve
her adayda koşturmak aramayı saniyeler yerine dakikalar yapardı.

## Sonuçlar
Tepeli zeminde sekiz kilometrede, beş metrelik bir toleransla ve her 250
m'de bir levha dururken: 600 m aralıkta yirmi bir mevcut yol levhası
gereksinimi 274736 TL'ye karşılıyor. On altı amaca özel yirmi beş metrelik
direk aynı gereksinimi 1529323 TL'ye karşılıyor.

Beş buçuk kat; ve levhalar, direğin 5,52 km'sine karşı 1,66 km'ye
erişmelerine rağmen kazanıyor. Yükseklik menzil satın alır ve kıt olan
menzil değildir; kıt olan paradır ve zaten duran bir levha, durmayan bir
direğin otuz dörtte birine mal olur.

İşte karışık montaj stratejisi budur; iddia edilerek değil aranarak varıldı
ve menzil değerlerinin verdiği sezgiyi ters çeviriyor.

Arama reddeder de. Telsizin kendi ölçüm tabanının altındaki bir tolerans bir
yerleşim sorunu değildir ve hiçbir direk düzeni onu karşılamaz; dolayısıyla
kötü bir kümenin en iyisi yerine hiçbir şey döner.

Aramanın yapamayacağı şey bir etüt uydurmaktır. Hangi yapının nerede durduğu
yapılandırmadır ve varsayılanlar tipik bir Türk karayolu kesimi hakkında bir
varsayımdır. Gerçek bir yerleşim onları gerçekte orada olanla değiştirir ve
cevap oynar.
