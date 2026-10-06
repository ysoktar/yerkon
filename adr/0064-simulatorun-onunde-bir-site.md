# ADR-0064: simülatörün önünde bir site

## Durum

Kabul edildi.

## Bağlam

`yerkon view` tek bir sayfa açıyordu ve o sayfa gürültü katsayısının
sürgüsüyle başlıyordu. Çalışmanın içinde olan biri için doğru ilk ekran.
Olmayan için değil: YERKON'un ne olduğunu, bu deponun neyi ölçtüğünü ve
neyi ölçmediğini bilmeden bir sürgü hiçbir şey anlatmıyor.

İkinci sorun tablonun kaç yerde durduğu. Terminalde basılıyor, README'de
alıntılanıyor, ve bir sayfada gösterilecekse orada da duracak. İkisi
kopya, ve elle yapılan bir kopya bir sonraki koşuda kayıyor: bu oturumda
yayılım modeli düzeltilirken sayılar dört kez oynadı ve her seferinde
aynı kırk hücre başka bir dosyaya elle yazıldı.

## Karar

**Simülatörün önüne bir site.** Altı sayfa: anasayfa, sorun, sistem,
yöntem, sonuçlar, kaynaklar. Simülatör `/simulasyon` adresinde
bunlardan biri. `index.html` `simulator.html` oldu; `/` artık anasayfa.
Her sayfada simülatöre giden bir düğme, simülatörün panelinde geri dönen
bir bağlantı var.

**Sayfalar sunucuda üretiliyor, dosya olarak durmuyor.** Üç sebep.
Sonuç sayfası tabloyu koşunun yazdığı kayıttan okumak zorunda. Dil
sayfanın değil okuyanın özelliği. Ve betik çalışmasa da açılıyorlar,
ki bir belge sayfasının boş açılması bir hata değil bir kusur olurdu.

**Dil oturumda duruyor.** `?dil=en` oturumu çeviriyor, yani simülatörün
panelindeki TR/EN ile site aynı ayarı paylaşıyor: sitede İngilizceye
geçip simülatöre giren biri İngilizce bir panel buluyor (ADR-0035).

**Yayımlanan tablo bir dosya.** `yerkon table --publish` koştuğu şeyi
`published.toml`'a yazıyor: dört satır, on hücre, artı koşunun tarihi,
neyi okuduğu ve **ne kadar ince okuduğu**. İki şeyi reddediyor:
eksik bir tablo ve kaba bir okuma (ADR-0063). İkisi de bir dosyanın
içinde yayımlanmış bir koşuya benziyor, ve hiçbiri değil.

**Sitede elle yazılmış bir tablo hücresi yok.** Bunu bir sınama
söylüyor: sayfaları kayıt olmadan çiziyor ve yayımlanan her hücreyi
içlerinde arıyor. İlk hâli tek bir hücreyi bir cümlenin içinde buldu,
ve aranınca iki tane daha çıktı. Üçü de yeniden yazıldı: bir hücreyi
tekrarlamak yerine bulguyu anlatıyorlar. "Kırsalda bir paket, konum
alınabilen zeminin 2,6 katına ulaşır" hem daha doğru hem de bir sonraki
koşuda eskimiyor.

Sınama hücreyi tek başına arıyor, daha uzun bir sayının içinde değil.
Tünel satırının alanı 0,02 km², ve sayfada duran 0,024 başka bir figür.

**Her cümle iki dilde.** `Words(tr=..., en=...)` iki alanlı, yani
eksiği bir sınama tek satırda buluyor. İkinci sınama, Türkçesi ı, ş ya
da ğ taşıyan bir cümlenin İngilizcesinin ondan farklı olmasını istiyor:
`E28-2G4M27S` iki dilde aynı ve öyle kalıyor, kopyalanmış bir cümle
yakalanıyor.

Sınama sayfaları değil modülün kendi adlarını geziyor, ve bunu bir hata
yaptırarak öğrendim: sayfalardan geçen ilk hâli, İngilizce üstbilgi
Türkçe yazılmışken "her şey yerinde" diyordu. Üstbilgi, sütun başlıkları
ve tablonun altındaki satır hiçbir sayfanın içinde değil, her sayfanın
üstünde.

## Sonuçlar

Tarayıcıda yürüdüm: anasayfadan altı sayfanın hepsine, oradan dile,
oradan simülatöre ve geri. Sayfa hatası yok.

| | önce | sonra |
|---|---|---|
| `yerkon view` neyi açıyor | simülatör | anasayfa |
| simülatörün adresi | `/` | `/simulasyon` |
| tablonun durduğu yer | terminal ve README | `published.toml` |

Tablonun ilk üç sütunu iki dilde de Türkçe kalıyor. Rapora giren adlar
bunlar, ve sonuç sayfası bunu bir satırla söylüyor.

## Yapılmayanlar

**Site yalnızca sunucu çalışırken var.** Statik bir dışa aktarma yok:
simülatör motoru gerektiriyor, ve yarısı çalışan bir statik kopya
ikisinden de kötü olurdu.

**Sayfalardaki ölçümler hâlâ elle yazılı.** 37,60 dB, 239 ms, 0,0793
ppm ve benzerleri tablo hücresi değil, dolayısıyla yukarıdaki sınama
onları görmüyor. Model oynarsa elle güncellenmeleri gerekir, tıpkı
README'deki karşılıkları gibi.

**Yayımlamak yalnızca komut satırında.** ADR-0024 terminal olmadan da
yapılabilmesini istiyor, ama sayfadan yayımlamak sayfanın o anki
ayarlarını yayımlardı: yayımlanan tablo gönderilen ayarların çıktısıdır,
birinin sürgüyü nereye bıraktığının değil.

**README tabloyu hâlâ metin olarak taşıyor.** Kayıtla aynı olduğunu bir
sınama söylüyor, ama eşitlemeyi elle yapıyorsun. Kaydı okuyup README'yi
yazan bir komut yok.
