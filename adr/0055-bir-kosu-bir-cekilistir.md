# ADR-0055: bir koşu bir çekiliştir

## Durum

Kabul edildi.

## Bağlam

Aynı anten, aynı mesafe, aynı görünen zemin — ve ölçülen kayıp aynı
değil. Kaldırımdaki kamyonet, iki profil örneği arasına düşen bina
köşesi, bir sıra ağaç, modelin yuvarladığı o bir kat. Model ortancayı
taşıyordu ve etrafındaki yayılımı hiç taşımıyordu.

Bunun bedeli şuydu: **her hücre ya geçiyordu ya kalıyordu.** Kapsama
kenarı bir çizgi olarak çiziliyordu, oysa o bir geçiş. Gerçek kapsama
"konumların %X'i" diye verilir ve içinde yayılım olmayan bir modelden
öyle verilemez.

Yayımlanan karasal modellerin hepsinde bir tane var: 3GPP TR 38.901
senaryo başına gölge sönümlemesi olarak, ITU-R P.1546 ve P.1812 konum
değişkenliği olarak, ve 2 GHz civarında hepsi 4 ile 8 dB arası veriyor.

## Karar

**Gölgeleme bir alan olarak eklendi** (`world.Shadowing`), σ = 6 dB
varsayımıyla — aralığın ortası, adı konmuş bir varsayım olarak
`defaults.toml`'da.

İki özelliği genişliği kadar önemli:

**Bir yer hakkında bir olgu, bir çekiliş değil.** Aynı alıcı aynı
noktadan aynı direğe her seferinde aynı gölgeyi görüyor — zeminin kendi
pürüzü ve anket hatası gibi (ADR-0019). Gürültü olarak çekilseydi bir tur
boyunca ortalamaya giderdi ve etkinin tamamı kaybolurdu.

**Bağlantı başına, yer başına değil.** Bir noktada durup bakınca kimi
direkler bir şeyin arkasında, kimileri değil. Saha üzerinde tek bir alan
hepsini birlikte gölgelerdi ve asıl sabitlemeyi kaybettiren durumu hiç
üretmezdi: erişimde üç direk, biri kamyonun arkasında.

Alan köşeler arasında aradeğerleniyor, hücrelerde tutulmuyor: hücre
sınırını geçen bir alıcı yoksa bir adımda birkaç desibel sıçrardı.
Aradeğerleme dört bağımsız köşeyi karıştırdığı için genişliği daraltır,
o yüzden yeniden normalleniyor — yoksa verilen σ hücrenin ortasında bir
başka, köşesinde bir başka olurdu. Ölçtüm: köşede 6,04, ortada 6,12.

Korelasyonun **şekli** de aradeğerlemeden geliyor ve Gudmundson'ın
üsteli değil, iki doğrusal bir alanın çadırı: beş metrede 0,99, yirmi
beşte 0,73, verilen ellide 0,28, yüzün ötesinde hiç. Yani bu sayı çadırın
genişliği; doğru mertebe, doğru eğri değil.

### Ve sonra asıl mesele çıktı

Gölgeleme açılınca **bir koşu bir çekiliş** oldu. Kırsal satırın 95.
yüzdeliği sekiz çekilişte şöyle geldi:

| 14,6 | 16,1 | 16,5 | 16,6 | 21,9 | 29,4 | 66,5 | **279,6** m |

Varsayılan tohum en kötüsünü veriyordu. Şehir satırı sağlamdı (8,6–9,9).
Sebep: kırsal satırın kullanılabilirliği %47, hayatta kalan sabitleme
sayısı az ve 95. yüzdelik bir kuyruk.

**Yüzdelik, çekilişlerin örnekleri birlikte alınarak hesaplanıyor.** Sekiz
yüzdeliğin ortalaması hiçbir şeyin yüzdeliği değildir; bu proje aynı
reddi ağırlıklı satır için zaten veriyor (ADR-0005).

Kaç çekiliş gerektiğini ölçtüm, varsaymadım:

| çekiliş | kırsal P95 | şehir P95 |
|---|---|---|
| 1 | 279,6 | 9,08 |
| 3 | 32,0 | 8,70 |
| 5 | 32,0 | 9,00 |
| **8** | **23,7** | **9,32** |
| 12 | 25,1 | 9,24 |
| 16 | 25,7 | 9,08 |
| 24 | 24,2 | 9,14 |

Sekizden sonra 24–26 m arasında oturuyor. **Sekiz.**

**Tarama üç çekilişte koşuyor, sekizde değil.** İkisi bambaşka hızlarda
oturuyor ve bu da ölçüldü: alan binlerce hücrenin ortalaması, Kızılay'da
üç çekiliş 6,19 · 6,32 · 6,28 km² veriyor. Sekiz kez süpürmek, zaten
cevaplanmış bir soruya tablonun maliyetini iki katına çıkarmak olurdu.

**Havuzlama `study`'nin, `run`'ın değil.** Bir benzetim bir düzenlemedir;
`run(URBAN)` hâlâ tek çekiliş ve hâlâ 31 saniye. Havuzlayan şey raporu
üreten yol, ki yayımlanan sayının nerede kararlaştırıldığı da orası.

## Sonuçlar

| | ADR-0053 | şimdi |
|---|---|---|
| Şehir içi HPE P95 | 10,14 m | **9,32 m** |
| Şehir içi kullanılabilirlik | %79,84 | **%80,95** |
| Şehir içi alan | 5,69 km² | **6,26 km²** |
| Kırsal HPE P95 | 29,62 m | **23,74 m** |
| Kırsal kullanılabilirlik | %41,87 | **%47,46** |
| Ağırlıklı HPE P95 | 14,97 m | **12,93 m** |

Bazı sütunlar **iyileşti**, ve bu gölgelemenin ne olduğunu anlatıyor:
yayılım simetriktir. Ortanca kaybın tam çıtada olduğu her yerde,
bağlantıların yarısı çıtanın altına geçiyor. Eşiğin yakınında oturan
kalabalık bir nüfus varsa, yayılım onları kurtarıyor. Bu tam olarak
kapsamanın neden bir yüzdeyle verildiği.

`yerkon table` dört çekirdekte yetmiş saniyeden **3 dk 50 sn**'ye çıktı
(boş makinede ölçüldü; sekiz çekilişin kendisi on bir dakika işlemci
zamanı, paralelleştirilmiş hâli bu). Sınamalar etkilenmedi, çünkü `run`
hâlâ tek çekiliş.

### Bir sınama üçüncü kez yazıldı, ve bu sefer doğru şeyi söylüyor

`test_how_long_a_rural_round_runs_cannot_be_settled_on_one_seed` bir tur
başına sekiz direk yoklamakla on direk yoklamak arasındaki sıralamanın
**bir tohumdan okunamayacağını** iddia ediyor. İddiayı iki tohumda bir
ters dönüşle çiviliyordu, ve model her oynadığında o ters dönüş
kayboluyordu: ADR-0053'te bir kez, gölgeleme gelince bir kez daha.

Ters dönüş, olgunun bir örneği; olgu değil. Sekiz tohumda ölçtüm:

| on kaç tohumda önde | ortalama fark | tohumdan tohuma yayılım |
|---|---|---|
| 5/8 | +0,008 | 0,020 |

**Etki, içinde ölçüldüğü gürültünün dörtte biri.** Sınama artık bunu
söylüyor — bir çift tohum aramıyor — ve modelin bir dahaki oynayışında
kendiliğinden ayakta kalıyor.

## Yapılmayanlar

**Sayfa havuzlamıyor.** Görüntüleyici tek çekiliş gösteriyor — canlı bir
sürgünün sekiz koşu beklemesi sayfayı kullanılamaz yapardı. Gösterdiği
şey bir düzenleme, tablo ise bir istatistik; ikisinin farkı ADR-0001'de
zaten yazılı ama sayfa bunu söylemiyor.

**σ tek bir sayı.** Yayımlanan modeller görüş alanı içi ve dışı için
ayrı veriyor (38.901: 4 dB LOS, 7,82 dB NLOS). Burada ikisi de 6.

**Çadır, üstel değil.** Korelasyonun şekli aradeğerlemeden geliyor.
