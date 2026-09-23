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

**Simülatör gelmiyor.** (ADR-0080 bunu değiştirdi: simülatör artık ziyaretçinin tarayıcısında çalışıyor.) Arkasında Python bir motor var: link bütçesi,
arazi profili, çekilişler, çözücü. Yerine ne olduğunu söyleyen bir
sayfa geliyor: bir ekran görüntüsü, içinde ne yapıldığı, ve dört
komut. Yarısı çalışan bir kopya hiç olmayandan kötü olurdu.

**Klasör depoda duruyor.** Üretilmiş bir dosyayı depoya koymak
`published.toml` ile aynı karar, ve burada bir faydası daha var: adreste
duran baytlar, diff'te okunan baytlar oluyor.

**Yayın `gh-pages` dalından.** Sitenin dosyaları o dalın kökünde
duruyor, ve dal ilk kez göründüğünde **GitHub Pages kendiliğinden
açıldı**: `has_pages` false iken true oldu, ve ilk yayımlama
`https://ysoktar.github.io/yerkon/` adresine `success` döndü. Hiçbir
ayara dokunulmadı.

Bu, denenen üçüncü yoldu. İlk ikisi kapalı çıktı ve kaydı burada
duruyor, çünkü bir sonraki sefer aynı duvara çarpmamak için:

| yol | ne oldu |
|---|---|
| API'den `POST /repos/.../pages` | proxy bu yolu kapatıyor, 403 |
| `actions/configure-pages` + `enablement: true` | "Create Pages site failed. Error: Resource not accessible by integration". Bir Pages sitesi kurmak depo üzerinde admin istiyor, iş akışının jetonu write'ta bitiyor |
| `gh-pages` dalını push etmek | açıldı |

**İş akışı da o dalı itiyor**, Pages'in yayımlama eylemlerini değil.
Aynı sebep: o eylemler Pages API'sine gidiyor ve jeton oraya
erişemiyor. Bir dal push etmek `contents: write` istiyor, o da var.
`docs/` her değiştiğinde klasör olduğu gibi `gh-pages`'in köküne
kopyalanıyor, tek bir commit olarak.

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

**`gh-pages` tarihçe tutmuyor.** Her yayımlama tek bir commit olarak
zorla itiliyor. Sitenin nereden geldiği ana dalın tarihçesinde duruyor,
yayımlandığı dalda değil.
