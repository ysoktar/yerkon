# ADR-0065: dosya olarak duran site

## Durum

Kabul edildi.

## Bağlam

ADR-0064 siteyi sunucuda üretti, ve sunucu yalnızca `yerkon view`
çalışırken var. Siteyi görmek için depoyu klonlamak, Python kurmak ve
bir komut çalıştırmak gerekiyordu. Kimseye bir bağlantı gönderilemiyordu,
ki bir yarışmaya sunulan bir fikir için bağlantı gönderebilmek işin
kendisi.

GitHub Pages dosya sunar ve hiçbir şey çalıştırmaz. Sayfalar zaten düz
HTML; sorun yalnızca bağlantıların nasıl yazıldığı ve simülatörün
gelemeyeceği.

## Karar

**`yerkon pages` siteyi bir klasöre yazıyor.** On yedi dosya: iki dilde
yedişer sayfa, biçem dosyası, bir ekran görüntüsü ve `.nojekyll`.
Türkçe kökte, İngilizce `en/` altında: rapor Türkçe, ve dil sormadan
adresi açan biri projenin yazıldığı dili görmeli.

**Adresler tek bir yerde.** `Where` nesnesi bir sayfanın diğerini nasıl
adlandırdığını biliyor: sunucu `/sorun` diyor, klasör `sorun.html`.
İkisinin anlaşamadığı tek şey bu, ve bir nesnede durduğu için sayfalar
iki kez yazılmıyor. Hiçbir bağlantı `/` ile başlamıyor, çünkü site
`ysoktar.github.io/yerkon/` altında duruyor ve orada kök başka bir yer.

**Simülatör gelmiyor.** Arkasında Python bir motor var: link bütçesi,
arazi profili, çekilişler, çözücü. Yerine ne olduğunu söyleyen bir
sayfa geliyor: bir ekran görüntüsü, içinde ne yapıldığı, ve dört
komut. Yarısı çalışan bir kopya hiç olmayandan kötü olurdu.

**Klasör depoda duruyor.** Üretilmiş bir dosyayı depoya koymak
`published.toml` ile aynı karar, ve burada bir faydası daha var: adreste
duran baytlar, diff'te okunan baytlar oluyor.

**Yayına bir iş akışı sokuyor**, `docs/` değiştiğinde çalışıp o klasörü
olduğu gibi yükleyerek. Hiçbir şey kurmuyor ve hiçbir şey üretmiyor;
`actions/configure-pages` gerekirse Pages'i kendisi açıyor, yani siteyi
yayına almak bir ayar bulmak değil bir push.

**Ve eskiyebilir**, `published.toml`'un eskiyemeyeceği şekilde: onu bir
koşu yazıyor, bunu hiçbir şey yeniden yazmıyor. O yüzden bir sınama
klasörü geçici bir yere yeniden çiziyor ve bayt bayt karşılaştırıyor.
Sayfayı düzenleyip `yerkon pages` koşmayı unutan da, yeni bir koşu
yayımlayıp siteyi yenilemeyen de burada duruyor.

**Yayımlanmış koşu yoksa yazmıyor.** Sonuç sayfasında "yayımlanmış bir
koşu yok" yazan herkese açık bir site, site olmamasından kötü.

## Sonuçlar

Klasörü bir alt yolun altında (`/try-site/`) sunup tarayıcıda yürüdüm:
altı sayfanın hepsi, ekran görüntüsü, `en/` içine ve dışına dil
değişimi. 404 yok, sayfa hatası yok.

| | sunucuda | dosyada |
|---|---|---|
| `/sorun` | sunucu cevaplıyor | `sorun.html` |
| dil | oturumda, `?dil=en` | `en/` klasörü |
| simülatör | gerçek olan | nasıl çalıştırılacağını söyleyen sayfa |
| tablo | kayıttan, her istekte | kayıttan, yazıldığı anda |

## Yapılmayanlar

**`yerkon pages` elle çalıştırılıyor.** İş akışı klasörü yayına alıyor
ama yeniden çizmiyor. Sınama unutulduğunu söylüyor, kendisi yazmıyor.

**Yayımlanan kökte sitenin dosyaları dışında bir şeyler de var.**
`docs/` zaten `HANDOFF.md`, `TRY-IT.md`, `WINDOWS.md` ve `adr/`
taşıyordu, ve bunlar da adresten okunabiliyor. Depo herkese açık olduğu
için yeni bir şey açılmıyor.

**Ekran görüntüsü elle alındı.** Model değişse de aynı kalır, ve hiçbir
şey bunu hatırlatmıyor.

**Özel alan adı yok.** Site depo adını taşıyor.
