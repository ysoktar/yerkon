# ADR-0022: turu, bir sabitlemenin kaç direğe ihtiyaç duyduğuna göre değil kaçının cevap verdiğine göre boyutla

## Durum

Kabul edildi.

## Bağlam

Gerçek Ankara zemininde kırsal satır zamanın %82,3'ünde bir konum
üretiyordu. Bu tablodaki en zayıf sayı ve onun bariz okumalarının hepsi
yanlıştı.

İlk soru başarısızlıkların gerçekte ne olduğuydu. Kullanılabilirlik,
kapanmamış bir bağlantıyı hiç menzilde olmamış bir bağlantıyla aynı sayar ve
ikisinin çareleri zıttır: daha çok direk mesafeyi çözer, aralık hakkında
hiçbir şey bir sırtı çözmez. Ölçmek ikisini tamamen ayırdı:

| | kırsal bağlantıların payı |
|---|---|
| kapanan | %53,9 |
| zeminin öldürdüğü | %46,1 |
| açık zeminde bile fazla uzak | **%0,0** |

Tek bir kırsal bağlantı bile mesafe yüzünden düşmüyor. Arazi kaldırılsa her
bir başarısızlık kapanırdı. Direkler fazla aralıklı değil; birbirlerini
göremiyorlar.

## Denenenler

**Yükseklik.** Daha uzun bir direk daha çok sırtın üzerini görür ve işe
yarıyor: aralık değişmeden 25 m'den 35 m'ye çıkmak kullanılabilirliği
%82,3'ten %87,8'e götürdü, tek bir fazladan direk olmadan. Yükseklik
fiyatlanana kadar bu bir kelepir gibi okunuyor. Çelik ve temel yükseklikten
hızlı büyür — kabaca karesiyle — dolayısıyla eşit parada karşılaştırma
tersine dönüyor:

| aralık | yükseklik | direk | kullanılabilirlik | direk sermayesi |
|---|---|---|---|---|
| 4000 m | 25 m | 33 | %82,3 | 2 805 000 TL |
| 4000 m | 35 m | 33 | %87,8 | 5 497 800 TL |
| **3000 m** | **30 m** | **49** | **%90,5** | **5 997 600 TL** |
| 3000 m | 35 m | 49 | %90,7 | 8 163 400 TL |

Yaklaşık altı milyon liraya ya uzun direklerle %87,8 ya da daha çok direkle
%90,5 satın alabilirsin. Eşit bütçede aralık kazanıyor. Her iki hâlde de
yedi puan için kabaca iki katı sermaye.

**Bir komşu listesi.** En yakın direk bir sırtın ardındayken iki katı uzakta
olan biri apaçık görünüyorsa, mesafeye göre sıralanmış bir tur kendini
kapanamayacak bağlantılara harcar. Bir tanılama bunu destekliyordu: en yakın
sekiz, bir birimi zamanın %25'inde dört kullanılabilir menzilden yoksun
bırakıyor; bütün alan ise %20'sinde bırakırdı. Dolayısıyla alıcı, geçen turda
cevap vereni geri aramaya ve yenilerini keşfetmek için iki yuva boş tutmaya
başladı — gerçek alıcıların yaptığı ve hiçbir direğe, güce ve hava süresine
mal olmayan şey.

İlk tohumda +2,57 puan verdi. **Üç tohum boyunca +2,57, +0,01 ve −1,24
verdi.** Gürültüydü ve tek bir koşumun gücüne dayanarak neredeyse
gönderiliyordu. Beş puanlık tanılama gerçekti ama kullanılabilirliğe
ulaşmıyor, çünkü kullanılabilirlik dört direk elde etmeye bağlı değil:
izleme süzgeci bir turu tek bir menzille atlatıyor, dolayısıyla soğuk
başlangıç eksiğinin çoğu sütunda hiç görünmüyor.

**Daha az müşkülpesent olmak.** Ölçüm toleransını 30 m'den 60 m'ye
yükseltmek hiçbir şey değiştirmedi — iki ondalık basamağa kadar tek bir
değer bile. Kapanan hiçbir kırsal bağlantı 30 m'den gürültülü değil, yani
kabul kapısı hiç bağlamıyordu. Ölü bir kol; öldüğünü bilmeye değer.

## Karar

Kırsal satırda tur başına sekiz yerine on iki direk yokla.

| tur başına direk | kullanılabilirlik | HPE P50 | tur |
|---|---|---|---|
| 8 | %82,3 | 2,31 m | 509 ms |
| **12** | **%89,6** | **2,71 m** | **763 ms** |
| 16 | %89,9 | 2,97 m | 1018 ms |

Üç tohum boyunca: +7,29, +5,32, +3,85 puan. Her seferinde pozitif; komşu
listesinin olmadığı şey de buydu.

Sekiz, senaryolar alan olduğunda seçilmişti; bir konumun dörde ihtiyaç
duyduğu ve biraz payın cömert göründüğü gerekçesiyle. O gerekçe açık zeminde
tutuyor ve gerçek rölyefte çöküyor. Yoklanan direklerin yarısı hiç cevap
vermiyor, dolayısıyla sekiz deneme yaklaşık dört yanıt veriyor — soğuk bir
sabitlemenin gerektirdiğinin *tam kendisi*, yedeksiz; sütunun seksenlerin
başında oturmasının sebebi de bu. On iki deneme yaklaşık altı veriyor. On
altı, 0,8 puan daha getiriyor ve güncelleme hızında getirdiğinden fazlasını
götürüyor.

`max_anchors_per_round` zaten projeye değil yerleşime aitti, dolayısıyla bu
kırsal senaryoda tek bir sayı. Şehir içi ve tünel sekizde kalıyor: bir
şehirde 500 m ızgarada ve bir tünelde 150 m aralıkta yoklananın neredeyse
hepsi cevap veriyor ve daha uzun bir tur hiçbir şey satın almaz, güncelleme
hızına mal olur.

## Sonuçlar

Kırsal satır hiç sermaye harcamadan %82,26'dan %89,55 kullanılabilirliğe
gidiyor. Bedeli güncelleme hızı — birim başına saniyede 1,96 sabitlemeden
1,31'e — ve yaklaşık 0,4 m yatay hata, çünkü bir turdaki menziller artık 763
ms'ye yayılıyor ve araç o sürede 21 m yol alıyor. Amacı GNSS yokken orada
olmak olan bir sistem için kullanılabilirlik, mal olduğu saniyede üçte bir
sabitlemeden daha değerli.

Taşınmaya değer genelleme şu: **bir tur, bir konumun kaç direğe ihtiyaç
duyduğuna göre değil kaç direğin cevap verdiğine göre boyutlanır.** Bu ikisi
yalnızca hiçbir şey gizlemeyen bir zeminde aynı sayıdır, ki öyle bir yer yok
(ADR-0021).

İki olumsuz sonuç silinmek yerine yukarıda kayıtlı. Komşu listesi ikisinin
daha faydalısı: makul, ucuz, gerçekçi kulağa gelen ve burada işe yaramayan
bir mekanizma; onu düşünecek bir sonraki kişi bunu bir öğleden sonrada değil
bir paragrafta öğrensin.

Yaklaşık %90'ı geçmek para gerektiriyor — yukarıdaki tabloya göre kabaca iki
katı direk sermayesi — ya da açık arazi üzerinde bir dikdörtgen yerine bir
yolu izleyen bir yolculuk. İkincisi henüz mümkün değil: bu zemini getiren
makineden OpenStreetMap'e erişilemiyor, dolayısıyla paketteki hiçbir saha yol
geometrisi taşımıyor ve her kırsal yolculuk orada ne varsa onun üzerinde
gidiyor. Gerçek bir güzergâh bu değeri yeniden yükseltirdi ve biri getirilene
kadar kırsal satır, varsayılmak yerine yazılmış bir sebeple ihtiyatlıdır.
