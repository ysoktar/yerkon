# ADR-0032: aynı türden şey anlatmayan iki sürgü

## Durum

Kabul edildi.

## Bağlam

Sahanın iki boyutu vardır ve sayfada her biri için bir sürgü vardır.
**En** ve **Boy** üst üste durur, birbirinin aynı görünür ve tamamen
farklı şeyler yapıyordu.

En, direkleri doğrudan biçimlendirir: bir alan üzerinde bir dizi, yoldan
`width_m`'e kadar bir ızgara serer; yani sahayı genişletmek direk
sıraları ekler ve bunun olmasını izlersiniz.

Boy onlara hiçbir şey yapmıyordu. Bir direk dizisi kendi `from_m` ve
`to_m` değerlerini taşır ve onu yerleştiren de bunlardır; dolayısıyla
**Boy**'u yirmi kilometreden sekize çekmek, otuz altı direği yarısından
kısa bir saha boyunca tam olarak durdukları yerde bırakıyordu. Güzergâhı
değiştiriyordu ve — ağ güzergâhı izlemeye başladıktan sonra — zemini.
Yerleşimi değil.

Bu bakışımsızlık bir sıra kazasıdır. En sonradan geldi ve direklere
bağlandı; boy zaten oradaydı ve dizinin kendi uçları onunla hiç
uzlaştırılmadı.

## Karar

Sahayı kısaltmak, direk dizilerini onun içine alır ve bunu onay
panelinden geçerek yapar (ADR-0009); bu projenin bir değişikliğin başka
bir değişikliği zorladığı durumlar için zaten sahip olduğu kural budur.
**Boy**'u 8 km'ye çekin ve panel şunu der:

    İstediğin değişiklik    Sahanın boyu    20000 → 8000
    Bunlar da değişiyor     Grubun bitişi   20000 → 8000

Evet denene kadar hiçbir şey kımıldamaz.

Yalnızca boy sürgüsü kırpar. Bir diziye elle uç yazmak, o dizi hakkında
açıkça konuşan bir insandır ve altından onu kırpmak, sormadığı bir
soruyu yanıtlamak olurdu — dolayısıyla bir diziye kasıtlı olarak, elle,
sahanın ötesinde bir uç hâlâ verilebilir.

## Sonuçlar

İki sürgü artık aynı türden şey anlatıyor ve direkleri kımıldatan olan,
kımıldatmadan önce bunu söylüyor.

Raporun kendi satırlarına dokunulmadı: `scenarios.catalogue()` direkleri
bir dizi üzerinden değil doğrudan yerleştirir ve hazırlanmış üç sekmenin
hepsinde dizi zaten tam olarak koridoru kaplıyordu, dolayısıyla tablodaki
hiçbir figür kımıldamaz.

Değerlendirilen diğer seçenek, enin ızgarayı sessizce büyütmesi gibi
sessizce kırpmaktı. Reddedildi, çünkü ikisi benzer değil: genişletmek
kişinin belirdiğini görebildiği direkler ekler, kısaltmak ise bir öğleden
sonrasını harcamış olabileceği yerleşimleri atar — elle sürüklenmiş
direkler dahil. Emeği yok edebilecek bir değişiklik panelden geçer.
