# ADR-0028: üç satır aynı anda tutulur, biri girip çıkmaz

## Durum

Kabul edildi.

## Bağlam

Görüntüleyicinin dört kipi bir açılır listenin arkasında yaşıyordu ve
geçiş yapmak düzeni sıfırdan yeniden kuruyordu. Kırsal satıra harcanmış
bir öğleden sonra — yükseltilmiş bir direk, sürüklenmiş direkler,
daraltılmış bir aralık — biri tünele bakar bakmaz yok oluyordu.

Bu, sayfanın var olma sebebini olanaksız kılıyordu. Tablonun üç satırı
vardır; onları karşılaştırmak üçünü de hazırlamak demektir ve hiçbiri
hazırlanamıyordu, çünkü hiçbiri başka yere atılan bir bakıştan sağ
çıkmıyordu.

Aynı sorunun ikinci, daha sessiz bir sürümü vardı. Sayfadan başlatılan
bir koşu senaryolarını `catalogue(settings)`'ten yeniden kuruyordu —
sayfanın figürleri uygulanmış hazır düzen. Yani bir tablo koşusu,
ekrandakini değil kataloğun yerleşimini bildiriyordu. Bir direği
sürükle, tabloyu çalıştır; geri gelen sayı başka bir şeyi anlatıyordu.

## Karar

Üç sekme, satır başına bir tane, hepsi aynı anda tutuluyor. `Session`
satır başına bir `ViewState` ve hangisinin gösterildiğini saklar; geçiş
yalnızca sonuncusunu değiştirir. Sıfırlamak gösterilen satırı sıfırlar,
diğerlerine dokunmaz.

Bir koşu **satırları hazırlandıkları gibi** alır: `deployments_of` her
sekmenin kendi `ViewState`'inden kurar, kataloğdan değil. Ne
kurduysanız onu çalıştırırsınız.

Çalıştırmak ya gösterilen satırı — tek satırlık çıktı — ya da üçünü
birden kapsar; ikincisi üç satırı ve onların oluşturduğu ağırlıklı satırı
üretir. Bu, 15. sayfadaki bloğun biçimidir; yani sayfa ile rapor artık
aynı şeyi rastlantıyla değil kuruluşu gereği üretiyor.

Dördüncü bir kip olan karışık koridor bir hazır ayar olarak kalktı.
Türce hiçbir şey kaybolmadı: herhangi bir sekme hâlâ istediği kadar
modülden istediği kadar direk dizisi taşıyabilir ki karışık koridor da
hep bundan ibaretti. Onu kapsayan sınamalar artık böyle birini doğrudan
kuruyor.

## Sonuçlar

Hazırlamak ve karşılaştırmak ilk kez olanaklı.

Değişiklikten, kendi başlarına hata olan iki şey düştü. Kırsal sekme
Gölbaşı tepelerinde açılıyordu, oysa tablonun kırsal satırı Polatlı
ovasında durur; yani resim ile yayımlanan figür farklı yerleri
anlatıyordu. Ve tünel sekmesi bir tünel askısı yerine bir yol kenarı
levhası üzerinde çalışıyordu, çünkü sayfanın montaj listesi elle
yazılmıştı ve askıyı hiç edinmemişti — `design.MOUNTING_CHOICES` de onu
hiç edinmemişti, dolayısıyla birini istemek hata yükseltiyordu.
Birbiriyle ve modelle çelişen iki katalog.

Sayfa artık bu listelerin hiçbirini tutmuyor. Montajları, telsizleri ve
satırları motor sunar; böylece var olan bir montaj seçilebilir, olmayan
biri ise sunulamaz.
