# Alıcı ve sensör füzyonu

YERKON raporu çıplak bir menzil ölçüm cihazı tarif etmiyor. IMU, tekerlek
odometrisi ve harita kısıtlarını Kalman filtresiyle birleştiren, ölçüm
kesintilerinde konumu sürdüren bir alıcı tarif ediyor ve parçaları isim
isim veriyor: yaya ve araç alıcılarında BNO085, araç alıcısında CAN
üzerinden tekerlek hızı ve direksiyon açısı, IoT alıcısında tekerlek
enkoderleri.

Bu yüzden tablodaki doğruluk değerleri filtrelenmiş sonuçtan geliyor.
Radyo-tek sonuç da hesaplanıyor ve JSON çıktısında duruyor, ama o raporun
önermediği bir sistemi anlatır.

Kod: `yerkon/receiver.py` (alıcılar), `yerkon/fusion.py` (filtre),
`yerkon/path.py` (zaman-serili yörüngeler).

## Filtre

Durum vektörü: `[x, y, z, vx, vy, vz, pusula_sapması]`, yani konum, hız ve
IMU'nun pusula sapması.

**Yayılım IMU ile yapılır.** Filtre sabit hız varsaymaz; IMU'nun bildirdiği
ivmeyi entegre eder. Bu kozmetik bir ayrım değil: 50 km/h'de bir virajı
dönen araç yanal olarak yaklaşık 0,6 m/s² çeker, bu da tüketici sınıfı bir
IMU'nun gürültüsünün birkaç katıdır. Sabit hız modeli her virajda geride
kalır, menzil yenilikleri (innovation) büyür, aykırı değer kapısı onları
reddeder ve filtre kör kalır. İlk denemede tam olarak bu oldu: yatay hata
116 m'ye çıktı ve menzil ölçümlerinin %81'i reddedildi.

**Dört ölçüm türü durumu günceller:** anchor'lara menziller (5 Hz),
tekerlek hızı (10 Hz), IMU pusulası (10 Hz) ve harita yüksekliği (10 Hz).

**Aykırı değer kapısı** 4σ. Gerçek alıcılar mevcut kestirimle ciddi çelişen
menzilleri reddeder; kapı olmadan tek bir kaba NLOS dönüşü filtreyi
saniyelerce saptırır.

## Sonucu asıl belirleyen: hangi hata ortalamayla yok olur

Filtrenin kendisinden çok, hata modelinin nasıl kurulduğu belirleyici. Bunu
yanlış kurmak, gerçekçi görünen ama uydurma bir sonuç üretmenin en kolay
yolu.

**Menzil hatasının tamamı ortalamayla yok olmaz.** 5 Hz'de çalışan bir
filtre bir dakikada aynı anchor'a yüzlerce menzil ölçümü görür. Her hata
bağımsız gürültü olsaydı ortalama sıfıra giderdi ve metre sınıfı bir
radyodan santimetre raporlanırdı. Gerçek menzil hatasının bir kısmı sabit
kurulum ofsetidir (anten gecikmesi, montaj, yerel çok yolluluk geometrisi);
her ölçümde aynı şekilde tekrar eder ve ortalanamaz. Robinson'un altı
noktası ikisini ayıramadığı için oran açık bir parametre:
`bias_variance_fraction`, varsayılan 0,5.

**NLOS de beyaz değil.** Alıcı ile bir anchor arasındaki engel, geometri
sürdüğü sürece sürer. 8 saniyelik korelasyon süresiyle modellendi, her
epoch yeniden çekilmiyor.

**Harita sabit biçimde yanlıştır, gürültülü biçimde değil.** Bir noktadaki
ölçülmüş yükseklik bir saniyeden diğerine değişmez. Kısıtı her adımda
bağımsız gürültü olarak vermek, filtrenin yüzlerce okumayı ortalayıp dikey
hatayı haritanın kendi doğruluğunun çok altına indirmesine yol açar; yarım
metrelik bir haritadan 14 cm yükseklik iddia edilmesinin yolu budur. Harita
hatası koşu başına bir kez çekilip sabit tutuluyor.

**IMU pusula hatası da yavaş bir hata.** 3,5 derecelik değer bir saniyede
ortalanıp yok olmaz. Koşu başına sapma ve daha küçük beyaz kısım olarak
ayrıldı, ve **sapma filtrede durum olarak kestiriliyor**. Kestirilmediğinde
tekrarlanan pusula güncellemeleri filtreyi yanlış bir yöne ikna ediyor ve
yardım fayda yerine zarar veriyordu: kırsal koridorda yatay P95, sapma
durumu eklenmeden önce 22 m'den 35 m'ye çıkmıştı.

**Odometri ölçek hatası bir sapmadır.** Nominal yarıçapının %2 altındaki
bir lastik tüm yolculuk boyunca %2 kısa bildirir.

## Yardımcı sensörler ne katıyor

Aynı senaryo, yardımcılar tek tek kapatılarak (HPE P50/P95, VPE P50/P95, m):

| Yapılandırma | Şehir içi HPE | Şehir içi VPE | Kırsal HPE | Kırsal VPE | Tünel HPE | Tünel VPE |
|---|---|---|---|---|---|---|
| Tam | 2,19 / 4,35 | 0,26 / 1,12 | 5,90 / 21,65 | 0,33 / 0,62 | 0,15 / 0,60 | 0,32 / 0,68 |
| Haritasız | 2,19 / 4,52 | 4,08 / 12,70 | 4,83 / 19,69 | 14,04 / 31,03 | 0,21 / 0,87 | 0,84 / 3,22 |
| Odometresiz | 1,76 / 3,95 | 0,25 / 1,11 | 6,52 / 25,54 | 0,34 / 0,63 | 0,17 / 0,59 | 0,32 / 0,72 |
| Pusulasız | 2,21 / 4,74 | 0,25 / 1,11 | 6,93 / 21,97 | 0,34 / 0,63 | 0,17 / 0,58 | 0,31 / 0,72 |
| Sadece menzil (filtreli) | 1,71 / 3,95 | 4,50 / 13,28 | 6,08 / 19,82 | 12,00 / 31,91 | 0,23 / **295,77** | 0,98 / **422,59** |

Üç bulgu:

**Dikey ekseni harita kurtarıyor, radyo değil.** Harita kısıtı kaldırılınca
dikey hata her senaryoda on kattan fazla artıyor. Karasal geometri yüksekliği
çözemiyor; çözen şey aracın ölçülmüş bir yüzeyin üstünde olduğunun
bilinmesi.

**Tünelde de esas katkı dikeyde.** Odometri, pusula ve harita
kapatıldığında yatay P95 1,28 m'den 1,71 m'ye, dikey P95 ise 0,70 m'den
5,69 m'ye çıkıyor. Burada daha önce "yardım olmadan filtre ıraksıyor,
yatay P95 295 m'ye çıkıyor" yazmıştım. O bir artefaktmış ve geri alındı,
gerekçesi [WAVEFORM.md](WAVEFORM.md#geri-alınan-bir-bulgu) içinde.

**Açık alanda odometri yatayda küçük bir zarar veriyor.** Şehir içinde
odometresiz HPE P50 1,76 m, odometriyle 1,64 m. Sebebi %2'lik ölçek
sapması: 13,9 m/s hızda 0,28 m/s'lik bir hız sapması demek ve şehir içinde
radyo geometrisi zaten iyi olduğu için odometri bilgi eklemek yerine sapma
ekliyor. Kırsalda yanal harita kısıtı geometri boşluğunu zaten kapattığı
için odometri orada da bilgi eklemiyor: P50 odometresiz 2,10 m,
odometriyle 2,55 m. Kısıt eklenmeden önce tersiydi, yani bir yardımcı
sensörün faydası kapattığı boşluk başka bir şeyle kapanınca kayboluyor.

Aynı sebeple harita kısıtı yatayda küçük bir bedel doğuruyor: yanlış
sabitlenen bir yükseklik, menzilleri açıklamak için x-y'yi bir miktar
kaydırıyor. Dikeyde 12,70 → 1,12 m kazanç için yatayda 4,52 → 4,35 m'lik
nötr-hafif iyileşme; kırsalda ise 19,69 → 21,65 m'lik kayıp.

## Kalıcı sapma oranının etkisi

`bias_variance_fraction` = menzil hatası varyansının ne kadarının sabit
kurulum ofseti olduğu. 0 = hepsi ortalanabilir gürültü, 1 = hiçbiri.

| Oran | Şehir içi HPE P50/P95 | Kırsal HPE P50/P95 | Tünel HPE P50/P95 |
|---|---|---|---|
| 0,00 | 1,15 / 3,45 | 2,02 / 7,25 | 0,15 / 0,55 |
| 0,25 | 2,05 / 4,21 | 5,02 / 14,18 | 0,15 / 0,59 |
| **0,50 (kullanılan)** | **2,20 / 4,37** | **5,97 / 21,88** | **0,15 / 0,60** |
| 0,75 | 2,34 / 4,58 | 6,96 / 28,11 | 0,16 / 0,61 |
| 1,00 | 2,52 / 5,08 | 7,92 / 26,26 | 0,17 / 0,60 |

Şehir içinde hata 0'dan 1'e giderken iki katına, kırsalda dört katına
çıkıyor. Bu, çalışmadaki en etkili modelleme kararlarından biri ve
ölçülmüş bir dayanağı yok: Robinson'un altı noktası sabit ofset ile
gürültüyü ayıramıyor. 0,5 varsayılan olarak seçildi ve etkisi burada
gösteriliyor.

Tünel neredeyse etkilenmiyor, çünkü UWB'nin menzil hatası zaten 0,35 m.

## Harita doğruluğu doğrudan dikey sonuca geçiyor

Şehir içi senaryosu, harita yükseklik belirsizliği değiştirilerek:

| Harita σ | VPE P50 | VPE P95 | HPE P50 |
|---|---|---|---|
| 0,2 m | 0,17 m | 0,41 m | 1,64 m |
| 0,5 m (kullanılan) | **0,44 m** | **1,00 m** | **1,64 m** |
| 1,0 m | 0,87 m | 1,91 m | 1,65 m |
| 2,0 m | 1,63 m | 3,42 m | 1,66 m |

VPE harita σ'sıyla doğrusal ölçekleniyor ve HPE hiç değişmiyor. Bu,
tablodaki VPE sütununun ne ölçtüğünü açıkça söylüyor: haritayı, radyoyu
değil. Rapora bu satır yazılırken belirtilmeli.

## Alıcı tipi

Tünel senaryosu, raporun üç alıcısıyla:

| Alıcı | HPE P50/P95 | VPE P50/P95 |
|---|---|---|
| Kara aracı (IMU + odometri + harita 0,5 m) | 0,15 / 0,60 | 0,32 / 0,68 |
| Yaya (IMU, odometri yok, harita 1,5 m) | 0,20 / 0,75 | 0,99 / 2,73 |
| IoT robot (enkoder + IMU, harita 0,3 m) | 0,14 / 0,57 | 0,20 / 0,41 |

Yaya alıcısı en kötüsü: tekerlek yok, ve bir yaya ölçülmüş bir taşıt
yolunda olmadığı için harita kısıtı da zayıf. IoT robotu en iyisi: bilinen
bir zeminde bilinen bir tekerlekle çalışıyor.

Tablo satırları kara aracı alıcısıyla üretildi; üç senaryo da karayolu
senaryosu ve karşılaştırılabilirlik için tek alıcı kullanmak gerekiyordu.

## Yakınsama ve süreklilik

Her filtrelenmiş koşunun ilk 12 saniyesi atılıyor: alıcı ilk tek-atım
fix'inden yakınsarken geçen süre, bir dakikadır çalışan bir alıcının
durumunu anlatmaz. Yakınsama süresi ayrı raporlanıyor
(`median_convergence_s`) ve dört senaryoda da 0 s çıkıyor, yani filtre ilk
fix'ten sonraki 5 saniyelik pencerede zaten 10 m'nin altında kalıyor.

Kullanılabilirlik sütunu hâlâ **radyo seviyesindeki** fix üretme oranını
gösteriyor. Filtrelenmiş alıcı, menzil ölçümü gelmediği anlarda da IMU ve
odometriyle konum üretmeye devam eder; raporun "konum sürekliliği korunmaya
çalışılacaktır" dediği davranış budur. Yani gerçekte sunulan süreklilik bu
sütundan yüksek, doğruluğu ise kesinti boyunca düşer.

## Hâlâ modellenmeyenler

- **Manyetik bozulma.** Tünelde ve şehir kanyonunda pusula, demir ve akım
  kaynaklı bozulmadan 3,5 derecelik spesifikasyonun ötesinde etkilenir.
- **Tekerlek kayması.** Frenleme ve viraj sırasında odometri gerçek yolu
  fazla/eksik sayar; sabit ölçek sapması bunu kapsamıyor.
- **Harita eşleme.** Yalnızca yükseklik kısıtı uygulandı. Yol ekseni
  boyunca yanal kısıt (aracın şeritte olduğu bilgisi) uygulanmadı; bu
  uygulanırsa yatay hata da düşer.
- **Kanal doluluğu ve çakışma.** Paket kaybı sabit olasılık, trafik yüküne
  bağlı değil.
- **Menzile bağlı hata büyümesi.** Uzak bağlantılar kısa bağlantılarla aynı
  hata dağılımını kullanıyor.
