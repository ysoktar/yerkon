# YERKON simülasyonunun bağlamı

Bu depo, YERKON donanımından kurulan karasal bir konumlandırma ağının
gerçekte ne vereceğini ve neye mal olacağını kestirir. Tek çıktısı,
başvurudaki karşılaştırma tablosunun YERKON bloğudur: üç satır, on sütun;
her sayı ya bir veri sayfasına, ya yayımlanmış bir ölçüme, ya bir standarda
ya da açıkça söylenmiş bir varsayıma kadar izlenebilir.

## Sözlük

Bu terimleri tam olarak böyle kullan. Raporda belirsiz kalan bir terim için
bu dosya bir anlam seçer ve kod ona uyar.

Her terimin başlığında **kodun kullandığı İngilizce ad** durur; kod
İngilizcedir ve bu dosyanın işi tam olarak Türkçe raporla o adlar arasında
köprü olmaktır. Parantez içindeki Türkçe karşılık, raporun ve arayüzün
kullandığıdır.

**Simulation** (simülasyon): bu deponun yaptığı iş. Türkçesi her yerde
*simülasyon*; *benzetim* de doğru bir karşılıktır ama site bir yerde
"Benzetim", bir yerde "Simülasyon" yazıyordu ve aynı şeyin iki adı
vardı. Tek ad seçildi (ADR-0071).

**Anchor** (direk, raporda *yayın birimi*): ölçülmüş bir konumda duran
sabit verici. Üç ürün çeşidi vardır ve birbirinin yerine geçmezler, çünkü
her biri farklı bir telsiz taşır.

**Receiver** (alıcı): konumu kestirilen hareketli birim. İki ürün çeşidi:
yaya ve kara aracı.

**Link** (bağlantı): belirli bir anda bir ölçüm paketi alışverişi
yapabilecek, sıralı bir telsiz çifti. Bir bağlantı ya kapanır ya kapanmaz;
ve buna karar veren hesabın kendisi, taşıdığı ölçümün kalitesini de
belirler. Bu kod tabanının hiçbir yerinde ayrı bir "azami menzil" sabiti
yoktur; menzil bir girdi değil, bir sonuçtur. ADR-0002'ye bak.

**Observation** (gözlem): alıcının kestiricisinin görmesine izin verilen
şey. Asla gerçeği içermez. Bir menzil gözlemi ölçülmüş bir mesafe,
direğin ölçülmüş konumu, bir zaman damgası ve bir varyans taşır. Bir
büyüklük bir Observation içinde değilse kestirici onu kullanamaz.
ADR-0003'e bak.

**Truth** (gerçek): benzetilen fiziksel durum. Yalnızca dünya ve algılayıcı
modelleri onu okuyabilir. Kestirici okuyamaz.

**Fix** (sabitleme): bir konum kestirimi, kovaryansıyla birlikte.

**Deployment** (yerleşim): bir **Site** boyunca ya da üzerine yerleştirilmiş
bir direk kümesi, artı orada kullanılan alıcı ürünü. Maliyeti olan şey
budur.

**Site** (saha): fiziksel yer: arazi, yollar, tüneller, binalar. Yolların
eğimi vardır, dolayısıyla bir alıcının yüksekliği yol boyunca değişir. Bu
kod tabanında hiçbir şey bir yolu sabit bir yüksekliğe sabitlemez.
ADR-0004'e bak.

**Buildings** (binalar): `site/model.py`. Her bina bir yükseklik ve
getirilen gerçek ayak izi; ayak izi yoksa merkezinin çevresinde bir
daire. Ayak izinin içindeki bir nokta çatıyı okur. ADR-0097'ye bak.

Kodda `Site` her zaman budur. Tarayıcıda açılan **web sitesi** başka bir
şeydir ve kodda o adı taşımaz: sayfaları `viewer/pages.py` içinde durur
(ADR-0064).

**Service area** (hizmet alanı): bir yerleşimin çalıştığı iddia edilen
zemin alanı, km² cinsinden. *Bir konum üretmeye yetecek kadar direğin
erişilebilir olduğu* zemindir; bir koridor şeridi olarak çizilmez, gerçek
arazi üzerinde taranır. Karşılaştırma tablosunun GNSS satırlarındaki km²
paydasının anlamına uymasını sağlayan budur.

Yalnızca *ulaşılan* zemin (en az bir direğin eriştiği) bambaşka ve çok
daha büyük bir sayıdır; ikisinin asla karıştırılmaması için yan yana
bildirilir: 25 m direklerde her 4 km'de bir direkle, bir direk 392,5 km²'ye,
dört direk 15,2 km²'ye erişir. ADR-0012'ye bak. Koridor yerleşimleri için
güzergâh kilometresi başına maliyet de yanında bildirilir.

**Layout** (yerleştirme): direklerin nereye konulacağına karar veren
adlandırılmış yöntem. Kafesler (kare, altıgen, koridor, çevre),
aramalar (kapsama, geometri, k-örtme) ve elle. Hepsi tek bir dikişten
geçer: `place(plan, ground)`. ADR-0040'a bak.

**Placement search** (yöneylem yerleşimi): `placement.py`. Direkleri
ızgara yerine zaten duran ya da zaten yüksek yerlere koyan arama: sokak
donanımı, yol boyundaki direkler (şehirde aydınlatma, kırsalda elektrik
dağıtım direği), tepelere dikilecek direkler ve ızgaranın kendi noktaları.
Çatılar kiralık olduğu için aday sayılmıyor (ADR-0104). Kapsamayı bağlantı bütçesiyle deniyor; bir hücre dört
direk ona ulaşıp çevresindeki dört çeyreğin en az üçünde durduğunda
sayılıyor. Seçim lira başına açgözlü, sonra bırakma ve değiş tokuş.
Simülatörde "Yerleştir", komut satırında `yerkon place`. Cevap `placed`
yöntemli bir direk grubu olarak gelir. ADR-0081'e bak.

**Placement** (kayıtlı yerleşim): `placed.py`. Aramanın cevabı veri
olarak, `src/yerkon/placements/<satır>.toml`: her direğin yeri, üstünde
durduğu yapı ve kavşakta olup olmadığı. Şehir içi ve kırsal satırlar
`<satır>.layout = "placed"` iken buradan okuyor; simülatörün sekmesi de.
Başka bir zeminde satır ızgaraya döner. ADR-0096'ya bak.

**Row figures** (satırın değerleri): `scenarios.row_figures`,
`ROW_SEEDS`, `ROW_UNITS` ve `site_road`. Bir satırın konum dışında neyle
koşturulduğu tek yerde duruyor; tablonun kataloğu da simülatörün sekmesi
de oradan okuyor, bu yüzden bir sekmede "Çalıştır" satırın kendisini
koşturur (ADR-0084).

**Band recording** (bant kaydı): SDR++'ın temel bant WAV'ı ya da
SDRangel'in `.sdriq` dosyası. `yerkon calibrate` bunu okuyup paket kaybı
varsayımının yerine ölçülmüş bir değer yazar: 31,8 ms'lik bir
alışverişin kanalda başka bir yayına denk gelme olasılığı. Programların
kendisi simülasyonun içinde çalışmaz; kayıtları çalışır. ADR-0083.

**Measured reach** (zeminde ölçülen menzil): bir aramanın adaylarını
puanladığı disk, üzerinde durduğu zeminde ölçülerek. `reach_of` düz arazi
rakamıdır ve kendi belgesi "bir iddia değil" der: bir halka için doğru,
bir karar için yanlış. Kızılay'da halka 3825 m, ölçülen 478 m. Kafesler
diski okumaz, yalnızca aramalar (`layout.SEARCHES`). ADR-0047'ye bak.

**Dilution** (seyreltme, HDOP): direk geometrisinin menzil hatasını ne
kadar büyüttüğü. İki bilinmeyen için (x ve y), çünkü iki yollu menzil
ölçümü mesafeyi doğrudan ölçer, saat kayması durumda yoktur (ADR-0010)
ve düşey yoldan gözlenebilir değildir (ADR-0011). Bir sıra hâlindeki
direkler enine yönde seyreltmeyi sonsuza götürür; bu, kapsamanın
göremediği şeydir.

**Aerial** (hava görüntüsü): sahanın uydu fotoğrafı, zemine giydirilir.
Simülasyonun hiçbir yerinde okunmaz (link bütçesi bir tarlanın ne renk
olduğunu umursamaz), yalnız çizilir. Yayımlanmış site Esri World Imagery
kullanıyor; komut satırında karo adresini kullanan verir. ADR-0041 ve
ADR-0086'ya bak.

**Place picker** (yer seçici): getirilecek zemini haritada çizme.
Merkez artı boyut yalnızca kare tarif eder; kutunun dört köşesi
çekilebilir ve getirme o köşeleri alır. Aynı anda yalnızca biri geçerli:
merkezi elle yazmak ya da boyut sürgüsüne dokunmak çizilmiş kutuyu
düşürür. ADR-0042'ye bak.

**Preset** (düzenleme): bir sekme hakkındaki her şey, adıyla kaydedilmiş.
Zemin, sahanın boyu ve eni, bütün diziler ve alıcılar, elle taşınmış ve
silinmiş direkler, elle değiştirilmiş değerler. Her satır için
*varsayılan* ve *boş* hazır gelir; gerisi `presets/` klasörüne yazılır.
`yerkon table --preset` ile yayımlanan bir satırı da sürebilir; o zaman
künye düzenlemenin adını, yolunu ve içerik hash'ini yazar, çünkü
`konya` iki koşu arasında değişebilir. ADR-0043'e bak.

**Coverage layers** (örtü katmanları): aynı taramanın dört okuması:
kaç direk erişiyor, sinyal marjı (dB), geometri (HDOP), ve beklenen konum
hatası (menzil sigması × geometri). Link bütçesi zaten koşuyordu; bunlar
atılanı tutuyor, %3'e. Hata bir kestirimdir: saat kayması, paket kaybı ve
gerçekten oradan geçen bir alıcı yoktur; yayımlanan sayı koşudan gelir.
ADR-0044'e bak.

**Furniture** (yol kenarı donanımı): direğin cıvatalanabileceği, zaten
duran yapılar: trafik ışığı, otobüs durağı, aydınlatma direği, yol
levhası. Overture'ın altyapı temasından geliyor ve iki türe indirgenerek
saklanıyor: *column* (trafik ışığı ve aydınlatma direği) ile *sign*
(durak ve yol levhası). Kızılay 232 taşıyor: 77 column, 155 sign. İkiye
indirgendiği için kaçının ışıklı kavşak olduğu bu veriden sayılamıyor;
ADR-0077'nin dörtte biri o yüzden bir sayım değil bir okuma.
Duvar, bordür, çit ve kamusal sanat aynı temada ve montaj noktası değil,
o yüzden listede yok. Arayan yerleştirmeler kafes yerine bunları puanlar
(ADR-0015, ADR-0040). ADR-0046'ya bak.

**Route** (güzergâh): bir alıcının sürdüğü şekil. Yedi tane, alıcı
başına seçilir: düz çizgi, gidiş-dönüş, çevre turu, sekiz çizme, tarama
(boustrophedon), rastgele duraklar (Johnson ve Maltz 1996) ve gerçek yol.
Hepsi tek bir dikişten geçer: `trace(trip, course)`. Direklerin dizildiği
omurga bundan etkilenmez. ADR-0045'e bak.

**Scenario** (senaryo): bir Deployment artı bir alıcı yolculukları kümesi
artı değerlendirme ayarları. Bir senaryo bir tablo satırı üretir.

**Weighted row** (ağırlıklı satır): artık yok. Tablonun dördüncü satırı
olarak üç senaryonun ham hata örneklerini sabit ağırlıklar altında
birleştiriyordu. Rapordan çıkarıldığı için buradan da çıkarıldı;
ADR-0068'e bak. Onunla birlikte senaryoların yolculuk payları, `--weight`
ve `evaluate.combine` de gitti.

Kalan kural aynı: üç P95 değerinin ortalaması bir P95 üretmez. Bu kod
tabanı yüzdelik ortalamayı hiçbir yerde yapmaz; gölge çekilişleri de
havuzlanır, ortalanmaz. ADR-0055'e bak.

**Comparison table** (karşılaştırma tablosu): raporun on üç sistemi aynı
sütunlarla yan yana koyan tablosu. Üç satırı bu deponun çıktısı ve
`published.toml`'dan gelir; kalan on satır GPS, Galileo, GLONASS,
BeiDou, QZSS, NavIC, TerraPoiNT, Locata, Pozyx ve eLoran'ın kendi
kaynaklarının yayımladığı değerlerdir ve `comparison.toml`'da durur.
Oradaki hiçbir sayı hesaplanmaz; her birinin yanında ona ne yapıldığını
söyleyen bir not vardır. ADR-0069'a bak.

**Bibliography** (kaynakça): raporun kaynakça slaytındaki 48 bağlantı ve
sitenin maliyet ve mevzuat hesapları için eklediği kaynaklar,
`sources.toml`'da gruplar altında. Notlar bunları anahtarla anar
(`sources = ["gps-gov"]`), yani bir adres tek yerde değişir. Hiçbir
notun anmadığı girdi de listede kalır: liste raporun kaynakçasıdır,
sitenin kullandıklarının listesi değil. ADR-0070'e bak.

## Ürünler

**Bill** (malzeme listesi): `bom.toml` ve `bom.py`. Her parça satıcısının
kademe tablosuyla yazılı (`ladder`: en küçük adet ve o adetten başlayan
birim fiyat). Bir ürünün fiyatı, parçaların o kadar kart için alınan
adetteki fiyatlarının toplamı; yayımlanmamış bir kademede indirim
varsayılmaz. Tablo 1000 adetlik fiyatı kullanıyor. ADR-0105'e bak.

| Ürün | Ana parçalar | 1 adet | 100 adet | 1000 adet |
|---|---|---|---|---|
| Şehir içi ve kırsal yayın birimi | E28-2G4M20S (SX1280), GW.22.5151, STM32G031, ATECC608B | 2049,79 | 1531,32 | 1381,83 |
| Kritik bölge yayın birimi | DWM3000, STM32G031, ATECC608B | 2276,48 | 1755,47 | 1680,26 |
| Yaya alıcısı | E28-2G4M12S, DWM3000, ESP32-S3, BNO085, ATECC608B | 3082,55 | 2586,76 | 2309,77 |
| Kara aracı alıcısı | E28-2G4M20S, DWM3000, STM32G0B1, BNO085, ATECC608B, CAN, ekran, GW.22.5151 | 4528,63 | 4069,88 | 3309,05 |

Fiyatlar TL, kartın bütün parçalarıyla (besleme, koruma, kutu, pasifler,
baskılı devre, dizgi). Şehir içi ve kırsal yayın birimi aynı kart: 20 dBm
yükselteçli E28-2G4M20S ve dış ortam tipi 5 dBi çubuk anten (Taoglas
GW.22.5151, IP67). Cihaz uyarlamalı frekans atlamalı (FHSS) olarak
belgelendiriliyor; bu belgeyle yoğunluk sınırı kalkıyor ve 20 dBm e.i.r.p.
sınırı kalıyor (ADR-0092, ADR-0094, ADR-0099). Kara aracı alıcısı da aynı
modülü ve aynı anteni taşıyor. Yaya alıcısı E28-2G4M12S'nin kendi
anteniyle çalışıyor.

E28-2G4M12S ve E28-2G4M20S anten değil, SX1280 modülüdür. Link bütçesi her
antenin yayımlanmış kazancını ve hüzme genişliğini kullanır.

## Tablo sütunları ne demek

**HPE, VPE**: yatay ve düşey konum hatası, metre cinsinden, belirtilen
yüzdelikte, değerlendirilen yolculuklar üzerinden.

**Kullanılabilirlik**: denenen turlardan, filtrenin kendi yatay
belirsizliği 5,78 m'yi (HPE P95 < 10 m hedefinden türetilen çıta) geçmeyen
bir konum üretenlerin oranı. Çıtayı geçmeyen turda alıcı izlemeyi sürdürür
ama konum sunmaz ve hatası örneğe girmez (ADR-0084). Yalnızca modellenen
başarısızlık sebeplerini ölçer: bağlantı kapanması, paket kaybı, çözücü
başarısızlığı ve yetersiz doğruluk. Bir hizmet kullanılabilirliği değeri
değildir ve GNSS satırlarına karşı öyleymiş gibi okunmamalıdır.

Bu tanımla turun uzunluğu, turdaki mesafe sayısından çok önemli: filtrenin
belirsizliği turlar arasında büyür. Tünel turda sekiz direk yoklar
(ADR-0085). Gerçek yollarda ve aramanın direkleriyle on iki yeniden öne
geçti; şehir içi ve kırsal on iki yokluyor (ADR-0099).

**Arazi karosu**: AWS'deki açık Terrarium karoları; her pikselin rengi
bir yükseklik (Türkiye'de EU-DEM 25 m). Yayımlanmış sitenin zemin
kaynağı, masaüstünde Copernicus'un yedeği (ADR-0086).

**Alan**: yukarıda tanımlandığı gibi hizmet alanı.

**CAPEX**: yayın birimlerinin 1000 adetlik fiyatı, montajı ve gerekiyorsa
güneş paneli ile akünün toplamı, hizmet alanına bölünmüş (tünelde güzergâh
kilometresine). Test, belgelendirme, vergi ve kargo dahil değil.

**OPEX**: km² başına yıllık işletme maliyeti. Rapor bunu boş bırakır. Bu kod
tabanı onu, yinelenen kalemlerden oluşan açıkça belirtilmiş bir envanterden
doldurur. ADR-0006'ya bak.
