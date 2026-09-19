# ADR-0063: denemek için kaba okuma

## Durum

Kabul edildi.

## Bağlam

ADR-0055 tabloyu sekiz gölge çekilişinin havuzu yaptı, ADR-0062 zemin
profilini on metrede bir okuttu. İkisi de doğru ve ikisi de pahalı:
`yerkon table` 70 saniyeden 15 dk 33 sn'ye çıktı.

Bu, denemeyi bitiriyor. Bir direği iki yüz metre kaydırıp ne olduğuna
bakmak isteyen biri çeyrek saat bekleyemez, ve beklemeyeceği için ya
hiç bakmaz ya da bir kez bakıp sonucu genelleştirir. İkisi de daha
kötü.

İki figür bir koşunun **ne kadar sürdüğüne** karar veriyor, **neyi
anlattığına** değil:

| figür | yayımlanan | kaba |
|---|---|---|
| `site.shadow_draws` | 8 | 1 |
| `site.profile_spacing_m` | 10 m | 0 (sabit 64 örnek) |

İkisi de geri alınabilir. Model değişmiyor, daha kaba okunuyor.

## Karar

**`settings.HURRIED`**, bu iki figür ve kaba değerleri, tek bir yerde.
`hurried(settings)` onları herhangi bir ayar kümesinin üzerine
uyguluyor, `is_hurried(settings)` kaba olup olmadığını söylüyor.

**Komut satırında `--fast`.** `_settings_from` her verbin ayarlarını
aldığı tek huni, yani bayrak oraya konunca altı verb birden aldı ve
sonra eklenen bir verb de o huniyi kullandığı için alacak. **En son**
uygulanıyor: hız isteyip yine de çeyrek saat beklemek bu bayrağın
yapmaması gereken tek şey.

**Sayfada bir düğme**, "Hızlı dene", sonuç panelinin yanında.
Hazır seçeneklerin arasında değil: bir seçenek bir *yerleşim* tercihi,
bu ise aynı yerleşimin ne kadar ince okunduğu. Basınca iki figür
override olarak yazılıyor, tekrar basınca siliniyor.

**Uyarı figürlere bakıyor, düğmeye değil.** `site.shadow_draws`
değerini elle 1 yapan da aynı satırı görüyor. Hem tabloda hem panelde,
ve hangi iki okumanın kabalaştığını adıyla yazıyor.

**Ve hangi yöne yanlış olduğunu söylüyor.** İki kabalık da kaybı eksik
okuyor, yani hızlı bir cevap yerleşimi kayırıyor. Bu, uyarının en işe
yarar kısmı: hızlı okumada kötü görünen bir satır gerçekten kötüdür.

## Sonuçlar

| | yayımlanan | hızlı |
|---|---|---|
| `yerkon table` | 15 dk 33 sn | **54 sn** |
| sayfada bir koşu (şehir) | 39,5 sn | **12,0 sn** |
| şehir HPE P95 | 8,19 m | 7,20 m |
| kırsal HPE P95 | 22,72 m | 18,59 m |
| kırsal kullanılabilirlik | %41,83 | %52,00 |
| ağırlıklı HPE P95 | 13,44 m | 11,89 m |

Tarayıcıda yürüdüm: düğme kapalı başlıyor, basınca yanıyor ve iki figür
yazılıyor, koşu hızlanıyor ve panelde "gölgeler sekiz yerine bir kez
çekiliyor, profil 10 m yerine sabit 64 örnekle okunuyor" satırı çıkıyor,
tekrar basınca ikisi de siliniyor.

Sayfanın `HURRIED` kopyası ile `settings.HURRIED` bir sınamayla
birbirine çivili. Sayfa fizik taşımıyor ve motorunkini içe aktaramıyor,
yani iki kopya var; ayrılırlarsa düğme motorun kaba saymadığı figürleri
yazar ve uyarı hak eden sayıların yanında görünmez olur.

## Yapılmayanlar

**Kaba okumanın ne kadar yanlış olduğu satır başına ölçülmedi.** Yukarıdaki
tablo yayımlanan üç satır için, ve fark satıra göre değişiyor: kırsalda
4,13 m, şehirde 0,99. Başka bir sahada başka bir şey olur.

**Aradaki kademeler yok.** Bayrak açık ya da kapalı. Dört çekiliş ve 20 m
aralık muhtemelen birkaç dakikada yayımlanmaya yakın bir cevap verirdi,
ve bu ölçülmedi.

**Düğme yalnızca iki figürü biliyor.** Yavaş olan başka bir şey eklenirse
(daha ince bir kapsama taraması gibi) `HURRIED` elle büyütülmeli; hiçbir
şey bunu hatırlatmıyor.
