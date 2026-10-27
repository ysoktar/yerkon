# ADR-0046: yollar ve yanlarındaki yapılar

## Durum

Kabul edildi.

## Bağlam

İki şey bu veriyi bekleyerek yazılmış ve gelene kadar gri durmuştu:
gerçek yolu süren güzergâh (ADR-0045) ve direği zaten duran bir yapıya
cıvatalayan yerleştirmeler (ADR-0040). İkisi de aynı getirmenin konusu.

Ve istenen şey açıktı: *"haritadaki yolların kenarındaki yol işaretlerine
veya trafik ışıklara yerleştirme için kullanan seçenekler olsun."*

Sorulacak ilk soru, uydurmam gerekip gerekmeyeceğiydi. Gerekmedi.

## Karar

**Aynı makine, kovanın başka yerine bakıyor.** Binaların okuyucusu — bir
listeleme, bir altbilgi taraması, bir satır grubu dizini, bir menzil
okuması — temadan bağımsız hâle getirildi. Tema başına ayrı dizin
dosyası, yoksa bir yol taraması binaların satır gruplarını alır ki bu
yavaş değil **yanlış** bir cevaptır.

**WKB elle çözülüyor.** Overture şekli her mekânsal veritabanının yazdığı
ikili biçimde tutuyor; bir çizgiyi oradan çıkarmak bir bayt sırası, bir
tür kodu ve bir dizi çift duyarlıklı sayıdır. Bunun için bir kütüphane,
arkasında derleyici olan bir bağımlılık demekti — bu proje kendi karo
indiricisini, kendi haritasını ve kendi 3B boyayıcısını yazmışken.

**Kızılay'ın 3×3 km'sinde gerçekte ne var:**

| | |
|---|---|
| Yol parçası | 2 596 — 561 konut, 542 yaya, 364 servis, 333 birincil, 243 ikincil… |
| Altyapı | 810 satır, içinde **77 trafik ışığı** ve 155 otobüs durağı |

**Yalnızca direğin cıvatalanabileceği şeyler `MOUNTABLE`.** ADR-0015'in
söylediği, *zaten duran bir yapının* bedava olduğu; veride ne varsa
olduğu değil. Duvar, bordür, çit ve kamusal sanat aynı temada ve hiçbiri
bir montaj noktası değil, o yüzden hiçbiri listede yok.

**Yayalar sürülecek yol değil.** Yaya yolu, merdiven ve bisiklet yolu
dışarıda — ama bir kural değil bir parametre, çünkü yayaları inceleyen
bir çalışma tam olarak onları isterdi.

**Ağ bir yol değildir.** Bir yol her kavşakta bölünüyor, yani Kızılay
1 638 parça. Listeyi sırayla sürmek aracı birbirine değmeyen yollar
arasında ışınlardı. `road` güzergâhı ağda **yürüyor**: uçları örtüşen
parçaları birleştirip bulabildiği en uzun sürekli koşuyu sürüyor
(Kızılay'da 3 166 m, Polatlı'da 9 693 m). Açgözlü, çünkü bir çizgede en
uzun yol NP-zordur ve burada bir deneme güzergâhı seçiliyor.

**Yol sahaya kırpılıyor, geri çekilmiyor.** Sınıra geri çekilmiş bir yol,
olmadığı yerde bükülen bir yoldur. Dışarıdaki noktalar düşüyor, içeride
kalan koşular ayrı parçalar oluyor (ADR-0037).

**Ağ taşımak, sürülecek yol olmak değildir.** Tünel satırının getirmesi
dört parça getirdi ve hiçbiri onun iki kilometrelik koridorunun içinde
değil. Sayfa `drivable()` soruyor — ağın boş olup olmadığını değil —
çünkü sunulup sonra reddedilen bir yöntem, canlı görünüp hiçbir şey
yapmayan denetimdir (ADR-0036).

## Sonuçlar

Dört saha da yol taşıyor: Kızılay 1 638, Gölbaşı 5 905, Polatlı 5 365,
Kızılcahamam 4. Yapı sayıları 232 / 438 / 22 / **0** — sonuncusu bir dağ,
ve künye bunu "direğe uygun yapı bulamadı" diye yazıyor.

**Asıl bulgu, ve beklediğim gibi çıkmadı.** Kızılay'da aynı çıtaya:

| | direk | hepsi zaten duran yapıda mı | CAPEX | km² başına |
|---|---|---|---|---|
| ızgara | 36 | hayır, 36 yeni direk | 157 178 TL | 17 620 TL |
| geometriye göre arama | 4 | **evet, dördü de** | 44 464 TL | 555 803 TL |

Yani arama gerçekten de her direği zaten duran bir yapıya koyuyor ve
toplam maliyet üçte bire iniyor — **ama hizmet alanı 8,92 km²'den
0,08 km²'ye düşüyor**, dolayısıyla km² başına otuz kat pahalı.

Sebebi aritmetik ve altında gerçek bir tutarsızlık var: dört direk
sahanın köşelerine yayılıyor (2 885 × 2 230 m), erişim 3 825 m, sahanın
köşegeni ~4 200 m. Yani her noktadan **dördü birden** görünmüyor. Arama
`FEWEST_FOR_A_FIX = 3` görüşü hedefliyor; alan sütunu ise `≥4 direk`
sayıyor. İkisi de savunulabilir — üç bir konum için en az, dört onu
denetler — ama aynı şey değiller, ve bu yüzden aramayla yerleştirilmiş
bir yerleşim alan sütununda her zaman kendi inandığından kötü görünür.

Bunu düzeltmedim. İkisinden birini diğerine uydurmak, ölçütü bulguya
uydurmak olurdu; doğrusu ikisinin ayrı şeyler olduğunu yazmak.

## Sonraki adımlar

Aramanın çıtası ile alan sütununun saydığı şey arasındaki fark bir karar
istiyor: arama dörde mi hedeflemeli, yoksa alan sütunu üçü mü saymalı, ya
da ikisi ayrı kalıp rapor bunu söylemeli mi. Üçü de savunulabilir ve
hiçbiri veri işi değil.
