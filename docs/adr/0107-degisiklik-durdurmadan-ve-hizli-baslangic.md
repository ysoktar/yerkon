# ADR-0107: değişiklik kullanıcıyı durdurmadan uygulanır; haritadan hızlı başlangıç

## Durum

Kabul edildi (proje sahibinin isteği, 28 Eylül 2026). ADR-0009'un "önce
onay" kuralının yerine geçer; o kaydın asıl amacı, bir değişikliğin
zorladığı her şeyin görünür olması, olduğu gibi kalıyor.

## Bağlam

ADR-0009'a göre bağlantı bütçesinin okuduğu bir ayar değişince sayfa
önce tam ekran bir pencere açıyor, zorlanan değişiklikleri listeliyor ve
"Uygula" ya da "Vazgeç" bekliyordu. Bir zemin seçmek, getirilen bir yere
geçmek, aramanın bulduğu yerleşimi uygulamak ve kayıtlı bir düzenlemeyi
yüklemek hep bu pencereden geçiyordu. Sayfayı ilk kez açan biri için bu,
her adımda durup anlamadığı bir listeyi onaylamak demekti.

Ayrıca sayfayı hiç bilmeyen birinin "şu yer için en iyi yerleşim ne
verir" sorusuna ulaşması altı adımın dördünü gerektiriyordu: yer getirme
paneli, zemin seçimi, altıncı adımdaki yerleştirme araması ve en alttaki
çalıştır düğmesi.

## Karar

- Değişiklik hemen uygulanıyor. Motor yine ne kadarını zorladığını
  söylüyor; sayfa bunu sahnenin altında, işi durdurmayan bir notta
  gösteriyor. Notta "Geri al" düğmesi var: değişiklikten önceki değerleri,
  zorlanabilecek alanlarla (sahanın boyu ve eni, direk grupları, elle
  taşınan ve silinen direkler) birlikte geri yazıyor.
- Kayıtlı bir düzenlemeyi yüklemek de aynı şekilde: hemen yükleniyor, not
  sekmenin önceki hâline dönüşü sunuyor.
- Onay penceresi yalnız geri alınamayan tek iş için kaldı: kayıtlı bir
  düzenlemenin dosyasını diskten silmek.
- Panelin başına "Hızlı başla" kutusu eklendi. Haritada bir kutu seçmek
  yetiyor; sayfa sırasıyla şunları yapıyor:
  1. Yerin zeminini, binalarını, yollarını ve uydu görüntüsünü getiriyor.
  2. 16 km²'ye kadar kutuyu şehir içi, daha büyüğünü kırsal satırında
     açıyor; sahayı getirilen alanın tamamı yapıyor.
  3. Yerleştirme aramasını koşuyor (şehirde "aynı kapsama daha ucuza",
     kırsalda "aynı maliyetle daha çok kapsama", ADR-0096'daki gibi) ve
     sonucu uyguluyor.
  4. Simülasyonu kaba okumayla (ADR-0063) koşuyor.
  Her adım paneldeki elle yapılan adımın aynısı; akış yeni bir hesap
  eklemiyor. Kutu 2 km ile açılıyor; 16 km²'yi geçen kutuda sürenin
  uzayacağı önceden söyleniyor.
- Yeni bir direk grubu ve yeni bir alıcı, tablonun direklerinin ve
  aracının taşıdığı 20 dBm modülle (EBYTE E28-2G4M20S) açılıyor. 12,5 dBm
  modülün adı "Semtech SX1280 (EBYTE E28-2G4M12S)" yerine "EBYTE
  E28-2G4M12S" oldu, çünkü satın alınan parça EBYTE modülü. Yaya alıcısı
  tabloda olduğu gibi bu modülü taşımaya devam ediyor.

- Yerleştirme yöntemlerinin adları proje sahibinin onayıyla sadeleşti ve
  liste dört başlık altında toplandı:

  | Yöntem | Eski ad | Yeni ad | Başlık |
  |---|---|---|---|
  | grid | Kare ızgara: kaydırmalı satırlar | Düzenli ızgara | Hazır desenler |
  | hex | Altıgen kafes: bir alanı en az direkle örter | Petek ızgara: alanı en az birimle örter | Hazır desenler |
  | corridor | Yol boyunca: iki yanda dönüşümlü | Yol boyunca, iki yanda sırayla | Hazır desenler |
  | perimeter | Çevre: yalnızca sahanın kenarında | Yalnız sahanın kenarında | Hazır desenler |
  | greedy-coverage | Arama: en çok zemini örten (klasik kapsama) | Otomatik: sinyal en geniş alana ulaşsın | Otomatik arama |
  | greedy-dop | Arama: en iyi geometri (konum için doğru ölçüt) | Otomatik: en iyi konum geometrisi | Otomatik arama |
  | k-cover | Arama: her noktaya yeter sayıda direk | Otomatik: her noktaya dört birim | Otomatik arama |
  | placed | Yöneylem: var olan yüksek yerler (Yerleştir düğmesi) | En iyi yerleşim: var olan direk ve yapılar (tablonun kullandığı) | Var olan yapılar |
  | manual | Elle: hiçbiri, boştan başla | Elle: boş başla, birimleri kendin koy | Elle |

  "Yöneylem yerleşimi" bölümünün adı "En iyi yerleşimi bul" oldu.
- Yerleştirme araması adayları artık sahanın ölçülen zemininin içinde de
  tutuyor. Önceden yalnız o anki direklerin kapladığı alanla sınırlıydı;
  başka bir zeminden taşınan bir yerleşim kendi koordinatlarını koruduğu
  için, yeni bir 2 km'lik kutuda arama kutunun 700 m dışında aydınlatma
  direkleri seçmişti. Tablonun kayıtlı yerleşimleri bu sınırın içinde
  bulunduğu için etkilenmiyor.
- Uydu görüntüsü kapsama renklerinin altında kalıyor ve bu, yüklenmemiş
  bir görüntü gibi okunuyordu. Onay kutusunun altındaki not, renksiz
  görmek için sahnedeki listeden «Yalnız zemin (uydu ve yollar)»
  seçilmesini söylüyor.

- Fotoğraf, ekran ölçeği %125 ya da %150 olan ekranlarda karelere hiç
  döşenmiyordu. Döşeme kodu, sayfanın ekran ölçeği için koyduğu dönüşümü
  kendi dönüşümüyle değiştiriyordu; fotoğraf karenin dışına çiziliyor,
  her kare tek renk kalıyordu. İki dönüşüm artık birleştiriliyor.
- Kamera yaklaşınca aynı sağlayıcıdan, ekrandaki bölge için daha ince
  karolar isteniyor: en fazla 48 karoya sığan en ince düzey, sahanın
  kendi düzeyinin en çok üç üstü ve en fazla 19. Kızılay'da bu 0,9
  m/pikselden yaklaşık 0,2 m/piksele iniyor.
- Tarayıcının eski bir çizim dosyasını kullanmaması için simülatörün
  dosyaları, içeriklerinden hesaplanan bir sürüm etiketiyle
  isteniyor; bir dosya değişince adresi de değişiyor.
- Sitedeki dört görsel PNG yerine WebP (1,5 MB yerine 216 KB); boyutları
  sayfada yazılı ve aşağıdakiler gerektiğinde yükleniyor.
- Ana sayfadaki fiyat, sunum ve formdaki gibi yuvarlak: 1000 adette
  yaklaşık 1400-1700 lira (malzeme listesinde 1381,83 ve 1680,26).

## Sonuç

Tablonun sayıları değişmiyor: hiçbir satırın modülü, yerleşimi ya da
ayarı değişmedi. Değişen, sayfanın bir değişikliği nasıl karşıladığı ve
ilk kez gelen birinin nereden başladığı.

Ankara'da 2 km'lik bir kutuyla denendi: yerel sunucuda hızlı başlama
129 saniyede bitti (13 birim, hepsi sahanın içinde); tarayıcıda çalışan
sürümde de dört adım tamamlandı.
