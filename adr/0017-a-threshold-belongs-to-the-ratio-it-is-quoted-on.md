# 0017. Bir çözme eşiği, üzerinde verildiği orana aittir

## Durum
Kabul edildi. Bu projenin kendi link bütçesini düzeltir.

## Bağlam
Kalan saat kaymasını ölçmek için bir MATLAB betiği yazmak alıcıyı
benzetmek, alıcıyı benzetmek de onu hangi sinyal-gürültü oranında
benzeteceğini seçmek demekti. Link bütçesi bağlantıların 30,1 dB'lik yayma
kazancından *sonra* −20 dB'ye kadar kapandığını söylüyordu, dolayısıyla
betiğin ilinti sonrası −20 dB'de çalışması gerekiyordu.

İlinti sonrası −20 dB'de hiçbir şey çalışmaz. İlinti tepesi gürültü
tabanının yüzde biridir; bulunacak bir tepe yoktur. İlk işaret buydu.

İkincisi aritmetikti. Modelin iddia ettiği 38,9 km'lik kapanma menzilinde
alınan güç −156,0 dBm'di; en iyi durumda yayımlanmış hassasiyeti −132 dBm
olan bir parçaya karşı. Hiçbir anten düzeni bir telsizin kendisinin yirmi
dört desibel altını duymasını sağlamaz.

Sebebi tek bir satırdı. Bir LoRa veri sayfasının "−20 dB"si, *işgal edilen
bant genişliğindeki* oran üzerinden verilir: gürültü tabanının altında
çalışmak yaymanın satın aldığı şeydir ve değer bunu zaten varsayar. Model
yayma kazancını ekliyor, sonra da aynı değerle karşılaştırıyordu; yani her
bağlantıya otuz desibeli iki kez veriyordu.

## Karar
Bir telsiz, eşiğinin hangi oran üzerinden verildiğini söyler ve kapanma ona
karşı sınanır. `threshold_is_in_band`, LoRa değeri yaymayı zaten varsayan
SX1280 ailesi için `True`; varsayılacak bir yayma olmadığı için çalışma
noktası önsöz birikiminden sonra verilen darbeli telsiz için `False`.

İşlem kazancı hâlâ vardır ve hâlâ önemlidir. İlgili niceliğin gürültü
yoğunluğuna bölünmüş sembol başına enerji olduğu Cramér-Rao sınırına aittir,
kapanma sınamasına değil.

## Sonuçlar
SX1280'in kapanma menzili 38,9 km'den 11,7 km'ye düşüyor. Kenardaki alınan
güç −124,8 dBm; parçanın altında değil üstünde.

Kullanılabilir menzil hiç oynamıyor: 25 m'lik bir direkten 5,52 km, öncesinde
de sonrasında da. Onu belirleyen sınır her zaman ilinti sonrası oranı
kullandı ve her zaman doğruydu. Yanlış olan tek şey, bir bağlantının işe
yaramayı bıraktıktan sonra ne kadar çalışmaya devam ettiğine dair iddiaydı —
yani ADR-0007'nin ayrımının abartılmış yarısı.

Dolayısıyla dört tablo satırı zar zor oynuyor. Bir yerleşimin içindeki her
bağlantı zaten 11,7 km'nin epey içindeydi ve düzeltilmiş model cevabı şurada
burada onda bir metre değiştiriyor. Ciddi biçimde yanlış olan şey, kimsenin
kullanmadığı şeydi.

İki iddia geri çekiliyor. "Erişmek ölçmek değildir" yedi kattı, iki kat.
Ve artık hiçbir yasal yapılandırma altmış kilometrelik aramayı geçmiyor;
eskiden en yüksek sesli olan geçiyordu.

Bir bulgu geri çekilmek yerine yeniden kuruldu. Yumuşak rölyefin düz zemini
yendiği iddiası, ona denk gelen tek bir mesafeye dayanıyordu. Bir koridor
boyunca tarandığında rölyef bir takas: düz zemin her mesafede kapanıyor ve
medyan hatası 5,63 m; on metre rölyef bunların %72'sinde kapanıyor ve medyanı
3,08 m; seksen metre %17'sinde kapanıyor. Rölyef sağ kalan bağlantıları
iyileştiriyor ve çukurdakileri öldürüyor.

Benzetim artık bütçeyle uyuşuyor ve önemli olan denetim budur: frekans
kayması kestiricisi ilinti sonrası +10 dB'den yukarıda çalışıyor ve ilinti
sonrası +10 dB, düzeltilmiş eşiğin bağlantının kenarını koyduğu yerin ta
kendisi.
