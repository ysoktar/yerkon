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
bağlantı, kutu). Üç yayın biriminde de bu kalan 1 adette 18,0 ile 18,6
USD arasında çıkıyor. Kart aynı kart olduğuna göre öyle olması gerekir;
dökümün raporla tutarlı olduğunu gösteren kontrol de bu. Bir sınama bu
kalanların birbirinden bir dolardan fazla ayrılmamasını istiyor.

**Aynı işi daha ucuza yapan parçalar.**

| önce | sonra | 1 adet |
|---|---|---|
| RF Solutions LAMBDA80-24S (SX1280, 12,5 dBm) | EBYTE E28-2G4M12S (SX1280, 12,5 dBm) | 16,49 → 4,39 USD |
| Qorvo DWM3000, DigiKey | aynı parça, LCSC | 23,62 → 16,60 USD |
| STM32G0B1MET6 (512 KB) | STM32G031K8T6 (64 KB) | 3,61 → 1,93 USD |
| Newhaven 2,8 inç ekran (araç alıcısı) | 2,8 inç ILI9341 modülü | 21,80 → 10,90 USD |

Sipariş notu: doğru parça ek harfsiz **E28-2G4M12S**. EBYTE'ın "X" ekli
modülleri (E28-2G4M12SX) SX1281 taşıyor ve SX1281'de ölçüm motoru yok;
satıcı ilanları iki adı karıştırıyor.

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

Birim fiyatlar (1000 adette): şehir içi 1366,07 → 815,88 TL, kırsal
1082,68 → 815,88 TL, tünel 1634,44 → 1194,64 TL.

**Varsayımlar dayanaklarından yeniden kuruldu.**

- *Tüketim* yılda 35 kWh idi, yani sürekli 4 W. Bir SX1280 kartı dinlerken
  birkaç mA çekiyor; dönüştürücü kaybıyla birlikte 0,34 W bir üst sınır.
  Yeni değer yılda 3 kWh.
- *Veri hattı* 600 TL/yıl varsayılmıştı. Bulunan en ucuz kurumsal M2M
  paketi ayda 99 TL, yani yılda 1188 TL. Varsayım gerçek fiyatın
  yarısıymış; bu yükseltildi. Ucuzlatmak için paketi ucuz varsaymak yerine
  paylaşım modellendi: hattı olmayan birim durum bilgisini zaten konuştuğu
  telsizle bir komşusuna aktarıyor, ve on birim bir paketi paylaşıyor
  (`operating.anchors_per_data_plan`, bir tasarım kararı).
- *Güneş seti* 9500 TL idi ve 4 W'lık bir yüke göre boyutlanmıştı. 10 W
  panel (700 TL), 12 V 7 Ah akü (611,27 TL), denetleyici, tutucu ve kablo:
  2600 TL.
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

## Sonuçlar

Tam çözünürlükte, sekiz çekilişle yeniden yayımlandı:

| | HPE P95 | kullanılabilirlik | alan | CAPEX | OPEX |
|---|---|---|---|---|---|
| Şehir içi | 8,84 m (aynı) | %83,98 (aynı) | 6,68 km² | 23518 → 17592 TL/km² | 10088 → 4366 TL/km²/yıl |
| Kırsal | 22,72 → 11,83 m | %41,83 → %65,85 | 143,75 → 209,00 km² | 18618 → 1879 TL/km² | 772 → 656 TL/km²/yıl |
| Tünel | 2,90 m (aynı) | %98,29 (aynı) | 0,02 km² | 34355 → 32376 TL/km | 6553 → 3415 TL/km/yıl |

Şehir içi ve tünelde doğruluk sütunları hane hane aynı, çünkü oralarda
değişen hiçbir şey bir bağlantının kapanıp kapanmadığını etkilemiyor.
Kırsal satır yeni bir düzen; orada P50 3,70'ten 2,91 m'ye, VPE P95
232,33'ten 140,75 m'ye de indi. Kırsal OPEX'in en büyük kalemi artık
varsayılan direk kirası.

Hızlı okuma kırsal kullanılabilirliği 8,6 puan iyi okudu (%74,48'e
karşı %65,85), P95'i ise bu kez kötü okudu (13,02'ye karşı 11,83 m).
Sayfalardaki "hızlı okuma iyimser" cümlesi kullanılabilirlik üzerinden
yeniden yazıldı.

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
