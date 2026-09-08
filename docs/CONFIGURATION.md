# Üç senaryonun yapılandırması nasıl seçildi

Tablodaki üç satırın her biri bir yapılandırmanın çıktısı: menzil bant
genişliği, düğüm aralığı, radyo. Bu belge o seçimlerin nasıl yapıldığını
yazıyor.

Yöntem her senaryoda aynı. Yapılandırmalar süpürüldü, her biri tam
senaryoyla çalıştırıldı (füzyonlu, 16 koşu, seed 42), sonuçlar maliyet ve
HPE P50 üzerinde Pareto'ya göre elendi. Bir yapılandırma ancak kendisinden
hem ucuz hem doğru bir başkası yoksa Pareto'da kalıyor.

Kararlar iki türe ayrılıyor. **Bedava seçim**, yeni yapılandırmanın
mevcudunu iki eksende birden yenmesi. Ödünleşim yok, daha önce yanlış
noktada durulmuş. **Gerçek ödünleşim** ise ucuzlamanın doğruluğa mal
olması. Orada karar gerekiyor ve gerekçesi yazılmalı.

## Şehir içi

Seçilen yapılandırma 406 kHz menzil bandı ve 175 m ızgara aralığı.

### Bant genişliği

| Bant | HPE P50 | HPE P95 | Not |
|---|---|---|---|
| 203 kHz | 2,82 m | 5,96 m | zamanlama çözünürlüğü yetersiz |
| 406 kHz | **1,64 m** | **3,40 m** | Semtech'in ranging modunun ayarı |
| 812 kHz | 2,35 m | 4,98 m | çok yolluluk seçme hataları başlıyor |
| 1625 kHz | 5,01 m | 10,07 m | NLOS hatalarının %28'i 10 m'yi aşıyor |

Eğri U biçimli, çünkü iki etki ters yönde çalışıyor. Geniş bant zamanlama
çözünürlüğünü artırıyor. Aynı zamanda çok yolluluğu ayrı tepelere ayırdığı
için tepe dedektörünün yanlış yolu seçmesini mümkün kılıyor. Ayrıntısı
[WAVEFORM.md](WAVEFORM.md) içinde.

Sonuç raporun lehine. 406 kHz zaten parçanın ranging varsayılanı, yani
şehir içi için örtük tercih doğruymuş. Değiştirilecek bir şey yok.

### Izgara aralığı

| Aralık | Düğüm | TL/km² | HPE P50 | HPE P95 | En az anchor |
|---|---|---|---|---|---|
| 125 m | 81 | 110652 | 2,17 m | 4,44 m | 8 |
| 150 m (eski) | 49 | 66937 | 1,95 m | 3,99 m | 8 |
| 175 m | **36** | **49179** | **1,64 m** | **3,40 m** | 5 |
| 200 m | 36 | 49179 | 1,69 m | 3,23 m | 8 |
| 225 m | 25 | 34152 | 1,97 m | 4,76 m | 4 |
| 250 m | 25 | 34152 | 2,06 m | 4,68 m | 4 |
| 275 m | 16 | 21857 | 2,29 m | 4,86 m | 4 |

Bu bedava bir seçim. 175 m, 150 m'yi hem %27 ucuzlukta hem doğrulukta
yeniyor.

Sebebi geometri. Bir fix en fazla sekiz anchor kullanıyor. Alıcı sekizden
fazlasını duyduğu anda fazlalar hiç kullanılmıyor, ve ızgarayı sıklaştırmak
yalnızca en yakın sekizinin yaydığı tabanı daraltıyor. Daha çok donanımla
daha kötü geometri. 150 m'de alıcı 20 anchor duyup 8'ini kullanıyor,
175 m'de 15 duyup yine 8 kullanıyor, ve o sekizi daha geniş yayılmış
oluyor.

225 m maliyeti bir kez daha yarıya indirip 150 m'nin doğruluğunu veriyor.
Alınmadı, çünkü yolun en kötü noktasında sadece dört anchor kalıyor. Dört,
3B fix için asgari sayı, yani kaybolan bir pakete tolerans yok. 175 m beşte
kalıyor. Bütçe sıkışırsa 225 m masada.

## Kırsal

Seçilen yapılandırma 812 kHz menzil bandı ve 750 m levha aralığı. İkisi de
bedava seçim.

### Bant genişliği

| Bant | HPE P50 | HPE P95 |
|---|---|---|
| 203 kHz | 5,82 m | 12,07 m |
| 406 kHz | 3,22 m | 5,96 m |
| 812 kHz | **2,55 m** | **3,86 m** |
| 1625 kHz | 3,54 m | 6,79 m |

Maliyet bant genişliğiyle değişmiyor, hata %21 düşüyor. Optimum şehir
içindekinden bir katlama geniş, çünkü koridor daha açık: engellenen link
oranı %35 değil %15. Çok yolluluk seçme hatası daha seyrek olduğu için
zamanlama çözünürlüğü kazancı daha uzun sürüyor.

Bu bir konfigürasyon değişikliği, donanım değişikliği değil.

### Levha aralığı

| Levha aralığı | Düğüm | TL/km² | HPE P50 | HPE P95 | VPE P95 |
|---|---|---|---|---|---|
| 500 m (eski) | 187 | 200854 | 2,88 m | 7,57 m | 0,98 m |
| 750 m | **131** | **140705** | **2,55 m** | **3,86 m** | 1,00 m |
| 1000 m | 103 | 110631 | 2,46 m | 11,07 m | 1,52 m |
| 1500 m | 75 | 80557 | 2,59 m | 7,39 m | 1,26 m |

Şehir içindekiyle aynı etki. 750 m, 500 m'den %30 ucuz ve hem medyanda hem
kuyrukta daha iyi, dolayısıyla bedava.

750 m'den sonrası ödünleşime dönüyor. 1000 m medyanda 9 cm kazandırıp
kuyruğu üç katına çıkarıyor, 1500 m ise ikisinde de daha kötü. Medyan
750 m'den sonra düz gidiyor çünkü onu yanal harita kısıtı belirliyor,
kuyruk ise anchor seyrekleştikçe bozuluyor.

## Tünel

Seçilen yapılandırma 60 m düğüm aralığı, yani değişiklik yok.

| Aralık | Düğüm | TL/km² | HPE P50 | HPE P95 | VPE P95 | En az anchor |
|---|---|---|---|---|---|---|
| 40 m | 1250 | 2043050 | 0,36 m | 0,96 m | 1,04 m | 7 |
| 50 m | 1000 | 1634440 | 0,39 m | 1,02 m | 1,26 m | 6 |
| 60 m | 834 | **1363123** | **0,43 m** | 1,45 m | **0,69 m** | 5 |
| 70 m | 715 | 1168625 | 0,55 m | 1,34 m | 0,87 m | 4 |
| 75 m | 667 | 1090171 | 0,43 m | 1,02 m | 1,72 m | 4 |

Burada Pareto tamamen ödünleşim. Hiçbir yapılandırma bir diğerini iki
eksende birden yenmiyor.

75 m %20 ucuz ve yatayda 60 m'den kötü değil. İki sebeple alınmadı. Dikey
hata 0,69'dan 1,72 m'ye çıkıyor, ve tünel satırının varlık sebebi GNSS'in
hiç olmadığı yerde yükseklik verebilmek. İkincisi, 75 m tam olarak
`aralık ≤ menzil/2` sınırında oturuyor (menzil 150 m), yani yolun en kötü
noktasında dört anchor kalıyor. Tünelde paket kaybı %3 ve kullanılabilirlik
zaten %99,3. Beş ölçümden ikisini kaybetmek fix'i bitiriyor, dörtten birini
kaybetmek de bitirir. Marj bırakmaya değer.

Ters yönde 50 m aralık P50'yi 0,43'ten 0,39 m'ye indiriyor, ama maliyeti
%20 artırıyor ve dikey hatayı kötüleştiriyor. Tünel zaten km² başına en
pahalı satır, ve oraya konan paranın karşılığı 4 cm.

Tünel sayıları koşular arası yaklaşık %15 oynuyor
([WAVEFORM.md](WAVEFORM.md), tekrarlanabilirlik bölümü). 60 m ile 75 m
arasındaki yatay fark bu belirsizliğin içinde kalıyor. Dikey fark kalmıyor,
ve karar ona dayanıyor.

## Özet

| Senaryo | Değişen | Kazanç | Türü |
|---|---|---|---|
| Şehir içi | Izgara 150 m yerine 175 m | %27 ucuz, %16 daha doğru | bedava |
| Şehir içi | Bant 406 kHz | zaten doğruymuş | doğrulama |
| Kırsal | Bant 406 kHz yerine 812 kHz | %21 daha doğru, maliyet aynı | bedava |
| Kırsal | Levha aralığı 500 m yerine 750 m | %30 ucuz, kuyruk %49 daha iyi | bedava |
| Tünel | Aralık 60 m | değişmedi | ödünleşim reddedildi |

Üç bedava kazanç var ve üçü de konfigürasyon: iki aralık ve bir radyo
ayarı. Ek donanım, ek düğüm, yeni parça yok. Şehir içi km² başına maliyet
66937 TL'den 49179 TL'ye, kırsal 200854 TL'den 140705 TL'ye iniyor, ve
her iki satır aynı anda daha doğru hale geliyor.

Bunlara ek olarak kırsalda ve tünelde yanal harita kısıtı devreye alındı.
O da ücretsiz, çünkü yüksekliği veren haritanın aynısı taşıt yolunun
nerede geçtiğini de veriyor. Kırsal HPE P95'i 26,49 m'den 3,86 m'ye
indiriyor, gerekçesi README'de.

Bu seçimler üç varsayıma dayanıyor: engellenen link oranları (%35 ve %15),
NLOS kanalının sertliği, şehir içi yol kaybı üsteli. Üçü de bu projenin
seçimleri, ölçüm değil. Optimum bant genişliği ve aralık bu sayılara bağlı,
o yüzden saha ölçümü geldiğinde süpürme yeniden çalıştırılmalı.
