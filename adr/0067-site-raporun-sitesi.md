# ADR-0067: site raporun sitesi, benzetim onun bir sayfası

## Durum

Kabul edildi. ADR-0064'ün kurduğu siteyi yeniden düzenliyor.

## Bağlam

ADR-0064 siteyi kurarken başlığına "YERKON benzetimi" yazdı ve sayfaları
benzetimin etrafına dizdi. Bu, deponun ne olduğuna sadıktı ama projenin
ne olduğuna değil.

Proje YERKON: yol kenarındaki mevcut noktalara takılan yayın
birimlerinden kurulan bir karasal konumlandırma yedek katmanı önerisi.
Benzetim o önerinin bir parçası ve tek bir işi vardı, karşılaştırma
tablosunun dört YERKON satırını doldurmak. Tabloda on dört satır var;
benzetim dördünü üretti, kalanı yayımlanmış kaynaklardan geliyor.

Siteyi açan biri önce projeyi görmeli.

## Karar

**Sekiz sayfa, raporun bölümleriyle aynı sırada**: anasayfa, sorun,
sistem, AR-GE, fayda, sonuçlar, benzetim, kaynaklar. Benzetim artık
başlık değil, sayfalardan biri, ve kendi sayfası ilk cümlesinde ne
olduğunu söylüyor.

**İçerik sunumdan geliyor.** Mimarinin üç parçası, neden çift yönlü
ölçüm, üç kurulum grubu ve menzilleri, üç alıcı modülü, dört araştırma
sorusu, pilot doğrulama ve hedefleri, sektör faydası, ticarileşme
aşamaları, ve donanım fiyatları hem tek adet hem yüz adet kademesiyle.

**Üç resim de sunumdan**, ve üçü de açıklayıcı: yol ve tünel çizimi
anasayfada, uydu takımyıldızı sorun sayfasında, YERKON Mimarisi şeması
sistem sayfasında. Hepsi okuma sütununu aşıp sayfada ortalanıyor, çünkü
bir şema paragraf genişliğine indirildiğinde okunmuyor.

**İki palet.** Sayfa okuyanın sistem ayarını izliyor, ve bunu bir
`prefers-color-scheme` sorgusuyla yapıyor, yani betik çalışmasa da doğru
paletle açılıyor. Başlıktaki düğme bunu ezmek için, seçim
`localStorage`'da duruyor. Düğme markup'ta gizli geliyor ve betik onu
gösteriyor: hiçbir şey yapmayan bir düğme, düğme olmamasından kötü.

**Sunumun resimleri açık zeminli.** Koyu paletde her biri parlayan bir
levha olurdu, o yüzden resimler iki paletde de açık kalan bir altlığın
üzerinde duruyor.

## Sonuçlar

Tarayıcıda iki paletde de yürüdüm, düğmeyle ileri geri geçtim, sayfa
hatası yok.

| | önce | sonra |
|---|---|---|
| başlık | YERKON benzetimi | YERKON |
| sayfa | 6 | 8 |
| resim | 1 (ekran görüntüsü) | 4 |
| palet | 1 | 2, sistem ayarını izleyerek |

Statik dışa aktarmada simülasyon düğmesi artık benzetim sayfasına
gidiyor; ADR-0065'in yalnız bu iş için yazdığı ayrı sayfa kalktı, çünkü
benzetim sayfası zaten aynı şeyi söylüyor.

## Yapılmayanlar

**Karşılaştırma tablosunun tamamı sitede yok.** Yalnız dört YERKON satırı
var. Diğer on satır yayımlanmış kaynaklardan gelir ve otuz üç dipnot
taşır; onları siteye koymak elle yazılmış bir veri kümesi demek olurdu,
ki bu deponun tam da kaçındığı şey. Sonuç sayfası nereden geldiklerini
söylüyor.

**Ağırlıklı satırın ağırlıkları iki belgede farklı.** Depo %50, %40, %10
kullanıyor; sunumun dipnotu %50, %35, %15 diyor. Sayılar depodan geldiği
için site depoyu gösteriyor. Hangisinin doğru olduğuna karar verilmedi.

**Sunumdaki fotoğraflar alınmadı.** Kaza fotoğrafı ve stok görseller
haber ve stok kaynaklı; açıklayıcı olanlar alındı, olmayanlar
bırakıldı.
