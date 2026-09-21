# ADR-0076: simülatör tabloyu üretebilmeli

## Durum

Kabul edildi.

## Bağlam

Simülatörü açıp "Simülasyonu çalıştır"a basınca panel sekiz çekilişi
havuzluyor ve bir HPE P95 yazıyor. Okuyanın bunu yayımlanan satır
sanmak için her sebebi var; aynı sitede, aynı adlarla, aynı ölçüler.

Sanmamalıydı. Şehir içi sekmesinde panel **5,86 m** diyordu, tablo
**8,84 m**. Kullanılabilirlik %92,70'e karşı %83,98.

`pool()` fonksiyonunun kendi notu şöyle diyordu:

> What the table publishes, by the same arithmetic (`report.folded`).

Aritmetik gerçekten aynıydı. Girdiler değildi.

Sebep, simülatörün yerleşim geometrisinin **ikinci bir kopyası** olması:
`state.py` içinde her satır için bir şablon, aralığı, kaydırması ve
yolculuk süresi doğrudan yazılmış. İki değer kaymıştı:

* **Şehir içi yolculuk 240 saniye**, tablonunki 600. Daha kısa bir
  yolculuk yolun daha azını geziyor ve bu durumda daha kolay olan
  kısmında kalıyor.
* **Tünel aralığı 150 m**, varsayılan ADR-0072 ile 225 m'ye taşındıktan
  sonra bile. Simülatör 14 askı çiziyordu, tablo 9.

Diğer üç değer (kırsal yolculuk, kırsal aralık, şehir içi aralık)
tesadüfen aynıydı. Yani bu bir tasarım tercihi değildi; iki kopyadan
biri güncellenmişti.

ADR-0023 zaten şunu söylüyordu: *bir yerleşimi şekillendiren her sayı
ayar dosyasından gelir.* Görüntüleyicinin şablonu bu kuralın dışında
kalmıştı ve kural tam da bu yüzden vardı.

## Karar

**Şablon kendi kopyasını taşımıyor.** Aralık ve kaydırma
`defaults.toml`'dan, yolculuk süresi tablonun değerlendirdiği
dağıtımdan okunuyor. Kaymanın kaynağı ortadan kalkıyor, çünkü artık
kayacak ikinci bir sayı yok.

**Bir sınama üçünü de tutuyor.** Simülatörün çizdiği direk sayısı
tablonunkiyle aynı olmalı, ve sürdüğü saniye tablonunkiyle aynı olmalı.
Sınama önce yazıldı ve iki kaymayı da yakaladı.

## Sonuçlar

Simülatörü açıp çalıştırmak yayımlanan satırı üretiyor. Panelin
söylediğiyle tablonun söylediği aynı şey.

Şehir içi sekmesi artık 600 saniye sürüyor, yani bir koşu 240
saniyelikten uzun. Bedeli bu; karşılığı panelin doğru sayıyı
göstermesi.

Taşınmaya değer genelleme: **iki yerde duran bir sayı, er geç iki
farklı sayıdır.** Bu depo bunu daha önce de yaşadı — aynı kutunun
haritada 9 900, panelde 10 000 metre olması (ADR-0052), ve hiçbir şeyi
değiştirmeyen bir yedek rölyef ayarı (ADR-0027). Üçünde de kopya, asıl
değerin yanında masum görünüyordu.

## Yapılmayanlar

**Yolculuk süresi hâlâ bir ayar anahtarı değil.** `scenarios.py`
içinde bir literal, ve şablon onu oradan okuyor. Ayar dosyasına taşımak
daha doğru olurdu; bu ADR yalnızca iki kopyayı bire indiriyor.

**Şablonun geri kalanı okunmadı.** Montaj tipi, telsiz, alıcı sayısı ve
tolerans hâlâ şablonda yazılı. Bunların hiçbiri şu an kaymış değil, ve
sınama direk sayısı ile yolculuk süresini tuttuğu için bir kayma
sessiz kalmaz; ama aynı kopya sorunu orada da duruyor.
