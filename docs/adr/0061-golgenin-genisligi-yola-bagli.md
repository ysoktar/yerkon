# ADR-0061: gölgenin genişliği yola bağlı

## Durum

Kabul edildi. ADR-0055'i genişletir.

## Bağlam

ADR-0055 gölgelemeyi modele soktu ve tek bir genişlikle: 6 dB, "yayımlanan
aralığın ortası" diye adı konmuş bir varsayım.

Yayımlanan modellerin hiçbiri tek bir sayı taşımıyor. 3GPP TR 38.901
Tablo 7.4.1-1:

| senaryo | görüş hattı var | yok |
|---|---|---|
| UMi-Street Canyon | 4 dB | 7,82 dB |
| UMa (şehir makro) | 4 dB | 6 dB |
| RMa (kırsal makro) | 4 dB | 8 dB |

Üçünde de görüş hattı 4 dB, ve kesildiğinde varyans kabaca ikiye
katlanıyor. Sebep fiziksel: doğrudan ışın varken gelen alan tek bir
yoldan geliyor ve sapma o yolun etrafındaki tek tük engellerden ibaret;
ışın kesildiğinde gelen şey kenarların üzerinden dolaşan bir toplam ve
her kenar kendi şansı.

Tek 6 dB, açık yolları fazla ve kapalı yolları eksik cezalandırıyordu.

## Karar

**İki genişlik, ve hangisinin geçerli olduğuna zemin karar veriyor.**

```python
sigma_db: float = 0.0                        # yol açıkken
sigma_obstructed_db: Optional[float] = None  # kapalıyken
```

`None` ikisi için tek figür demek, yani ayrımdan önceki davranış, ve o
zaman kaydedilmiş bir düzenleme kendisi olarak yükleniyor (ADR-0035).

Ayrım bir olasılık değil geometri. TR 38.901 senaryo başına bir görüş
hattı olasılığı veriyor çünkü elinde arazi yok; burada var. Bir yol,
iki uç arasındaki düz çizgi araziyi *ve dünyanın kendi kavisini*
geçiyorsa açık. Fresnel payı yok: soru ışının rahat olup olmadığı değil,
var olup olmadığı.

Bu, bütçenin bildirdiği noktayı seçen `worst_ratio`'dan ayrı
hesaplanıyor. Onun içinde kavis yok ve oraya eklemek yayımlanan tabloyu
bu kararla ilgisi olmayan bir sebeple oynatırdı.

**Çekiliş değişmiyor, sadece genişliği.** Aynı yer aynı şansı tutuyor ve
bir tepenin arkasına geçen bir bağlantı ayrıca başka bir çekiliş almıyor;
yoksa iki genişlik karşılaştırılamazdı.

**Varsayılanlar 4,0 ve 7,82.** İkisi de TR 38.901'den, yani bu iki değer
artık `ASSUMPTION` değil `STANDARD`.

## Sonuçlar

Satır başına kapalı yol payı, gerçek zemin üzerinde ölçüldü:

| satır | kapalı | açık |
|---|---|---|
| Kızılay | %98,1 | %1,9 |
| Polatlı | %79,4 | %20,6 |
| tünel | %0,0 | %100,0 |

Yayımlanan tablo:

| | tek 6 dB | 4 / 7,82 |
|---|---|---|
| şehir HPE P95 | 9,61 m | **8,78 m** |
| şehir kullanılabilirlik | %81,23 | **%80,08** |
| şehir alan | 6,32 km² | **6,84 km²** |
| kırsal HPE P95 | 20,90 m | **31,77 m** |
| kırsal kullanılabilirlik | %47,49 | **%51,80** |
| kırsal alan | 163,08 km² | **175,67 km²** |
| tünel HPE P95 | 3,03 m | **2,93 m** |
| tünel kullanılabilirlik | %99,97 | **%100,00** |
| ağırlıklı HPE P95 | 13,31 m | **14,28 m** |

İki satır iki yöne gidiyor ve sebep aynı. Geniş bir yayılım çıtanın iki
yanına da bağlantı itiyor. Şehirde bağlantıların çoğu çıtanın üstünde
duruyor, yani genişlemek bir kısmını altına itiyor: kullanılabilirlik
düşüyor ve düşenler en kötüleri olduğu için sağ kalanların kuyruğu
iyileşiyor. Kırsalda çoğu çıtanın altında (%80,3'ü kaybediliyor), yani
genişlemek bir kısmını üstüne itiyor: kullanılabilirlik ve alan artıyor
ve yeni kapananlar doğruca kuyruğa giriyor. Aynı mekanizma, ters yön.

**Tünel kullanılabilirliği %100,00 okuyor.** Bir yuvarlama değil: notlar
"her tur yine de bir konum üretti" diyor. Tünel baştan sona görüş hattı,
yani gölgesi 6 dB'den 4'e indi. Sütunun ne saydığı tablonun kendi
notunda duruyor: yalnızca modellenmiş başarısızlıklar, bir hizmet
kullanılabilirliği değil.

## Düşen bir sınama, ve yeniden ölçülen bir iddia

`test_how_long_a_rural_round_runs_cannot_be_settled_on_one_seed` tur
uzunluğunun ölçülemeyecek kadar küçük olduğunu iddia ediyordu. Artık
değil, ve sebebi bu kararın kendisi.

| | tek 6 dB | 4 / 7,82 |
|---|---|---|
| on direk kaç tohumda kazanıyor | 5/8 | **8/8** |
| ortalama fark | +0,008 | **+0,0227** |
| tohumdan tohuma yayılım | 0,020 | 0,0069 |
| etki / gürültü | 0,4 | **3,3** |

Mekanizma doğrudan: bu satırın bağlantılarının %79,4'ü kapalı ve
onların yayılımı 6 dB'den 7,82'ye çıktı, yani daha çoğu çıtanın
yakınında duruyor, yani bir turda daha çok aday bulundurmak daha çok
kazandırıyor.

Sınama `test_how_long_a_rural_round_runs_is_measured_over_seeds_not_one`
oldu. Ölçme yöntemi aynı kaldı, çünkü asıl iddiası o: bir tohumda
ölçülen değişim hiçbir şeyde ölçülmüş değildir. İddianın yönü iki kez
oynadı ve yöntem ikisini de yakaladı.

## Yapılmayanlar

**Tek bir çift, satır başına değil.** TR 38.901 sokak kanyonunda 4/7,82,
şehir makroda 4/6, kırsalda 4/8 veriyor. Bu proje üç satıra tek bir çift
uyguluyor ve 7,82 sokak kanyonunun sayısı. Kırsal satır muhtemelen 8'i
hak ediyor, şehir satırı 6'yı; ikisi de 7,82 alıyor.

**Ayrım sert.** Bir yol ya açık ya kapalı, ve düz çizgiyi bir metre
kaçıran bir tepe genişliği 4'ten 7,82'ye sıçratıyor. Gerçekte geçiş
kademeli ve TR 38.901'in kendi olasılık modeli de bunu böyle yazmıyor.

**Kavis 4/3 dünya yarıçapıyla.** Geri kalan her yerdeki `earth_bulge_m`
ile aynı, yani kırılma varsayımı tutarlı, ama normal havayı varsayıyor.
