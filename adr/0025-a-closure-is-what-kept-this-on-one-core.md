# ADR-0025: bunu tek çekirdekte tutan şey bir kapanıştı

## Durum

Kabul edildi.

## Bağlam

Bu projede yavaş olan her şey aynı biçimdedir: birbirine bağlı olmayan
onlarca senaryo koşusu. Tablo üçtür. Hata ayrıştırması satır başına on
altı, yani kırk sekiz. Bir kırsal yerleşim araması otuz altıdır. Her
koşu onlarca saniyedir ve hepsi tek bir çekirdeğe sıraya diziliyordu,
diğer üçü boş otururken.

Engel işin tasarımı değildi. Her arazi kurucusundaki bir satırdı.
`Terrain.elevation_m` bir kapanış tutuyordu — `lambda x, y: elevation_m`
ya da bir sahayı yakalayan bir `def elevation` — ve bir kapanış bir süreç
sınırını geçemez. `Road` aynısını `graded_alignment` üzerinden yapıyordu;
o da örneklenmiş bir kesit üzerine kapanan bir `surface` işlevi
döndürüyordu. Yani bir `Scenario` turşulanamıyordu, dolayısıyla onu tutan
hiçbir şey bir işçiye verilemiyordu.

Bu, büyük sonucu olan küçük bir gerçekleştirme ayrıntısıdır ve hiç
yüzeye çıkmamıştı çünkü hiçbir şey denememişti.

İkinci bir şey daha vardı ve onu bir sınama değil kullanıcı buldu.
`yerkon solve`, senaryo başına sabit yazılmış kısa bir figür listesini
arıyordu; yani sayfa değerleri yeniden ayarlayabiliyor ama aramaya hangi
figürlerin gireceğini hiç seçemiyordu. Başkasının yazdığı bir arama
uzayı bir araç değil bir menüdür — ve komut satırı hep `--vary`
alıyordu.

## Karar

**Kapanışları küçük çağrılabilirlerle değiştir.** `Level`, `Rolling`,
`Sloping` ve `Fetched`, `__call__` taşıyan donmuş veri sınıflarıdır;
`Alignment` ise yol boyunca uzaklığa göre geri okunan yol kesitidir.
Turşulanırlar, dolayısıyla bir `Scenario` turşulanır, dolayısıyla iş
dağılır. Ayrıca kapanışların yapmadığı bir şeyi yaparlar: yazdırılır ve
karşılaştırılırlar.

**`yerkon.parallel.spread` bağımsız işleri çalıştırır.** Onu üç kural
biçimlendirir ve her biri bir cevabı sessizce değiştirmemenin bir
yoludur:

*Sonuçlar gittikleri sırayla geri gelir.* Bir ayrıştırma, koşuları hata
kaynaklarına konuma göre eşler; onları tamamlandıkça geri veren bir
havuz, bir kaynağın koşularını bir başkasına yazardı ve her figür makul
ve yanlış olurdu.

*Bir işçi tohumunu senaryodan alır.* `run_scenario` zaten
`Scenario.seed`'den yeniden tohumlar, yani bir koşu makinenin değil
düzenin bir özelliğidir. Paylaşılan bir üreteçten çeken herhangi bir şey,
yayımlanan her figürü kaç çekirdeğin boş olduğuna bağımlı kılardı.

*Makineye bir çekirdek bırakır.* Bir arama, başlatıldığı görüntüleyiciyi
kullanılamaz hale getirmemelidir ve tek bir iş asla bir havuz başlatmanın
bedeline değmez.

Havuzun hiç başlayamadığı yerde — bir kum havuzu, donmuş bir yapı,
tutamağı tükenmiş bir makine — işleri burada çalıştırır. Yavaş, bozuktan
iyidir.

**Arama uzayı sayfada kurulur.** Ayarlar dosyasındaki herhangi bir figür
bir aramaya eklenebilir, ondan çıkarılabilir ya da yeniden ayarlanabilir;
motor anahtarı zaten doğruluyor ve karşılığı olmayanı reddediyordu.
Senaryo başına kısa liste, hep olması gerektiği şeye dönüştü: önerilen
bir başlangıç noktası, değiştirilmesi bir tık uzakta.

**Ve çalışma kendini yazıyor.** `yerkon deliver` dört Markdown dosyası
üretir — satırlar ve altlarındaki zemin, hata bütçesi, her figür ve neye
dayandığı, onun yerine kurulabilecek yerleşimler — çünkü bu projenin
*amacı* 15. sayfadaki blok ve arkasındaki savdır; şimdiye kadar bunların
tamamı bir uçbirimde ya da bir tarayıcı sekmesinde yaşıyordu. Ayrıştırma
atlanabilir, çünkü açık ara en yavaş parçadır ve tabloyu tazeleyen
birinin onu beklemesi gerekmez.

## Sonuçlar

Dört çekirdekte, üçünü kullanarak:

| | önce | sonra |
|---|---|---|
| `yerkon table` | ~4 dk | 71 sn |
| `yerkon budget --only tunnel` | 82 sn | 43 sn |
| kırsal arama (36 aday) | ~25 dk | ~9 dk |

Her figür seri koşuyla birebir aynıdır — varsayılmadı, denetlendi ve
artık bir sınama: aynı senaryo iki süreçte ve burada çalıştırıldığında
kullanılabilirlik ve her iki yüzdelik üzerinde anlaşmak zorunda.

Hız, saatin söylediğinden çok daha önemli. Yarım saat süren otuz altı
adaylı bir arama, insanın bir kez çalıştırıp kabul ettiği aramadır;
dokuz dakikada ise farklı hedeflerle üç kez çalıştırdığı arama olur.
Sayfadaki `--vary` kutuları da tam aynı anda ve aynı sebeple işe yarar
hale geldi.

Değişmeyen şey: iş hâlâ her adayın tam olarak benzetilmesidir. Buradaki
hiçbir şey daha hızlı bir model değildir ve birkaç koşuya uydurulmuş bir
vekil model yine aynı şeyin ikinci bir modeli olurdu (ADR-0023).
