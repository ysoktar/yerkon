# ADR-0075: siteyi slayta göre senkronlamak

## Durum

Kabul edildi.

## Bağlam

Rapor sunumu güncellendi (YERKON_4) ve site onun bir önceki
revizyonundan üretilmişti. Sayfa sayfa karşılaştırma yapıldı; sunum
doğru referans kabul edildi, **tek istisnayla**: karşılaştırma
tablosunun üç YERKON satırı. Orada sitenin 21 Eylül 2026 tarihli
yayımlanmış koşusu sunumdan yenidir ve o kalır.

Farkların büyük bölümü tek bir kalıptaydı: **site sunumdan daha kesin
konuşuyordu.** Sunum bir hedef derken site bir sonuç diyordu, sunum
"olabilir" derken site "olur" diyordu.

| Site | Sunum |
|---|---|
| 1000-1600 lira | 100 adetlik üretimde 1000-1600 lira |
| yeni direk/enerji hattı gerekmiyor | mevcut AUS altyapısının yeniden kullanılması hedeflenir |
| ikisi tutmuyorsa sahte sinyal var | karşılaştırma aldatmanın tespitine yardımcı olabilir |
| araç ekrandan hiç kaybolmaz | konum sürekliliğinin korunmasına yardım eder |
| sekiz kilometreye ulaşıyor | 8-10 km bir haberleşme/kapsama hedefi |
| 2-4 km şehir menzili | ±1 m **mesafe ölçüm** doğruluğu; konum hatası ayrı |
| kırsalda 10-15 m saha doğruluğu | (sunumda yok) |
| 50-100 m menzil, santimetreye iner | ~10 cm **mesafe ölçüm** hassasiyeti hedefi |
| TDoA her direğe atomik saat ister | hassas senkronizasyon *gerekebilir*; atomik saat bir *örnek* |

Son üç satır aynı hatanın üç kere tekrarı: **bir telsizin iki nokta
arasındaki mesafeyi ne kadar iyi ölçtüğü, sistemin konumu ne kadar iyi
bulduğu değildir.** Sunum bunu üç kurulum grubunda da ayrı ayrı
yazmış; site üçünde de ikisini birbirine karıştırmış.

## Karar

**Sunum ne diyorsa o**, yukarıdaki istisna dışında. Kesinlik farkları
sunumun diline çekildi, olgu hataları düzeltildi, eksikler eklendi.

Düzeltilen olgular: Tartu'da havalimanı kapanmadı, Finnair uçuşları
haftalarca durduruldu. Karadeniz'de sinyalleri Rus elektronik harp
birimleri değiştirdi. Yaya ve araç alıcısının malzeme listesinde
ATECC608B eksikti. Araç alıcısı "uyumlu araçların" CAN hattına bağlanır
ve iki telsizi birden taşır. Sıra numarasıyla tekrar oynatma koruması
AR-GE güvenlik cevabına girdi. Kritik bölge listesinden sınır kapıları
çıktı. Ürün adları ve uzun vade maddeleri sunumun hâline getirildi.

**İki yerde sunumun dilini almadık.** Site "kentsel kanyon" yerine
"yüksek binaların arasında" diyor ve kısaltmaları açıyor (ADR-0071).
Anlam aynı; okuyucu farklı.

## Sonuçlar

Sitenin iddiaları sunumun iddialarıyla aynı, ve hiçbiri sunumun
söylediğinden fazlasını söylemiyor.

**Bir kontrol de ters yönde çalıştı.** Sunumun güncel hâline dair
verilen özet, slayt 9'un aldatma metriklerinden yanlış alarm oranını ve
tespit oranını çıkardığını söylüyordu. Slayt okunduğunda ikisi de
duruyordu. Özet yerine kaynak esas alındı, ve sitede olan ama slaytta
olmayan üçüncü bir metrik (saat sapması) çıkarıldı. Bir karşılaştırmayı
kaynağa bakmadan uygulamak, düzeltmeyi bozmak olurdu.

## Yapılmayanlar

**Sunumun 16-18. slaytları güncellenmedi.** Bu depo siteyi üretiyor,
sunumu değil. O slaytlardaki YERKON satırları ve metodoloji dipnotları
21 Eylül koşusundan geride: tablo değerleri farklı, ve slayt 18 hâlâ
"tek-epoch çözüm" ile "kalibreli SX1280 senaryosu" diyor. Model artık
gerçek Ankara arazisinde koşuyor ve bir turdaki ölçümlerin eşzamanlı
olmadığını modelliyor. Güncel değerler README'de ve `published.toml`'da.

**Diğer on sistemin satırları sorgulanmadı.** Sunum onlar için doğru
referans kabul edildi; zaten `comparison.toml` onları kendi
kaynaklarından taşıyor (ADR-0069, ADR-0070).
