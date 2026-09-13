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
| `site/` | bir kez önbelleğe getirilen gerçek zemin ve binalar, artı paketin içinde gelen dört Ankara sahası |
| `observation.py` | kestiricinin görebileceği tek tip; hiçbir şey import etmez |
| `ranging.py` | çift yönlü alışveriş, saatleri ve hava süresinde maliyeti |
| `estimator.py` | menzilleri konuma çevirir, başka hiçbir şey görmez |
| `evaluate.py` | yolculuklar, sabitleme başına hata örnekleri, kullanılabilirlik, hizmet alanı |
| `cost.py` | malzeme listesinden CAPEX, envanterden OPEX |
| `scenarios.py` | tablonun anlattığı üç yerleşim, yapılandırma olarak |
| `report.py` | dört satır, on sütun ve altlarındaki notlar |
| `terms.py` | adlandırılmış yedi hata kaynağı; her biri kapatılabilsin diye |
| `budget.py` | dağılım: her kaynağın neye değdiği, yeniden koşarak |
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
5. **Binalar ve yolların kendisi.** Zemini getiren makineden OpenStreetMap'e
   erişilemedi, dolayısıyla dört Ankara sahasının hiçbiri bir bina taban
   alanı ya da bir yol güzergâhı taşımıyor. İki sonucu var, ikisi de
   ihtiyatlı yönde: şehir içi satırın engeli gerçekten orada olan
   binalardan değil kilometre başına bir engel kaybı değerinden geliyor ve
   her kırsal yolculuk, zemini izleyen bir yol değil zeminin üzerinde bir
   dikdörtgen. Gerçek bir güzergâh kırsal değerleri yükseltirdi, çünkü
   yollar bağlantıların geçtiği yerden geçer. Overpass'a erişebilen bir
   makineden tek bir `yerkon fetch` ikisini de çözer. Bu artık kırsal satır
   ile daha iyi bir sayı arasında duran en büyük tek şey: %89,6
   kullanılabilirlikte kalan başarısızlıklar yoldaki zemindir ve açık arazi
   üzerindeki bir dikdörtgen yerine bir yolu izleyen bir yolculuk bunun
   çoğundan kaçınırdı (ADR-0022).
6. **Direklerin gerçekte ne kadar iyi ölçülebileceği.** `yerkon budget`
   bunu tünel satırı için en sonuçlu tek değer yapıyor: varsayılan 0,15
   m'de orada 1,84 m konum hatasına değiyor, diğer her şeyin toplamı olan
   0,17 m'ye karşı; çünkü tünelin geometrisi bir menzilin sigmasını on
   sekizle çarpıyor ve bir etüt hatası ortalamayla asla kaybolmuyor. Şehirde
   0,09 m'ye değiyor ve önemi yok. Tek bir sayı, iki zıt cevap; ve bunu
   yalnızca gerçek bir etüt çözer.

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
  yükseltiyor: SX1280'in 2,94 m'lik tabanı hem şehir içi satırın (1,62
  m'nin 1,14 m'si) hem ağırlıklı satırın en büyük tek katkısı, dolayısıyla
  o sayının gerçekte ne olduğu bütün tablonun açık yol hakkında ne
  söylediğine karar veriyor.

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
