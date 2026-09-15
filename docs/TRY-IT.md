# Son çalışmaları denemek

Aşağıdaki her şey `claude/3d-localization-benchmark-bm3unn` dalında.
Her adım bir şeyi gösterecek şekilde sıralandı ve yavaş olanlar ne kadar
yavaş olduklarını söylüyor.

```bash
git pull
pip install -e ".[dev]"
```

Buradaki hiçbir şey ağ gerektirmiyor. Tablonun üzerinde durduğu zemin
paketin içinde işlenmiş durumda. Tek istisnası **kendi bölgeni eklemek**;
onun için `pip install -e ".[dev,sites]"` gerekiyor ve o bölüm aşağıda.

Windows'taysan `docs/WINDOWS.md`'ye bak: PowerShell 5.1 üç yerde bash'ten
ayrılıyor ve üçü de bu komutları kırıyor.

**Acelen varsa:**

| ne istiyorsun | nereye git |
|---|---|
| gönderilen sayıları görmek | [Tablo](#tablo) |
| resmi görmek, sayıları oynatmak | [Buradan başla: uygulama](#buradan-başla-uygulama) |
| **kendi bölgende sayı üretmek** | [Kendi bölgeni ekle](#kendi-bölgeni-ekle) |
| neyin yanlış olduğunu bulmak | [Nereden itiraz etmeli](#nereden-itiraz-etmeli) |

---

## Buradan başla: uygulama

```bash
yerkon view
```

**Ana giriş arayüz** — komut satırının yaptığı her şeyi sayfa da yapar ve
gönderilen varsayılanlara değil sayfanın gösterdiği ayarlara karşı koşar.

### İki dil (bu yeni)

Arama kutusunun yanında **TR / EN**. Her şeyi değiştirir: panel, yetmiş
iki değerin notları ve neyi etkiledikleri, zeminin kendi açıklaması, hazır
seçeneklerin gerekçeleri, çözücünün çıktısı ve uzun bir iş sürerken
akan ilerleme kütüğü. Hiçbir sayı, hiçbir geometri
ve hiçbir sonuç ikisi arasında farklı değil; bunu bir test bütün tabloyu
iki kez kurarak söylüyor (ADR-0035).

Denemeye değer: EN'e geç, **Basis**'i aç ve değerlerin gerçekte ne
dediğini oku. Sonra geri dön ve aynı değerin Türkçe de aynı şeyi
söylediğini kontrol et.

Henüz iki dilli *olmayan* ve sayfanın aksini iddia etmediği kısım:
tablonun satır adları ile sütun başlıkları, Markdown teslimlerinin içeriği
ve komut satırının kendisi. Bunlar raporun kendi sözleridir ve yalnızca
Türkçedir. Bir sahanın künye notları da öyle: onlar o günkü indirmenin
kaydıdır, sayfanın ayarı değil (ADR-0035).

### Panel (bu yeni)

Altı adım, taze bir alan için birinin gerçekten çalıştığı sırayla; her
biri o an ne tuttuğunu söyleyen tek bir satıra kapanıyor:

    1 YER       kizilay · ölçülmüş zemin
    2 SAHA      3,0 km × 3,0 km alan
    3 YERLEŞİM  49 direk · 1 grup · 2 alıcı
    4 HEDEF     ±5,0 m · TR · tek yönlü
    5 DAYANAK   72 değerin 35 tanesi varsayım
    6 ÇALIŞTIR  üç satır ve ağırlıklı ortalama

Aynı anda biri açık. **Sonuç** alta sabitlenmiş ve hiç kaymıyor, yani bir
kontrolü değiştirip ne yaptığını görmek iki hareket değil bir hareket.

Denemeye değer:

- **Arama kutusuna yaz** (ya da `/` tuşuna bas). Her kontrolü ve yetmiş
  iki değerin hepsini kapsıyor. Türkçe katlanıyor, yani `gurultu`
  *gürültü katsayısı*'nı, `olcum` da ölçüm olanları buluyor. Yalnızca
  isabet içeren adımlar açılıyor.
- **Her sürgünün yanında artık bir sayı var.** *Direk aralığı*'na 4000
  yaz — adımı 500 olan bir sürgüye bu verilemezdi. Sayı, bilerek sürgünün
  uçlarını da geçebilir.
- **Dayanak'ı aç ve *Yalnız varsayımları göster*'i işaretle.** Yetmiş
  ikinin otuz beşi. Her değer Türkçe adlandırılmış, `defaults.toml`
  anahtarı imleci üstüne getirince, ve değerin nereden geldiğini gösteren
  renkli bir nokta var. Direk maliyeti (85 000 TL) bir öğleden sonraya
  değen tek değer.
- **Kırsal sekmesinde *Boy*'u aşağı çek.** Artık direk grubuna ne
  yapacağını yapmadan önce öneriyor.

### Gezinme (bu bozuktu)

Kamera yalnızca sabit bir noktanın etrafında dönebiliyordu ve her
düzenleme onu yeniden ortalıyordu, yani kaydırmanın anlamı yoktu.

- **Sürükle** döndürür.
- **Sağ tık**, orta tık ya da **Shift+sürükle** zemini kaydırır. Tuttuğun
  nokta imlecin altında kalır. *Bu eskiden titriyordu* — sürükleme
  sürdüğü sürece sahne ileri gidip geri sıçrıyordu. Eksen zemine biner,
  zemin gözü oynatır, göz imlecin değdiği yeri oynatır, o da ekseni
  oynatır: kazancı birden büyük bir döngü. Kaydırma artık imleci, zemini
  tuttuğun andaki kameraya karşı okuyor (ADR-0033).
- **Tekerlek** *imlece doğru* yaklaşır, tekerleğin gerçekte ne kadar
  döndüğüyle ölçeklenerek — touchpad süzülür, fare çentiği adımlar.
- **W A S D** / oklar kameranın baktığı yöne yürür. Shift hızlandırır.
- **Q** / **E** döndürür. **R** / **F** eğer. **+** / **−** yaklaştırır.
  **G** her şeyi çerçeveler.
- Bir direği sürükle: artık tek bir düz düzlemi değil araziyi izliyor.

Bir görüş kur, herhangi bir sürgüyü değiştir ve kameranın *yerinde
kaldığını* kontrol et. Düzeltme budur.

Burada üç şey daha değişti ve her biri doğrudan bakmaya değer:

- **Resim kare başına bir kez çiziliyor.** Eskiden her fare olayında
  çiziliyordu ve bir touchpad, bu sahnenin çizilebileceğinden çok daha
  hızlı bildiriyor — yani sürükleme sürdüğü sürece kuyruk büyüyor ve
  görüntü elin arkasından geliyordu. Matematik baştan sona doğruydu.
- **Kameranın etrafında döndüğü nokta artık zemine biniyor.** Kırsal
  satırın dört yüz elli metrelik rölyefi boyunca kaydır, sonra döndür:
  tepenin altına gömülü bir eksenden sahayı ekranın önünden geçirmek
  yerine baktığın şeyin etrafında dönüyor.
- **Yaklaşmak artık tepeyi gösteriyor.** Saha ağı bütün sahaya yayılmış
  birkaç bin örnek, ki yirmi kilometrede bu her yedi yüz metrede bir
  demek — yakından bu düz bir yeşil duvardı. Yaklaşınca motordan aynı
  bütçe ekrandaki pencere için isteniyor, altmış metreye kadar; ki bu da
  alttaki 30 m yükseklik modelinin sınırına yakın. Hiçbir şey
  uydurulmuyor: benzetimin çağırdığı `height_at`'ın kendisi (ADR-0031).

Onlarla birlikte iki çizim hatası da gitti, ikisi de aynı sebepten
(ADR-0030). Yol, çiziciye tek bir mesafesi olan tek bir şekil olarak
veriliyordu, dolayısıyla ortalama mesafesinden yakın her tepe onun
tamamının üzerine boyanıyordu — kırsal turun yarısı görünmüyor, sağ kalan
yarısı da alan yerleşimini bir tarlaya çizilmiş çizgi gibi gösteriyordu.
Ve ağ, sahanın oranları ne olursa olsun sabit yüze kırktı; yani yirmi
kilometreye yirmi kilometre bir yönde her 460 m'de, diğer yönde her 1100
m'de örnekleniyordu: zemin çizgi çizgi çıkıyordu.

### Okunmayan değerler kilitli (bu bozuktu)

**Zemin**'den ölçülmüş bir yer seç. *Tepe yüksekliği*, *tepe aralığı* ve
*yüzey pürüzü* griye döner ve artık değişmez — sürgüsü de yanındaki sayı
kutusu da. Eskiden yalnızca sürgü kilitleniyordu; kutuya 700 yazmak
kabul ediliyor, ekranda görünüyor ve hiçbir şeyi değiştirmiyordu, çünkü
zemin ölçülmüştü (ADR-0036).

**Tünel** sekmesinde zemini *Modellenmiş*'e çevir: üçü kilitli kalır. Bir
tünel tepenin içinden geçer, üzerinden değil; tabanı iki portal
arasındaki düz çizgidir ve bu üç değer o satırda hiç okunmaz. Bu hiç
doğru çizilmemişti.

*Engel kaybı* kilitlenmez ve kilitlenmemeli: ölçülmüş zemin bina ve ağaç
getirmez, o yüzden o değer hâlâ okunuyor.

### Çalışma yalnızca indirilen bölgede (bu bozuktu)

Bir yer indir, sonra **Boy**'u ya da **En**'i indirdiğin kutudan büyük
yapmayı dene: sürgü artık o kadar ileri gitmiyor, kutuya yazarsan da
onay paneli sayıyı geri getiriyor ve neyin kımıldadığını gösteriyor.
Daha küçük bir **Zemin** seçmek de aynı kapıdan geçiyor: boy, en ve direk
dizileri onunla birlikte içeri çekiliyor.

Sebebi şu: `height_at` ızgarasının dışında kenara kırpar. Sınıra değip
geçen bir link yolu için doğru, bir direk için değil — kenarın ötesinde
kırpma, sınır satırını bir düzleme uzatır ve düzlem bu modelin
çizebileceği en elverişli zemindir. Hazır satırlarda da oluyordu: şehir
içinde 46 direğin 10'u, kırsalda 33'ün 5'i ölçülen ızgaranın dışında
duruyordu (ADR-0037).

Bu tabloyu kımıldattı; sayılar ADR-0037'de yan yana. En çarpıcısı kırsal
kullanılabilirlik: **%89,50 → %72,64**. Kaybolan on yedi puanın tamamı,
ölçülen zeminin 140 m ötesinde duran ve turun uzak kolunu besleyen tek
bir mast sırasından geliyor.

### Satırlar ve dil artık kaçmıyor (bu da bozuktu)

Sekmeler ile TR/EN panelin tepesine sabitlendi. Beşinci adımı aç, yetmiş
iki değerin içine kadar kaydır: ikisi de yerinde duruyor. Eskiden
kaydırıp gidiyorlardı, yani satır değiştirmek için önce başa dönmek
gerekiyordu. Sonuç zaten alta sabitliydi; üst uç atlanmıştı.

### Sahanın iki sürgüsü

**En** ve **Boy** alt alta duruyor ve eskiden tamamen farklı şeyler
yapıyorlardı. En, direkleri ızgarayla kendine kadar yayıyordu; Boy ise
güzergâhı oynatıp otuz altı direği yarısından kısa bir sahanın üzerinde
bırakıyordu, çünkü bir grup kendi başlangıcını ve bitişini taşır
(ADR-0032).

**Boy**'u şimdi aşağı çek; onay paneli direk gruplarına ne yapacağını
yapmadan önce söylüyor:

    İstediğin değişiklik    Sahanın boyu    20000 → 8000
    Bunlar da değişiyor     Grubun bitişi   20000 → 8000

Hayır de, hiçbir şey oynamasın. Bir gruba elle bitiş yazmak hâlâ senin:
yalnızca sürgü kesiyor.

### Zemin

**Zemin**, yerleşimin neyin üzerinde durduğunu seçer. Paketle dört gerçek
Ankara yeri geliyor:

| saha | nedir |
|---|---|
| `kizilay` | şehir — 3 km'de 91 m rölyef, 5 231 bina |
| `polatli` | şehirlerarası yolların geçtiği bozkır — 20 km'de 486 m |
| `golbasi` | tepeler — 20 km'de 907 m |
| `kizilcahamam` | tünelin içinden geçtiği dağ |

Ne seçicide ne de rölyef sürgüsünde **düz bir seçenek var**. Hiçbir yer
düz değil ve düz bir düzlem, bu modelin çizebileceği en tarafsız değil en
elverişli zemin.

---

## Kendi bölgeni ekle

Buradaki dört yer Ankara çünkü rapor Ankara'yı soruyor. Sorduğun yer
başkaysa onu getir; dört sahanın geldiği yolun aynısı ve ağa dokunan tek
şey bu.

### Sayfadan (önerilen)

**1 YER → Yeni bir yer getir**, sonra üç şey:

| alan | ne yazılır |
|---|---|
| **Ad** | klasör adı olacak: `konya`, `izmir-ring`. Harf, rakam, tire. |
| **Merkez** | `37.8716, 32.4847` — herhangi bir haritada ilgilendiğin noktaya **sağ tıkla**, koordinat çıkar, yapıştır. |
| **Kutunun boyu** | kaç kilometre. Sürgünün altındaki satır kaç ızgara noktası edeceğini söyler. |

Dört köşe girmiyorsun: haritaya bakan birinin elinde bir iğne ve "şu
kadar etraf" vardır, dört ondalık derece değil. Kutu merkezden kare
olarak kuruluyor — boylam derecesi enlem derecesinden kısa olduğu için
ikisi eşit alınsa kimsenin istemediği bir dikdörtgen çıkardı.

**Izgara aralığı** 30 m'de bırak. Copernicus zaten 30 m; daha sıkını
istemek yeni bilgi getirmez, daha seyreği tepeleri yumuşatır. Satır kaç
nokta olacağını söylüyor: 3 km'de 10 000, 12 km'de 160 000. Yüz binlerin
üstü dakikalar ve kimsenin istemediği bir dosya demek.

**Getir**'e bas. İlerleme kütüğü akar — bu iş için birkaç dakika normal.
Bittiğinde yer **hemen Zemin listesinde** belirir; sonucun altındaki
**bu zemini kullan** düğmesi satırı onun üzerine oturtur ve onay
panelinden geçer, çünkü daha küçük bir yer sahanın boyunu, enini ve direk
dizilerini içeri çeker (ADR-0037).

Sonra **6 ÇALIŞTIR → Simülasyonu çalıştır**. Bulgular artık senin
zeminin.

### Komut satırından

```bash
yerkon fetch --centre 37.8716,32.4847 --size 12 --into konya
```

`--into konya` gibi **çıplak bir ad**, paketin kendi saha klasörüne
yazar — `fetched()` ile zemin seçicisinin baktığı tek yer orası. İçinde
eğik çizgi olan bir şey yol sayılır ve olduğu gibi kullanılır. (Bu ikisi
eskiden aynıydı: `--into konya` kabuğun bulunduğu yere yazıyordu, komut
başarıyla dönüyordu ve saha hiçbir yerde görünmüyordu.)

Komut ne getireceğini önce söyler — kaç km, kaç ızgara noktası — ve
bittiğinde bulguya giden iki adımı adıyla yazar.

Dört köşeyi zaten elinde tutuyorsan `--south --west --north --east` hâlâ
çalışıyor. İkisini birlikte vermek iki farklı kutu tarif ettiği için
reddediliyor.

### Baştan sona bir örnek

Konya, 12 km, iki komut:

```bash
yerkon fetch --centre 37.8716,32.4847 --size 12 --into konya
# 11970 x 11940 m, engebe 334 m; Overture'dan 91 689 bina

# defaults.toml'u kopyala, rural.site = "konya" yap, sonra:
yerkon table --only rural --defaults konya.toml
```

Çıkan satır:

| | HPE P50 | HPE P95 | Kullanılabilirlik | Alan |
|---|---|---|---|---|
| Kırsal, Polatlı'da | 3,11 m | 15,09 m | %72,75 | 218,75 km² |
| Kırsal, Konya'da | **2,59 m** | **7,62 m** | **%100,00** | 62,50 km² |

Aynı yerleşim, aynı direkler, aynı telsizler — başka zemin. Polatlı'nın
20 km'de 486 m engebesi bağlantıları kesiyor; Konya ovası kesmiyor. Tablo
bunu sana söyleyemezdi, çünkü tabloda yalnızca Polatlı var. Kendi
bölgeni eklemenin bütün anlamı bu.

### Ne getiriliyor

**Zemin**: Copernicus DEM 30 m, doğrudan genel nesne deposundan. Karo
başına yüz megabayt ve diske alınıyor, yani aynı derece karesindeki
ikinci bir yer bedava.

**Binalar**: sırayla iki kaynak — önce Overture Maps, sonra
OpenStreetMap. Overture, OpenStreetMap artı Microsoft ve Google'ın
makineyle çıkarılmış taban alanlarından kurulur: başka bir ölçüm değil,
aynı verinin daha doldurulmuş hâli. Önemli olan yol: Overpass bir sorgu
servisi ve pek çok ağ onu reddediyor (benimki de ediyor), Overture ise
Copernicus karolarının geldiği türden bir nesne deposundan menzilli
okuma. İlk cevap veren kazanır, cevap vermeyen künyeye yazılır
(ADR-0038).

İlk indirme Overture'ın 512 dosyasının künyesini tarar — bir dakika. O
dizin sürüm başına diske yazılır, yani ikinci bölge bu bir dakikayı
ödemez.

### Getirdikten sonra ne değişir

Bunları bilmeden bakarsan sayıların "yanlış" göründüğü yerler:

- **Saha, indirdiğin kutudan büyük olamaz.** Kutu 5 km ise saha 5 km.
  Sürgüler o sınırın ötesini sunmaz; ötesinde ölçüm yok, yalnızca sınır
  satırının bir düzleme uzatılmışı var (ADR-0037).
- **Zemin bina getiriyorsa engel kaybı sürgüsü griye döner.** Engel artık
  arazinin içinde; ikisini birden saymak aynı binaları iki kez saymak
  olurdu (ADR-0038).
- **Tepe yüksekliği, tepe aralığı ve yüzey pürüzü de griye döner.**
  Ölçülmüş zemin kendi rölyefini ve kendi pürüzünü getirir.
- **Alan sütunu küçülebilir.** Kapsama taraması da ölçümün dışına
  çıkmıyor, dolayısıyla hizmet alanı sahadan büyük çıkamaz.

### Bir bölge eklemek neyi sınamaz

Getirdiğin zemin gerçek, ama **yol geometrisi yok**: kırsal yolculuk
zemini izleyen bir yol değil, zeminin üzerinde bir dikdörtgen tur. Ve
Copernicus bir **yüzey** modeli, çıplak toprak değil — 30 m adımda
binaları bir ölçüde zaten içeriyor, dolayısıyla Overture yüksekliklerini
üzerine katlamak bina yüksekliğini kısmen iki kez sayıyor olabilir. Ne
kadarını söyleyecek olan aynı bölgenin çıplak toprak modeliyle
karşılaştırılması ve o yapılmadı (ADR-0038).

---

## Uygulamanın geri kalanı

### Üç sekme, üçü birden tutuluyor

**Şehir içi · Kırsal · Tünel.** Her sekme hazır bir yerleşim tutar;
aralarında geçmek kurduğunu atmaz. **Çalıştır → Hangi satırlar** altından
ya üzerinde olduğun sekmeyi (bir satır) ya da üçünü birden koşarsın —
üçü artı ağırlıklı satır çıkar.

Bir koşu **sekmedeki düzeni** kullanır, gönderilen kataloğu değil — bir
direği sürükle, koştuğun tablo bunu yansıtsın.

**En** sahanın bir çizgi mi bir alan mı olduğuna karar verir: sıfırda
direkler bir yolun kenarına dizilir ve birimler düz gider; sıfırın
üstünde kaydırmalı bir ızgaraya yayılır ve birimler bir tur atar. Şehir
içi ve kırsal alan olarak, tünel çizgi olarak açılır.

### Yerleştirme yöntemi (bu yeni)

Her direk grubunun kartında artık bir **Yerleştirme** listesi var. Sekiz
yöntem, dört aile — ve amaç birer tane verip geçmek değil: bir yöntemin
ne yaptığı ancak yanında başkası varken görülüyor.

| aile | yöntem | ne yapar |
|---|---|---|
| kafes | **Kare ızgara** | bugüne kadarki tek yöntem; her şeyin karşılaştırıldığı taban |
| kafes | **Altıgen kafes** | bir alanı en az direkle örter (Kershner, 1939) |
| kafes | **Yol boyunca** | güzergâh üzerinde, iki yanda dönüşümlü |
| kafes | **Çevre** | yalnızca sahanın kenarında |
| arama | **En çok zemin örten** | klasik kapsama açgözlüsü (MCLP) |
| arama | **En iyi geometri** | seyreltmeye (HDOP) göre seçer |
| arama | **Her noktaya yeter direk** | k-örtme; bir konum üç menzil ister |
| — | **Elle** | hiçbiri; boştan başla |

**Denemeye değer olan şu.** Şehir içi sekmesinde listeyi sırayla değiştir
ve **Direk sayısı** ile **Konum sıklığı**na bak:

| yöntem | direk | tur süresi | konum sıklığı |
|---|---|---|---|
| Kare ızgara | 36 | 509 ms | 1,96 /s |
| Altıgen kafes | 42 | 509 ms | 1,96 /s |
| **En iyi geometri** | **3** | 191 ms | 5,24 /s |
| **En çok zemin örten** | **1** | 64 ms | 15,72 /s |

Kapsamaya göre seçen arama **tek bir direk** koyuyor. Yanlış değil:
Kızılay'da bir direğin erişimi 3825 m ve saha 2970 m, yani bir tanesi
gerçekten bütün sahayı örtüyor. Ama bir direkle hiçbir yerde konum
alınamaz — bir konum üç menzil ister. Geometriye göre seçen arama üçünü
koyuyor ve her yerde konum çıkıyor.

Kapsama, haberleşme ağının ölçütü. Konumlandırma ağının ölçütü geometri.
İkisini yan yana koymak bu farkı iddia etmek yerine ölçülebilir yapıyor
(ADR-0040).

**Arama yöntemlerinde sürgüler değişiyor:** aralık yerine bir çıta
(*Hedef HDOP*, varsayılan 2) ve bir bütçe (*En çok direk*). Arama çıtada
duruyor, bütçede değil — çıtası olmayan bir arama kendisine verilen
bütçeyi döndürür, çünkü bir direk daha her zaman biraz iyileştirir.

### Her sayı, canlı

**Varsayılan değerler** paneli artık eskiden kodda birer sabit olan *on
altı yerleşim değerini* tutuyor — direk aralığı, saha uzunluğu, kaydırma,
tur başına yoklanan direk, menzil toleransı, tünel genişliği — artı zemin
yaması kontrollerini. Bir sürüm boyunca sayfaya gönderiliyorlardı ama
altlarına çizilecekleri bir başlık yoktu, yani mevcut, doğru ve
görünmezdiler. Artık oradalar.

`<satır>.site`, gerçekten getirilmiş sahaların bir seçicisi olarak
çiziliyor.

### Çalıştırma (Çalıştır)

| düğme | ne yapar | ne kadar sürer |
|---|---|---|
| **Tablo** | rapor satırları | üçü birden ~70 sn |
| **Hata dağılımı** | hata dağılımı, çubuk olarak çizilmiş | üçü birden ~4 dk |
| **Markdown olarak yaz** | bütün çalışmayı dosyalara yazar | yalnız tablo: ~70 sn |

Hızlandırmak için **Hangi satırlar**'dan tek bir satır seç. Koşarken satır
satır bildirirler.

### Çözücü

Bir hedef koy — bir kutuyu boş bırakırsan koşul sayılmaz — ve **onu
karşılayan en ucuz düzeni** arasın, en iyisini değil. **Sayı ekle**
altından *hangi* değerlerin aranacağını ve hangi değerlerin deneneceğini
sen seçersin; senaryo başına kısa liste bir menü değil, bir başlangıç
noktası.

Denemeye değer, çünkü kimsenin bulmadığı bir şey buldu:

- Senaryo `tunnel`, HPE P50 ≤ 1,0, kullanılabilirlik ≥ 0,99
- 120 m askı aralığını buluyor: **1,77 m → 0,48 m**, yaklaşık 23000 TL'ye.

**Kaydedilecek ad** altından bir ad ver, listenin sonra sunacağı bir
seçenek olarak kaydetsin.

---

## Terminalden

```bash
yerkon table                  # dört satır              ~70 sn
yerkon budget                 # hata dağılımı           ~4 dk
yerkon budget --only tunnel   #                         ~45 sn
yerkon options                # adlandırılmış yerleşimler
yerkon options rural-dense    # birini tam olarak
yerkon table --option rural-hard-ground     # aynı kırsal satır, tepelerde
yerkon solve --scenario tunnel --hpe-p50 1.0 --availability 0.99
yerkon deliver --into docs/teslim --no-budget   # çalışma, Markdown olarak
yerkon defaults --full        # her değer ve neye dayandığı
```

Her şey makinenin ayırabildiği kadar çekirdekte koşar — sahip olduğundan
bir eksik, böylece görüntüleyici kullanılabilir kalır. `yerkon table`
bundan önce dört dakikaydı, şimdi yetmiş saniye.

---

## Neye bakmalı ve neye mal oldu

### Tablo

| | HPE P50 | HPE P95 | Kullanılabilirlik |
|---|---|---|---|
| Şehir içi | 2,14 m | 5,36 m | %99,79 |
| Kırsal | 3,11 m | 15,09 m | %72,75 |
| Tünel | 1,77 m | 2,99 m | %100,00 |
| Ağırlıklı | 2,37 m | 9,76 m | %83,36 |

Kırsal satır ADR-0037'den önce %89,50 diyordu. Aradaki fark, ölçülmemiş
zeminde duran bir mast sırasıydı. Şehir içi satır ADR-0038'den önce 1,79
m diyordu; aradaki fark, artık gerçekten orada duran 5 231 bina.

### Kendin denemeye değer beş bulgu

**Tünel, en iyi donanıma rağmen en az hassas satır.** `yerkon budget
--only tunnel` koş. Şehirden yirmi dokuz kat daha iyi ölçüyor ve daha iyi
konumlamıyor, çünkü bir tünel bir menzilin hatasını on sekizle çarpıyor ve
en sert çarptığı şey direk etüt hatası — ortalamayla asla kaybolmayan tek
terim. Askıları düzgün ölçmek o satırı 1,77 m'den 0,17 m'ye indiriyor.
Daha iyi bir telsiz hiçbir şey satın almıyor.

**Tur boyunun ne ettiği artık ölçülemiyor, ve bu bir bulgu.** Tek bir
kırsal bağlantı bile mesafe yüzünden düşmüyor — her başarısızlık yoldaki
zemin; orası değişmedi. Değişen, "sekiz yerine on iki direk yoklamak 5,5
puan eder" cümlesi: yalnızca indirilmiş zemin üzerinde koşulduğundan beri
(ADR-0037) iki tohum üzerinde ölçüm şöyle:

| tur başına | tohum 202 | tohum 404 |
|---|---|---|
| 6 | %65,50 | %65,47 |
| 8 | %73,41 | %69,94 |
| 10 | %69,23 | **%74,75** |
| 12 | %72,64 | %72,19 |
| 16 | **%74,33** | %72,51 |

Altı açıkça az: yoklananın yarısı cevap vermiyor, altı deneme üç yanıt
veriyor ve bir konum dört istiyor. Sekizin üstünde sıralama tohumla
dönüyor ve komşu değerler arasındaki fark tohumlar arasındaki kadar. On
iki, tek bir tohumla değiştirmemek için duruyor — bu projenin bir kez
yaptığı hata tam olarak buydu. Bir sınama artık kazananı değil, dönüşün
kendisini sabitliyor.

**İki kırsal seçeneğin notları bir kez daha eskidi ve bu, denemeye
değer olanın ta kendisi.** Varsayılan %82,26'da dururken yazılmışlardı;
tur boyu düzeltmesi onu bedelsiz %89,50'ye çıkardı ve satın aldıklarının
çoğu onunla gitti. ADR-0037 ise varsayılanı %72,64'e indirdi — daha küçük
zeminde daha sık bir ızgaranın yeniden değerli olup olmadığı açık bir
soru. `yerkon solve` ile kendin sor; notlarına güvenme.

**Bir eğim kırk kat pürüz sayılıyordu.** %12 eğimde model, zeminin 7 cm'ye
kadar düz olduğu yerde 2,8 m pürüz bildiriyordu. Bunu düzeltmek — ve
yanında gelmesi gereken eğim terimini düzeltmek — tabloyu tohum
gürültüsünden az oynattı, çünkü eski model aynı yere yanlış yoldan
varıyormuş.

**Gönderilen bir seçenek hiçbir şey yapmıyordu.** `rural-hard-ground`,
varsayılanın sayılarını basamağı basamağına üretiyordu. Şimdi `yerkon
table --option rural-hard-ground` dene, kırsal satır çökmeli; öncesinde
hiçbir şeyin okumadığı bir değeri değiştiriyordu.

---

## Nereden itiraz etmeli

- `docs/adr/` — kırk karar, her biri neye mal olduğuyla. Son olanlar
  0030–0040.
- `src/yerkon/defaults.toml` — yetmiş iki değer. Otuz beşi hâlâ vekil;
  85000 TL'deki direk maliyeti, direklerin mi mevcut yol donanımının mı
  kazanacağına karar veren değer.
- `yerkon defaults --full` hepsini, her birinin neyi etkilediğiyle
  yazdırır.

Buradan yapamadığım şey, varsayılmak yerine yazıldı: Overpass kum
havuzumdan erişilemiyor, dolayısıyla OpenStreetMap yolu denenmiş değil —
kaydedilmiş bir Overpass yanıtına karşı sınanıyor ve orada duruyor.
Binalar Overture'dan geldi ve dört saha da onları taşıyor. Yol
geometrisi hâlâ yok: her kırsal yolculuk, zemini izleyen bir yol yerine
zeminin üzerinde bir dikdörtgen.

Bir şey de ölçülmedi ve öyle yazıldı: Copernicus bir **yüzey** modelidir,
çıplak toprak değil, yani 30 m adımda binaları bir ölçüde zaten içerir.
Overture yüksekliklerini üzerine katlamak bina yüksekliğini kısmen iki
kez sayıyor olabilir. Ne kadarını söyleyecek olan aynı bölgenin çıplak
toprak modeliyle karşılaştırılması ve o yapılmadı (ADR-0038).
