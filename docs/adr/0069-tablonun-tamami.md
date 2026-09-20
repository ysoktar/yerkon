# ADR-0069: tablonun tamamı sitede

## Durum

Kabul edildi.

## Bağlam

Site yalnızca YERKON satırlarını gösteriyordu, ve sonuç sayfası "geri
kalanı raporun dipnotlarında" diyordu. Bu, karşılaştırma tablosunu
karşılaştırma olmaktan çıkarıyor: 22,72 m'nin ne anlama geldiğine karar
vermek için yanında GPS'in 8 m'si ve eLoran'ın 15,72 m'si durmalı.

Tabloyu siteye koymanın bedeli belli: on satır daha, ve hiçbiri bu
deponun ürettiği bir sayı değil. Hepsi yayımlanmış kaynaklardan, ve
çoğu ham değil türetilmiş. GPS'in km² başına CAPEX'i, 7,2 milyar
dolarlık tarihsel bir yatırımın dünya yüzey alanına bölünmesi. Bunu
dipnotsuz koymak, tablonun en yanıltıcı hâli olurdu.

## Karar

**On satır `comparison.toml` içinde, otuz iki notla birlikte.** Kodun
içinde değil, bir veri dosyasında: bir hücrenin nereden geldiği o
hücrenin yanında duruyor ve değiştirmek için Python'a dokunmak
gerekmiyor.

**Hücreler metin, sayı değil.** Çoğu sınır, çift ya da yokluk: "≤ 8",
"≥ %99 / ≥ %90", "-". Bunları sayıya çevirmek taşıdıkları bilgiyi
atmak olurdu.

**Notlar anahtarla işaretleniyor, numarayla değil.** Hücrede `^gps-capex`
yazıyor; sayfa onları ilk göründükleri sırayla numaralandırıyor. Yeni
bir not eklemek dosyadaki hiçbir numarayı kaydırmıyor.

**Boş hücrenin de notu var.** GLONASS'ın CAPEX'i boş, çünkü elde olan
değer saf kurulum maliyeti değildi; QZSS'in alanı boş, çünkü resmî
kaynaklar tek bir toplam km² yayımlamıyor. Bir vekilin sessizce yerine
geçmesi, boşluktan kötü.

**YERKON satırları oraya girmiyor.** Onlar `published.toml`'dan geliyor
ve bir koşu yazıyor. Sayfa ikisini birleştiriyor, ve bizimkileri koyu
zeminle ayırıyor: on üç satırlık bir tabloda hangisinin kimin olduğu
görünmeli.

**Yayımlanmış bir koşu yoksa tablo hiç çizilmiyor.** Sayfa
karşılaştırma sayfası; karşılaştıracak kendi satırımız yoksa on satırı
tek başına göstermek sayfayı başka bir şey yapardı.

## Sonuçlar

On üç satır, otuz iki not, her not iki dilde ve her biri bir hücreye
bağlı. Bir sınama bunu iki yönden de tutuyor: işaret edilen her not var,
ve hiçbir notun işaret edilmediği kalmamış.

Tablo okuma sütununu aşıp 1400 piksele kadar genişliyor; dar pencerede
kendi içinde kayıyor ve sayfayı yana itmiyor.

## Yapılmayanlar

**Kaynak bağlantıları yok.** Notlar kaynağın adını söylüyor, adresini
değil. Raporun kaynakçası adresleri taşıyor, ve onları buraya
kopyalamak üçüncü bir kopya olurdu.

**Diğer on satır elle yazıldı.** YERKON satırlarının aksine onları
üreten bir koşu yok, çünkü onlar başkalarının ölçümleri. Kaynak bir
değeri güncellerse dosya elle güncellenir; bunu hatırlatan bir şey yok.

**Sunumun dipnot numaraları ile sitenin numaraları aynı değil.** Site
kendi sırasıyla numaralandırıyor, ve ağırlıklı satırın notu artık yok
(ADR-0068).
