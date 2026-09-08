# Üç senaryonun yapılandırması nasıl seçildi

Tablodaki dört satırın her biri bir yapılandırmanın çıktısı: menzil bant
genişliği, düğüm aralığı, radyo. Bu belge o üç seçimin nasıl yapıldığını
ve hangilerinin bir ödünleşim, hangilerinin bedava olduğunu anlatıyor.

Yöntem her senaryoda aynı: yapılandırmalar süpürüldü, her biri tam
senaryoyla (füzyonlu, 16 koşu) çalıştırıldı, sonuçlar maliyet ve HPE P50
üzerinde Pareto'ya göre elendi. Bir yapılandırma ancak kendisinden hem
ucuz hem doğru bir başkası yoksa Pareto'da kalıyor.

Ayırt edilmesi gereken iki durum var:

- **Bedava seçim.** Yeni yapılandırma mevcudunu her iki eksende birden
  yeniyor. Ödünleşim yok, sadece daha önce yanlış noktada durulmuş.
- **Gerçek ödünleşim.** Ucuzlamak doğruluğa mal oluyor. Burada karar
  gerekiyor, ve gerekçe yazılmalı.

---

## Şehir içi: iki eksende birden kazanç

**Seçilen: 406 kHz menzil bandı, 175 m ızgara aralığı.**

### Bant genişliği

| Bant | HPE P50 | Not |
|---|---|---|
| 203 kHz | 3,52 m | zamanlama çözünürlüğü yetersiz |
| **406 kHz** | **1,93 m** | Semtech'in ranging modunun ayarı |
| 812 kHz | 3,44 m | çok yolluluk seçme hataları başlıyor |
| 1625 kHz | 6,00 m | %28 hata >10 m |

U biçimli, çünkü iki etki ters yönde çalışıyor. Geniş bant zamanlama
çözünürlüğünü artırıyor, ama çok yolluluğu ayrı tepelere ayırdığı için
tepe dedektörünün yanlış yolu seçmesini de mümkün kılıyor. Ayrıntısı
[WAVEFORM.md](WAVEFORM.md).

Sonuç raporun lehine: 406 kHz zaten parçanın ranging varsayılanı, yani
şehir içi için örtük tercih doğruymuş.

### Izgara aralığı

| Aralık | Düğüm | TL/km² | HPE P50 | En az anchor |
|---|---|---|---|---|
| 125 m | 81 | 110.652 | 2,14 m | 8 |
| 150 m (eski) | 49 | 66.937 | 1,93 m | 8 |
| **175 m** | **36** | **49.179** | **1,60 m** | 5 |
| 200 m | 36 | 49.179 | 1,67 m | 8 |
| 225 m | 25 | 34.152 | 1,93 m | 4 |
| 250 m | 25 | 34.152 | 1,99 m | 4 |

Bu **bedava bir seçim**: 175 m, 150 m'yi hem %27 ucuzlukta hem doğrulukta
yeniyor.

Sebebi geometri. Bir fix en fazla sekiz anchor kullanıyor. Alıcı sekizden
fazlasını duyduğu anda fazlalar hiç kullanılmıyor, ve ızgarayı
sıklaştırmak yalnızca en yakın sekizinin yaydığı tabanı daraltıyor. Daha
çok donanımla daha kötü geometri. 150 m'de alıcı 20 anchor duyuyor ama
8'ini kullanıyor; 175 m'de 15 duyuyor, yine 8 kullanıyor, ve o sekizi daha
geniş yayılmış oluyor.

225 m maliyeti bir kez daha yarıya indirip 150 m'nin doğruluğunu veriyor,
ama yolun en kötü noktasında sadece dört anchor kalıyor — 3B fix için
asgari sayı, kaybolan bir pakete tolerans yok. 175 m beşte kalıyor. Bu
yüzden 175 m seçildi; 225 m isteyen için tablo yukarıda.

---

## Kırsal: bant bedava, aralık ödünleşim

**Seçilen: 812 kHz menzil bandı, 500 m levha aralığı.**

### Bant genişliği: bedava

| Bant | HPE P50 | TL/km² |
|---|---|---|
| 406 kHz | 13,83 m | 200.854 |
| **812 kHz** | **8,68 m** | 200.854 |
| 1625 kHz | 14,06 m | 200.854 |

Maliyet değişmiyor, hata %37 düşüyor. Optimum şehir içindekinden bir
katlama geniş, çünkü koridor daha açık: engellenen link oranı %35 değil
%15, dolayısıyla çok yolluluk seçme hatası daha az ve zamanlama
çözünürlüğü kazancı daha uzun sürüyor.

**Bu bir konfigürasyon değişikliği, donanım değişikliği değil.**

### Levha aralığı: gerçek ödünleşim

| Levha aralığı | Düğüm | TL/km² | HPE P50 | HPE P95 | VPE P95 |
|---|---|---|---|---|---|
| **500 m** | 187 | 200.854 | **8,68 m** | **36,73 m** | **0,98 m** |
| 1000 m | 103 | 110.631 | 9,74 m | 58,38 m | 1,48 m |
| 1500 m | 75 | 80.557 | 14,33 m | 64,58 m | 1,27 m |

Burada bedava bir seçim yok: her ucuzlama doğruluğa mal oluyor. 1000 m
maliyeti %45 düşürüyor ve P50'yi sadece %12 bozuyor — cazip görünüyor.
Ama P95 36,73'ten 58,38 m'ye çıkıyor, yani kötü durum yarı yarıya
kötüleşiyor, ve dikey hata %50 artıyor.

500 m'de kalındı çünkü kırsal satırın zaten en zayıf tarafı kuyruğu
(P95 36,73 m, P50'nin dört katı) ve onu daha da uzatmak satırı
kullanılamaz hale getirir. Bütçe baskısı varsa doğru soru levha aralığı
değil, koridorun tamamının mı yoksa bir kısmının mı kapsanacağıdır.

---

## Tünel: ucuzlatmak mümkün ama alınmadı

**Seçilen: 60 m düğüm aralığı (değişmedi).**

| Aralık | Düğüm | TL/km² | HPE P50 | HPE P95 | VPE P95 | En az anchor |
|---|---|---|---|---|---|---|
| 40 m | 1250 | 2.043.050 | 0,38 m | 1,04 m | 1,04 m | 7 |
| 50 m | 1000 | 1.634.440 | 0,39 m | 1,00 m | 1,26 m | 6 |
| **60 m** | 834 | **1.363.123** | **0,45 m** | 1,51 m | **0,69 m** | 5 |
| 70 m | 715 | 1.168.625 | 0,66 m | 1,58 m | 0,87 m | 4 |
| 75 m | 667 | 1.090.171 | 0,51 m | 1,21 m | 1,75 m | 4 |

Pareto burada tamamen ödünleşim: hiçbir yapılandırma bir diğerini iki
eksende birden yenmiyor.

75 m %20 ucuz ve yatayda 60 m'den kötü değil, ama iki sebeple alınmadı.
Dikey hata 0,69'dan 1,75 m'ye çıkıyor, ve tünel satırının varlık sebebi
GNSS'in hiç olmadığı yerde yükseklik verebilmek. İkincisi, 75 m tam olarak
`aralık ≤ menzil/2` sınırında (menzil 150 m), yani yolun en kötü noktasında
dört anchor kalıyor. Tünelde paket kaybı %3 ve kullanılabilirlik zaten
%99,3 — beş ölçümden ikisini kaybetmek fix'i bitiriyor. Dört ölçümden
birini kaybetmek de bitirir. Marj bırakmaya değer.

Ters yönde, 50 m aralık P50'yi 0,45'ten 0,39 m'ye indiriyor ama maliyeti
%20 artırıyor ve dikey hatayı kötüleştiriyor. Tünel zaten km² başına en
pahalı satır; oraya para koymanın karşılığı 6 cm.

Not: tünel sayıları koşular arası ±%15 oynuyor ([WAVEFORM.md](WAVEFORM.md),
tekrarlanabilirlik bölümü). Yukarıdaki tabloda 60 m ile 75 m arasındaki
yatay fark bu belirsizliğin içinde; dikey fark değil, ve karar ona
dayanıyor.

---

## Özet

| Senaryo | Değişen | Kazanç | Türü |
|---|---|---|---|
| Şehir içi | Izgara 150 → 175 m | %27 ucuz, %17 daha doğru | bedava |
| Şehir içi | Bant 406 kHz | (zaten doğruymuş) | doğrulama |
| Kırsal | Bant 406 → 812 kHz | %37 daha doğru, maliyet aynı | bedava |
| Kırsal | Levha aralığı 500 m | değişmedi | ödünleşim reddedildi |
| Tünel | Aralık 60 m | değişmedi | ödünleşim reddedildi |

İki bedava kazanç var ve ikisi de konfigürasyon: bir ızgara aralığı ve bir
radyo ayarı. Ek donanım, ek düğüm, yeni parça yok.

Bu seçimlerin dayandığı varsayımlar — engellenen link oranları (%35, %15),
NLOS kanalının sertliği, şehir içi yol kaybı üsteli — bu projenin
seçimleri. Optimum bant genişliği ve aralık bu sayılara bağlı, o yüzden
saha ölçümü geldiğinde süpürme tekrar çalıştırılmalı.
