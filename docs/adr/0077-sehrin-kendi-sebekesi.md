# ADR-0077: şehrin direkleri zaten elektrikli ve bir kısmı zaten bağlı

## Durum

Kabul edildi.

## Bağlam

Şehir içi satırın maliyet avantajı modelde vardı ve hiçbir yerde
yazmıyordu.

Bir şehirde direk taşıyacak yapı zaten duruyor: aydınlatma direkleri,
levhalar, portallar, ışıklı kavşakların sinyal direkleri. Hepsinin
ortak özelliği elektrik dağıtım şebekesine bağlı olması. Model bunu
`MountingOption.has_power` ile ta baştan biliyordu ve şehir içi satır
aydınlatma direği kullandığı için şebeke dışı besleme kalemini hiç
ödemiyordu. Ama tabloda bu bir *yokluk* olarak görünüyordu: ödenmeyen
bir satır kimsenin dikkatini çekmez.

Ne kadar olduğunu ölçtük. Aynı 36 direk, aynı 6,68 km², tek farkla —
şehrin yapılarını kullanmak yerine her direk için 25 m'lik bir direk
dikmek ve güneş paneli takmak:

| | mevcut yapılara | dikilen direklere |
|---|---|---|
| direk başına sermaye | 4 366 TL | 95 866 TL |
| CAPEX | 23 518 TL/km² | 516 388 TL/km² |
| OPEX | 10 088 TL/km²/yıl | 21 537 TL/km²/yıl |

**Sermayede 22 kat, işletmede 2,1 kat.** Tablodaki şehir içi
rakamlarının tamamı bu seçimin sonucudur ve site bunu hiç söylemiyordu.

İkinci bir şey de söylemiyordu, çünkü model onu henüz bilmiyordu.
Elektrik bir yapının verdiği iki şeyden yalnızca biri. Işıklı bir
kavşakta sinyal dolabı durur: hem besleme hem de trafik yönetim
merkezine giden bir hat. Belediyenin kameraları ve dedektörleri o hattı
zaten kullanıyor. Model ise her şehir içi direğine ayrı bir hücresel
veri paketi yazıyordu — 36 direk × 600 TL/yıl, işletme maliyetinin
%29,7'si.

## Karar

**Işıklı kavşaktaki direk bağlıdır.** Kataloğa
`at_a_signalised_junction()` girdi: aynı yapı, `has_backhaul=True`.
Yükseklik ve montaj bedeli *yeni yazılmıyor*, aydınlatma direğinden
türetiliyor — çünkü iki yerde duran bir sayı er geç iki farklı sayı
olur (ADR-0052, ADR-0076).

**Izgaranın dörtte biri kavşakta duruyor.** `urban.junction_every = 2`:
her ikinci sıranın her ikinci noktası. Bir şehrin ana caddeleri
ışıklıdır. Dörtte bir ihtiyatlı okuma; Ankara merkezinde ana cadde
kavşaklarının yarısı da savunulabilir ve iki katı tasarruf ederdi.

**Geometri kımıldamıyor.** Kavşak direği, aynı yükseklikte aynı
aydınlatma direği. Kullanılabilirlik ve yatay hata harfi harfine aynı
kalıyor; değişen tek kalem bağlantı. Kaba okumada: %86,24 ve 8,39 m
ikisinde de aynı, OPEX 10 709 → 9 915 TL/km²/yıl.

Bu bilerek böyle. Bir bağlantı tasarrufunun altına gizlice geometri
koymak, sonra "şehrin şebekesi doğruluğu artırdı" demek olurdu; artırmaz.

## Sonuçlar

Şehir içi işletme maliyeti %7,4 düştü, sermaye ve doğruluk sabit.

Site artık 22 katı söylüyor. Şehir içi satırın ucuzluğu bir tesadüf
değil, bir yerleşim kararıdır ve kararın bedeli yazılıdır.

Üç sınama tutuyor, üçü de yakaladıkları hatayı geri koyarak
doğrulandı: kavşak direği aynı yükseklik ve aynı bedel
(`test_world`), bağlantı kalemi dışında hiçbir kalem kımıldamıyor
(`test_cost`), ve şehir içi yerleşimi gerçekten kavşakları kullanıyor
(`test_ground`).

## Yapılmayanlar

**Sinyal direğinin kendisi kataloğa girmedi.** Bir sinyal direği 6 m,
aydınlatma direği 12 m. Direği kavşağa taşımak bağlantıyı bedava
yapardı ama altı metre yükseklik götürürdü. Direk aydınlatma direğinde
kalıyor, hattını yanındaki dolaptan alıyor — belediyenin kamerasının
yaptığı da bu.

**Kırsal satır değişmedi.** Orada ışıklı kavşak yok; 25 m'lik direğin
85 000 TL'si ve güneş panelinin 9 500 TL'si duruyor. Karşılaştırmanın
anlamlı olmasının sebebi de bu.

**Kavşak payı ölçülmedi.** Dörtte bir bir sayım değil, bir okuma.
Ankara'nın ışıklı kavşak envanteri sayılırsa bu değer değişir ve
ayarlar dosyasındaki tek satır onu değiştirir.
