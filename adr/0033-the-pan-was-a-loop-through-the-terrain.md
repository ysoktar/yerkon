# ADR-0033: kaydırma, araziden geçen bir döngüydü

## Durum

Kabul edildi.

## Bağlam

Sahneyi sürüklemek titriyordu. Her zaman değil — döndürmek pürüzsüzdü,
kaydırmak değildi.

Tahmin edilmedi, ölçüldü: düzgün bir sürükleme sırasında tuvali ardışık
karelerde yakala ve farklarını al. Düzgün bir hareket her pikseli biraz
değiştirir, dolayısıyla fark düz olmalıdır. Döndürme 9,4 / 9,5 / 9,6 /
9,7 verdi; hafifçe yükselen. Kaydırma 9,8 / 5,7 / 9,6 / 5,7 / 9,2 / 4,4
verdi — temiz bir iki adımlı çevrim; yani sahne dönüşümlü karelerde ileri
gidip geri sıçrıyor.

ADR-0029'un düzeltmesi kameranın dayanak noktasını altındaki zemine
koydu; döndürmenin sahayı ekranın önünden savurmak yerine bir şeyin
etrafında yürümek gibi hissettirmesinin sebebi budur. Bu, kimsenin
bakmadığı bir döngüyü kapadı:

- dayanak noktasının yüksekliği altındaki zeminden gelir;
- göz, dayanak noktasından sabit bir kaydırmayla oturur, yani dayanak
  noktasının yüksekliği gözü kımıldatır;
- kaydırma, imlecin ışınının zeminle **gözden** nerede kesiştiğini sorar;
- ve kaydırma dayanak noktasını kımıldatır.

Gerçek engebe üzerinde bu döngünün kazancı birin üzerindedir, dolayısıyla
çınlar.

Önce zemin yüksekliğini aradeğerlemek denendi; en yakın örnek araması —
yedi yüz metre genişliğinde bir merdiven — her basamakta yerel olarak
sonsuz kazançlı diye. Düzeltmedi: 8,8 / 4,5 / 8,8 / 4,4. Kararsızlık
nicemleme değil, döngünün kendisi.

## Karar

Bir kaydırma, sonraki her imleç konumunu, zemin yakalandığı andaki
kameraya karşı okur. O zaman dayanak noktasından kaydırmaya geri dönen
bir yol kalmaz ve döngü biter: 6,7 / 6,7 / 6,5 / 6,3 / 6,4; bir döndürme
kadar düz.

Katı bir sürüklemenin anlamı da budur. Hareketin verdiği söz, tuttuğunuz
noktanın imlecin altında kalacağıdır ve bunu doğru kılan piksel–zemin
eşlemesi, ona tutunduğunuz anda ekranda olan eşlemedir.

Aradeğerleme kalıyor, çünkü bir merdiven, başka ne olursa olsun bir
zemin yüksekliği için yanlış biçimdir: dayanak noktasını, sürüklenen
direği ve kapsama hücrelerini aynı şekilde basamaklandırıyordu.

## Sonuçlar

Kaydırma pürüzsüz ve dayanak noktası hâlâ zemin üzerinde gidiyor.

Bedeli: uzun bir kaydırma engebeyi geçerken göz zeminle birlikte
yükselip alçalır, dolayısıyla yakalanan nokta imleçten, geçilen engebe
kadar kayar. Bu, alternatifle aynı büyüklüktedir — hareket boyunca
dayanak noktasının yüksekliğini dondurup bırakışta yeniden oturtmak —
ama sonunda sıçramak yerine sürükleme boyunca yumuşakça yayılmış hâli.

Tutmaya değen kısım yöntemdir. "Titriyor", kimsenin üzerine hareket
edebileceği bir hata bildirimi değildir ve bunun için kodu okumak dayanak
noktası değişikliğini bulup ona doğru derdi ki doğrudur. Ardışık
karelerin farkını almak onu dönüşümlü bir sayıya çevirdi ve dönüşümlü bir
sayı kendi sebebini adlandırır: bir geribesleme döngüsü; bir yeniden
çizim hatası, bir sıralama düzeni ya da bir indirme değil.
