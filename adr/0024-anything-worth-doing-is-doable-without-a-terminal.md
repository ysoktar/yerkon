# ADR-0024: yapmaya değer her şey uçbirim olmadan da yapılabilir

## Durum

Kabul edildi.

## Bağlam

Proje her seferinde bir eylemle büyüdü. `table` raporu çalıştırır,
`budget` her satırın hatasını parçalarına ayırır, `solve` yerleşimleri
arar, `options` adlandırılmış olanları listeler, `defaults` figürleri
listeler. Hepsine yalnızca bir kabuktan ulaşılabiliyordu.

Görüntüleyici ise hızlı olan tek şeyi yapabiliyordu: sahneyi çizmek ve
sürgüler hareket ettikçe birkaç sayıyı yeniden hesaplamak. Dakikalar
süren her şey komut satırında kaldı; bu da tasarımı keşfetmesi en olası
kişinin — bir direği kaydıran, bir direği sürükleyen, bir aralık
deneyen kişinin — resmi terk etmesi, neyi değiştirdiğini hatırlaması,
onu bayrak olarak yeniden yazması ve cevabı başka bir yerde okuması
demekti.

Bir figürün kaybolma biçimi de budur. Görüntüleyicinin düzenlemeleri
kendi oturumunda yaşar; başka bir penceredeki `yerkon table` onlardan
habersizdir.

Aynı yerde ikinci bir sorun vardı. Kamera yalnızca sabit bir nokta
etrafında dönebiliyordu. Yirmi kilometrelik bir kırsal bölgede bu bir
kısıt değil, bir duvardır: bir köşeye bakmanın yolu yoktur. Daha kötüsü,
`refreshScene` her yanıtta kamerayı yeniden ortalıyordu; yani hedef bile
elle kaydırılamıyordu — her değişiklik bir sonraki düzenlemeyle geri
alınırdı. Yakınlaştırma her tekerlek olayında sabit yüzde on iki
adımlıyordu; bunu bir dokunmatik yüzey sarsıntıya, bir fare
belirsizliğe çeviriyordu ve imlece değil ortaya doğru
yakınlaştırıyordu, dolayısıyla bir direğe yaklaşmak önce yakınlaşıp
sonra onu aramak demekti.

## Karar

**Uzun işler bir iş parçacığında çalışır ve ilerledikçe bildirir.** Bir
hata ayrıştırması on iki dakikadır; bir tarayıcı çok önce pes eder ve on
iki dakikalık sessizlik bozulmuştan ayırt edilemez. `yerkon.viewer.jobs`
işi başlatır, yazdırdığı satırları toplar ve sayfanın saniyede bir
yokladığı bir kimlik geri verir. Bir başarısızlık, kimsenin bakmadığı
bir uçbirimdeki yığın izi yerine sayfadaki bir ileti olur.

**Her şey sayfanın gösterdiği ayarlara karşı çalışır.** Hazır gelen
varsayılanlara karşı değil. Bir öğleden sonrasını figürleri kaydırmakla
geçiren biri, düzeninin ne tuttuğunu, hatasının nereden geldiğini ve bir
hedefe ulaşmak için neyin gerektiğini, hiçbirini önce bir dosyaya
yazmadan sorabilir. `yerkon.viewer.tasks` dikiş yeridir: o düzenler ve işi
tablonun kurulduğu modüllerin aynısı yapar (ADR-0001).

**Seçenekler üstyazma olarak uygulanır.** Birini seçmek, düzenlemelerini
bir kişinin el düzenlemelerinin yaşadığı yere indirir; böylece onların
işinin yerini almak yerine onunla birleşir ve aynı şekilde geri alınır.

**Kamera hareket eder.** Sağ sürükleme, orta sürükleme ya da basılı bir
değiştirici tuş zemini imlecin altından kaydırır; yakalanan nokta
imlecin altında kalır, ki bu bir dürtme gibi değil bir harita gibi
hissettiren tek kaydırmadır. Tekerlek yakınlaştırması tekerleğin
gerçekte ne kadar döndüğüyle ölçeklenir ve imlece doğru gider. WASD ve
ok tuşları dünyanın eksenleri boyunca değil kameranın baktığı yönde
yürür, çünkü "ileri" ekranda olan demektir. `F` her şeyi çerçeveler; bu,
kaybolduktan sonra insanın ihtiyaç duyduğu tek harekettir — ve kaybolmak,
her yere gidebilmenin bedelidir. Her hareket tuval üzerinde yakalanır,
böylece panele taşan bir sürükleme düğme kalkana kadar çalışmayı
sürdürür.

Çerçeveleme artık bir kez oluyor: ilk yüklemede ve bir kip
değişikliğinde, bir daha asla.

## Sonuçlar

Komut satırı ile sayfa aynı şeyleri yapar ve bir sınama eylemleri adıyla
sayar; böylece bir uçbirime eylem ekleyip sayfaya eklememek başarısız
olur.

Kimse fark etmeden iki sınama da zayıflatılmıştı ve bu ikisini de
buldu. Güzergâh sınaması yalnızca tırnaklı yolları eşliyordu, yani bütün
bir özelliğin ``ask(`/api/job?id=${...}`)`` çağrısı denetlenmeden
geçerdi — tam da yakalamak için var olduğu ölü güzergâh. Ve öbür yönü
hiçbir şey denetlemiyordu: sayfanın çizdiği her düğmeye, kutuya ve
menüye betiğin gerçekten ulaştığı. Canlı görünüp hiçbir şey yapmayan bir
denetim, hiç denetim olmamasından kötüdür.

Bitmiş uç noktaların duman sınaması gerçek bir raporlama hatası da
çıkardı. Tek senaryo istendiğinde tablo, ona birebir eş bir "ağırlıklı
ortalama" satırı yazdırıyordu — tek bir şeyin ağırlıklı ortalaması o
şeyin kendisidir ve onu bir birleştirme vaat eden bir ad altında iki kez
yazdırmak, hiç yazdırmamaktan kötüdür. `build` artık o satırı yalnızca
birleştirecek birden çok yerleşimi olduğunda ekler.

Bunun yapmadığı şey, işi hızlandırmak. Üç senaryo üzerinden bir
ayrıştırma hâlâ on iki dakikadır, çünkü içindeki her figür uydurulmuş bir
modelden değil gerçek benzetimi çalıştırmaktan gelir (ADR-0020). Sayfa
artık bunun olmasını izleyebiliyor, ki bu da mevcut dürüst iyileştirmedir.
