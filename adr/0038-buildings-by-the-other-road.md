# ADR-0038: binalar, öteki yoldan

## Durum

Kabul edildi.

## Bağlam

Bu proje kurulduğundan beri hiçbir sahası bina taşımıyordu. Sebep model
değil ağdı: OpenStreetMap'e erişim Overpass üzerinden gidiyor, Overpass
bir sorgu servisi ve bu çalışmanın koştuğu ağ onu reddediyor (ADR-0021'de
kayıtlı, bugün yeniden denendi: üç ayna da CONNECT'e 403).

Bina olmayınca şehir içi satırın engeli tek bir sayıyla temsil
ediliyordu: kilometre başına 30 dB'lik yayvan bir kayıp. Değerin kendi
notu ne olduğunu söylüyordu — "şehir içi bir direğin ne kadar
eriştiğini, dolayısıyla şehir içi satırın tamamını" belirleyen bir
vekil.

Aynı anda, ekranda sahanın etrafında büyük bir boş alan duruyordu.
Çizilen ağ, taramanın kenar payı kadar her şeyin ötesine uzanıyordu;
`height_at` ise ızgarasının dışında kenara kırpar. Kızılay'da bu, 3,0
km'lik bir sahanın etrafında 10,7 km'lik bir yaprak demekti: **ekrandaki
zeminin %92'si uydurma**, gerçek tepelerle aynı yeşile boyanmış.

## Karar

**Ölçümün bittiği yerde arazi de biter, ve bunu arazi bilir.**
`Terrain.extent_m`, zeminin ne kadarının ölçüldüğünü yerel metre olarak
taşır; modellenmiş zeminde yoktur, çünkü o bir ızgara değil bir işlevdir
ve her yerde cevap verir. Bir tünelde yalnızca x'te vardır: `Sloping`
y'yi hiç okumaz, dolayısıyla enine söylenecek bir kenar yoktur.

Üç şey onu okur: çizilen ağ, ayrıntı ağı ve **kapsama taraması**.
Sonuncusu bir başlık sayısına karar veriyordu ve kimse bakmamıştı: şehir
içi satır, 8,73 km²'lik bir sahanın üzerinde **31,72 km² hizmet alanı**
bildiriyordu. Bir saha kendinden büyük bir alana hizmet edemez.

**Overture Maps, Overpass'in yanına ikinci bir bina kaynağı olarak.**
Overture, OpenStreetMap artı Microsoft ve Google'ın makineyle çıkarılmış
taban alanlarından kurulur — yani başka bir ölçüm değil, dünyanın daha
çoğu doldurulmuş OpenStreetMap verisi. Önemli olan yol: Overpass bir
sorgu servisi, Overture ise Copernicus karolarının geldiği türden bir
genel nesne deposuna yapılan menzilli okuma. Hangisinin cevap verdiği
yerin değil ağın bir özelliği, o yüzden ikisi de sunulur ve ilk cevap
veren kazanır.

Satırları bulmak işin püf noktası. Tema 512 dosyada çeyrek terabayt, ama
uzamsal sıralı ve her satır grubu kendi sınır kutusunu parquet
künyesinde taşıyor. 512 künyeyi paralel okumak bir dakika sürüyor ve
şehir boyunda bir kutu için üç dosyada beş satır grubu buluyor —
gerçekten okunacak dört megabayt. Künye dizini sürüm başına diske
yazılıyor, yani ikinci indirme bedava.

Veri de daha iyi: Overpass'ten merkezler isteniyordu, dolayısıyla taban
alanı yükseklikten *varsayılıyordu*; Overture'ın her satırı kendi sınır
kutusunu taşıyor, dolayısıyla yarıçap **ölçülüyor**.

**Kendi binasını getiren bir zemine yayvan engel kaybı işlenmez.**
O değer, arazinin gösteremediği engelin vekilidir; arazi onu
gösteriyorsa ikisini birden saymak aynı binaları iki kez saymaktır.
Kızılay üzerinde ölçüldüğünde — taban alanları zeminin %40'ını kaplıyor:

| şehir içi satır | kullanılabilirlik | HPE P50 |
|---|---|---|
| yalnız 30 dB/km (eski) | %97,62 | 1,79 m |
| yalnız binalar | %99,79 | 2,14 m |
| **ikisi birden** | **%71,22** | **3,22 m** |

Üçüncü satır Ankara'yla değil aritmetikle kötüleşmiş bir satırdır.
Görüntüleyicide *Engel kaybı* denetimi, zemin bina getiriyorsa griye
döner ve sebebini söyler (ADR-0036).

**Binalar bir uzamsal dizinden sorulur.** Link bütçesi her yol için
altmış beş noktada "burada ne duruyor" diye sorar. Kızılay'ın 5 231
tabanını her seferinde baştan sona taramak tabloyu bitemez hale getirdi.
Tekdüze hücrelerden bir ızgara, her soruyu o hücreye değen birkaç binaya
indirir. İlk kullanımda kuruluyor ve turşuya girmiyor: bir işçi onu
almak yerine yeniden kuruyor (ADR-0025).

## Sonuçlar

Dört Ankara sahası binalarıyla yeniden indirildi: kizilay 5 231,
polatli 20 899, golbasi 26 282, kizilcahamam 43. Yükseklik hâlâ çoğunlukla
eksik — Kızılay'da 42'si etiketli, 77'si kat sayısından, 5 112'si
varsayılan — ve künye üçünü de sayıyor.

**Tablo:**

| | ADR-0037 sonrası | şimdi |
|---|---|---|
| Şehir içi HPE P50 | 1,79 m | 2,14 m |
| Şehir içi HPE P95 | 4,79 m | 5,36 m |
| Şehir içi kullanılabilirlik | %97,62 | %99,79 |
| Şehir içi alan | 7,87 km² | 8,93 km² |
| Kırsal HPE P50 | 3,13 m | 3,11 m |
| Kırsal alan | 427,50 km² | **218,75 km²** |
| Kırsal CAPEX | 6 253 TL/km² | **12 235 TL/km²** |
| Ağırlıklı HPE P50 | 2,08 m | 2,37 m |

Şehir içinde binalar doğruluğa mal oluyor (1,79 → 2,14 m) ve iki kez
sayılan engel kalkınca erişim ile kullanılabilirlik yükseliyor. Kırsalda
doğruluk yerinde duruyor ama **alan yarıya iniyor**, çünkü tarama artık
ölçülmemiş zemini saymıyor; kilometrekare başına maliyet de buna bağlı
olarak iki katına çıkıyor.

Şehir içi alanın 8,93 km² çıkması sahanın 8,73 km²'sinin biraz üstünde:
tarama 250 m'lik hücrelerle sayıyor ve son hücre kenardan taşıyor. %2,3;
ölçülmemiş zemin değil, taramanın kendi çözünürlüğü.

## Yapılmayan

**Copernicus bir yüzey modelidir (DSM), çıplak toprak değil.** 30 m
adımda binaları bir ölçüde zaten içerir, dolayısıyla Overture
yüksekliklerini üzerine katlamak bina yüksekliğini kısmen iki kez sayar.
Ne kadarını, bu kod tabanı bilmiyor: bunu söyleyecek olan aynı bölge için
bir çıplak toprak modeli (DTM) ile karşılaştırmaktır, ve o yapılmadı.
Yayvan engel kaybındaki iki kez sayma ölçüldü ve giderildi; bu ikincisi
ölçülmedi ve burada yazılı duruyor.
