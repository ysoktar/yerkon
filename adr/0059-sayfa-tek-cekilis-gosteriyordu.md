# ADR-0059: sayfa tek çekiliş gösteriyordu

## Durum

Kabul edildi. ADR-0055'in sayfa tarafını tamamlar.

## Bağlam

ADR-0055 yayımlanan tabloyu sekiz gölge çekilişinin havuzu yaptı. Sayfa
aynı gün tek çekilişte kaldı ve bunu hiçbir yerde yazmadı.

Fark küçük değil. Aynı düzenleme, aynı zemin, sekiz çekiliş:

| satır | tek çekiliş | havuz | çekilişlerin aralığı |
|---|---|---|---|
| şehir | 6,92 m | 6,04 m | 5,22 - 6,92 |
| kırsal | 10,02 m | **14,03 m** | 9,67 - 18,75 |
| tünel | 0,71 m | 0,69 m | 0,65 - 0,77 |

Kırsalda sayfa %40 iyimser okuyordu, üstelik sabit tohum sekiz
çekilişin en iyisine denk geldiği için. Bir kişi sayfada 10 m görüp
tabloda 14 m bulunca ikisinden birinin yanlış olduğunu düşünür.

## Karar

**Önce tek çekiliş, sonra havuz.** Sayfa ilk çekilişi hemen gösterir ve
üstündeki satırda hangisi olduğunu yazar, kalan yedisi arkada koşar,
gelince rakamlar havuzlanmışla değişir (ADR-0050 aynı deseni kuruyor).

```
Gölge çekilişi   1/8, kalanı hesaplanıyor      →  8 çekiliş havuzlandı
HPE P95          6,92 m                        →  6,04 m
```

İki uç nokta: `/api/simulate` bir çekiliş, `/api/simulate/pooled` hepsi.
Aritmetik `report.folded`'ın aynısı: örnekler havuzlanır çünkü bir
yüzdelik bir popülasyon hakkındadır, alanlar ortalanır çünkü bir alan
çekiliş başına bir cevaptır.

**Alanlar `AREA_DRAWS`'ta durur, tablonunkiler gibi.** Kızılay'ın sekiz
çekilişinde kapsanan alan 6,280 ile 6,760 km² arasında gezdi, ortalamanın
%7,3'ü; kırsalın 95. yüzdeliği 9,67 ile 18,75 m arasında gezdi, %94. Bir
alan oturur, bir kuyruk oturmaz.

**Çekilişler saklanıyor.** İlk geçişin çekilişi havuz geçişinde yeniden
koşulmaz, ve aynı düzenlemeye dönmek bedava. Şehir satırında ilk geçiş
17,2 sn, havuz geçişi 29,9 sn daha, aynı düzenlemeye ikinci kez 0,49 sn.

**Düğme ilk çekiliş ekrana gelince geri geliyor.** Havuz geçişi kırsalda
dakikalar sürüyor ve o kadar süre ölü duran bir düğme beklemenin
kendisinden kötü.

## Sonuçlar

Düğmenin canlı kalması yarışı erişilebilir yapıyor: bas, düzenlemeyi
değiştir, tekrar bas, ve ilk basışın havuz cevabı en son iniyor. Süzgeç
sweep'inkiyle aynı, `simulationWanted`.

Tarayıcıda yürüdüm. Cevabı **isteği değil yanıtı** tutarak geciktirmek
gerekiyor: tutulan bir istek sunucuya sonra varıyor ve yeni düzenlemeyi
okuyor, yani yarışmıyor. Süzgeç kaldırılınca ilk basışın 6,04 m'si
düzenlemenin kendi 6,83 m'sinin üstüne yazdı; süzgeçle 6,83 kalıyor.

## Yapılmayanlar

**Havuz geçişi kırsalda hâlâ dakikalar sürüyor.** Sekiz yolculuk, her
biri 52 sn, dört çekirdekte. İlk çekiliş ekranda olduğu için beklemek
engellemiyor ama kısalmıyor da.

**Sayfa çekilişlerin yayılımını göstermiyor.** Havuzlanmış bir 95.
yüzdelik, arkasındaki sekiz çekilişin 9,67 ile 18,75 arasında gezdiğini
söylemiyor. Bir aralık göstermek doğru olurdu ve panelin şu anki biçimi
satır başına tek bir değer alıyor.

**Alanlar üç çekilişte duruyor ve bu ölçülmedi.** Tablodan devralınan
sayı. Kızılay'ın yayılımı %7,3 ve üç çekilişin bunu ne kadar daralttığı
ölçülmedi.
