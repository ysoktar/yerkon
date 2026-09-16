# Devir

Ne kurulmuş, sırada ne var ve neye hâlâ karar verilmemiş. Başka bir
oturumun ya da başka bir modelin bütün geçmişi okumadan devralabilmesi
için yazıldı.

Önce sözlük için `CONTEXT.md`'yi, kararlar için `docs/adr/` altını oku.
İkisi de isteğe bağlı değil: bu projenin şimdiye kadar yaptığı hataların
çoğu sözcük hatasıydı ve her ADR bunlardan birini kaydediyor.

## Tek teslimat

Raporun 15. sayfasındaki karşılaştırma tablosunun YERKON bloğu: dört satır
(şehir içi, kırsal, tünel, ağırlıklı), on sütun. Her sayı bir veri
sayfasına, yayımlanmış bir ölçüme ya da açıkça söylenmiş bir varsayıma
kadar izlenebilir.

Rapor OPEX sütununu dört satır için de boş bırakıyor. Doldurmak kapsam
içinde; oranlar modüler yapılandırmadır ve sonradan araştırılacaktır
(ADR-0006).

## Değişmeyen kısıtlar

- **Menzil.** En az 5 km, hedef 5–10 km, 15 km'ye kadar değerlendirilmiş;
  yalnızca raporun malzeme listesinin adını verdiği modüllerle ve onların
  stok anteniyle. Daha iyi bir anten varsayılmıyor.
- **Yolların eğimi vardır.** Hiçbir şey bir alıcıyı sabit bir yüksekliğe
  sabitlemez (ADR-0004).
- **Kestirici, yükseklik kısıtı olmayan bir tümleştirmedir.**
- **Hizmet alanı, direklerin eriştiği gerçek alandır**, koridor şeridi
  değil.
- **Montaj karışıktır**: mevcut yol donanımı (levhalar, portallar, panolar)
  ile amaca özel direkler bir arada.
- **Bir koridor her şeyden birden fazlasını taşır**: birkaç montaj üzerinde
  birkaç direk modülü ve havayı paylaşan farklı türden birkaç birim
  (ADR-0014).
- **Sayılar virgüllü ondalık ayırıcı kullanır, binlik ayırıcı kullanmaz.**
- **Bir şeyi değiştirmek başka bir şeyi zorluyorsa onay gerekir**;
  değişecek her değeri listeleyen bir panel olarak gösterilir ve bütün küme
  için tek bir evet/hayır ile cevaplanır. Hem komut satırı hem uygulama
  aynı paneli çizer (ADR-0009). Kuruldu.
- **İki dil, yan yana.** Türkçe ve İngilizce; hiçbiri diğerinin çevirisi
  değil. Değerler, geometri ve her sonuç ikisinde aynıdır (ADR-0035).

## Kurulmuş olanlar

| Modül | Neyin sahibi |
|---|---|
| `evidence.py` | `Sourced` ve `Provenance`; bir veri sayfası değeri ile bir tahmin birbirine benzemesin diye |
| `hardware.py` | raporun adını verdiği modüller, yayımlanmış değerleriyle |
| `regulatory.py` | her bölgenin kurallarının izin verdiği: Türkiye, Avrupa, Amerika, lisanslı |
| `rf.py` | link bütçesi |
| `world.py` | arazi, eğimli yol güzergâhları, montaj yapıları ve yansıtıcı zemini yerden yere değiştiren yama örgüsü |
| `site/` | bir kez önbelleğe getirilen gerçek zemin, binalar, yollar, yol kenarı yapıları ve (istenirse) hava fotoğrafı, artı paketin içinde gelen dört Ankara sahası |
| `observation.py` | kestiricinin görebileceği tek tip; hiçbir şey import etmez |
| `ranging.py` | çift yönlü alışveriş, saatleri ve hava süresinde maliyeti |
| `estimator.py` | menzilleri konuma çevirir, başka hiçbir şey görmez |
| `evaluate.py` | yolculuklar, sabitleme başına hata örnekleri, kullanılabilirlik, hizmet alanı, ve taramanın dört okuması (sayım, marj, geometri, beklenen hata) |
| `cost.py` | malzeme listesinden CAPEX, envanterden OPEX |
| `scenarios.py` | tablonun anlattığı üç yerleşim, yapılandırma olarak |
| `report.py` | dört satır, on sütun ve altlarındaki notlar |
| `terms.py` | adlandırılmış yedi hata kaynağı; her biri kapatılabilsin diye |
| `budget.py` | dağılım: her kaynağın neye değdiği, yeniden koşarak |
| `layout.py` | direklerin nereye konulacağı: sekiz adlandırılmış yöntem, tek dikiş `place(plan, ground)` |
| `siting.py` | bir hedefi karşılayan en ucuz yerleşimin aranması |
| `settings.py` | raporun vermediği her değer ve bir yerleşimi şekillendiren her sayı, `defaults.toml`'dan |
| `options.py` | adlandırılmış yerleşim seçenekleri: kısa bir düzenleme listesi ve gerekçesi |
| `solve.py` | bir hedefi karşılayan en ucuz düzenin aranması |
| `parallel.py` | bağımsız koşuların makinenin çekirdeklerine yayılması |
| `deliver.py` | bütün çalışmanın Markdown olarak yazılması |
| `calibrate.py` | bir MATLAB ölçümünün varsayılan olarak geri okunması |
| `language.py` | iki dil: projenin kendi kurduğu cümleler, ikisinde de |
| `viewer/` | yerel web uygulaması: durum, sahne, sunucu, kendi çizicisi ve komut satırının her fiili (`tasks.py`, `jobs.py`) |
| `design.py` | birinin seçtiği ayarlar ve neyi ima ettikleri |
| `proposal.py` | onay paneli: bir düzenleme, bir evet/hayır, her sonuç gösterilmiş |
| `numbers.py` | virgüllü ondalık ayırıcı, binlik ayırıcı yok |
| `routes.py` | alıcının sürdüğü şekil: yedi güzergâh, tek dikiş `trace(trip, course)` |
| `presets.py` | adlandırılmış düzenlemeler: bir sekmenin tamamı, kaydedilip geri yüklenen |
| `viewer/static/map.js` | yer seçici: kayan harita, serbest çizilen kutu, ad araması |
| `cli.py` | `fetch`, `design`, `table`, `view`, `site`, `budget`, `defaults` ve `calibrate` fiilleri |

`tests/test_architecture.py` import'ları denetler, böylece kestirici gerçeğe
erişemez. Bilerek bir kural değil, bir testtir.

### Çalışmanın üzerinde döndüğü tek modül

`rf.py` tek bir hesaptan iki ayrı şeye karar verir: bir bağlantının
kapanıp kapanmadığına ve ne kadar hassas ölçebildiğine. İkisini bir arada
tutmak, menzili bir sabit değil bir sonuç yapan şeydir (ADR-0002); ayırmak
ise bu projeyi sessizce bozma ihtimali en yüksek değişikliktir.

ADR-0007'nin korumak için var olduğu ayrım: **erişmek ölçmek değildir.**
15 km'deki bir bağlantının elinde hâlâ 29 dB vardır ve mesafeyi hâlâ yirmi
altı metreye ölçer. Bağlantı kapanmasını kapsama gibi bildiren her şey
yanlıştır.

## Geriye kalanlar

Özgün listedeki her şey kuruldu. Kalan kod değil, ölçüm.

1. **Değerler.** Hepsi `src/yerkon/defaults.toml` içinde; her birinin neyi
   etkilediği ve ölçülmüş olanlarda iki katına çıkarmanın ne yaptığı
   yazılı. İş listesi için `yerkon defaults --full`. En sonuçlu olanı direk
   maliyeti: yerleşim araması mevcut levhaların direkleri beş buçuk kat
   yendiğini söylüyor ve başabaş noktası 6588 TL.
2. ~~**Frekans düzeltmesinden sonra kalan saat kayması.**~~ Yapıldı:
   2026-09-10'da 0,0793 ppm ölçüldü (ADR-0018) ve dosyadaki tahmin olmayan
   tek değer o. Ondan geriye kalan bir tezgâh: benzetim toplanır gürültüyü
   kapsıyor; faz gürültüsünü, çok yolluluğu ve alışveriş sırasında
   sürüklenmeyi kapsamıyor.
3. **Uygulama tabanı**, 2,94 m, bir benzetim değil bir tezgâh istiyor. 1625
   kHz'de tek bir çip 184 m uçuştur, yani bir dalga formu benzetimi 18 m der
   ve bir ölçümle, sebebi zaten anlaşılmış biçimde çelişir. SX1280'in ölçüm
   zamanlaması sembol ilintisinden gelmiyor; parçanın içindeki belgesiz bir
   mekanizmadan geliyor.
4. **Hangi yapının gerçekte nerede durduğu.** Yerleşim aramasının cevabı
   etütle birlikte oynuyor ve varsayılanlar tipik bir Türk karayolu kesimi
   hakkında bir varsayım.
5. **Yolların kendisi.** Binalar halledildi: Overpass bu ağdan
   erişilemiyor ama Overture Maps aynı veriyi genel bir nesne deposundan
   veriyor ve dört Ankara sahası da artık bina taşıyor — şehir içi satırın
   engeli artık gerçekten orada duran 5 231 binadan geliyor, kilometre
   başına bir engel kaybı değerinden değil (ADR-0038).

   **Yollar da geldi** (ADR-0046): dört saha da yol taşıyor — Kızılay
   1 638, Gölbaşı 5 905, Polatlı 5 365 parça — ve yol kenarında direğe
   uygun yapılar da (232 / 438 / 22 / 0). Yani hem gerçek yolu süren
   güzergâh hem de direği zaten duran bir yapıya cıvatalayan yerleştirme
   artık koşuyor.

   **Kalan, yayımlanan satırların bunu kullanması.** `scenarios.py`'deki
   üç satır hâlâ zeminin üzerinde bir dikdörtgen tur sürüyor; gerçek
   güzergâh görüntüleyicide seçilebiliyor ama tabloyu süren senaryolara
   girmedi. Kırsalda %89,6 kullanılabilirlikte kalan başarısızlıklar
   yoldaki zemindir ve bir yolu izleyen yolculuk bunun çoğundan kaçınırdı
   (ADR-0022) — bu artık bir veri işi değil, bir karar.

   Zeminin *fotoğrafı* ayrı bir şey ve geldi (ADR-0041) — ama yalnızca
   çiziliyor, hiçbir sayıya girmiyor.
6. **Direklerin gerçekte ne kadar iyi ölçülebileceği.** `yerkon budget`
   bunu tünel satırı için en sonuçlu tek değer yapıyor: varsayılan 0,15
   m'de orada 1,84 m konum hatasına değiyor, diğer her şeyin toplamı olan
   0,17 m'ye karşı; çünkü tünelin geometrisi bir menzilin sigmasını on
   sekizle çarpıyor ve bir etüt hatası ortalamayla asla kaybolmuyor. Şehirde
   0,09 m'ye değiyor ve önemi yok. Tek bir sayı, iki zıt cevap; ve bunu
   yalnızca gerçek bir etüt çözer.

7. ~~**Aramanın çıtası ile alan sütununun saydığı şey aynı değil.**~~
   Yapıldı (ADR-0047). Üç ayrı hataydı: arama 2B seyreltmenin alt
   sınırını (üç) bir yerleşimin gereksinimi (dört) yerine kullanıyordu;
   aynı sayı `AnchorRun.cover_k` içinde üçüncü kez yazılıydı ve o kopya
   kazanıyordu; ve arama, `reach_of`'un kendi belgesinin "bir iddia
   değil" dediği düz arazi rakamına karar verdiriyordu. Kızılay'da
   0,08 km² olan hizmet alanı **8,60 km²** oldu; Gölbaşı şehir içinde
   arama artık **23 direkle 41,24 km²** veriyor, ızgaranın 36 direkle
   verdiği 29,64'ten iyi.

   Ondan geriye iki şey kaldı. **`greedy-coverage` hâlâ işe yaramaz bir
   yerleşim üretebiliyor** — Gölbaşı şehir içinde üç direkle 0,00 km².
   Bu MCLP'nin tanımı ve ADR-0040 zaten bunu söylemek için var, ama
   arayüzde seçilebilen bir seçenek olarak duruyor. Ve **arama çıtasına
   ulaşamadığında bunu söylemiyor**: Kızılay'da 478 m'lik bir diskle
   HDOP ≤ 2 hiç karşılanmıyor, arama adayları tükenene kadar gidiyor
   (232 direk — sahadaki monte edilebilir yapı sayısı), ve dışarıdan
   çıtasını karşılayıp duran bir aramadan ayırt edilemiyor. ADR-0023'ün
   uyardığı şey tam olarak bu.

## Açık sorular

- **OPEX oranları ve saha maliyetleri.** Her biri `ASSUMPTION` işaretli,
  mertebe düzeyinde bir vekil ve birlikte bir maliyetlendirmenin %99'unu
  ediyorlar. 85000 TL'lik direk değeri en sonuçlusu: amaca özel direklerin
  mi mevcut yol donanımının mı kazanacağına o karar veriyor ve bu karar,
  telsiz seçiminin etkilediği her şeyden daha değerli.
- **Frekans düzeltmesinden sonra kalan saat kayması**, milyonda yarım
  parça, ölçüm modelindeki en az desteklenen sayıydı. Yavaş telsizde tek
  yönlü ölçümün kullanılabilir olup olmadığına o karar veriyor ve ölçülmeye
  değer ilk şeydi.
- **Çok yollu kanal ve uygulama tabanı** MATLAB'a karşı kalibrasyon
  istiyor. Taban şu anda telsiz başına yayımlanmış tek bir ölçüm ve model
  artık bunun çoğunun zamanlama çözünürlüğü değil saat olduğunu söylüyor;
  aynı ölçüm bunu doğrulayabilir ya da çürütebilir. Dağılım bahsi
  yükseltiyor: SX1280'in 2,94 m'lik tabanı hem şehir içi satırın (1,79
  m'nin 1,22 m'si) hem ağırlıklı satırın en büyük tek katkısı, dolayısıyla
  o sayının gerçekte ne olduğu bütün tablonun açık yol hakkında ne
  söylediğine karar veriyor.

## Sayfanın gerçekten yürünmesinden çıkanlar

Üç ayrı hata, birer birer tarayıcıda bulundu (`yerkon view`, her yöntem,
her güzergâh, ayarlar, simülasyon, harita):

- **Kart "6 direk" diyordu, sahnede 26 direk vardı.** Sahne bir direğin
  hangi gruba ait olduğunu yerleştirmeyi ikinci kez çalıştırarak
  buluyordu, ve ikinci çağrıda yol da yapılar da ölçülen menzil de
  yoktu. Tanınmayanlar renksiz, halkasız, sayılmadan duruyordu
  (ADR-0049). Aynı düzeltme `greedy-dop`'un sahne başına iki kez
  aranmasını da bitirdi: 21,8 s → 9,3 s, ikinci seferde 0,1 s.
- **Panel çalışırken bir önceki düzenlemenin sayılarını gösteriyordu.**
  Şehirden kırsala geçişte 36 direk ile 219 km² yan yana duruyordu
  (ADR-0050). Artık hesaplanan bir sayı `…`, olmayan bir sayı `—`.
- **`pip install -e ".[dev]"` ile kurulan bir kopya saha indiremiyor**
  ama sayfa bunu ancak kutu çizilip getirme başlatıldıktan sonra
  söylüyordu (ADR-0051). Artık panel baştan söylüyor ve komutu veriyor.

## Bu projenin şimdiye kadar yanlış yaptıkları

Her biri tekrarlanmaya değmeyecek bir hata olduğu için tutuluyor.

- Zemine yakın bağlantılar için serbest uzay yol kaybı, kaybı 13–34 dB
  eksik gösterdi ve "50 dB payla 10 km" iddiasını üretti. Yerine iki ışınlı
  zemin yansıması geçti (ADR-0007).
- "En geniş bant genişliğini kullan" yanlıştı. Konum hatası bant
  genişliğinde U biçimlidir, çünkü geniş bir kanal çok yolluluğu ayrı
  tepelere çözer ve bir tepe dedektörü en güçlüsünü seçer — engellenmiş bir
  kanalda o da bir yansımadır.
- Senaryolar arasında paylaşılan durumlu bir rastgele sayı üreteci, eski
  deponun belgelerindeki her taranmış karşılaştırmayı kirletti.
- Tek başına Cramér-Rao, 100 m'de dar bantlı bir telsizden 2 cm iddia
  ediyordu; ölçülen yaklaşık 3 m. Model artık sınır ile ölçülen tabanın
  büyüğünü bildiriyor.
- LAMBDA80-24S bir anten değil, SX1280 modülüdür. Anten Inventek
  W24P-U'dur.
- Dünya tümseği, teğet düzlem biçimi değil orta nokta çökmesi
  `d₁d₂/(2kR)`'dir; teğet düzlem biçimi 15 km'de gereken açıklığı dört kat
  fazla gösteriyordu.
- "Buradan yükseklik verisi indiremem" yanlıştı; üç sunucuya bakılarak
  çıkarılmıştı. Copernicus karoları doğrudan genel nesne depolamasından
  geliyor.
- Konumsal `{}` ile iki dil: Türkçe cümle toplamı önce sayar, İngilizce
  varsayımı önce sayar ve biri sessizce diğerinin sayılarını alır. İki
  alanı olan ilk cümlede aldı da (ADR-0035).
- İki dil yapıldıktan sonra bile uzun işlerin ilerleme kütüğü İngilizce
  kaldı, çünkü satırları bir kataloğa değil `tell`'e verilen sabit
  dizgilere yazılmıştı; İngilizce bir satır, biri sayfayı değiştirene
  kadar sıradan koddan ayırt edilemiyor. Artık bir sınama `tell`'e sabit
  dizgi verilmesini reddediyor (ADR-0035).
- "Tur başına on iki direk yoklamak 5,5 puan eder" bulgusu, kısmen
  ölçülmemiş zeminin ürünüymüş. Yalnızca indirilmiş zemin üzerinde
  sekizin üstündeki sıralama tohumla dönüyor ve komşu değerler
  arasındaki fark tohumlar arasındaki kadar (ADR-0037). Bunu, tek tohuma
  güvenmemek için yazılmış bir sınama yakaladı.
- Merkez kutusunu boş bırakıp Getir'e basmak, arka planda
  `KeyError: 'south'` veriyordu: sayfa dört köşe göndermeyi bırakmıştı
  ama görev hâlâ onlara düşüyordu. Daha kötüsü, kutunun kendi örnek
  yazısı `39,9250 32,8370` idi — virgüllü ondalık, yani ayırıcıyı
  virgülden arayan okuyucu dört sayı görüyordu. Yani *doğru* yazan da
  çöküyordu. Artık bir virgülün ayırıcı mı ondalık mı olduğuna yanındaki
  boşluk karar veriyor, ve yazım hatası yığın izi değil cümle üretiyor.
- Sahalar bina taşımıyordu ve sebep model değil ağdı: Overpass bir sorgu
  servisi ve buradaki ağ onu reddediyor. Overture Maps aynı veriyi genel
  nesne deposundan veriyor ve o açık; dördü de artık bina taşıyor
  (ADR-0038). Engel bir kere daha iki kez sayılıyordu — gerçek binalar
  *artı* kilometre başına 30 dB — ve ikisi birlikte şehir içi satırı
  %71'e indiriyordu; tek başına hiçbiri indirmiyor.
- Hazır gelen satırlar, altlarında indirilmiş ızgaradan büyüktü: şehir
  içinde 46 direğin 10'u, kırsalda 33'ün 5'i ölçülen zeminin dışında
  duruyordu. `height_at` kenarın dışında kırptığı için hata yükselmiyor,
  sınır satırı bir düzleme uzuyor ve düzlem üzerinde her link kapanıyordu.
  Kırsal kullanılabilirliğin on yedi puanı oradan geliyormuş (ADR-0037).
- Ölçülmüş zemin seçilince kilitlenen üç değerin yalnızca sürgüsü
  kilitleniyordu; yanındaki sayı kutusu canlı kalıyordu. Gri bir
  sürgünün altında canlı bir kutu, üç durumun en kötüsü: kilidin
  sebebini gösteriyor ve kilidi tutmuyor. Aynı üç değer tünel satırında
  da hiç okunmuyor ve orada hiç kilitlenmemişti (ADR-0036).
- Bir sınama kalıntısı depoya işlenmişti: `site/places/probe`, yükseklik
  kaynağı `fake`, getirilme zamanı `now`. Zemin listesinde dört gerçek
  getirmenin yanında, onlardan ayırt edilemeden duruyordu. Uydurma bir
  ölçümü gerçek olanların arasına koymak, bu projenin kaçınmak için
  kurulduğu tam olarak o şey (ADR-0001); silindi (ADR-0041).

  **Sayfayı sınayan için tuzak:** `Getir` düğmesine tarayıcıdan basmak
  gerçekten getirir ve paketin `site/places/` klasörüne gerçekten yazar
  — bu tasarım gereği (ADR-0039), çünkü çıplak bir ad oraya yazmasa yer
  zemin listesinde görünmez. Yani bir kullanıcı fetch'i ile bir sınama
  artığı diskte aynı şeye benziyor, ve bunu bir sınamayla yasaklamak
  kullanıcının normal akışını kırardı. İşlemeden önce `git status`
  okumak; ya da sayfayı sınarken `/api/run` isteğini kesip ne
  gönderildiğine bakmak, ki o zaten daha iyi bir sınama — soru
  Copernicus'un ne cevapladığı değil, panelin ne sorduğu.
- Gri gösterme kuralı yalnızca `label.knob.dead` idi, dolayısıyla yeni
  eklenen bir onay kutusu `dead` sınıfını alıyor, sebebini de taşıyor,
  ama rengi değişmiyordu: kilitli ama kilitli görünmeyen bir denetim.
  Kural artık `label.dead` (ADR-0036).
- Saha boyu/eni sürgüleri 500'er metre adımlıydı, ama bir getirme
  yuvarlak sayıyla gelmiyor: Kızılay 2970 m. Tarayıcı ızgaraya düşmeyen
  değeri aşağı yuvarladığı için **sürgü 2500'de, kutu 2970'te** duruyordu
  — kolun iki yarısı farklı şey söylüyordu, ki bu projede üçüncü kez
  (ADR-0048). Adım 10 m oldu; tavan da artık kolun iki yarısına birden
  konuyor.
- "Direk yok" hatası `anchors()` içindeydi, yani üzerinde hiçbir şey
  olmayan bir sekme *çizilemiyordu* — ve üzerine bir şey kurulacak boş
  sayfa tam olarak budur. Hata doğruydu, katmanı yanlıştı: çizmek boşu
  kabul eder, bir sayı üretmek etmez (ADR-0043).
- Bir düzenleme 12 direkle kaydedilip 9 ile geri geldi. Altından iki
  hata çıktı: yükleme `within_site()` uygulayıp geri getirmek yerine
  sessizce düzeltiyordu, ve "Grup ekle" sahanın uzunluğuna bakmadan
  3000 m'ye uzanan bir dizi kuruyordu — Kızılay 2970 m, yani son sütun
  sahanın dışındaydı ve hiçbir şey yükselmiyordu, çünkü arazi kendi
  dışında kırpar (ADR-0037). İkisi de düzeldi.
- Yazdığım ilk yuvarlak-gidiş sınaması sunucunun kodunu değil, benim
  kopyaladığım mantığı sınıyordu — yani sunucudaki bir gerilemeyi
  göremezdi. Gerçek işleyiciden geçecek şekilde yeniden yazıldı, ve
  yakaladığını hatayı kasten geri koyarak denedim.
