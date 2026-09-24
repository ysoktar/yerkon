# Başvuru incelemesi: sunum, form, şartname ve model

24 Eylül 2026. Karşılaştırılanlar:

- `YERKON.pptx` (20 slayt, 24 Eylül yüklemesi),
- `yerkon_guncel_basvuru_formu.docx`,
- `guncel-sartname_1.docx` (Ulaşan ve Erişen Türkiye 2053 Ar-Ge Fikir Yarışması şartnamesi),
- bu depo: model, `published.toml` (23 Eylül koşusu) ve site.

Her bulgunun yanında nereden geldiği yazıyor. Modelden gelen sayılar
`src/yerkon` altındaki koddan, sitede yayımlanan sayılar `published.toml`
dosyasından okundu; hiçbiri elle yazılmadı. Dış kaynaklardan gelenlerin
bağlantısı var. Bu ortamdan erişilemeyen siteler ayrıca belirtildi.

## En önemli on bulgu

1. **Sunumdaki YERKON sayıları eski.** Slayt 16'daki üç satır (ör. şehir
   içi HPE P50 1,28 m, kullanılabilirlik yaklaşık %98, alan 1,00 km²)
   bugünkü modelin çıktısı değil. Site şehir içi için 2,11 m, %75,27 ve
   5,96 km² yayımlıyor (24 Eylül). Kırsalda fark daha büyük: sunum
   yaklaşık %98,9, site %61,03. Sitenin kullanılabilirliği artık
   doğruluğa bağlı (ADR-0084), sunumunki değil. Sunum, form ve site aynı sayıyı söylemeli; şartnamenin
   "sonuçların tutarlılığı" ölçütü tam olarak buna bakıyor.
2. **Kırsal birim için "8-10 km" ve 27 dBm'lik modül iddiası Türkiye
   kuralıyla tutmuyor.** Türkiye'de 2400-2483,5 MHz için genel sınır
   20 dBm e.i.r.p.; frekans atlamasız geniş bant iletimde ayrıca
   10 dBm/MHz güç yoğunluğu sınırı var (TS EN 300 328). SX1280'in en
   doğru mesafe ölçümü ayarı olan 1625 kHz'de ikincisi bağlayıcı:
   10 mW/MHz × 1,625 MHz yaklaşık 12,11 dBm e.i.r.p. Model iki sınırı da
   uyguluyor ve düşük olanı alıyor (`regulatory.py`). E28-2G4M27S'nin
   üreticinin 8 km'yi ölçtüğü 27 dBm'i bu ayarda havaya çıkamıyor; model
   E28-2G4M12S ile aynı sonucu veriyor (ADR-0079). Mesafe ölçümü EN 300
   328 anlamında frekans atlamalı yapılırsa yoğunluk sınırı düşer ve
   20 dBm geçerli olur; o zaman amplifikatör yeniden anlam kazanır (bkz.
   "Model doğruluğu"). Menzil sayıları (bağlantı 7,4 km, 5 m hassasiyet
   3,5 km) yasal ya da fiziksel sınır değil, modelin belirli
   varsayımlarla ürettiği sonuç; en çok da doğrulanmamış bir alıcı
   duyarlılığına bağlı.
3. **SX1280 için "±1 m" tek bir ölçümün değeri değil.** Semtech'in
   AN1200.29 notundaki yaklaşık 1 m, 40 frekansa atlanarak yapılan
   yaklaşık 80 ölçüm alışverişinin ortalaması. Modeldeki tek alışveriş
   tabanı 2,94 m ve bu projede gerçek parça üzerinde ölçülmüş tek değer
   (Stuart Robinson, 0-250 m).
4. **Maliyetin büyük kısmı elektronik değil.** Şehir içi yatırımda
   36 birimin kendisi 25850 TL, montaj 88200 TL. Kırsalda birimler
   35184 TL, montaj 225400 TL, güneş paneli ve akü 114170 TL. Sunum ve
   form fiyat tartışmasını 1000-1600 TL'lik karta indiriyor; asıl
   kaldıraç montaj, enerji ve bakım.
5. **Kartların fiyatı da düştü.** Aynı parçaların daha ucuz satıcıları ve
   muadilleriyle şehir içi yayın birimi 100 adette 1366,07 TL'den
   797,84 TL'ye, 1000 adette 718,05 TL'ye iniyor. Formun "1.100-1.650 TL"
   aralığı hem eski hem sunumun kendi tablosuyla (1082-1634 TL) çelişiyor.
6. **TWR'nin hava süresi sunumda sayıyla yok.** SX1280'de SF10 ve
   1625 kHz ile bir mesafe ölçümü 31,8 ms sürüyor. Tur başına 12 direk
   sorulunca bir alıcı 382 ms'de bir konum alıyor. Model bütün sahayı tek
   kanal sayıyor; bu varsayımla saniyede bir konum için sahada iki alıcı
   sığıyor. Bu, TWR'nin bilinen zayıf yanı ve sunumun kendi araştırma
   sorusu; sayıyla yazılırsa güçlü bir Ar-Ge gerekçesi olur.
7. **Her yanıtı ECDSA ile imzalamak hava süresini ikiye katlıyor.** 64
   baytlık bir imza yanıt çerçevesine girince SX1280'de bir alışveriş
   31,8 ms'den 63,9 ms'ye çıkıyor. UWB'de fark yok (2,4 ms'den 2,5 ms'ye).
   İmzayı her mesafe ölçümüne değil, kimliği, koordinatı ve sayacı
   taşıyan seyrek bir yayına koymak gerekiyor.
8. **Uçak ve havalimanı örnekleri sistemin yapabileceğini aşıyor.**
   Yol kenarındaki direkler yerdeki bir alıcıya hizmet etmek için
   konumlandırılıyor. Modelde düşey hata (VPE P95) şehirde 64 m, kırsalda
   141 m; bu, dağa yaklaşan bir uçağa yardım edecek bir düşey değil.
   New Mexico kazası gerçek, ama NTSB nedeni henüz belirlemedi; sunum
   nedeni kesinmiş gibi yazıyor.
9. **Şartnamenin biçim kuralları formda uygulanmamış.** Formdaki yanıtlar
   Calibri 11 pt; şartname Times New Roman, 14 pt kalın başlık ve 1,5
   satır aralığı istiyor. Formun "Projeyi açıkladığımız web sitesi"
   satırı boş; sunumda adres var.
10. **Sayfa sınırı belirsiz ve sınırda.** Şartname "sunum dosyası ve
    başvuru formu en fazla 20 sayfa" diyor. Sunum tek başına 20 slayt.
    Sınır ikisi için birlikteyse aşılıyor. UDHAM'a sorulmalı ya da sunum
    kısaltılmalı.

## Şartnameye uygunluk

| Şartname maddesi | Durum | Ne yapılmalı |
|---|---|---|
| Lisans öğrencisi, en fazla 5 kişi, bir temsilci | Üç lisans öğrencisi, temsilci belli (slayt 2) | Tamam |
| Tek alan seçimi | Formda "Karayolu" işaretli | Tamam. Sunumdaki havacılık ve denizcilik örnekleri alanı bulandırıyor; "ileride uyarlanabilir" diye tek cümlede kalmalı |
| Başvuru formu imzalı | İmza bölümü boş, kişisel alanlar boş | Tüm üyeler ve varsa danışman imzalamalı |
| Taahhütname, öğrenci belgesi (e-Devlet barkodlu), imzalı özgeçmiş | Yüklenen dosyalarda yok | Her üye için hazırlanmalı |
| Yazım dili Türkçe | Tamam | "Cross-check", "reconvergence time", "deployment" gibi İngilizce kelimeler Türkçe karşılıklarıyla yazılmalı |
| Times New Roman, başlıklar 14 pt kalın, 1,5 satır | Sunum çoğunlukla Times New Roman ve 1,5 satır. Slayt içi başlıklar ("Dünyadan Örnekler", "YERKON Mimarisi", "Grup 1") kendi boyutu tanımlanmadan gövde boyutunu alıyor, 14 pt'nin altında görünüyor. Form yanıtları Calibri 11 pt | Form yanıtları Times New Roman'a çevrilmeli; slayt içi başlıklar 14 pt kalın yapılmalı. PowerPoint'te kontrol edilmeli |
| Sunum ve form en fazla 20 sayfa | Sunum 20 slayt | Sınırın ortak olup olmadığı sorulmalı. Güvenli yol: slayt 17 ve 18'deki dipnotları kısaltıp birleştirmek, slayt 20'yi ("Arz ederim") kaldırmak |
| Özet, kapak dahil en fazla 5 sayfa, sekiz başlığı içermeli | Sunumda "Özet" diye bir bölüm yok; formdaki özet kısa | Tanım, önem ve amaç, özgün yönler, beklenen etkiler, **uygulama süreci**, **sonuçlar**, sektöre katkı, sosyal, ekonomik ve teknik faydalar. İkisi eksik: bir zaman çizelgesi (iş paketleri, aylar) ve güncel simülasyon sonuçları |
| Özgünlük: başka yarışmada sunulmamış | Formda "Hayır" | Tamam. Proje sitesi herkese açık; bu bir sunum sayılmaz ama patent düşünülüyorsa açık yayın tarihinin yenilik değerlendirmesine etkisi bir patent vekiline sorulmalı |

### Değerlendirme ölçütlerine göre

- **Özgünlük ve yaratıcılık.** Güçlü yan: var olan AUS kabinlerini,
  aydınlatma direklerini ve dağıtım şebekesini kullanmak, TWR ile ağ
  senkronizasyonundan kurtulmak, GNSS bütünlük haritası. Sitedeki
  yöneylem yerleşimi (ADR-0081) bu fikrin sayısal karşılığı: direkleri
  zaten yüksek olan yerlere koyarak aynı parayla daha çok alan.
- **İhtiyaca çözüm.** Tünel satırı en ikna edici: %98,61 kullanılabilirlik
  ve metre altı P50. Sunumun ilk ticarileşme alanı olarak tünelleri
  seçmesi modelle uyumlu.
- **Sürdürülebilirlik.** Çevresel boyut zayıf anlatılmış. Modelde bir birim
  yılda 3 kWh tüketiyor; kırsalda şebekesiz birimler güneşle çalışıyor.
  Bunlar sunuma bir cümleyle girmeli.
- **Bilimsel yöntem.** En güçlü yan olabilir: gerçek Ankara zemini
  (Copernicus yükseklik modeli, OpenStreetMap binaları), gerçek bir
  ölçümle kalibre edilmiş SX1280 tabanı, ITU-R P.526 kırınımı, sekiz
  gölge çekilişi, her varsayımın kaynağıyla birlikte dosyada durması ve
  tarayıcıda çalışan simülatör. Ama sunum bu yöntemi değil eski bir
  Monte Carlo koşusunu anlatıyor (slayt 18, dipnot 28-32). Dipnotlar
  bugünkü yöntemi anlatacak şekilde yeniden yazılmalı.

## Sunum, form ve model arasındaki farklar

### Sonuç tablosu (slayt 16)

| Satır | Sütun | Sunum | Site (24 Eylül koşusu) |
|---|---|---|---|
| Şehir içi | HPE P50 | 1,28 m | 2,11 m |
| Şehir içi | HPE P95 | 2,99 m | 6,05 m |
| Şehir içi | VPE P95 | 31,47 m | 3,67 m |
| Şehir içi | Kullanılabilirlik | yaklaşık %98,0 | %75,27 |
| Şehir içi | Alan | 1,00 km² | 5,96 km² |
| Şehir içi | CAPEX | yaklaşık 66937 TL/km² | 13281 TL/km² |
| Şehir içi | OPEX | boş | 2857 TL/km²/yıl |
| Kırsal | HPE P50 | 4,17 m | 1,95 m |
| Kırsal | HPE P95 | 14,29 m | 5,35 m |
| Kırsal | VPE P95 | 24,14 m | 4,72 m |
| Kırsal | Kullanılabilirlik | yaklaşık %98,9 | %61,03 |
| Kırsal | Alan | 1,01 km² | 209,00 km² |
| Kırsal | CAPEX | yaklaşık 471524 TL/km² | 1793 TL/km² |
| Kırsal | OPEX | boş | 590 TL/km²/yıl |
| Tünel | HPE P50 | 0,25 m | 0,80 m |
| Tünel | HPE P95 | 1,88 m | 2,72 m |
| Tünel | VPE P95 | 5,53 m | 2,04 m |
| Tünel | Kullanılabilirlik | yaklaşık %97,0 | %98,61 |
| Tünel | CAPEX | yaklaşık 545903 TL/km² | 31910 TL/km (güzergâh) |
| Tünel | OPEX | boş | 3234 TL/km/yıl |

Farkın nedenleri modelde değişenler: gerçek Ankara zemini ve binaları,
ITU-R P.526 kırınımı, gölgelenme, sekiz çekiliş, sahanın çevresinden ve
köşegeninden geçen bir sürüş turu, alanın kapsama taramasıyla ölçülmesi
ve maliyete montaj, enerji ve bakımın girmesi. Sunumdaki tablo "yalnız
ana donanım bileşenleri" ile ve 1 km² civarındaki bir senaryo alanıyla
hesaplanmış (dipnot 32). Kırsal CAPEX'in 471524'ten 1793'e inmesinin nedeni alanın
1,01 km²'den ölçülmüş 209 km²'ye çıkması.

Önerilen düzeltme: slayt 16'daki üç YERKON satırını sitenin tablosuyla
değiştirmek ve dipnot 28-32'yi bugünkü yöntemle yeniden yazmak. Sitenin
"Maliyet" sayfası her hücrenin dökümünü veriyor; dipnot oraya
gönderebilir.

### Kart fiyatları (slayt 15 ve form)

| Ürün | Sunum, 1 adet | Sunum, 100 adet | Şimdi, 1 adet | Şimdi, 100 adet | Şimdi, 1000 adet |
|---|---|---|---|---|---|
| Şehir içi (ve kırsal) yayın birimi | 1983,71 | 1366,07 | 1158,56 | 797,84 | 718,05 |
| Kırsal yayın birimi (E28-2G4M27S) | 1549,67 | 1082,68 | 1310,80 | 915,79 | 824,21 |
| Kritik bölge yayın birimi | 2241,42 | 1634,44 | 1662,69 | 1212,43 | 1091,19 |
| Yaya alıcısı | 3913,16 | 3117,74 | 2987,03 | 2379,86 | 2141,87 |
| Kara aracı alıcısı | 5202,69 | 4002,29 | 3748,56 | 2883,67 | 2595,30 |

Değişenler (`bom.toml`, ADR-0079): LAMBDA80-24S yerine E28-2G4M12S
(aynı SX1280), STM32G0B1 yerine yayın birimlerinde STM32G031. Kırsal
birim artık amplifikatörsüz kartın aynısı, çünkü amplifikatör Türkiye'de
hiçbir şey kazandırmıyor. Bazı fiyatlar distribütör sitelerine bu
ortamdan erişilemediği için arama sonuçlarından alındı; dosyada her
parçanın satıcısı ve bağlantısı var, siparişten önce doğrulanmalı.

Formdaki pilot bütçesi (10-15 yayın birimi, bir yaya ve bir araç alıcısı,
tek adet fiyatla) 24600-42700 TL. Aynı hesap bugünkü fiyatlarla
18321-31676 TL.

Formdaki tutarsızlıklar:

- "100 adet üretimde yayın birimlerinin referans ana bileşen maliyeti
  yaklaşık 1.100-1.650 TL" diyor; sunumun kendi tablosu 1082-1634 TL,
  slayt 5 ise "1000-1600". Üçü aynı olmalı. Bugünkü değer 798-1212 TL
  (100 adet), 718-1091 TL (1000 adet).
- Kırsal birimi E28-2G4M27S ile anlatıyor. Yukarıdaki nedenle
  E28-2G4M12S olmalı.

### Diğer uyumsuzluklar

| Nerede | Ne diyor | Ne olmalı |
|---|---|---|
| Slayt 3 | "istenilen yerde istenilen doğrulukta" | Modelin sonuçlarıyla desteklenmiyor. "Ortama göre metre sınıfında" gibi ölçülü bir ifade |
| Slayt 4 | Grup 2'nin "8 kilometreyi bulabilen menzili" | Haberleşme menzili ile konum için kullanılabilir menzil farklı: 10 m direkte 7,4 km ve 3,5 km |
| Slayt 4 | Karadeniz: "40 km (25 mil) içerideki Gelencik Havalimanı" | Kaynaklar "25 deniz mili" (yaklaşık 46 km) ya da "yaklaşık 32 km" diyor. Kaynağın kendi sayısı kullanılmalı |
| Slayt 4 | New Mexico: uçak "karıştırma aktivitesine maruz kalarak bir dağa çarptı" | NTSB karıştırmanın uçuş sırasında aktif olduğunu söylüyor, nedeni henüz belirlemedi. "Karıştırmanın aktif olduğu bir uçuşta" demek doğru |
| Slayt 4 | Grup 3 havalimanında uçağın inişini sağlayabilir | Bir yaklaşma pistten kilometrelerce önce ve yüzlerce metre yükseklikte başlıyor; yerdeki direklerden o açıdan düşey gözlenemiyor (ADR-0011). Anlamlı kullanım apron ve yer araçları |
| Slayt 5 | TDoA için birim başına yaklaşık 100000 TL | Kaynak yok. Ya kaynak eklenmeli ya da "hassas senkronizasyon altyapısı gerektirir" diye sayısız yazılmalı |
| Slayt 6 | DWM3000 "yaklaşık 10 cm" | Modelde tünelde P50 0,78 m. 10 cm tek mesafe ölçümünün sınıfı, konum hatası değil; sunum bunu zaten söylüyor, tablo da aynı şeyi göstermeli |
| Slayt 10 ve 16 | İngilizce kısaltmayla "karasal ..." | Site bu kısaltmayı kullanmıyor (ADR-0066); "karasal konumlandırma" yazılmalı |
| Slayt 18 | "IMU, odometri, harita kısıtı ve Kalman filtresi kullanılmamıştır" | Model mesafeleri tek tek işleyen sabit hızlı bir Kalman filtresi ve yükseklik için harita kısıtı kullanıyor (ADR-0088). IMU ve odometri hâlâ yok. Cümle buna göre düzeltilmeli |
| Form, "Yöntem" | "TWR-CDMA ve SDR tabanlı yöntemler araştırılacaktır" | Aşağıdaki SDR bölümüne bakın: SDR++ yalnız alıcı; bu araştırma zaman damgalı bir SDR ister |

## Model doğruluğu

Simülasyonun mantığı kod üzerinden okundu. Bulgular, önem sırasıyla.

### 1. Alıcı duyarlılığı doğrulanmamış ve her şeyi belirliyor

Model bağlantıyı alınan güç −125,9 dBm olana kadar kurulmuş sayıyor:
6 dB gürültü faktörü (varsayım) ve −20 dB demodülasyon eşiği.
`hardware.py` eşiği "SX1280 veri sayfası, SF10" diye veriyor; ama LoRa'da
−20 dB genellikle SF12'nin, SF10'un değeri yaklaşık −15 dB. Başka bir
değerlendirme veri sayfasında SF10 ve 1600 kHz için yaklaşık −114 dBm
olduğunu söylüyor. Veri sayfasına bu ortamdan erişilemedi (DigiKey,
Mouser, TME, HY-LINE, Semtech engelli), bu yüzden doğrulanamadı.

Ne kadar önemli olduğu (10 m dağıtım direği, düz zemin; satırlar kaba
okuma, tek çekiliş):

| Bağlantı eşiği | 5 m hassasiyet | Bağlantı | Şehir içi kullanılabilirlik | Şehir içi P95 | Kırsal kullanılabilirlik | Kırsal alan |
|---|---|---|---|---|---|---|
| −125,9 dBm (model) | 3,5 km | 7,4 km | %86,24 | 8,39 m | %74,48 | 246,25 km² |
| −120,9 dBm | 2,6 km | 5,6 km | %77,26 | 9,87 m | %67,88 | 197,25 km² |
| −114,0 dBm | 1,8 km | 3,7 km | %52,17 | 20,30 m | %58,03 | 70,75 km² |

Veri sayfasının duyarlılık tablosu modele girmeden yayımlanan sayılar
güvenilir değil. Bu, sunuma geçmeden önce çözülmesi gereken tek bulgu.

### 2. Menzil sayıları neyin sonucu

7,4 km radyo ufku değil: 10 m ve 1,5 m yükseklikte 4/3 dünya ile ufuk
yaklaşık 18 km. Modeldeki sınır yer yansıması: düzgün zeminde doğrudan
ve yansıyan ışın yaklaşık 0,5 km'den sonra birbirini söndürüyor ve kayıp
mesafenin dördüncü kuvvetiyle artıyor (ADR-0007). 3,5 km ise bu kaybın
üstüne mesafe hatasının Cramér-Rao sınırının (işlem kazancıyla) 5 m'yi
geçtiği yer; tabanı ölçülmüş 2,94 m. İkisi de model çıktısı.

### 3. Çok yollu yayılım ve görüş dışı hata modelde yok

Artık bir seçenek olarak var (ADR-0084): doğrudan ışın kesilince mesafeye
üstel dağılımlı pozitif bir yanlılık ekleniyor. Kapalı geliyor; açık ve
kapalı hâlin tam tablosu karşılaştırıldı.

Önceki durum: mesafe ölçümüne eklenen hatalar: gürültü (Cramér-Rao sınırı, saat, 2,94 m
taban), bir engel doğrudan ışını kestiğinde engelin üstünden dolaşmanın
getirdiği pozitif fazla yol, yayın biriminin sabit ölçüm hatası ve
paket kaybı. `rf.py` "çok yollu yayılım kanal modelinde eklenir" diyor
ama hiçbir yerde eklenmiyor. Sokak kanyonunda yansıyan yollardan ölçülen
mesafeler metrelerce uzun okunur. Şehir içi doğruluk büyük olasılıkla
iyimser. SX1280'in alınan güce bağlı yanlılığı (Semtech kalibrasyon
öneriyor) da modelde yok.

### 4. Kullanılabilirliğin tanımı gevşek

Filtre bir kez başladıktan sonra, içinde tek bir mesafe olan bir tur bile
"konum var" sayılıyor ve belirsizlik sınırı (500 m) hiç devreye girmiyor.
Kaba bir koşuda şehir içi konumların %19,9'u, kırsaldakilerin %30,1'i
dörtten az mesafeli turlardan geliyor. Dört mesafe şartıyla
kullanılabilirlik şehir içinde %86,24'ten %69,04'e, kırsalda %74,48'den
%52,10'a iniyor. İkisi de savunulabilir, ama sunumun dipnot 1'i
"tanımlanan doğruluğu karşılayan" diyor. Tanım seçilmeli ve sunumla aynı
olmalı. Ayrıca alan (dört birim, 5 m hassasiyet) ve kullanılabilirlik
(15 m ya da 30 m kabul, filtre) farklı çıtalarla ölçülüyor.

Karar: doğruluğa bağlı tanım. Bir tur, filtrenin yatay belirsizliği
5,78 m'yi (HPE P95 < 10 m hedefinden) geçmiyorsa konum sayılıyor
(ADR-0084).

### 4a. Simülatörün sekmeleri tablonun satırlarını koşturmuyordu

Sekmeler her satırı ölçüm hatası ve paket kaybı olmadan, farklı kabul
eşikleriyle, turda 12 yerine 8 birimle, kendi tohumlarıyla, farklı bir
sürüş turuyla ve tünelde çift yönlü yöntemle koşturuyordu. Var olan
sınama yalnız yerleşimi ve yolculuk süresini karşılaştırdığı için
yakalamadı. Satırın değerleri artık tek yerde; yeni sınama her satırı iki
yoldan koşturup hataları birebir karşılaştırıyor (ADR-0084).

### 5. Filtre aykırı ölçümleri elemiyor

Kalman filtresi gelen her mesafeyi alıyordu; yenilik testi (innovation
gating) yoktu. Artık bir seçenek (`estimator.gate_sigmas`), görüş dışı
yanlılıkla birlikte açılıyor (ADR-0084).

### 6. Doğru olanlar

- Türkiye güç sınırı: iki tavan, düşük olan (20 dBm ve 10 dBm/MHz).
- Mesafeler gerçek 3B uzaklıktan, yayın biriminin ölçüm hatası hattın
  yönündeki bileşeniyle, her alışveriş kendi anında ölçülüyor.
- Kırınım ITU-R P.526 (Bullington ve smooth earth), yansıma ile kırınım
  toplanmıyor, büyüğü alınıyor (ADR-0058).
- Kanal bütün saha için tek sayılıyor; bu, uzak alıcıların aynı anda
  konuşabildiği büyük bir ağ için kötümser, iki alıcılı satırlar için
  doğru.

### Frekans atlama seçeneği

Mesafe ölçüm alışverişleri EN 300 328'in frekans atlamalı tanımına
uyarsa güç yoğunluğu sınırı yerine 20 dBm'lik toplam sınır geçerli olur.
Modelde (10 m direk):

| Kural | Modül | e.i.r.p. | 5 m hassasiyet | Bağlantı |
|---|---|---|---|---|
| Bugünkü (yoğunluk sınırı) | E28-2G4M12S ya da 27S | 12,11 dBm | 3,5 km | 7,4 km |
| Frekans atlamalı | E28-2G4M12S | 15,70 dBm | 4,3 km | 9,1 km |
| Frekans atlamalı | E28-2G4M27S | 20,00 dBm | 5,5 km | 11,7 km |

Semtech'in yaklaşık 1 m'si zaten 40 kanalda atlayarak elde ediliyor; yani
atlama doğruluğu da artırıyor. Atlama düzeninin standarttaki tanıma uyup
uymadığı bir test laboratuvarına ya da BTK'ya sorulmalı.


## Mevzuat için doğrulanması gerekenler

- **UWB sabit dış mekân kurulumu.** Avrupa'daki genel UWB kuralları (ECC
  kararları ve ETSI EN 302 065) sabit dış mekân kurulumlarını genel
  kullanımın dışında tutuyor. Tünel içi bir kurulumun bu anlamda iç mekân
  sayılıp sayılmadığı ve BTK'nın Türkiye'deki düzenlemesi sorulmalı.
  Model bunun serbest olduğunu varsayıyor.
- **2,4 GHz güç yoğunluğu.** Model TS EN 300 328'i uyguluyor ve
  amplifikatörü bu yüzden etkisiz buluyor. Bir sertifika laboratuvarının
  bu okumayı doğrulaması iyi olur.

## YERKON'un maliyeti nasıl daha da düşer

Önce nereye gittiği (23 Eylül tablosu, `cost.price`):

| Kalem | Şehir içi (36 birim) | Kırsal (49 birim) | Tünel (9 birim) |
|---|---|---|---|
| Birimler | 25850 | 35184 | 9821 |
| Montaj ve yapı | 88200 | 225400 | 54000 |
| Şebekesiz enerji | 0 | 114170 | 0 |
| **Yatırım toplamı** | **114050** | **374754** | **63821** |
| Bakım (yıllık) | 12960 | 39690 | 3240 |
| Direk kirası (yıllık) | 0 | 58800 | 0 |
| Yenileme (yıllık) | 3231 | 18669 | 1228 |
| Merkezî sistem (yıllık) | 8640 | 11760 | 2160 |
| Enerji (yıllık) | 346 | 0 | 86 |
| **İşletme toplamı (yıllık)** | **25177** | **128919** | **6714** |

Sırayla, en büyük kaldıraçtan başlayarak:

1. **Montajı ucuzlatmak.** Şehirde birim başına 2450 TL montaj, kartın
   üç katından fazla. Bu değer bir sepetli araç ve ekip gününden türetilmiş bir
   varsayım. Belediyenin aydınlatma bakım turlarına eklemek (araç zaten
   sahada), bir ekibin günde taktığı birim sayısını artıran tak-çalıştır
   bir muhafaza ve kelepçe, ve koordinatın kurulum sırasında alıcıyla
   ölçülmesi (ayrı bir ölçüm ekibi yerine) bu kalemi doğrudan düşürür.
   Önce gerçek bir teklifle varsayım değiştirilmeli.
2. **Kırsalda şebekesiz enerjiden kaçınmak.** 49 birimin güneş paneli ve
   aküsü 114170 TL, ayrıca şebekesiz birimler yılda fazladan bakım
   ziyareti istiyor. Köy girişindeki trafo direkleri, aydınlatılmış
   kavşaklar, baz istasyonu sahaları ve AUS kabinleri gibi elektriği olan
   yerler bu kalemi sıfırlar. Yöneylem yerleşimi (ADR-0081) bu seçimi
   maliyetle birlikte yapıyor.
3. **Direk kirası.** Kırsal işletmenin en büyük kalemi (yılda 58800 TL).
   Değer bir varsayım (direk başına yılda 1200 TL). Dağıtım şirketiyle
   kamu yararı gerekçesiyle kirasız ya da toplu bir anlaşma, satırın
   işletme maliyetini yarıya yakın düşürür.
4. **Bakım ziyaretleri.** Yılda birim başına 0,2 ziyaret, ziyaret başına
   1800 TL. Uzaktan izleme (birim her yayınında kendi durumunu da
   bildirirse) ve bakımı var olan tur programlarına bağlamak bu kalemi
   düşürür.
5. **Daha az direkle aynı hizmet.** Yöneylem yerleşimi şehirde
   ızgaranın kullanılabilirliğini aynı tutup km² başına maliyeti beşte
   bir düşürüyor (ADR-0081, kaba okuma, dört çekiliş). Kırsalda aynı
   parayla alanı %27 büyütüyor.
6. **Kartın "diğer" kısmı.** Şehir içi yayın biriminde adı konmuş
   parçalar 8,70 USD, "diğer" (güç dönüştürme, koruma, bağlantı,
   muhafaza) 15,22 USD: kartın %64'ü. Birim bir AUS kabininin ya da
   aydınlatma direğinin içine girecekse kendi muhafazası ve şebeke
   adaptörü gerekmeyebilir; 12 V ya da 24 V'tan beslenen yalın bir kart
   bu kalemi küçültür. Bu kalem raporun toplamından geriye doğru
   hesaplandığı için önce gerçek bir tasarımla ölçülmeli.
7. **Hacim.** 1000 adet fiyatı 100 adetin %90'ı varsayılıyor (tek
   varsayım). Gerçek bir teklif alınmalı.

Elektroniğin kendisi zaten küçük pay. Kartı yarıya indirmek şehir içi
yatırımı yalnızca yaklaşık %11 düşürür; montajı yarıya indirmek %39.

## Kullanılabilirlik ve doğruluk nasıl artar

1. **Direkleri geometriye göre yerleştirmek.** Aynı sayıda direkle
   yöneylem yerleşimi şehirde P95'i 9,61 m'den 9,02 m'ye, kırsalda
   kullanılabilirliği %74,03'ten %76,44'e taşıyor (kaba okuma, dört
   çekiliş, ADR-0081).
2. **Yükseklik bilgisi eklemek (harita kısıtı ya da barometre).**
   Yapıldı (ADR-0088): yükseklik birimin haritasından, Copernicus'un
   yayımlanmış doğruluğuyla (2,43 m) alınıyor. VPE P95 onlarca metreden
   birkaç metreye indi; yatay hata ve kullanılabilirlik de iyileşti.
3. **IMU ve odometri.** Model yalnız mesafe ölçümleriyle çalışıyor.
   Mesafe gelmeyen kısa aralıkları IMU ve tekerlek hızıyla köprülemek
   kullanılabilirliği doğrudan artırır; kırsaldaki %65,85'in bir kısmı
   kısa kesintiler. Modele eklenmesi gereken bir sonraki şey bu.
4. **Frekans atlamalı ortalama.** Semtech'in yaklaşık 1 m'si 40 kanalda
   80 alışverişin ortalaması. Birkaç kanalda birkaç alışveriş bile
   çok yollu yayılımın bir kısmını ortalar, ama her biri hava süresi
   harcıyor. Doğruluk ile konum sıklığı arasındaki bu değiş tokuş
   sahada ölçülmeli ve modele girmeli.
5. **Kırsalda direk aralığı.** `rural-dense` seçeneği (2500 m arayla
   direk) kırsal satırı sıklaştırıyor; hangi aralığın maliyetine değdiği
   çözücüyle aranabilir (`yerkon solve`).
6. **Tünelde aralık.** Çözücünün bulduğu 120 m askı aralığı tünelin
   P50'sini belirgin biçimde düşürüyor (README, `tunnel-precise`).
7. **Hava süresi.** Tur başına sorulan direk sayısı ve SF, hem
   kullanılabilirliği hem konum sıklığını belirliyor. İmzayı her
   yanıttan çıkarmak (bulgu 7) konum sıklığını ikiye katlar. Daha düşük
   SF her adımda hava süresini yaklaşık yarıya indirir ama duyarlılık
   kaybettirir; bu değişim için veri sayfasının SF başına duyarlılık
   tablosu modele girmeli.
8. **Kanal doluluğunu ölçmek.** Şehirdeki paket kaybı %15 varsayılıyor.
   Pilot sahada 2,4 GHz doluluğu ölçülürse (aşağıda SDR) bu varsayım bir
   ölçüme döner.

## SDR++ ve SDRangel

Bu depo ikisini de kullanmıyor. Depoda herhangi bir SDR yazılımına tek
başvuru yok; yalnız sitede "TWR CDMA ve yazılım tanımlı radyo ile
denenecek" diye bir plan cümlesi var.

İki sitenin kendisine (sdrpp.org, sdrangel.org) bu çalışma ortamının ağ
vekil sunucusu erişim vermedi. Aşağıdakiler arama sonuçlarından ve
projelerin GitHub belgelerinden:

- **SDR++**: yalnız alıcı. Windows, macOS, Linux ve Android'de çalışıyor,
  GPL lisanslı, çok VFO'lu ve eklentili, donanımı kendi modülleri ve
  SoapySDR üzerinden destekliyor.
- **SDRangel**: alıcı ve verici. Airspy, BladeRF, HackRF, LimeSDR,
  PlutoSDR, RTL-SDR, SDRplay ve FunCube destekleniyor. **ChirpChat**
  adında, topluluğun tersine mühendisliğine dayanan LoRa uyumlu bir
  demodülatör ve modülatör eklentisi var. Meshtastic demodülatörü de
  var. GPL lisanslı.

Nerede işe yarar:

1. **Pilot sahada 2,4 GHz doluluk ölçümü.** Bir HackRF, PlutoSDR ya da
   LimeSDR ile SDR++ ya da SDRangel'in spektrum ve şelale ekranı
   bandın ne kadar dolu olduğunu gösterir. Bu, modeldeki %15'lik paket
   kaybı varsayımını ölçüme çevirmenin en ucuz yolu. RTL-SDR bu işe
   yaramaz: yaklaşık 1,7 GHz'in üstünü göremez.
2. **Yayın birimini doğrulamak.** SDRangel'in ChirpChat demodülatörü
   birimlerin çerçevelerini, SF ve bant genişliğini, ne sıklıkla
   yayın yaptığını gösterebilir. Güç ölçümü için değil: bir SDR kalibre
   edilmiş bir güç ölçer değildir, TS EN 300 328 uygunluğu için
   laboratuvar ölçümü gerekir.
3. **GNSS karıştırma izleme.** L1 (1575,42 MHz) RTL-SDR'nin aralığında.
   Ucuz bir RTL-SDR ile L1'deki gürültü tabanını izleyen bir istasyon,
   sunumdaki GNSS bütünlük haritasının ilk, düşük maliyetli adımı olur.
   SDR++ bunu gözle gösterir; sürekli kayıt için bir betik ya da
   SDRangel'in uzaktan kontrolü gerekir. Aldatma tespiti için ise bir
   GNSS alıcısının kendi çıktısı ya da GNSS-SDR gibi ayrı bir yazılım
   gerekir.
4. **TWR-CDMA araştırması.** İki yollu mesafe ölçümü nanosaniye
   mertebesinde zaman damgası ister. SDR++ yalnız alıcı olduğu için bu
   işi yapamaz. SDRangel verici de olsa, bir bilgisayarın USB üzerinden
   yaptığı zamanlama milisaniye mertebesinde ve oynak. Bu araştırma,
   örnek düzeyinde zaman damgası ve zamanlanmış gönderim sunan bir SDR
   (ör. UHD ile bir USRP) ve GNU Radio gibi bir çerçeveyle yapılır.
5. **UWB için değil.** DWM3000'in kanalları 6,5 ve 8 GHz'de, 500 MHz
   genişliğinde. Yukarıdaki SDR'lerin hiçbiri bu banda ve bu genişliğe
   ulaşmıyor.

Ürünün içinde yeri yok: her birime bir SDR koymak kartı onlarca kat
pahalılaştırır. İkisi de laboratuvar ve saha aracı. GPL lisansları araç
olarak kullanmaya engel değil; YERKON'un kendi yazılımına gömülürse
lisans yükümlülükleri doğar.

Depoya eklenen: `yerkon calibrate` artık SDR++'ın temel bant WAV'ını ve
SDRangel'in `.sdriq` dosyasını okuyor ve `site.urban_packet_loss` (ya da
`ranging.packet_loss`) için ölçülmüş bir değer yazıyor: 31,8 ms'lik bir
alışverişin kanalda başka bir yayına denk gelme olasılığı. İki biçim de
programların kaynak kodundan okundu (ADR-0083). Programların kendisi
simülasyonun içinde çalışmıyor ve çalışması bir şey kazandırmıyor;
kayıtları kazandırıyor.

## Öncelikli düzeltme listesi

1. Slayt 16'daki YERKON satırlarını sitenin tablosuyla değiştirmek,
   dipnot 28-32'yi yeniden yazmak.
2. Slayt 15'in ve formun fiyatlarını `bom.toml` ile eşitlemek; kırsal
   kartı E28-2G4M12S yapmak; formun "1.100-1.650" aralığını düzeltmek.
3. "8-10 km", "±1 m" ve havalimanı, uçak iddialarını modelle ve
   kaynaklarla uyumlu hâle getirmek.
4. Özete bir zaman çizelgesi (iş paketleri ve aylar) ve güncel sonuçları
   eklemek.
5. Form yanıtlarını Times New Roman'a çevirmek, web sitesi satırını
   doldurmak, imzaları ve ek belgeleri hazırlamak.
6. Sayfa sınırını UDHAM'a sormak ya da sunumu kısaltmak.
7. TWR hava süresini ve imza maliyetini sayıyla anlatmak; imzanın seyrek
   bir yayına taşınacağını yazmak.
8. UWB sabit kurulumu için BTK'ya sormak.

## Kaynaklar

- [Semtech AN1200.29, SX1280 ile mesafe ölçümüne giriş](https://www.scribd.com/document/750381548/AN1200-29-Introduction-to-Ranging-SX1280-V1-0)
- [Semtech, gelişmiş mesafe ölçümünün kuramı (AN1200.89)](https://www.semtech.com/uploads/technology/LoRa/theory-and-principle-of-advanced-ranging.pdf)
- [AOPA: GPS karıştırması King Air dağa çarptığında aktifti](https://www.aopa.org/news-and-media/all-news/2026/june/18/gps-jamming-active-when-king-air-struck-mountain)
- [KOB 4: NTSB ön raporu](https://www.kob.com/new-mexico/ntsb-gps-jamming-was-active-when-air-ambulance-crew-flew-into-capitan-mountains/)
- [Sophos: Karadeniz'de toplu aldatma şüphesi](https://news.sophos.com/en-us/2017/09/26/suspected-mass-spoofing-of-ships-gps-in-the-black-sea/)
- [The Maritime Executive: Karadeniz olayı](https://maritime-executive.com/editorials/mass-gps-spoofing-attack-in-black-sea)
- [SDRangel ChirpChat demodülatörü](https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/demodchirpchat/readme.md)
- [SDRangel ChirpChat modülatörü](https://github.com/f4exb/sdrangel/blob/master/plugins/channeltx/modchirpchat/readme.md)
- [SDR++ tanıtımı (LinuxLinks)](https://www.linuxlinks.com/sdr-community-edition-advanced-software-defined-radio/)
- [Microchip ATECC608B](https://www.microchip.com/en-us/product/atecc608b)
