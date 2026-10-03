# ADR-0081: direkler zaten yüksek olan yerlere, yöneylem aramasıyla

## Durum

Kabul edildi. Yayımlanan tablo değişmedi; arama simülatörde ve komut
satırında bir seçenek.

## Bağlam

Tablonun şehir içi ve kırsal satırları direkleri bir ızgaraya koyuyor:
şehirde 500 m, kırsalda 3 km arayla. Izgara kolay anlatılıyor ve kolay
fiyatlanıyor, ama zeminin sunduğu hiçbir şeyi kullanmıyor. Şehirde zaten
aydınlatma direkleri, tabelalar ve yüksek binalar var; kırsalda tepeler
ve yol boyunca dağıtım şebekesinin direkleri var. İstenen: vericileri
zaten yüksek olan, mantıklı yerlere koyan, ızgaradan başka bir yerleşim.

## Karar

**Adaylar zaten duran ya da zaten yüksek yerler** (`placement.candidates`):

- getirilen sokak donanımı: aydınlatma direği ve tabela;
- yüksekliği ölçülmüş binaların çatıları (şehirde 15 m, kırsalda 12 m ve
  üstü; çatının üstüne 2 m tutucu);
- çıplak zeminin yerel tepeleri (üzerlerine 25 m direk, çünkü orada bir
  yapı olduğunu bilmiyoruz);
- yol kenarı: şehirde aydınlatma direği, kırsalda dağıtım direği, yol
  boyunca her 150 m ya da 750 m'lik karede bir;
- ızgaranın kendi noktaları, ki arama ızgaradan kötü bir cevaba mecbur
  kalmasın.

**Kapsama bağlantı bütçesiyle karar veriliyor, diskle değil.** Her aday,
hizmet alanının hücrelerinde (şehirde 100 m, kırsalda 500 m) 1,5 m
yükseklikteki bir alıcıya karşı `evaluate.coverage`'ın kullandığı sınamayla
deneniyor: gerçek zemin, gerçek binalar, bağlantı kapanıyor ve menzil 5 m
toleransın içinde mi.

**Bir hücre, dört direk ona ulaştığında ve bu direkler çevresindeki dört
çeyreğin en az üçünde durduğunda hizmet almış sayılıyor.** İlk sürüm
yalnızca sayıyordu. Simülasyon o sürümün şehirde bulduğu yerleşimin P95
hatasını ızgaranınkinin neredeyse iki katı buldu: aynı caddeye dizilmiş
dört direk bir hücreye dört kez ulaşıyor ve cadde boyunca ölçmeyen hiçbir
şey bırakmıyor. Çeyrek koşulu bunu aramanın kendi sayımına taşıyor.

**Seçim bir bütçeli en çok k-örtme** (`placement.Cover`):

- açgözlü adım, lira başına en çok ilerlemeyi getiren adayı ekliyor;
- bırakma adımı, cevabın gerek duymadığı direkleri en pahalıdan
  başlayarak çıkarıyor;
- değiş tokuş adımı (Teitz ve Bart), seçilmiş her direği daha ucuz bir
  adayla, örtme korundukça değiştiriyor.

Maliyet bir direğin ömür boyu maliyeti: yatırım artı hizmet ömrü çarpı
yıllık işletme, `cost.price` üzerinden, yani bir oran değişikliği aramaya
tabloya ulaştığı yoldan ulaşıyor.

**İki amaç.** `better`: ızgaranın ömür boyu maliyetine en çok hücre.
`cheaper`: ızgaranın hizmet verdiği hücre payına en düşük maliyet.

**Hakem simülasyon.** Arama örtmeyi görüyor; simülasyon geometriyi,
turları, gölgeleri ve gürültüyü görüyor. Cevap, ızgaranın yanında aynı
alıcılar, aynı yolculuk ve aynı tohumlarla koşturuluyor.

## Sonuçlar

Hızlı okuma (`--fast`: profil aralığı kaba) ama dört gölge çekilişiyle;
tek çekilişte P95 çekilişten çekilişe fazla oynuyor ve bir karar
taşımıyor. Yayımlanabilir değil, karşılaştırma için.

Şehir içi, Kızılay:

| | Direk | P50 | P95 | Kullanılabilirlik | Alan km² | CAPEX TL/km² | OPEX TL/km² |
|---|---|---|---|---|---|---|---|
| Izgara | 36 | 2,61 | 9,61 | %85,30 | 6,84 | 16666 | 3679 |
| Arama, `better` | 36 | 2,75 | 9,02 | %84,95 | 7,27 | 15688 | 3463 |
| Arama, `cheaper` | 29 | 3,18 | 11,37 | %85,35 | 6,90 | 13315 | 2939 |

Kırsal, Polatlı:

| | Direk | P50 | P95 | Kullanılabilirlik | Alan km² | CAPEX TL/km² | OPEX TL/km² |
|---|---|---|---|---|---|---|---|
| Izgara | 49 | 2,64 | 10,80 | %74,03 | 248,25 | 1510 | 519 |
| Arama, `better` | 47 | 2,75 | 11,88 | %76,44 | 316,00 | 1573 | 357 |
| Arama, `cheaper` | 29 | 2,99 | 14,63 | %61,72 | 233,33 | 1235 | 302 |

- Şehirde `cheaper` ızgaranın kullanılabilirliğini (%85,35 ile %85,30)
  km² başına beşte bir daha az yatırım ve işletmeyle tutuyor; P95 9,61
  m'den 11,37 m'ye kötüleşiyor. `better` kullanılabilirliği neredeyse
  aynı tutuyor (0,35 puan aşağıda), P95'i 9,02 m'ye iyileştiriyor, alanı
  %6 büyütüyor ve km² başına %6 daha ucuz.
- Kırsalda `better` aynı paraya alanı %27 büyütüyor ve kullanılabilirliği
  2,4 puan artırıyor; km² başına işletme %31 düşüyor, yatırım %4 artıyor,
  P95 10,80 m'den 11,88 m'ye kötüleşiyor.
- Kırsalda `cheaper` önerilmiyor. Aramanın kendi sayımı ızgaranın hücre
  payını tutuyor, ama simülasyonun yolculuğunda kullanılabilirlik
  %74'ten %62'ye düşüyor. Arama hizmet alanının her hücresini eşit
  sayıyor; yolculuk bu alandan belirli bir çizgi. Hücre payının %36
  olduğu bir yerde ucuz cevap başka hücrelere hizmet verebiliyor.
- Şehirde arama çoğunlukla yol kenarındaki aydınlatma direklerini
  seçiyor, çatıları seçmiyor: sekiz yıllık çatı kirası (yılda 1200 TL,
  varsayım; toplam 9600 TL), aydınlatma direğindeki bir birimin bütün
  ömür boyu maliyetini (8763 TL) tek başına geçiyor. Kırsalda yol
  kenarı dağıtım direkleri, ızgaranın bir kısmı, birkaç tepe ve bir çatı
  seçiliyor.
- Bırakma ve değiş tokuş adımları açgözlü adımın maliyetini şehirde hiç,
  kırsalda %3 düşürdü.

## Doğrulamada bulunanlar

- **Polatlı'nın 20899 binasından 20887'si getirmenin varsayılan 9 m
  yüksekliğini taşıyor.** Yüksekliği ölçülmemiş bir çatı "zaten yüksek"
  bir yer değil. İlk kırsal arama bu çatılardan 63 tane seçmişti. Artık
  yalnızca yüksekliği ölçülmüş binalar aday; tam varsayılan yükseklikte
  etiketlenmiş bir bina da dışarıda kalıyor, bu da daha az çatı yönünde
  hata yapıyor.
- **Şehir ızgarasının 36 direğinden 13'ü bir bina izinin içine düşüyor**
  ve bu yüzden 12 m'lik aydınlatma direği 9 m'lik çatının üstünde, 21 m'de
  duruyor. Arazi bir noktada bina varsa çatıyı döndürüyor (ADR-0038) ve
  ızgara o noktaların bina içinde olup olmadığına bakmıyor. Bu, ızgarayı
  olduğundan iyi gösteriyor. Yayımlanan satır değiştirilmedi; ayrı bir
  karar.
- **Aramanın kendi adaylarında da aynı sorun vardı.** Kızılay'da 304 yol
  kenarı noktasından 21'i ve 120 sokak donanımından 7'si bir bina izinin
  içine düşüyordu. Artık çatı dışındaki hiçbir aday bir iz içinde
  durmuyor. Bu kural öncesindeki şehir koşusunda `better` %89,79
  kullanılabilirlik gösteriyordu; o kazancın bir kısmı çatıya çıkmış
  sokak direklerinden geliyordu. Yukarıdaki tablo kuraldan sonraki koşu.
  Kırsal sonuç değişmedi: çıkarılan adayların hiçbiri seçilmemişti.

## Simülatörde

"Yöneylem yerleşimi" bölümü, gösterilen sekmeyi (şehir içi ya da kırsal)
ölçülmüş zemininde arıyor ve cevabı `placed` yöntemli tek bir direk
grubu olarak öneriyor. Uygulamak onay panelinden geçiyor, çünkü satırın
bütün direklerini değiştiriyor. Çatı (`roof`) bu grubun içinde kullanılıyor
ama tek başına bir grubun yapısı olarak sunulmuyor: çatısız zemine
tutucu dizilirdi. Tarayıcıda süreç olmadığı için arama tek çekirdekte
koşuyor ve birkaç dakika sürüyor.

## Komut satırı

```bash
yerkon place --scenario urban --aim better --fast
yerkon place --scenario rural --aim cheaper --no-simulation
```
