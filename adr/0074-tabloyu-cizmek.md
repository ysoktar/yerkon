# ADR-0074: tabloyu çizmek

## Durum

Kabul edildi.

## Bağlam

Karşılaştırma tablosu on üç sistemi yedi ölçüyle yan yana koyuyor.
Doğru bir başvuru kaynağı ve kötü bir resim: YERKON'un nerede durduğunu
anlamak için okuyucunun on üç satırı kafasında tutması gerekiyor, ki
kimse tutmuyor.

Sayfada zaten sunumdan gelen üç resim vardı, ama üçü de şema; hiçbiri
tablonun kendi sayılarını göstermiyordu.

## Karar

**Dört çizim, hepsi tablonun kendi hücrelerinden.** Hiçbir şey
hesaplanmıyor: her işaret `published.toml`'un ya da `comparison.toml`'un
bir hücresi, ayrıştırılıp yerine konmuş. Hücre boşsa işaret yok;
uydurulmuş bir değer değil.

Sonuçlar sayfası **kapsama × doğruluk** ile açılıyor, çünkü bütün
tablonun konusu o takas: Pozyx santimetre veriyor çünkü bir depoyu
kapsıyor, GPS dünyayı kapsıyor çünkü metreyle yetiniyor. Ardından
doğruluk karşılaştırması ve kilometrekare başına maliyet. Simülasyon
sayfası her satırın ortancadan en kötü %5'e yayılımını ve yanında düşey
hatasını alıyor. Sorun sayfası dört olayı bir zaman çizelgesinde, sistem
sayfası saat argümanı için iki büyük sayı.

**On üç renk değil, vurgu.** Bizim üç satırımız vurgu renginde, diğer on
tanesi tek bir geri plan grisi. On üç kategorik renk okunamaz ve
sayfanın konusu olan satırları gömerdi.

**Grafik rengi, metin renginden ayrı bir token.** Koyu paletde sitenin
`--accent` ve `--quiet` ikilisi OKLab'de 12 birim ayrı; tam renk gören
bir okuyucunun iki işareti ayırt etmesi için 15 gerekiyor. Metin için
sorun değil — kelimelerin kendi şekli var — ama iki nokta için sorun.
`--chart-mark` ve `--chart-context` her palette ayrı seçildi ve
doğrulandı.

**Çubuk değil, nokta.** Ölçüler on bir basamak geziniyor, yani eksen
logaritmik olmak zorunda. Logaritmik eksende çubuk, uzunluğunun değer
olduğu iddiasını taşır ve bu yanlıştır; büyüyeceği bir sıfır da yoktur.
Çubuk olsaydı GPS, NavIC'in iki yüz bin katı değil dört katı görünürdü.
Nokta yalnızca konumunu iddia eder, ki eksen zaten onun için var.

**Sınır, sınır olarak çiziliyor.** `≤ 8` sekiz sayısı değildir. O
işaretler açık uçlu bir uç taşıyor ve altyazı bunu söylüyor; bir tavanı
nokta olarak çizmek bu resimlerin yalan söyleyebileceği tek yol.

**Çiftli hücrede nokta ilkinde durur ve yazan da odur.** `≤ 10 / ≤ 5`
bir ortalama ve bir en kötü durum taşıyor; işaret ikisinden birinde
duruyor, dolayısıyla yanına ikisini birden yazmak onu bulunmadığı bir
sayıyla etiketlemek olurdu.

**İşaretin yanındaki sayı tablonun kendi metni.** Ayrıştırılmış değerin
yuvarlanmışı değil. Resimle tablo arasında gidip gelen biri iki farklı
sayı bulmamalı.

**Her çizim iki kez.** Biri dizüstü genişliğinde, biri telefon
genişliğinde ve kısa adlarla. Geniş olanı telefonda kaydırılınca etiket
sütununda açılıyor ve hiç veri görünmüyordu; bir tablo aynı şeyi
yaptığında ilk sütunları yine bir şey söyler, bir grafik söylemez.

**SVG, kütüphane değil.** Site ağa çıkmadan ve betik çalışmadan açılan
bir klasör (ADR-0065).

## Sonuçlar

On sınama tutuyor, her biri yakaladığı hata geri konularak doğrulandı:
"R1 ≤ 1" içindeki bir rakamın değer sanılması, tavanın ölçüm gibi
çizilmesi, değerin tablodan sapacak şekilde yuvarlanması, palete
uymayan sabit bir renk, telefon eşinin düşmesi, bir etiketin sayfaya
biçimlendirme olarak ulaşması, kesme işaretinin `&#x27;` olarak
gelmesi, ve boş bir hücrenin doldurulması.

## Yapılmayanlar

**Hata bütçesi çizilmedi.** `yerkon budget` her hata kaynağının payını
veriyor ve bu iyi bir çizim olurdu, ama onu hesaplamak bir koşu sürüyor;
sayfa çizimi hızlı olmak zorunda. Yayımlanan kayda eklenirse çizilebilir.

**Alan çizimi kesildi.** Kapsama × doğruluk dağılımının yatay ekseni
zaten alan sütunu; ayrı bir çubuk grafiği yeni bir şey söylemiyordu.

**Tooltip yok.** Sayfa betiksiz açılmak zorunda, ve altındaki tablo
zaten her hücreyi veriyor.
