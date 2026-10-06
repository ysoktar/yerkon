# ADR-0020: kimsenin üzerine iş yapamayacağı bir hata değeri yarım sonuçtur

## Durum

Kabul edildi.

## Bağlam

Tablo, şehirdeki bir alıcının ellinci yüzdelikte 1,24 m, bir tünelde ise
1,81 m şaştığını söylüyor. İkisi de doğru ve ikisinin de üzerine iş
yapılamaz. Elinde bütçe olan birinin gerçekte sorduğu soru, o metrelerin
hangisini kaldırmanın en ucuz olduğudur ve tablo bunu cevaplamaz. Daha
kötüsü, sezgi yanlıştır: tünel, her donanım ölçütüne göre çalışmadaki en
hassas yerleşimdir — darbeli bir telsiz, on santimetrelik bir ölçüm tabanı,
yüz elli metre aralıklı direkler — ve üçünün *en az* hassası olarak çıkar.

Cevaplamanın iki yolu vardı.

**Analitik bir hata bütçesi** her terimi doğrusallaştırılmış bir geometriden
geçirir ve kareli toplar. Anlıktır ve aynı şeyin ikinci bir modelidir.
Benzetimle çeliştiği yerde hangisinin yanlış olduğunu hiçbir şey söylemezdi
ve çelişki, tam olarak cevabın en çok önem taşıdığı yerde en büyük olurdu:
bir koridorun tekile yakın geometrisinde, ortalamayla kaybolmayan bir
yanlılıkta, dakikalardır koşan bir süzgeçte.

**Bir hata kaynağı susturularak benzetimin yeniden koşulması** yavaştır —
senaryo başına on altı tam koşum, her biri birkaç dakika — ve tabloyla
çelişemez, çünkü tablonun kendi motorunun bir terimi kapatılmış hâlidir.

## Karar

Yeniden koşarak dağıt. `yerkon.terms.Terms` yedi kaynağı adlandırır;
`run_scenario` birini alır ve söyleneni susturur; `yerkon.budget`
birleşimleri koşar ve bildirir.

Koşumları karşılaştırılabilir kılan üç kural.

**Alıcının inancı değişmez.** `measure`, ne susturulursa susturulsun her
gözlemde modellenen bütün varyansı bildirmeye devam eder. Yalnızca gerçekten
enjekte edilen hata değişir. Süzgecin varyansını da daraltan bir koşum
kazançlarını sıkılaştırırdı ve iki böyle koşum arasındaki fark, kısmen
incelenen hata değil kestiricinin kendini yeniden ayarlaması olurdu.

**Taban bir terimdir, bir kırpma değil.** `sigma_terms_m`, uygulama tabanını
ona ulaşmak için kareli olarak eklenmesi gereken şey olarak döndürür; fizik
zaten onun üstündeyse bu sıfırdır. Toplandığında üç terim
`max(hypot(dalga formu, saat), taban)` değerini tam olarak yeniden üretir,
yani ayrım yayımlanmış hiçbir sayıyı değiştirmedi.

**İki okuma da yazdırılır.** *Tek başına*, o kaynak tek olsaydı kalacak
hatadır; *kalkarsa*, o kaynak gidip gerisi kalırsa bütünün ineceği yerdir.
Muazzam farklıdırlar ve yalnızca ikincisi bir satın alma kararıdır: 2,00
m'lik bir toplamdan 0,50 m çıkarmak 1,94 m bırakır. Yalnızca ilk sütunu
yazdıran bir rapor, altı santimetre değerinde iyileştirmeler satardı.

## Sonuçlar

Dağılım, tablonun davet ettiği okumayı hemen tersine çevirdi.

**Tünelde** direk etüt hatası tek başına 1,84 m değerinde ve diğer her şey
birlikte 0,17 m. Tünelin geometrisi bir menzilin sigmasını on sekizle
çarpıyor, çünkü her direk aynı çizginin dört metre içinde; ve en sert
çarptığı şey ortalamayla asla kaybolmayan tek hata. O yerleşime daha iyi bir
telsiz almak hiçbir şey satın almıyor. Askılarını düzgün ölçmek onu 1,81
m'den 0,17 m'ye indiriyor.

**Şehirde** sıralama ters dönüyor: modülün ölçüm tabanı 1,13 m, etüt hatası
0,09 m değerinde. Geometri çarpanı 0,6 — *birin altında*. Üzerinde bir
süzgeç koşan bir alan yerleşimi, tek bir menzilden daha iyi çıkıyor; bu da
koridor çerçevesinin gizlediği şeyin niceliksel hâli.

Dağılımın ürettiği bir değer bir bulgu değil zeminin bir yapaylığıydı ve
bunu görmek ADR-0021'i gerektirdi. `excess_path` dört satırda da tam olarak
0,00 m çıkıyordu; bu "engellerin maliyeti yok" diye okunuyordu ve aslında
"bu üç senaryonun ikisi bir düzlemin üzerinde duruyor ve bir düzlem hiçbir
şeyi engelleyemez" demekti. Gerçek Ankara zemininde her satırdaki üçüncü ya
da dördüncü en büyük terim. Bir dağılım, ancak yeniden koştuğu dünya kadar
dürüsttür.

Bedeli koşum süresi konusunda dürüstlüktür: `yerkon budget` saniyeler değil
dakikalar sürer ve başlamadan önce bunu söyler. Alternatifi, anında gelen ve
hiçbir şeye karşı denetlenemeyen bir sayıydı.
