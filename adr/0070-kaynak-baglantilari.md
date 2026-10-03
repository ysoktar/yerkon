# ADR-0070: kaynak bağlantıları

## Durum

Kabul edildi. ADR-0069'un "Yapılmayanlar" başlığındaki **Kaynak
bağlantıları yok** maddesinin yerine geçer.

## Bağlam

ADR-0069, on satırın notlarını yazdı ama adresleri dışarıda bıraktı:
"raporun kaynakçası adresleri taşıyor, ve onları buraya kopyalamak
üçüncü bir kopya olurdu."

Bu, okuyucuyu siteden çıkarıyordu. Sayfada "National Academies, GPS
tarihsel yatırım" yazıyor, ve o belgeyi görmek isteyen kişinin elinde
sunum dosyası yoksa arama motoruna gitmesi gerekiyor. Bir
karşılaştırma tablosunun asıl işi başkalarının sayılarını taşımaksa,
o sayıların nereden geldiği tıklanabilir olmalı.

Üçüncü kopya endişesi de yanlış çıktı. Adresler raporun kendisinden
okunabilir: `.pptx` bir zip, ve kaynakça slaytının köprüleri
`ppt/slides/_rels/slide19.xml.rels` içinde duruyor. Yeniden yazmak
yerine oradan çıkarılınca site ile rapor aynı adreste buluşuyor.

## Karar

**48 bağlantı `sources.toml` içinde, altı grup altında.** Raporun
kaynakça slaytından çıkarıldılar, elle yazılmadılar. Her girdinin bir
anahtarı, bir grubu, iki dilde etiketi ve adresi var.

**Notlar kaynakları anahtarla anıyor.** `comparison.toml` içindeki her
not bir `sources` listesi taşıyor; tablo altındaki not, dayandığı
girdilere bağlanıyor. Anahtar, hücrenin notu ve kaynakça girdisi
arasındaki tek bağ: bir adres değişirse tek yerde değişiyor.

**Hiçbir notun anmadığı girdi de listede kalıyor.** Bu liste raporun
kaynakçası, sitenin kullandıklarının listesi değil. Dördü haber
bağlantısı, biri TWR CDMA makalesi; onlar tablonun değil, metnin
içinde geçiyor.

**Metin içi bağlantı `[ne](nerede)` ile yazılıyor.** `_marked` bunu
`**kalın**` ve `` `kod` `` ile aynı yerde işliyor. Yalnızca `http` ve
`https`: bir cümle bu fonksiyon için veridir, ve `javascript:` bir
bağlantıda veriyi davranışa çeviren tek şeydir.

**Tanım notu kaynaksız.** Kullanılabilirlik sütununun uyarısı sütunun
ne anlama geldiğini anlatıyor, kimseden bir sayı almıyor. Sınama bu
tek istisnayı adıyla tanıyor; geri kalan otuz yedi notun hepsi bir
kaynağa dayanmak zorunda.

**Grubu tanınmayan girdi hata.** Bir yazım hatası girdiyi sessizce
sayfadan düşürüyordu; artık okuma başarısız oluyor.

## Sonuçlar

Tablo altındaki her not, dayandığı belgeye tıklanır durumda. Kaynaklar
sayfası kaynakçanın tamamını grupları ile birlikte taşıyor.

Not sayısı ADR-0069'un otuz ikisinden otuz sekize çıktı. Altı hücre
notsuzdu, yani kaynaksızdı: dünya yüzey alanı, Galileo performansı,
BeiDou kullanılabilirliği, TerraPoiNT doğruluğu, Locata değerleri ve
Pozyx değerleri. Her hücrenin bir kaynağı olması gerektiği kuralı
konunca bu altısı ortaya çıktı.

Metin, `html.escape` bir kez geçiyor ve adres ikinci kez kaçırılmıyor.
Bir ara sürümde `&` işareti iki kez kaçırıldı ve `&amp;amp;` olarak
çıktı, yani `pib.gov.in` adresleri yanlış yere gidiyordu. Bir sınama
şimdi bunu tutuyor.

## Yapılmayanlar

**Adresler denenmedi.** Rapor ne yazdıysa o taşındı. Bir bağlantının
bugün açılıp açılmadığını hiçbir şey kontrol etmiyor, ve ağa çıkan bir
sınama bu deponun kuralına aykırı olurdu (ADR-0008).

**Raporun bir bağlantısı yanlış görünüyor.** "dünya yüzey alanı" için
verilen NASA adresi Ay'ın sayılarını gösteren bir sayfaya gidiyor.
Rapor ne yazdıysa o taşındı; düzeltmek rapor sahibinin işi.

**Sunumun dipnot numaraları ile buradaki anahtarlar eşleşmiyor.**
Anahtarlar sitenin kendi işi (ADR-0069); sunum kendi numaralarını
sürdürüyor.
