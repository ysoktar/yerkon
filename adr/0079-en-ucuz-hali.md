# ADR-0079: her parça ve her varsayım, en ucuz hâliyle

## Durum

Kabul edildi.

## Bağlam

Tablonun maliyet sütunları iki şeye dayanıyordu: raporun 14. sayfasındaki
ürün toplamları ve ayarlar dosyasındaki işletme varsayımları. İkisinin de
dökümü yoktu. Rapor her ürün için iki toplam veriyor (1 adet ve 100
adette), parça fiyatı vermiyor. Varsayımların çoğu "bu proje" diyordu.

İstenen şey şuydu: her parçayı ve her varsayımı göstermek, internette
daha ucuzunu aramak, 100 ve 1000 adede bakmak ve tabloyu en ucuz hâline
getirmek.

## Karar

**Malzeme listesi parça parça yazıldı (`bom.toml`, `bom.py`).** Her ana
parça bulunduğu satıcı fiyatıyla duruyor. Raporun toplamından bu parçalar
çıkarılınca kalan tutar "diğer" satırına yazılıyor (güç dönüşümü, koruma,
bağlantı, kutu). Üç yayın biriminde de bu kalan 1 adette 14,9 ile 15,5
USD arasında çıkıyor. Kart aynı kart olduğuna göre öyle olması gerekir;
dökümün raporla tutarlı olduğunu gösteren kontrol de bu. Bir sınama bu
kalanların birbirinden bir dolardan fazla ayrılmamasını istiyor.

**Aynı işi daha ucuza yapan parçalar.**

| önce | sonra | 1 adet |
|---|---|---|
| RF Solutions LAMBDA80-24S (SX1280, 12,5 dBm) | EBYTE E28-2G4M12S (SX1280, 12,5 dBm) | 16,49 → 4,39 USD |
| Qorvo DWM3000, DigiKey | aynı parça, LCSC | 23,62 → 16,60 USD |
| STM32G0B1MET6 (512 KB) | STM32G031K8T6 (64 KB) | 6,86 → 1,93 USD |
| Newhaven 2,8 inç ekran (araç alıcısı) | 2,8 inç ILI9341 modülü | 21,80 → 10,90 USD |

Sipariş notu: EBYTE'ın ilanları bu modüldeki yongayı bazen SX1280,
bazen SX1281 diye adlandırıyor ve E28-2G4M12SX'i SX1281 ile satıyor.
SX1281'in ölçüm motorunu taşıyıp taşımadığı buradan kesinleştirilemedi:
Semtech'in veri sayfası açılamadı ve özetleri birbirini tutmuyor. Sipariş
modül adına değil yongaya göre verilmeli ve ölçüm özelliği satıcıya
doğrulatılmalı.

**Kırsal birimin yükselteci kalktı.** Türkiye'nin 2,4 GHz kuralı (TS EN
300 328) 1,6 MHz'lik ölçüm bant genişliğinde yayın gücünü yaklaşık
12,1 dBm ile sınırlıyor. Yükselteçsiz modül bu sınıra zaten ulaşıyor,
dolayısıyla E28-2G4M27S'nin 27 dBm'i burada kullanılamıyor. Kırsal satır
yükselteçsiz modülle yeniden koşuldu ve sonuç hane hane aynı çıktı: aynı
kullanılabilirlik, aynı P50 ve P95, aynı alan, aynı 3269 sabitleme. Artık
şehir içi ve kırsal birim aynı kart. Yükselteçli birim katalogda kalıyor,
çünkü ABD kuralı altında gücü kullanılabiliyor ve tasarım aracı onu
seçebiliyor.

**Tablo 1000 adetlik fiyatla hesaplanıyor.** İşletme modeli merkezî
sistemi zaten bin birime bölüyor. Donanımı 100 adetten fiyatlayıp ağı bin
birimlik gibi işletmek, bir satırda iki ağ büyüklüğü demekti. 100 adetlik
fiyat raporun kendi 1'den 100'e indirim oranıyla hesaplanıyor. 1000 adette
hiçbir satıcı kademesi okunamadığı için 100 adetlik fiyatın %90'ı
varsayıldı; listedeki tek varsayım bu.

Birim fiyatlar (1000 adette): şehir içi 1366,07 → 718,05 TL, kırsal
1082,68 → 718,05 TL, tünel 1634,44 → 1091,19 TL (doğrulamadan sonraki
değerler).

**Varsayımlar dayanaklarından yeniden kuruldu.**

- *Tüketim* yılda 35 kWh idi, yani sürekli 4 W. Bir SX1280 kartı dinlerken
  birkaç mA çekiyor; dönüştürücü kaybıyla birlikte 0,34 W bir üst sınır.
  Yeni değer yılda 3 kWh.
- *Veri hattı* kaldırıldı; aşağıda, "Doğrulamada düzeltilenler".
- *Güneş seti* 9500 TL idi ve 4 W'lık bir yüke göre boyutlanmıştı. 10 W
  panel (518,72 TL), 12 V 7 Ah akü (524,40 TL), denetleyici, tutucu ve
  kablo: 2330 TL.
- *Bakım* iki yılda bir, takvime bağlıydı. Merkezî sistem her birimin
  durumunu zaten izlediği için ekip arıza olduğunda gidiyor: beş yılda bir.
  Şebeke dışı ek ziyaret dört yılda bir, akü değişimi için.
- *Aydınlatma direğine montaj* 3000 TL idi ve hiçbir şeye dayanmıyordu.
  Şimdi kalemlerden hesaplanıyor: sepetli araç günü, usta yevmiyesi, günde
  sekiz birim ve malzeme. Sonuç 2450 TL.

**Maliyet sayfası.** Her satırın kalem kalem dökümü, her kartın parçaları
(satıcı bağlantısıyla), raporun ve şimdiki fiyatlar 1, 100 ve 1000 adette,
ve her varsayım dayanağıyla birlikte `/maliyet` adresinde. Sayfadaki
hiçbir sayı elle yazılmadı. Bir sınama sayfadaki dökümün son satırının
yayımlanan hücreyle aynı olmasını istiyor; bir fiyat değişip tablo yeniden
yayımlanmazsa bu sınama düşüyor.

**Kırsal satır elektrik dağıtım hattının direklerine taşındı.** 25 m'lik
dikilen direk 85000 TL ve kırsal sermayenin %96'sını tutuyordu. Köy
yollarında dağıtım hattının beton direkleri zaten duruyor. Kaba okumada
(tek çekiliş) birimi 10 m'de, 3000 m aralıkla bu direklere koymak:

| düzen | birim | kullanılabilirlik | P95 | alan |
|---|---|---|---|---|
| 25 m dikilen direk, 4000 m | 28 | %52,0 | 18,6 m | 178 km² |
| 12 m dağıtım direği, 3000 m | 49 | %75,5 | 10,4 m | 256 km² |
| 10 m dağıtım direği, 3000 m | 49 | %74,5 | 13,0 m | 246 km² |
| 10 m dağıtım direği, 3500 m | 36 | %56,7 | 15,6 m | 126 km² |
| 12 m dağıtım direği, 2500 m | 68 | %75,7 | 10,7 m | 278 km² |

10 m seçildi, çünkü orta gerilim direkleri 12-14 m ve birim iletkenlerin
en az iki üç metre altında kalmalı. 3500 m'de alan, direk sayısından
hızlı düşüyor ve kilometrekare başına maliyet artıyor; 2500 m bir şey
kazandırmıyor. Köyler arasındaki hat yalnızca orta gerilim taşıdığı için
her birim kendi güneş setini taşıyor. Direk dağıtım şirketinin olduğu için
kiralanıyor; modele bunun için bir kira kalemi eklendi. Yayımlanmış bir
ortak kullanım bedeli bulunamadı, ayda 100 TL varsayıldı ve öyle
işaretlendi. Montaj, köyler arası yol yüzünden günde dört birimle 4600 TL.

## Denenip alınmayanlar

**Şehir içinde daha seyrek ızgara.** 500 m'den 600 ve 700 m'ye çıkınca
direk sayısı 36'dan 25'e ve 23'e iniyor. Ama kaba okumada P95 8,4 m'den
9-13 m'ye kötüleşiyor ve kullanılabilirlik düşüyor. Daha ucuz, ama
tablonun GPS ile karşılaştırılabilen tek sütununu bozuyor.

**Daha yüksek aydınlatma direği.** 15 ve 20 m'lik direkler alanı biraz
büyütüyor, ama P95'i tek çekilişin gürültüsünden ayıracak kadar tutarlı
iyileştirmiyor. Şehirdeki direklerin hepsi o boyda da değil.

**Kırsalda daha seyrek direk.** 5000 ve 6000 m aralıkta kullanılabilirlik
%52'den %36-43'e düşüyor. 25 m'lik direk kırsal sermayenin %96'sını
tuttuğu için seyreltmek ucuzlatıyor, ama satırın zaten zayıf olan
sütununu daha da zayıflatıyor.

## Doğrulamada düzeltilenler

Her fiyat ikinci, bağımsız bir aramayla yeniden kontrol edildi ve
maliyet hücreleri ham dosyalardan elle yeniden hesaplandı (modelle
kuruşu kuruşuna aynı). Kontrol dört hata buldu:

- **SIM kartı kalktı.** Raporda hiçbir birime hücresel hat konacağı
  yazmıyor; o kalem ilk maliyet modelinin (ADR-0006) varsayımıydı ve
  sorgulanmadan taşınmıştı. Tünel omurgasından, şehirde sinyal
  dolabından bağlanıyor; geri kalan birimleri onlara karşı ölçüm yapan
  alıcılar izliyor. `operating.connectivity_tl_per_year` sıfır, paylaşım
  ayarı kaldırıldı, bir sınama hiçbir satırın veri hattına para
  ödemediğini tutuyor.
- **Veri paketi yanlış paketti.** "M2M IOT 2 GB, 99 TL" yazılmıştı; o
  paket 229 TL, 99 TL olan 100 MB'lık Standart Endüstri. SIM kalktığı
  için artık sayıya girmiyor.
- **STM32G0B1 fiyatı yanlış satıcı ve kademedendi.** 3,61 USD Arrow'un
  10 adetlik fiyatıydı; raporun kullandığı DigiKey'de 1 adet 6,86 USD.
  "Diğer" kalemi buna göre 18'den 15 USD civarına indi, STM32G031'e
  geçişin tasarrufu büyüdü. ATECC608B DigiKey'de 0,90 USD.
- **Daha ucuzu vardı.** Akü 611,27 değil 524,40 TL, panel 700 değil
  518,72 TL; güneş seti 2600'den 2330 TL'ye. Kur 4 Eylül'ün 48,44'ü.

Birim fiyatlar (1000 adette): şehir içi ve kırsal 718,05 TL, tünel
1091,19 TL.

## Sonuçlar

Tam çözünürlükte, sekiz çekilişle yeniden yayımlandı:

| | HPE P95 | kullanılabilirlik | alan | CAPEX | OPEX |
|---|---|---|---|---|---|
| Şehir içi | 8,84 m (aynı) | %83,98 (aynı) | 6,68 km² | 23518 → 17065 TL/km² | 10088 → 3767 TL/km²/yıl |
| Kırsal | 22,72 → 11,83 m | %41,83 → %65,85 | 143,75 → 209,00 km² | 18618 → 1793 TL/km² | 772 → 617 TL/km²/yıl |
| Tünel | 2,90 m (aynı) | %98,29 (aynı) | 0,02 km² | 34355 → 31910 TL/km | 6553 → 3357 TL/km/yıl |

Şehir içi ve tünelde doğruluk sütunları hane hane aynı, çünkü oralarda
değişen hiçbir şey bir bağlantının kapanıp kapanmadığını etkilemiyor.
Kırsal satır yeni bir düzen; orada P50 3,70'ten 2,91 m'ye, VPE P95
232,33'ten 140,75 m'ye de indi. Kırsal OPEX'in en büyük kalemi
varsayılan direk kirası.

Yeni düzen kırsal satırı sakinleştirdi. Bir turda 8 yerine 10 direk
yoklamanın değeri dört tohumda ölçüldü: dördünde de kazanıyor, ortalama
+0,0117, tohumdan tohuma saçılım 0,0015. Önceki üç ölçümde etki
saçılımla aynı mertebedeydi; 49 direkte saçılım dörtte birine indi ve
etki tek koşudan okunabiliyor. Bunu tutan sınama yeni şekli söyleyecek
biçimde yeniden yazıldı.

Kırsal için gönderilen iki seçenek eski, 25 m'lik direğe göre yazılmıştı.
`rural-dense` şimdi 2,5 km'lik dağıtım direği ızgarası (daha çok direk,
aynı sonuç), `rural-tall` ise direkte 12 m (iletkenlere daha yakın).

Hızlı okuma kırsal kullanılabilirliği 8,6 puan iyi okudu (%74,48'e
karşı %65,85), P95'i ise bu kez kötü okudu (13,02'ye karşı 11,83 m).

## Yapılmayanlar

**Fiyatlar satıcı sayfalarından okunmadı.** Bu oturumun ağ politikası
DigiKey, Mouser, LCSC, EBYTE, TCMB, EPDK ve Turkcell'i kapatıyor (vekil
sunucu 403). Fiyatlar web aramasının döndürdüğü değerler; her birinin
bağlantısı `bom.toml` içinde duruyor ve sayfada gösteriliyor.

**"Diğer" satırı ucuzlatılmadı.** Raporun o satırda ne varsaydığı
yazılı değil; içini görmeden bir kalemini değiştirmek tahmin olurdu.

**Elektrik birim fiyatı değişmedi.** Aydınlatma abone grubunun 2026
tarifesi bulunamadı. Tüketim yılda 3 kWh olunca kalem her satırda
OPEX'in %2'sinin altında kalıyor.
