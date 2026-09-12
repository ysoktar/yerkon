# YERKON benzetimi

*English: **[README.md](README.md)***

YERKON donanımından kurulan karasal bir konumlandırma ağının ne
verdiğini ve kurmanın ile işletmenin neye mal olduğunu kestirir. Çıktısı,
raporun 15. sayfasındaki karşılaştırma tablosunun YERKON bloğudur.

Bu bir yeniden yazımdır. Öncekinin sayıları kullanılmamalı; sebepleri
`docs/adr/` altında, kısası şu: süzgeci cevabı görebiliyordu ve link
menzili bir sonuç değil bir sabitti.

## Nereden başlamalı

- `CONTEXT.md` sözlüktür. Koddan önce onu oku.
- `docs/adr/` kararları ve her birinin neyin yerine geçtiğini tutar.
- `src/yerkon/rf.py` çalışmanın üzerinde döndüğü modüldür.

## Durum

Kurulmuş ve test edilmiş:

- `evidence.py` — bir veri sayfası değerini bir tahminden ayırt
  edilebilir kılar.
- `hardware.py` — raporun malzeme listesinin adını verdiği parçalar,
  yayımlanmış değerleriyle.
- `regulatory.py` — bir bandın izin verdiği güç, bölgeye göre.
- `rf.py` — link bütçesi: bir bağlantının kapanıp kapanmadığına da, ne
  kadar hassas ölçebildiğine de tek bir hesap karar verir.
- `world.py` — arazi, eğim verilmiş bir yol güzergâhı ve bir direğin
  monte edilebileceği yapılar.
- `site/` — bir kez getirilip önbelleğe alınan gerçek zemin ve gerçek
  binalar; paketin içine dört Ankara sahası işlenmiştir, böylece bir
  klon tabloyu ağa hiç çıkmadan yeniden üretir.
- `observation.py` — kestiricinin görmesine izin verilen tek tip. Hiçbir
  şey import etmez; ADR-0003'ü umut edilen değil zorlanan bir kural
  yapan budur.
- `estimator.py` — menzilleri konuma çevirir: sönümlü en küçük karelerle
  ilk sabitleme ve her menzili kendi anında alan sabit hızlı bir süzgeç.
- `evaluate.py` — parçaların buluştuğu yer: eğimli yol boyunca
  yolculuklar, sabitleme başına hata örnekleri, kullanılabilirlik ve
  taranmış hizmet alanı.
- `cost.py` — malzeme listesinden CAPEX, adlandırılmış yinelenen
  kalemlerden oluşan bir envanterden OPEX; her biri kendi kaynağını
  taşır.
- `scenarios.py` — tablonun anlattığı üç yerleşim, kod olarak değil
  yapılandırma olarak.
- `report.py` — dört satır ve neye dayandıkları.
- `terms.py` ve `budget.py` — adlandırılmış yedi hata kaynağı ve her
  senaryoyu birini susturarak yeniden koşan dağılım; böylece tablonun
  hassasiyet değerleri neden öyle olduklarının gerekçesiyle gelir.
- `siting.py` — bir hedefi karşılayan en ucuz yerleşimin aranması.
- `settings.py` ve `defaults.toml` — kimsenin vermediği her değer *ve*
  bir yerleşimi şekillendiren her sayı, başka hiçbir şeyin ekleme
  yapamayacağı tek bir dosyada.
- `options.py` ve `options/` — adlandırılmış yerleşim seçenekleri: o
  dosyaya yapılan kısa bir düzenleme listesi ve birinin bunu yapma
  gerekçesi.
- `solve.py` — bir hedefi karşılayan en ucuz düzenin aranması; kazananı
  yeni bir seçenek olarak kaydeder.
- `parallel.py` — bağımsız koşuları makinenin çekirdeklerine yayar.
- `deliver.py` — bütün çalışmanın Markdown olarak yazılması.
- `viewer/` — aynı motorun üzerinde yerel bir web uygulaması: sahanın üç
  boyutu, her ayar canlı, ve başka bir şeyi zorlayan her değişikliğin
  önünde onay paneli.
- `ranging.py` — çift yönlü alışveriş: saatler, şemalar, hava süresi.
- `design.py` ve `proposal.py` — birinin seçtiği ayarlar ve bir
  düzenlemenin her sonucunu uygulamadan önce gösteren panel.

`docs/HANDOFF.md` açık soruları ve hâlâ vekil olan değerleri tutar.

## Çalıştırma

```bash
pip install -e ".[dev]"
pytest
```

## Görüntüleyici

```bash
yerkon view
```

Yerel bir web uygulaması açar. Sahanın üç boyutu: zemin, güzergâh, her
direk ve toleransı içinde ölçebildiği halka; taranmış kapsama iki renkle
zemine boyanmış — biri bir paketin ulaştığı zemin, diğeri aynı anda dört
direğin erişimde olduğu zemin.

Üç sekme, tablonun her satırı için biri, üçü birden tutulur: sekme
değiştirmek hazırladığını silmez ve bir koşu ya üzerinde olduğun sekmeyi
(bir satır) ya da üçünü birden ve oluşturdukları ağırlıklı satırı alır
(ADR-0028).

**Panel altı adımdır, birinin çalıştığı sırayla** (ADR-0034): zemin
nerede, saha ne şekilde, üzerinde ne duruyor, neyi başarması gerekiyor,
bu neye dayanıyor ve ne koşulacak. Her biri kendi durumunu taşıyan tek
bir satıra kapanır —

    1 YER       kizilay · ölçülmüş zemin
    2 SAHA      3,0 km × 3,0 km alan
    3 YERLEŞİM  49 direk · 1 grup · 2 alıcı
    4 HEDEF     ±5,0 m · TR · tek yönlü
    5 DAYANAK   72 değerin 35 tanesi varsayım
    6 ÇALIŞTIR  üç satır ve ağırlıklı ortalama

— böylece bütün çalışma kaydırmadan okunur ve sonuç, onu oynatan
kontrolleri değiştirirken panelin altında sabit kalır. Aynı anda bir adım
açıktır; kapatmak hiçbir şey kaybettirmez, çünkü satır adımın ne
tuttuğunu söyler.

Aralıklı her ayarın hem sürgüsü *hem* tam sayısı vardır: adımı 500 olan
bir sürgüye 4000 verilemez, tek başına bir sayı da içinde yaşadığı aralık
hakkında hiçbir şey söylemez. Sayı sürgünün uçlarını geçebilir, çünkü
kırpmak bir kontrolün kendisine bakıldığı için bir ayarı değiştirmesi
olurdu.

**Arama kutusu** yetmiş iki değer dâhil her ayarı kapsar ve Türkçeyi
klavyenin düşünmeden ulaştığı harflere katlar — `gurultu`, *gürültü
katsayısı*'nı bulur. `/` onu odaklar. Bir adım tam olarak içinde bir
isabet varken açıktır.

**İki dil.** Arama kutusunun yanındaki TR/EN her şeyi değiştirir: panel,
yetmiş iki değerin notları ve neyi etkiledikleri, zeminin kendi
açıklaması, hazır seçeneklerin gerekçeleri. Hiçbir sayı, hiçbir geometri
ve hiçbir sonuç ikisi arasında farklı değildir; bunu bir test bütün
tabloyu iki kez kurarak söyler (ADR-0035).

**Zemin** neyin üzerinde durulduğunu seçer: getirilmiş Ankara — Kızılay,
Polatlı, Kızılcahamam, Gölbaşı — ya da modellenmiş tepeler. **Yeni bir
yer getir** başka her yeri getirir: bir sınır kutusu, bir ızgara aralığı
ve OpenStreetMap'e bina sorulup sorulmayacağı. Paketin kendi saha
klasörüne yazar, böylece seçicide hemen belirir ve her şeyle birlikte
işlenir. Ne seçicide ne de rölyef sürgüsünde düz bir seçenek vardır:
hiçbir yer düz değildir ve düz bir düzlem bu modelin çizebileceği en
tarafsız değil en elverişli yüzeydir (ADR-0021). Getirilmiş bir saha
seçmek modellenmiş arazinin üç sürgüsünü soldurur, çünkü gerçek bir
ızgara kendi rölyefini, pürüzünü ve engellerini getirir.

**En** — sahanın genişliği — her şeyin şeklini belirleyen düğmedir.
Sıfırken saha bir koridordur: direkler yolun iki yanına dizilir, birimler
düz gider. Sıfırdan büyükken bir alandır: direkler kaydırmalı bir ızgaraya
yayılır, birimler alanın çevresini ve ortasını dolaşır. Bir alıcının
ikisinden aldığı geometri karşılaştırılabilir değildir; ikisinin de
gösterilip birinin varsayılmamasının sebebi budur. Şehir içi ve kırsal
alan olarak açılır, tünel çizgi olarak. **Boy** — sahanın uzunluğu —
kısaldığında direk gruplarını içine alır; oynattığı her değeri gösteren
onay panelinden geçerek (ADR-0032).

Direkler *grup* olarak düzenlenir — tek bir modülü, tek bir montajı ve
tek bir aralığı taşıyan bir küme — ve bir saha kaç tanesine ihtiyacı
varsa o kadarını tutabilir; her biri kendi rengiyle ve kendi menzil
halkasıyla çizilir. Birimler de aynı şekilde: istediğin kadar, her biri
kendi hızı, başlangıcı, anten yüksekliği ve modül kümesiyle, izlediği
güzergâhın üzerinde çizilmiş.

Her şey canlıdır. Bir direği sürükle, Shift ile tıklayıp kaldır, bir grup
ya da bir birim ekle ya da çıkar, herhangi bir sürgüyü oynat — sahne ve
sayılar takip eder.

**Dayanak** altında yetmiş iki değerin her biri, `defaults.toml`
anahtarı imleci üstüne getirince görünecek şekilde adlandırılmıştır ve
değerinin nereden geldiğini gösteren renkli bir işaret taşır: veri
sayfası, ölçüm, standart, türetilmiş, tasarım kararı, varsayım. *Yalnız
varsayımları göster*, listeyi hâlâ tahmin olan otuz beşe indirir — birinin
bir öğleden sonrasına değen kısım odur.

**Gezinme.** Döndürmek için sürükle. Zemini kaydırmak için sağ tık, orta
tık ya da Shift+sürükle — tuttuğun nokta imlecin altında kalır ve
imlecin konumu, zemini tuttuğun andaki kameraya karşı okunur; canlı
kameraya karşı okumak arazi üzerinden çınlayan bir döngü kapatıyor
(ADR-0033). Tekerlek imlece doğru yaklaşır, tekerleğin gerçekte ne kadar
döndüğüyle ölçeklenerek: touchpad süzülür, fare çentiği adımlar. WASD ve
oklar kameranın baktığı yöne yürür, `Q`/`E` döndürür, `R`/`F` eğer ve `G`
her şeyi çerçeveler — kaybolduktan sonra istediğin budur. Kameranın
etrafında döndüğü nokta altındaki zemine biner, böylece dönüş tepenin
altına gömülü bir eksen etrafında değil baktığın şeyin etrafında kalır.
Çerçeveleme ilk açılışta ve satır değişiminde olur, bir daha olmaz;
kurduğun görüş kurulu kalır.

**Komut satırının yaptığı her şeyi sayfa da yapar** (ADR-0024) ve
gönderilen varsayılanlara değil sayfanın gösterdiği ayarlara karşı koşar
— böylece bir öğleden sonralık düzenleme, önce dosya yazmadan
maliyetlendirilebilir:

- **Hazır seçenekler** adlandırılmış seçenekleri listeler ve birini
  düzenleme olarak uygular; senin düzenlemelerinin yerine geçmez,
  yanlarına eklenir.
- **Tablo** rapor satırlarını koşar.
- **Hata dağılımı** hata dağılımını koşar ve her kaynağı en kötüsü başta
  olmak üzere çubuk olarak çizer.
- **Çözücü** yerleşimleri bir hedefe karşı arar ve kazananı yeni bir
  adlandırılmış seçenek olarak kaydeder; seçenek listesi de onu sunar.

Son üçü dakikalar sürer, çünkü içlerindeki her değer gerçek benzetimin
koşulmasından gelir. Bir iş parçacığında koşar ve satır satır bildirir,
böylece merak etmek yerine izleyebilirsin.

Başka değişiklikleri zorlayan değişiklikler — bölge, modül, montaj,
tolerans, pürüz — önce onay panelini kaldırır; oynayacak her değeri eski
ve yeni sayısıyla ve neden takip ettiğiyle listeler ve bütün küme için
bir kez cevaplanır (ADR-0009). Panel direk grubuna göre gruplanır ve
hangisini kastettiğini söyler, çünkü paylaşılan bir ayar her grubu aynı
şekilde oynatmaz: Amerikan kurallarına geçmek yayılı grupların tavanını
yükseltir, darbeli olanınkini hiç oynatmaz. Bir direği sürüklemek, bir
birim eklemek ya da araziyi değiştirmek hiçbir şeyi zorlamaz, bu yüzden
hemen uygulanır.

Sayfa hiçbir fizik tutmaz. Üzerindeki her sayı tabloyu kuran modüller
tarafından hesaplanmıştır, dolayısıyla resim ile rapor birbiriyle
çelişemez. Üç boyutunu bir içerik dağıtım ağından kütüphane yükleyerek
değil kendi çizer, böylece makine çevrimdışıyken de çalışır (ADR-0013).

## Varsayılan değerler

Rapor bir malzeme listesi verdi, başka bir şey vermedi. Bu projenin
ihtiyaç duyduğu diğer her değer birinin seçtiği bir varsayılandır ve
hepsi tek bir dosyada durur. Varsayım değil varsayılan denmesinin sebebi
kalıcı olanın bu olmasıdır: biri bir değere kaynak bulunca o değer
dosyadan çıkmaz, yalnızca varsayım olmayı bırakır.

```bash
yerkon defaults --full
```

`src/` içindeki hiçbir şey kendi başına bir varsayım kuramaz — bir test
her modülün sözdizim ağacını gezer ve bir tanesi denerse yapıyı düşürür,
yani dosya listenin tamamıdır (ADR-0016). Maliyetler, montaj
yükseklikleri, yayımlanmamış iki telsiz değeri, saatler, şehir içi engel
kaybı ve süzgecin manevra payı hepsi oradadır.

Birini değiştirmek tek bir yerde üç düzenlemedir: değer, kaynak ve
`provenance` alanının `ASSUMPTION` yerine artık ne olduğu. Sonra:

```bash
yerkon table --defaults my-figures.toml
yerkon site  --defaults my-figures.toml
yerkon view  --defaults my-figures.toml
```

Her şey ondan yeniden kurulur — senaryolar, montaj kataloğu, telsizler,
saatler, oranlar — ve her sonucun tahmine dayandığını bildirdiği pay
düşer. Yalnızca direk maliyetine kaynak bulmak, yerleşim cevabını %94
varsayımdan %69'a indirir.

**Ya da görüntüleyicide düzenle.** Hepsi `yerkon view` içinde,
gruplanmış ve her birinin altında neyi etkilediği yazılı olarak görünür.
Birini değiştir, her şey canlı yeniden kurulsun: direk yüksekliğini 25
m'den 40 m'ye çıkar, panel önce sorar, sonra sahnedeki menzil halkası
5,52 km'den 6,98 km'ye büyür. Bir saha maliyetini değiştir, hemen
uygulanır, çünkü bir fiyat hiçbir fiziği oynatmaz. Elle düzenlenen bir
değer, ona bir kaynak vermedikçe varsayım kalır — bu ayrım, keşfetmek ile
raporlamak arasındaki farktır. **Dosyaya yaz**, elindekini `--defaults`
ile doğrudan geri giren bir dosya olarak dışarı yazar.

Cevapları da oynatır. 8500 TL direk maliyetinde mevcut levhalar hâlâ
kazanır; 5000 TL'de direkler 17 direkle 264906 TL'ye devralır.
Maliyetlendirmenin 6588 TL'de öngördüğü başabaş noktasına tek bir satırı
düzenleyerek iki taraftan da yürüyebilirsin.

## Yerleşim araması

```bash
yerkon site --corridor 12000 --tolerance 5
```

Bir hedefi karşılayan en az masraflı yerleşimi arar; koridorun zaten
taşıdığı yapıları kullanır ve yalnızca hiçbiri yokken inşa eder. Her aday
birinin gerçekten kurabileceği bir yerleşimdir, tablonun kullandığı aynı
link bütçesiyle puanlanır ve aynı malzeme listesiyle fiyatlandırılır.

Tepeli zemin üzerinde 8 km'de, 5 m menzil toleransıyla, her 250 m'de bir
levha dururken:

| Yerleşim | Direk | CAPEX | Kapsanan koridor |
|---|---|---|---|
| Mevcut yol levhaları, her 600 m | 21 | 274736 TL | %96,7 |
| Mevcut yol levhaları, her 500 m | 25 | 327067 TL | %96,7 |
| Amaca özel 25 m direk, her 800 m | 16 | 1529323 TL | %96,7 |

**Levhalar beş buçuk kat kazanıyor**, üstelik direğin 5,52 km'sine karşı
1,66 km'ye erişirken. Yükseklik menzil satın alır ve kıt olan menzil
değildir — para kıttır, ve zaten duran bir levha, durmayan bir direğin
otuz dörtte birine mal olur. Bu, iddia edilerek değil aranarak varılan
karışık montaj stratejisidir ve menzil değerlerinin verdiği sezgiyi ters
çevirir (ADR-0015).

Arama reddeder de. Telsizin kendi ~2,94 m'lik ölçüm tabanının altındaki
bir tolerans bir yerleşim sorunu değildir ve hiçbir direk düzeni onu
karşılamaz; dolayısıyla kötü bir kümenin en iyisi yerine hiçbir şey
döner.

Yapamayacağı şey bir etüt uydurmaktır. Hangi yapının nerede durduğu
yapılandırmadır ve varsayılanlar tipik bir Türk karayolu kesimi hakkında
bir varsayımdır.

## Tablo

```bash
yerkon table
```

| Sistem | Teknoloji | Ortam | HPE P50 [m] | HPE P95 [m] | VPE P95 [m] | Kullanılabilirlik | Alan [km²] | CAPEX [TL/km²] | OPEX [TL/km²/yıl] |
|---|---|---|---|---|---|---|---|---|---|
| YERKON (Şehir içi) | Karasal PNT (SX1280/LoRa TWR) | Dış | 1,64 | 4,92 | 43,65 | %99,11 | 10,54 | 19055 | 8828 |
| YERKON (Kırsal) | Karasal PNT (E28-SX1280 TWR) | Dış | 2,71 | 10,35 | 143,34 | %89,55 | 671,75 | 4696 | 195 |
| YERKON (Tünel) | Karasal PNT (UWB/DWM3000 TWR) | İç + dış | 1,81 | 2,96 | 8,25 | %100,00 | 0,02 | 4453423 | 849511 |
| YERKON Ağırlıklı Ortalama | Karasal PNT | İç + dış | 2,02 | 7,65 | 109,84 | %93,39 | 273,97 | 456748 | 89443 |

Her satır **gerçek Ankara zemininin** üzerinde durur; Copernicus 30 m
DEM'inden bir kez getirilmiş ve paketin içine işlenmiştir, böylece bir
klon bu sayıları ağa hiç çıkmadan yeniden üretir (ADR-0008). Şehir
Kızılay'dır: bir kenarı üç kilometre, üzerinde 91 m iniş çıkışla. Açık
arazi Polatlı ovasıdır: bir kenarı yirmi kilometre, 486 m rölyefle. Tünel
Kızılcahamam'daki dağların içinden geçen gerçek bir 2 km'lik güzergâhtır;
yükseklikleri dağın kendisine ait iki portal arasında %1,79 düşüyor.

Hiçbir yerde hiçbir şey düz değildir ve bu bir ayrıntı değil bir karardır
— ADR-0021'e bak. Yansıtıcı zemin de yamadan yamaya değişir, iki ya da üç
ölçekte ve satır başına kendi tohumuyla (ADR-0026); o çalışmanın ortaya
çıkardığı şey, **bir eğimin kırk kat pürüz sayılmış olmasıydı** — bu da
eşevreli yansımayı düz olmayan her yerde kapatıyordu. Düzeltilince tablo
tohum gürültüsünden az oynadı: eski model aynı yere yanlış yoldan
varıyormuş. Her satır ayrıca havayı paylaşan iki birim taşır; güncelleme
hızının tek bir birimin göreceğinin yarısı olmasının sebebi budur. Ve
yalnızca tünel bir koridordur, ki bunu ADR-0014'ün eki açıklar.

OPEX sütunu raporun dört satır için de boş bıraktığı sütundur. Sermayenin
bir yüzdesi olarak değil, adlandırılmış yinelenen kalemlerden oluşan bir
envanterden gelir (ADR-0006) ve buradaki her maliyet değeri gibi
çoğunlukla kimsenin vermediği oranlara dayanır — komut bu payı yanında
yazdırır.

Tablonun söylemeden yapmayacağı üç şey:

**Tünelin km² başına maliyeti diğer satırlarla karşılaştırılabilir
değildir.** 2 km boyunca 12 m genişliğinde bir tünel 0,024 km²'dir, yani
buna bölmek büyük bir sayıyı yargıyla değil aritmetikle üretir. Güzergâh
kilometresi başına maliyette tünel 53441 TL'dir. Diğer iki satır çizgiye
değil alana hizmet eder, dolayısıyla güzergâh kilometreleri bir test
yolculuğunun uzunluğudur ve onlar için kilometre başına maliyet hiç
verilmez.

**Hizmet alanı, bir konumun alınabildiği yerdir**, bir paketin ulaştığı
yer değil. Kırsal bölge için bunlar 671,75 ve 1188,00 km²'dir, 1,8 kat, ve
notlar her seferinde ikisini de yazdırır (ADR-0012).

**Kırsal kullanılabilirliğe arazi ve bir turun uzunluğu karar verir.**
Tek bir kırsal bağlantı bile mesafe yüzünden düşmez — her bir başarısızlık
zemin kaldırılsa kapanırdı — yani daha çok direk yanlış içgüdüdür. Yanlış
olan turdu: yarısını engelleyen bir zemin üzerinde yoklanan sekiz direk
yaklaşık dört yanıt verir, ki bu da soğuk bir sabitlemenin gerektirdiğinin
tam kendisidir, yedeksiz. On ikiyi yoklamak satırı hiç sermaye harcamadan
%82,3'ten %89,6'ya çıkardı; karşılığında güncelleme hızının üçte birini ve
0,4 m yatay hatayı verdi. %90'ı geçmek para tutuyor: kabaca direk
sermayesinin iki katı, ya daha çok direk ya daha uzun direk olarak.
ADR-0022 fiyatlandırılmış eğriyi ve denenip işe yaramayan iki şeyi tutar.

**VPE geometrinin desteklediği kadardır**, hiçbir yerde yükseklik kısıtı
yoktur. Açıkta onlarca metre, tünelde yedinin altı — orada direkler
alıcının yanına dizilmek yerine onu çevreler (ADR-0011).

## Bir yerleşim seçmek

```bash
yerkon options                       # elde ne var
yerkon options rural-dense           # birini tam olarak
yerkon table --option rural-dense    # tabloyu ona karşı koş
```

Bir yerleşimi şekillendiren her sayı fizikle birlikte `defaults.toml`
içinde durur — direk aralığı, saha uzunluğu, kaydırma, tur başına
yoklanan direk, menzil toleransı, tünel genişliği. Dolayısıyla bir
**seçenek**, o dosyaya yapılan kısa bir düzenleme listesi artı birinin
bunu yapma gerekçesinden ibarettir ve yenisi bir kod değişikliğine değil
bir dosyaya mal olur (ADR-0023). Seçenekler `--defaults` ile birleşir,
böylece gerçek teklifler ve daha sık bir ızgara birlikte yaşar.

Beş tanesi paketle gelir, ve ilk ikisi bilerek birlikte durur:

| seçenek | nedir |
|---|---|
| `rural-dense` | 3 km'de 49 direk, 30 m boyunda — %90'ı geçmenin en ucuz yolu |
| `rural-tall` | Aynı 33 direk, 10 m daha uzun — eşit parada kaybeder, saha başına kazanır |
| `urban-dense` | Her iki aydınlatma direğinden birine değil, hepsine direk |
| `rural-hard-ground` | Gölbaşı tepeleri: bu tasarım gitmesi düşünülmeyen yerde neye mal olur |
| | *(bu, hiçbir şey yapmayan bozuk bir hâlde gönderilmişti — ADR-0027'ye bak)* |
| `tunnel-precise` | 120 m askı aralığı — HPE P50 1,81 m → 0,48 m, 23000 TL'ye. Çözücü buldu |

İlk ikisinden hangisinin doğru olduğu, kıt olanın para mı saha erişimi mi
olduğuna bağlıdır ve bu projenin bunu söyleyecek değerleri yok. Bu yüzden
birini seçmek yerine ikisini de gönderiyor.

### Yenisini aramak

```bash
yerkon solve --scenario tunnel --availability 0.99 --hpe-p50 1.0 --save tunnel-precise
```

Düzenleri bir hedefe karşı arar ve onu karşılayanların en ucuzunu
adlandırılmış bir seçenek olarak kaydeder. Her aday gerçek zemine karşı
tam bir benzetimdir — yavaş, ve cevapları kuruluş gereği tabloyla uyuşur.

Kimsenin denemediği bir şey buldu, çünkü denemek eskiden bir sabiti
düzenlemek demekti: **120 m askı aralığı tünel satırını ellinci
yüzdelikte 1,81 m'den 0,48 m'ye indiriyor.** On dört yerine on yedi
direk, 23000 TL fazla; üstelik kilometrekare başına maliyeti tabloda
zaten üç mertebe önde olan satırda.

Reddettiği iki şey var. Hedefi hiçbir şey karşılamıyorsa kötü bir kümenin
en iyisi yerine hiçbir şey döndürür, çünkü en az kötü başarısızlığını geri
veren bir arama her seferinde elle denetlenmek zorundadır. Ve ayarlar
hedefi zaten karşılıyorsa, hiçbir şeyi değiştirmeyen bir seçenek
kaydetmek yerine bunu söyler.

`--vary KEY=A,B,C` ayar dosyasındaki her değeri arar, senaryo başına
kısa varsayılan listeyi değil.

## Teslim

```bash
yerkon deliver --into docs/teslim               # her şey
yerkon deliver --into docs/teslim --no-budget   # yalnız tablo, hızlıca
```

Dört Markdown dosyası; çünkü farklı soruları cevaplarlar ve farklı
kişiler tarafından okunurlar:

| dosya | içinde ne var |
|---|---|
| `tablo.md` | dört satır, her birinin üzerinde durduğu zemin ve notlar |
| `hata-butcesi.md` | her hata kaynağı neye değdi ve kaldırmak ne gerektiriyor |
| `sayilar.md` | her değer, neyi etkilediği ve neye dayandığı — tasarım kararları vekillerden ayrı tutularak |
| `secenekler.md` | bunun yerine kurulabilecek yerleşimler |

Her dosya tarihini ve kaç değerden üretildiğini taşır, böylece teslim
edilmiş bir tablo bir ay sonra depoyla karşılaştırılabilir. Hata bütçesi
atlanabilir, çünkü açık ara en yavaş kısım odur.

## Hata nereden geldi

```bash
yerkon budget
```

Kimsenin üzerine iş yapamayacağı bir hassasiyet değeri yarım bir
sonuçtur. Bu, her senaryoyu tek seferde bir hata kaynağı susturularak
yeniden koşar — yedi kaynak, her biri için on altı koşu — ve her birinin
neye değdiğini bildirir (ADR-0020). Tablonun kullandığı motorun
kendisidir, dolayısıyla onunla çelişemez.

İki sütun, çünkü farklı soruları cevaplarlar. **Tek başına**, o kaynak
tek olsaydı kalacak hatadır. **Kalkarsa**, o gidip diğerlerinin hepsi
kalırsa bütün hatanın ineceği yerdir — her zaman daha küçük tasarruf,
çünkü hatalar kareli toplanır, ve ikisinden yalnızca o bir satın alma
kararıdır.

Tünel, her donanım ölçütüne göre çalışmadaki en hassas yerleşimdir ve
üçünün en az hassası olarak çıkar. Dağılım nedenini söyler: tüneli bir
menzilin sigmasını on sekizle çarpar ve en sert çarptığı şey direk etüt
hatasıdır — ortalamayla asla kaybolmayan tek terim. Ona daha iyi bir
telsiz almak hiçbir şey satın almaz; askılarını düzgün ölçmek onu 1,77
m'den 0,17 m'ye indirir.

Açık yolda sıralama tersine döner. Şehirde modülün kendi ölçüm tabanı
1,13 m, etüt hatası 0,09 m eder; kırsalda dalga formu gürültüsü 2,10 m ile
tabanın 1,51 m'sinin önüne geçer, çünkü kırsal bir bağlantı kilometrelerce
uzundur ve sınır mesafeyle yükselir. İkisinin geometri çarpanı *birin
altındadır* — 0,6 ve 0,5 — yani üzerinde bir süzgeç koşan bir alan, tek
bir menzilden daha iyi çıkar. O sayı, koridor çerçevesinin gizlediği şeyin
niceliksel hâlidir.

Tablonun bir satırı ancak zemin ölçülebilir olunca ölçülebilir oldu.
**Fazladan yol** — bir sinyalin bir engelin üzerinden kat ettiği ek
mesafe — üç senaryonun ikisi düz bir düzlemin üzerinde dururken her yerde
tam 0,00 m okuyordu; terim küçük olduğu için değil, bir düzlem hiçbir
şeyi engelleyemediği için. Gerçek Ankara'da kırsalda 0,42 m, şehirde 0,11
m, tünelde 0,09 m. ADR-0021'e bak.

## Bir saha getirmek

Gerçek zemin, bir kez, bir önbelleğe. Geri kalan her şey ona karşı
çevrimdışı koşar (ADR-0008).

```bash
yerkon fetch --south 39.85 --west 32.70 --north 39.98 --east 33.05 \
             --into sites/ankara-o20 --spacing 30
```

Sırayla üç kaynak denenir ve ilk cevap veren kazanır:

1. `--geotiff` ile verirsen elindeki bir GeoTIFF;
2. genel nesne depolamasındaki **Copernicus 30 m** paftaları — anahtar
   istemez, hız sınırı yoktur ve tam bir derecelik kareyi tek dosyada
   kapsar. Paftalar `sites/_tiles` altında önbelleğe alınır, böylece aynı
   karedeki ikinci bir saha hiçbir şeye mal olmaz;
3. daha yavaş, daha kaba ve günde bin çağrıyla sınırlı bir genel sorgu
   servisi. Bu yedektir, plan değil.

Binalar yanında OpenStreetMap'ten gelir. Getirilemezlerse saha, açık
arazi olduğunu ima etmek yerine kimsenin bakmadığını kaydeder.

## Bir ayarı değiştirmek

Ayarlar bağımsız değildir, dolayısıyla bir düzenleme neyi beraberinde
sürüklediğini gösterir ve bir kez sorar (ADR-0009):

```console
$ yerkon design --mounting sign
You asked to change:
  mounting  tall mast -> roadside sign

Which also changes:
  anchor height                         25,0 m -> 3,0 m
    because the mounting structure sets how high the anchor stands
  usable range                         5,52 km -> 1,66 km
    because range is whatever the link budget allows at the target precision
  range where the link still decodes  38,93 km -> 15,54 km
    because the same budget decides where the link stops decoding

Apply all of that? [y/N]
```

Sonuçlar, yanında tutulan bir kural listesiyle değil benzetimin üzerinde
koştuğu link bütçesinin kendisiyle hesaplanır ve bunu bir test zorlar.

## Bir yerleşim gerçekte ne veriyor

Bir koridor çalışması — tablonun satırlarından biri değil; ikisi alandır.
Tepeli zemin üzerinde 24 km, 25 m direklerde iki yana kaydırmalı direkler,
100 km/sa bir araç, yükseklik kısıtı yok:

| Direk aralığı | Direk | HPE p50 | HPE p95 | Kullanılabilirlik | Ulaşılan | Hizmet |
|---|---|---|---|---|---|---|
| 1500 m | 17 | 2,64 m | 9,58 m | 1,000 | 445,2 km² | 75,2 km² |
| 2000 m | 13 | 3,11 m | 10,46 m | 0,984 | 447,2 km² | 57,2 km² |
| 3000 m | 9 | 4,69 m | 17,05 m | 0,981 | 409,0 km² | 15,2 km² |
| 4000 m | 7 | 5,22 m | 22,82 m | 0,972 | 392,5 km² | 15,2 km² |

Ulaşılan, bir paketin vardığı zemindir. Hizmet, aynı anda dört direğin
erişimde olduğu zemindir — bir konumun gerektirdiği budur. 4 km aralıkta
yirmi altı kat farklıdırlar ve birincisini kapsama diye vermek km² başına
maliyeti aynı katsayıyla olduğundan az gösterirdi (ADR-0012).

Dolayısıyla aralık bir menzil sorusu değil bir geometri sorusudur. Dört
kilometre, bir direğin 5,5 km'lik kullanılabilir menzilinin epey içindedir
ve yine de koridorun çoğunda alıcıyı bir sabitlemeye bir direk uzakta
bırakır.

## Neye mal oluyor ve bu neye dayanıyor

24 km üzerinde on üç direk, 57,2 km²'lik bir hizmet alanında:

| | 13 direk (25 m) | 13 aydınlatma direği (12 m) |
|---|---|---|
| Direk birimleri | 14074,84 TL | 14074,84 TL |
| Yapılar ve montaj | 1105000,00 TL | 39000,00 TL |
| Bağımsız enerji | 123500,00 TL | 0,00 TL |
| **Sermaye** | **1242574,84 TL** | **53074,84 TL** |
| İşletme, yıllık | 51516,85 TL | 25834,84 TL |
| Telsizlerin sermayedeki payı | %1,1 | %26,5 |

Malzeme listesi — bütün bunların kaynağı belli tek kısmı — direk tabanlı
bir ağın maliyetinin yaklaşık yüzde biridir. Bir yerleşimin neye mal
olduğuna, içindeki telsizin hangisi olduğu değil, direklerin neye
cıvatalandığı ve şebeke elektriğinin onlara ulaşıp ulaşmadığı karar
verir.

Yerleşimin yapıları karıştırmasının ve her maliyetlendirmenin kendisinin
kimsenin vermediği değerlere dayanan payını yazdırmasının sebebi budur.
Yukarıdaki tablo için o pay %99'dur: saha maliyetleri ve bütün işletme
oranları, `ASSUMPTION` kaynağı ve bunu söyleyen bir not taşıyan mertebe
düzeyinde vekillerdir (ADR-0006). Bunlar yapılandırmadır ve kaynak
bulununca sayılar oynar.

## Link bütçesinin zaten söyledikleri

Yalnızca raporun adını verdiği parçalarla, Türkiye'nin izin verdiği güçte,
açık zemin üzerinde, alıcı araç tavanında 1,5 m'de:

| Bağlantı | Pay | Menzil sigması |
|---|---|---|
| 5 km, 25 m direk | 14,8 dB | 4,10 m |
| 10 km, 25 m direk | 2,7 dB | 16,41 m |
| 5 km, 35 m direk | 17,7 dB | 2,94 m |
| 10 km, 35 m direk | 5,7 dB | 11,72 m |
| 15 km, 35 m direk | kapanmıyor | — |

Bunların hepsi kapanır ve haklarındaki en ilgisiz şey budur. Kısıt
kapanma değil **hassasiyettir**. Elinde 33 dB olan bir bağlantı bile
mesafeyi on altı metreye ölçer, çünkü menzil sınırı, paket hâlâ çözülmeye
devam ederken çoktan sinyal-gürültü oranıyla birlikte düşmeye başlar.

Fark iki kattır; bu projenin iki hafta boyunca iddia ettiği yedi kat
değil. Link bütçesi 30,1 dB yayma kazancını ekliyor, sonra da onu zaten
varsayan bir eşiğe karşı sınıyordu; yani bağlantılar parçanın kendi
hassasiyetinin 24 dB altında "kapanıyordu". Alıcının bir benzetimini
yazmak bunu yakaladı: ilinti sonrası −20 dB'de hiçbir şey çözülmez, çünkü
bulunacak bir tepe yoktur. Düzeltildikten sonra SX1280 11,7 km'ye kadar
kapanır ve 5,52 km'ye kadar işe yarar biçimde ölçer (ADR-0017).
Kullanılabilir menzil oynamadı — yalnızca abartılmış yarısı oynadı.

Menzili satın alan şey yüksekliktir. Menzil sigmasının 5 m'ye ulaştığı
mesafeyi açık zemin üzerinde çözersek:

| Monte edildiği yer | Yükseklik | Kullanılabilir menzil |
|---|---|---|
| Yol levhası | 3 m | 1,66 km |
| Levha portalı | 6 m | 2,51 km |
| Pano | 10 m | 3,47 km |
| Aydınlatma direği | 12 m | 3,83 km |
| Amaca özel direk | 25 m | 5,52 km |
| Kule | 35 m | 6,53 km |

Dolayısıyla 5–10 km gereksinimi amaca özel direklerden karşılanır, mevcut
yol donanımından değil. Levhalar ve portallar durdukları yerde kullanmaya
değer, ama yalnızca onlardan kurulan bir ağın her iki üç kilometrede bir
direğe ihtiyacı olur.

`tests/test_rf.py` içinde sınanabilir iki sonuç daha:

Kırsal modülün 27 dBm yükselticisi Türkiye'de hiçbir şey satın almaz,
çünkü band yayılan gücü yoğunlukla sınırlar ve sınır bu bant genişliğinde
12,1 dBm'de bağlar. Dolayısıyla iki direk telsizi de aynı gücü yayar ve
aynı mesafeye erişir. İletilen gücü sınırlayan Amerikan kuralları altında
aynı yükseltici yaklaşık 18 dB değerindedir.

Dar bantlı bir telsiz kısa mesafede santimetre vermez. Dalga formu sınırı
100 m'de 2 cm der; parça yaklaşık 3 m ölçer. Model ikisinin büyüğünü
bildirir.

## Havayı paylaşmak neye mal oluyor

Bir yerleşim tek bir araca değil trafiğe hizmet eder ve birimler aynı
direklerde kuyruğa girer. Bir tur, her birimin alışverişlerinin uç uca
dizilmesidir; dolayısıyla ikinci bir birim işi yarıya indirmez —
beklemeyi ikiye katlar:

| | Tek birim | İki birim |
|---|---|---|
| Tur, 16 şehir içi direk | 509 ms | 1018 ms |
| Birim başına saniyedeki sabitleme | 1,96 | 0,98 |
| Yolculuk boyunca denenen tur | 179 | 178 |

Bulgu son satırdır. Ağın ürettiği toplam sabitleme sayısı neredeyse hiç
oynamaz, çünkü hava zaten tamamen harcanmıştı; değişen, nasıl
bölüşüldüğüdür. Şehir içi HPE medyanda tek birimle 3,35 m'den iki birimle
5,06 m'ye çıktı, çünkü her süzgeç artık güncellemeler arasında iki katı
kadar boşta süzülüyor. Önceki değer tek müşterisi olan bir ağı
anlatıyordu.

Malzeme listesindeki iki alıcı da hem bir SX1280 *hem* bir DWM3000
taşır; bir birimin yolda şehir direkleriyle, tünelin içinde tünel
direkleriyle hiçbir şey değiştirmeden ölçmesini sağlayan budur. Bir birim,
dalga formunu paylaştığı her direkle ölçer ve gerisini yok sayar — yani
yalnızca yayılı modülü taşıyan bir birim tünel direklerini hiç görmez.
ADR-0014 bunların hepsini kaydeder.

## Alışveriş üste ne ekliyor

Bir menzil bir link bütçesinden okunmaz. İki telsiz çerçeve alışverişi
yapar ve SF10'da bir çerçeve 15,8 ms sürer. Tek yönlü ölçümde iki saat
arasındaki fark, o bütün yanıt gecikmesini çarpar:

| Saat kayması | Tek yönlü hata | Çift yönlü hata |
|---|---|---|
| 10 ppm, düzeltilmemiş | 24,1 m | 0,3 mm |
| 0,0793 ppm, düzeltme sonrası ölçülmüş | 0,19 m | 0,003 mm |

Yirmi dört metre, parça üzerinde şimdiye kadar ölçülen en büyük hatanın
sekiz katıdır; yani yayımlanmış ölçümlerin kendisi, her alıcının zaten
yaptığı frekans kayması kestiriminin ölçüm işini de yaptığının kanıtıdır.
O olmadan bu telsizde ölçüm işlemez.

**O artık ölçüldü** ve bu, projede artık tahmin olmayan tek değerdir.
`matlab/yerkon_clock_residual.m` onu **0,0793 ppm** koyuyor — yerine
geçtiği 0,5'ten altı kat iyi (ADR-0018).

Ölçüm, tahminin söyleyemediği şeyi de söylüyor: onu neyin sınırladığını.
Artık sinyalle neredeyse hiç iyileşmiyor: 30 dB fazlası iki kat satın
alıyor, gürültüyle sınırlı olsa otuz kat alırdı. Hiç gürültü olmadan
koşulduğunda aynı kestirici, yalnızca tepenin FFT gözleri arasında nereye
düştüğüne bağlı olarak 0,0164–0,0643 ppm veriyor; bu da ölçülen platoyla
dört basamağa kadar uyuşuyor. **Taban kanal değil tepe aradeğerleyicisi**
— yani tekrarlanan alışverişlerde ortalamayla azalmıyor ve daha ince bir
aradeğerleyici onu düşürürdü.

Bununla birlikte bir tasarım kararı değişti. 0,5 ppm'de darbeli telsizin
tek yönlü saat terimi 10 cm'lik bir tabana karşı 10 cm'di, yani çift
yönlü ölçüm üçüncü çerçevesini hak ediyordu. Ölçülmüş hâliyle o terim 1,6
cm ve taban onu yutuyor. **Tünel yerleşimi artık tek yönlü**: üçte bir az
hava süresi, P95'te 1,00 yerine 0,72 m ve bir buçuk katı sabitleme.

Faz gürültüsü, çok yolluluk ve alışveriş sırasında sürüklenme
modellenmiyor; dolayısıyla bunu bir taban olarak oku.

Hava süresi artık çalışmanın harcayabileceği bir niceliktir ve göründüğünden
azını satın alır:

| | SF10'da SX1280 | DWM3000 |
|---|---|---|
| Ölçüm çerçevesi | 15,75 ms | 1,06 ms |
| Çift yönlü alışveriş | 47,86 ms | 3,77 ms |
| Saniyedeki menzil | 20,9 | 265,1 |

Dolayısıyla SX1280'de altı direğe karşı bir tur 239 ms sürer; bu sürede
100 km/sa giden bir araç 6,7 m yol alır — yanındaki 2,94 m'lik menzil
hatasının iki katından fazla. Bir turdaki menziller eşzamanlı değildir ve
öyleymiş gibi çözülemez. Bu, kestirici yazılmadan önce varılmış, kestirici
hakkında bir sonuçtur ve alıcının anlık üçgenleme yerine bir süzgeç
kullanmasının sebebidir.

## Gürültü olmayan üç hata

Yeterince gürültülü menzil verilen bir süzgeç gerçeğe yakınsar. Gerçek
sistemler böyle davranmaz, çünkü en kötü hataları gürültü değildir
(ADR-0019).

**Engellenmiş bir yol uzun ölçer.** Sinyal engelin üzerinden gider ve
menzil o sapmayı zamanlar: `h²/2 · (1/d₁ + 1/d₂)` — uzun bir bağlantıda
yumuşak bir yükselti için santimetreler, kısa bir bağlantıda enine bir
sırt için on metre. Her zaman pozitiftir, yani ortalamayla asla
kaybolmaz.

**Bir etüt hatası bir kurulumun özelliğidir**, direk başına bir kez
çekilir ve tutulur. Kestiriciye ölçülmüş konum söylenir ve onu kesin
sayar.

**Kaybolan bir paket hiçbir şey üretmez** — paylaşımlı bir bantta
girişim, bir çakışma, bir sönümleme. 2,4 GHz kablosuz ağlarla aynı
banttır; şehir değerinin açık yoldaki %5'e karşı %15 ve tünelde 0 olmasının
sebebi budur.

Bir cevabı değiştiren, etüt hatası oldu:

| Direk etüt hatası | Tünel HPE P50 |
|---|---|
| 0,00 m | 0,24 m |
| 0,05 m | 0,68 m |
| 0,15 m | 1,76 m |
| 0,30 m | 3,14 m |

**Direkleri ölçtüğünden daha iyi konumlanamazsın** ve bir koridorda on
katı kadar bile yaklaşamazsın — düşeyi gözlenemez bırakan geometri, bir
etüt hatasını aşağı yukarı aynı katsayıyla büyütür. Tünelin metre altı
değeri, kusursuz bilinen direklerin üzerinde duruyormuş.

Yol satırları neredeyse hiç oynamadı; bu da aynı bulgunun diğer
tarafıdır: yayılı bir telsiz yaklaşık 3 m'ye ölçer ve 15 cm'lik etüt
hatası onun altında kaybolur. Taban her yerleşimde vardır ve yalnızca
diğer her şeyin ondan iyi olduğu yerde bağlar.

## Kestirici ne alıyor

100 km/sa ile altı direğin yanından geçen bir alıcı, 17 s boyunca tur tur
ölçülmüş, yükseklik kısıtı yok:

| | Tur başına anlık | Süzgeç |
|---|---|---|
| HPE p50 | 5,20 m | 1,46 m |
| HPE p95 | 6,42 m | 2,55 m |
| VPE p50 | 51,90 m | 23,41 m |

Anlık olan daha kötüdür, çünkü sekiz metrelik araç hareketini menzillerin
üstüne yıkar. Süzgeç ölçümlerin 48 ms arayla olduğunu bilir ve yıkmaz.

Düşey başka bir sebeple kötüdür ve hiçbir süzgeçleme onu düzeltmez. Dört
kilometrelik bir taban çizgisine karşı yirmi iki metrelik montaj
yüksekliği yayılımı hiç yayılım değildir; dolayısıyla her menzil neredeyse
tamamen yataydır ve yükseklik aritmetiğe zar zor girer. 3 m'deki
levhalarla 25 m'deki direkleri karıştırmak ölçülebilir bir fark yaratmaz.
Onlarca metrelik VPE, yol kenarı direklerinden oluşan bir ağ için gerçek
cevaptır ve ADR-0011 neden kısıtlanıp yok edilmek yerine bildirildiğini
kaydeder.
