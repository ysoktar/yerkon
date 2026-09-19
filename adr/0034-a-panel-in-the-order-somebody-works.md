# ADR-0034: birinin çalıştığı sırada bir panel

## Durum

Kabul edildi.

## Bağlam

Bu projenin yapabildiği her şey sayfadadır (ADR-0024) ve sayfa bunu
motorun büyüdüğü sırayla tek bir sütun olarak gösteriyordu: saha biçimi,
direk grupları, alıcılar, arazi, mevzuat, hazır seçenekler, çalıştır,
çözücü, tarama, yetmiş iki ayar, sonuç. Yaklaşık üç bin piksel.

Kimse üç bin pikseli okumaz. Geldikleri tek denetimi ararken kaydırırlar
ve diğer bölümlerin hangi değerde olduğunu hepsini açmadan göremezler.
Cevap — bütün çalışmanın var olma sebebi olan dört figür — en altta,
yetmiş iki ayarın ötesindeydi; yani bir denetimi değiştirip ne yaptığını
görmek iki kez kaydırmak demekti.

Elinde taze bir yol parçası olan birini düşünün. Sırayla ne yaparlar?
Zemini bul. Sahanın biçimini söyle. Üzerine bir şey koy. Neyi başarması
gerektiğini söyle. Bunun neye dayandığını sor. Çalıştır. Bu sıra panelde
hiçbir yerde görünmüyordu ve ilk adım — bir yer indirmek — dördüncü
sıradaydı ve bir `<details>` içine katlanmıştı.

Yetmiş iki ayarın kendi sorunu vardı. Kendi anahtarlarıyla
etiketlenmişlerdi: `clock.crystal.residual_ppm`. Bu, `defaults.toml`
dosyasına ait olan ve dosyayı düzenleyen birinin ihtiyaç duyduğu şeydir;
bir ad değildir — yetmiş iki maddelik bir liste, bu çalışmanın dayandığı
şeyler kümesi olarak değil bir değişken dökümü olarak okunur. Ve
otuz beşi hâlâ tahmindir ki bu, listenin söyleyebileceği en yararlı tek
şeydir; onu bir `title` özniteliğinde söylüyordu, yani kimseye
söylemiyordu.

## Karar

O sırada altı adım; her biri, özeti kendi durumunu taşıyan bir
`<details>`:

    1 YER       kizilay · ölçülmüş zemin
    2 SAHA      3,0 km × 3,0 km alan
    3 YERLEŞİM  49 direk · 1 grup · 2 alıcı
    4 HEDEF     ±5,0 m · TR · tek yönlü
    5 DAYANAK   72 değerin 35 tanesi varsayım
    6 ÇALIŞTIR  üç satır ve ağırlıklı ortalama

Bir seferde biri açık ve açıldığında görüş alanına getiriliyor. Kapatmak
hiçbir şey kaybettirmez, çünkü satır adımın ne tuttuğunu söyler; paneli
bir ekrana sığdıran da budur.

Sonuç, panelin altına sabitlenmiştir ve asla kayıp gitmez.

Aralığı olan her ayar bir sürgü ve tam bir sayı çizer. Adımı 500 olan bir
sürgüye 4000 verilemez ve tek başına bir sayı, içinde yaşadığı aralık
hakkında hiçbir şey söylemez; sayı sürgünün uçlarını da geçebilir, çünkü
onu kısıtlamak, bir denetimin kendisine bakıldığı için bir ayarı
değiştirmesi olurdu.

Yetmiş iki figür dahil her ayarın üzerinde bir arama kutusu. Türkçe, bir
klavyenin düşünmeden ulaştığı harflere katlanır; böylece "gurultu",
gürültü katsayısını bulur. Bir adım tam olarak bir eşleşme tuttuğunda
açıktır ve içindeki eşleşmeyen her şey gizlenir.

Her figür, sayfanın geri kalanının yazıldığı dilde adlandırılır;
anahtarı bir imleç uzaklığındadır ve değerinin nereden geldiğini
gösteren renkli bir işaret taşır. "Yalnız varsayımları göster" listeyi
hâlâ tahmin olan otuz beşe indirir.

## Sonuçlar

Bütün çalışma artık kaydırmadan altı satırda okunuyor ve cevap her zaman
onu kımıldatan denetimlerin yanında, ekranda.

`defaults.toml` dosyasına Türkçe adı olmadan eklenen bir figür,
kaybolmak yerine kendi anahtarı olarak düşer — ve bir sınama adı
olmayanları adıyla sayar, böylece liste sessizce yeniden bir değişken
dökümüne dönüşmez.

Hâlâ tutarsız olan ve söylenmeye değen şey: her figürün altındaki, neyi
etkilediğini söyleyen satır motordan gelir ve İngilizcedir. Bu dizgiler
Python tarafında içlerinde sayılarla kurulur; onları çevirmek sayfanın
değil motorun işidir ve yapılmamıştır.

*Sonradan:* ADR-0035 tam olarak bunu yaptı. `affects`, `note`, `source`
ve `sensitivity` artık her figürün yanında iki dilde durur; yukarıdaki
paragraf yazıldığı andaki durumu anlatır.
