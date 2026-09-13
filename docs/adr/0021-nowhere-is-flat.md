# ADR-0021: hiçbir yer düz değildir ve bir düzlem tarafsız seçenek değildir

## Durum

Kabul edildi.

## Bağlam

Üç senaryonun ikisi `flat_terrain` üzerinde duruyordu. Şehir içi satırı
üzerinde bir engel kaybı değeri olan kusursuz düz bir düzlemdi; tünel satırı
kusursuz düz bir tüneldi. Yalnızca kırsal satırın rölyefi vardı ve 3 km
dalga boyunda 40 m — yumuşak tarım arazisi; kulağa makul gelen bir sayı
olduğu için seçilmişti, herhangi bir yer onu ölçtüğü için değil.

Düz bir düzlem tarafsız, ihtiyatlı, varsayımsız seçenek gibi görünür.
Hiçbiri değildir.

**Bu modelin çizebileceği en elverişli zemindir.** İki ışınlı terim,
uçlar arasındaki zeminden aynasal bir yansıma alır ve bir düzlem üzerinde
her yansıma tam olarak modelin varsaydığı aynasal açıyla varır. Gerçek zemin
o enerjinin çoğunu başka yere saçar. Düz zemin, iki ışınlı modelin en emin
ve en cömert olduğu yerdir.

Ayrıca, dağılımın ölçmek için yeni kurulduğu yedi hatadan birini kuruluş
gereği ortadan kaldırır: bir engelin üzerindeki fazladan yol (ADR-0019,
ADR-0020). Bir düzlem üzerinde hiçbir şey hiçbir şeyi engellemez,
dolayısıyla `excess_path` her satırda tam olarak 0,00 m okuyordu — terim
küçük olduğu için değil, arazi onu üretemediği için. Gerçek Ankara'da
kırsalda 0,41 m, şehirde 0,11 m, tünelde 0,09 m okuyor. Bir model, kendi
zemininin yasakladığı bir terimi ölçemez ve bu model o sıfırı bir bulgu diye
bildiriyordu.

Ve düşey geometriyi yozlaştırır. Düz bir tünelde her direk ve her alıcı tek
bir yükseklikte durur; bu da VPE hakkında bir şey söyleyebilmeye en az
elverişli düzendir.

Ankara düz değil. Merkezi üç kilometrede 91 m iniyor ve çıkıyor. Güneyindeki
açık arazi yirmi kilometrede 907 m tırmanıyor — bu projenin kullandığı
değerin bir mertebe üstü.

## Karar

Ankara'yı getir, paketle gönder ve asla bir düzleme düşme.

Paketin içine, `src/yerkon/site/ankara/` altına üç `yerkon fetch` koşumu
işlendi: şehir için `kizilay`, açık arazi için `golbasi`, tünelin içinden
geçtiği dağ için `kizilcahamam`. Toplamı bir megabayt. ADR-0008 zaten bir
önbellek klasörünün kendi kendine yeten bir eser olduğunu söylüyordu; proje
onu ilk kez ciddiye alıyor ve bu, bir klonun her sayıyı ağ olmadan yeniden
ürettiği anlamına geliyor.

**Bir tünel, kuralı kanıtlayan istisnadır.** Bir tünel, bir yolu arazinin
üzerine örterek kurulamaz, çünkü tepenin üzerinden değil içinden geçer.
`bore_terrain` iki portal arasında düz bir çizgidir — ve *eğimlidir*, çünkü
her karayolu tüneli bir drenaj eğimine göre yapılır. Güzergâh, getirilmiş
dağda boyunca üstünde kaya tutan ve bir karayolu tünelinin yapıldığı yüzde
yarım ile üç aralığına düşen iki kilometrelik bir çizgi aranarak bulundu.
Üstünde 9 ile 156 m arasında örtü tutuyor ve %1,79 düşüyor. O portal
yükseklikleri bir dağın, bir seçimin değil.

**Hiçbir şeyin getirilmediği yerde yedek tepeli zemindir, asla bir düzlem
değil.** Rölyefi ve sırt aralığı `defaults.toml`'da ne iseler o olarak
duruyor — getirilmiş ızgaralardan alınmış ölçümler, MEASUREMENT işaretli ve
Copernicus getirmesine kaynaklanmış — yani yedek uydurulmuş değil
izlenebilir.

`flat_terrain` kalıyor ve docstring'i artık ne olduğunu söylüyor: bir testte
tek bir değişkeni yalıtmak için bir laboratuvar aleti, herhangi bir yerin
tanımı değil. Gönderilen hiçbir şey onu kullanmıyor. Görüntüleyicinin rölyef
sürgüsü artık sıfıra ulaşmıyor ve görüntüleyici bir zemin seçicisi kazandı,
yani gerçek Ankara bir komut satırı getirmesi değil bir tık uzakta.

## Sonuçlar

Tablo oynadı ve kırsal satır iki kez oynadı.

Şehir içi ellinci yüzdelikte 1,24 m'den 1,64 m'ye, kullanılabilirlikte
%100'den %99,11'e gitti: gerçek zemin, bir düzlemin koyamayacağı şeyleri
yola koyuyor.

Tünel diğer yöne oynadı ve sebebi bu ADR'nin konusu olan şey. Düz bir tünel
her direği eksenden 4 m uzakta tek bir yüksekliğe, her alıcıyı başka birine
koyuyordu — tünel boyunca tekrarlanan sabit bir iki ışınlı geometri; ve
sabit bir geometri sabit bir sıfırın içinde oturabilir. Tabanı %1,79
eğimlendirmek o geometriyi tünel boyunca değiştiriyor ve kaybolan
alışverişler %37,7'den %7,8'e, kullanılabilirlik %98,02'den %100'e gitti.
Düz model orada da ihtiyatlı değildi; farklı biçimde yanlıştı.

Kırsal satır bulgunun kendisi ve doğru okumak iki getirme aldı.

Gölbaşı'ndaki tepelere konduğunda — yirmi kilometrede 907 m rölyef — satır
çöktü: %45,28 kullanılabilirlik, alışverişlerin üçte ikisi araziye kurban.
İlk içgüdü ızgaranın fazla seyrek olduğuydu. Değildi:

| Direk aralığı | Direk | Kullanılabilirlik |
|---|---|---|
| 4000 m | 33 | %45,3 |
| 3000 m | 49 | %48,3 |
| 2500 m | 77 | %53,6 |
| 2000 m | 116 | %57,8 |
| 1500 m | 189 | %60,8 |

Beş buçuk katı sermaye on beş puan satın alıyor. Her direği 1,5 km içindeki
en yüksek zemine yerleştirmek sekiz satın alıyor. Hiçbiri bir çözüm değil,
çünkü hiçbiri yanlış olanı ele almıyor: **şehirlerarası bir yol bir dağ
silsilesini bir dikdörtgen üzerinde geçmez** ve yanındaki ağ da geçmez. Bir
vadideki alıcı, kaç direk olursa olsun üstündeki sırtın ardındaki bir direği
göremez.

Yollar daha yumuşak zemini izler — şehirlerin orada olmasının sebebi de
budur — dolayısıyla kırsal satır artık Ankara'nın batısındaki Polatlı
ovasında duruyor: aynı yirmi kilometrede 486 m rölyef, ki bu ildeki
şehirlerarası bir koridorun gerçekten geçtiği zemin. Aynı otuz üç direk aynı
dört kilometrelik aralıkta orada %45,3 yerine **%82,3** kullanılabilirlik
veriyor; yalnızca zemin değişti.

Gölbaşı getirilmiş hâlde ve pakette kalıyor. Bu yerleşimin tasarlanmadığı
arazide neye mal olduğunu söyleyen durumdur ve o sayı, kimsenin yazmadığı
bir dipnotta değil raporda durur.

Düzeltilmeyen tek şey: kırsal yolculuk hâlâ zemini izleyen bir yol değil
zeminin üzerinde bir dikdörtgen. Bu getirmeleri yapan makineden
OpenStreetMap'e erişilemedi, dolayısıyla paketteki hiçbir saha bina ya da
yol geometrisi taşımıyor. Gerçek bir güzergâh her kırsal değeri yeniden
yükseltirdi ve biri getirilene kadar kırsal satır, varsayılmak yerine
yazılmış bir sebeple ihtiyatlıdır.
