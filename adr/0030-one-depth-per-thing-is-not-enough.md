# ADR-0030: şey başına tek derinlik yetmiyor

## Durum

Kabul edildi.

## Bağlam

Sahne arkadan öne boyanır: her yüzey izdüşürülür, ne kadar uzakta
olduğuna göre sıralanır ve o sırayla çizilir. Oluşturucunun tamamı budur
ve görüntüleyicinin hiçbir kitaplığa ihtiyaç duymamasının ve çevrimdışı
çalışmasının sebebi de budur (ADR-0008).

Tek bir varsayımı vardır ve o varsayım bir şeyin *bir* uzaklıkta
olduğudur. Kırsal satırı açmak, olmadığında ne olduğunu gösterdi.

Yol, yüz altmış noktada örneklenmiş yirmi kilometrelik bir devreydi ve o
noktaların ortalama derinliğiyle tek bir öğe olarak veriliyordu. Kameraya
o ortalamadan daha yakın olan her tepe, devrenin tamamının üzerine
boyanıyordu — tepenin önünde olan yakın kollar dahil. Devrenin yarısı
kayboluyordu ve sağ kalan yarı, alansal bir yerleşimi bir tarlaya
çizilmiş düz bir çizgi gibi gösteriyordu. Ekranda hangisinin gerçek
olduğunu söyleyen hiçbir şey yoktu.

Onu parça başına bir öğeye bölmek bunu düzeltti ve aynı varsayımı bir
kat aşağıda açığa çıkardı. Bu sahada bir zemin dörtgeni yedi yüz metre
genişliğindedir ve o da ortasının derinliğinde sıralanır: sıyırma
açısından bakıldığında ortası, uzak kenarından neredeyse bir hücre kadar
daha yakındır; dolayısıyla dörtgen, uzak tarafında yatan yol yarısının
üstünü örtüyordu. Yol kesik çizgi olarak geri geldi.

Aynı kare okumasından iki şey daha çıktı:

Ağ, saha ne olursa olsun sabit yüz çarpı kırktı. Yirmi kilometreye
yirmi kilometre böylece boyunca her 460 m'de, enine her 1100 m'de bir
örnekleniyordu — zemin çizgili çıkıyordu ve bir tepe sırt gibi
okunuyordu, çünkü ağ onu yalnızca tek yönde çözebiliyordu.

Ve komşu dörtgenler birbirinden bağımsız yumuşatıldığı için arka plan
her ortak kenardan kıl gibi görünüyordu. Dört bin tanesi, zemin yerine
tepenin üzerine serilmiş bir tel ızgara gibi okunuyordu.

Aynı yerden iki küçük şey daha çıktı. Gözün arkasındaki bir köşe
izdüşürülemez ve bunun için bütün yüzey atılıyordu — yani yakın bir
kameranın tam altındaki zemin, tam da ekrandaki tek şey olduğu uzaklıkta
kayboluyordu. Ve kapsama katmanı, boyacının onu gömmesini engellemek için
ağdan altmış birim yukarıda tutuluyordu; bu da beş kat abartıyla çizilen
on iki metrelik gerçek zemin demektir: yakından bakınca anlattığı tepenin
görünür biçimde üzerinde asılı durur.

## Karar

Zemin üzerinde yatan bir çizgi, sıralanmadan önce kameraya doğru bir ağ
hücresi kadar çekilir. Bir dörtgenin tek derinliğinin onun tamamını
anlatmayı bıraktığı ölçek budur, dolayısıyla doğru kaydırma da budur:
üzerinde yattığı dörtgene karşı kazanmaya yeter, önündeki bir tepeye
karşı kazanmaya yetmez. Ağı sayfa bilir, dolayısıyla onu sayfa sağlar.

Ağ, sahanın kendi oranlarından örneklenir; yaklaşık dört bin dörtgenlik
sabit bir bütçede kabaca kare hücreler için.

Her dörtgen kendi ortasından yarım piksel büyütülür; bu, komşusuyla olan
birleşimi kapatır. Her dörtgeni kendi renginde konturlamak da kapatır ve
dört binin tamamı üzerinde ikinci bir geçişe mal olur.

Gözün arkasında köşesi olan bir şekil yakın düzlemde kesilir ve öndeki
parçası çizilir.

Kapsama katmanı zemin üzerinde oturur ve üzerine çizilen her şey gibi
öne kaydırılır — ağ hücresinin yanı sıra kendi yarı genişliği kadar da;
çünkü her iki yüzey de geniştir ve her ikisi de ortalarının derinliğinde
sıralanır, dolayısıyla iki yayılım toplanır.

## Sonuçlar

Yol bir yol. Zemin zemin.

Genelleşen şey: bir boyacı oluşturucusu yalnızca aralarındaki derinlik
farklarına göre küçük olan şeyler için tamdır ve buradaki iki
başarısızlık da aynı hatanın farklı ölçeklerdeki hâliydi. Bir noktada
değil bir yüzey üzerinde çizilen her şeyin ya bir kaydırmaya ya da daha
ince bir bölüntüye ihtiyacı vardır ve ne kadar gerektiğini yüzeyin
büyüklüğü söyler.

Genelleşmeyen ve açıkça söylenmeye değen şey: bu bir derinlik
kaydırmasıdır, yani bir el çabukluğudur. Arazi üzerinde yatan çizgiler
için doğrudur, üzerinde duran bir duvar için doğru olmazdı. Sahne bir gün
gerçek düşey yayılımı olan bir şey edinirse, cevap piksel başına
derinliktir; o da WebGL demektir, o da ADR-0008'deki değiş tokuşun
yeniden yapılması demektir.
