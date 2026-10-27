# ADR-0053: bir yol tek bir engel değildir

## Durum

Kabul edildi.

## Bağlam

Model, yoldaki en kötü tek noktayı alıp oraya bir bıçak sırtı koyuyordu.
Kızılay üzerinde ölçtüm, 6 m direkten 1,5 m alıcıya, 200 m ile 1,2 km
arası 215 bağlantı:

| kaç engel | bağlantıların payı |
|---|---|
| 0 (açık görüş) | %14,9 |
| 1 | %14,0 |
| 2 | %18,1 |
| 3 | %14,0 |
| 4–7 | %24,3 |
| 8+ | %14,9 |

Ortanca bağlantının **üç** ayrı engeli var, en kötüsünün on altı. Bunların
en kötüsünü alıp kalanını unutmak, tam da şehir satırının yaşadığı yerde
iyimser olmak demek.

Yönü kesindi, büyüklüğü değildi. İki uç ölçtüm: Bullington'ın eşdeğer
kenarı tek kenarın ortanca 1,7 dB üstünde, düzeltmesiz Deygout ise
27,9 dB üstünde. Deygout, kenarlar birbirine yakın ya da benzer
yükseklikteyken, ki bir şehirde hep öyledir, fazla sayar; aradaki doğru
cevabı veren yöntem Tavsiye'nin kendi yöntemi.

## Karar

**ITU-R P.526-15 4.5.2, delta-Bullington.** Gerçek profil üzerinde
Bullington'ın eşdeğer kenarı, artı aynı uzunluktaki düz bir dünyanın
aynı kurgunun ötesinde götürdüğü kadarı. İkinci terim, ufkun kendisi
engelken uzun ve yumuşak bir yolun temiz görünmesini engelliyor
(4.2, artık serisinin ilk terimi).

**Zemin `Obstruction` ile birlikte taşınıyor.** Arazi zaten profili
örnekliyordu ve yalnızca en kötü noktasını veriyordu; artık hepsini
veriyor. Dikiş yerinde kaldı: geometri `world.py`'den çıkıyor, desibel
`rf.py`'de oluyor.

**Elle kurulmuş bir `Obstruction` hâlâ tek kenar.** İki sayıdan ibaret
bir engelin üzerinde yürünecek zemini yoktur ve tek kenar o zaman onun
söylediğinin dürüst okunuşudur.

**J(v) bir kez yazılı.** Tek noktalı eski işlev de artık aynı
`knife_edge_db`'yi çağırıyor (denklem 31).

## Sonuçlar

Aynı bağlantılar üzerinde kırınım kaybı: ortanca 24,5 → **38,9 dB**,
p90 32,4 → **50,2 dB**. İki ucun arasında, beklendiği yerde.

Tablo aşağı indi:

| | önce | sonra |
|---|---|---|
| Şehir içi HPE P95 | 5,36 m | **10,14 m** |
| Şehir içi kullanılabilirlik | %99,79 | **%79,84** |
| Şehir içi alan | 8,93 km² | **5,69 km²** |
| Kırsal HPE P95 | 15,09 m | **29,62 m** |
| Kırsal kullanılabilirlik | %72,75 | **%41,87** |
| Kırsal alan | 218,75 km² | **167,00 km²** |
| Ağırlıklı HPE P95 | 9,76 m | **14,97 m** |

Tünel satırı değişmedi: bir delik boyunca profil düz ve zaten hiçbir şey
kırınmıyordu.

**Ölçülen menzil kımıldamadı** (Kızılay 478 m, Polatlı 690 m). Şaşırtıcı
değil: o sayı zaten gerçek binaların arasından ölçülüyordu (ADR-0047) ve
bir bağlantıyı bitiren şey engelin kaç desibel ettiği değil, olup
olmadığı. Değişen, aradaki zemin: kenardaki, 10 ile 30 dB arası,
bağlantılar döndü, ve kapsama ile kullanılabilirliği onlar belirliyor.

### İki sınama yeniden yazıldı, gevşetilmedi

**"Düz zemin hiçbir şeyi engellemez"** artık doğru değil. Düz zemin
kendi eğriliğinden başka bir şey engellemiyor, ve o bir şey: on
kilometrede 2 m'lik bir antenin ilk Fresnel bölgesi tümseğin içinde
kalıyor ve Tavsiye'nin yöntemi buna altı desibel yazıyor, en kötü
noktaya konan tek bir bıçak sırtı yarım desibel yazıyordu. Yirmi dokuz
bağlantının biri, ve o en uzaktaki.

**"Yumuşak rölyef yardım eder"** (ADR-0026) yarısıyla ayakta. Mekanizma
ölçülüyor ve duruyor: yolda hiçbir şey yokken yumuşak zemin düzlemden
**9,8 dB ucuz**, çünkü eğik yansıma yaması götüren ışını alıcının yanına
nişanlıyor. Ama aynı tepeler yolun üstünde duruyor, ve altı kilometrede
kırınım 5,7 → 11,9 dB oluyor: verdiğinden fazlasını geri alıyor. Sınama
artık iddiayı yansıma üzerinde ölçüyor ve neti bir takas olarak
yazıyor, ki bir üstündeki sınamanın adı zaten o. (ADR-0058 bu neti
tekrar ölçtü: büyüğü ödenince takas kalmıyor, rölyef düpedüz maliyet.)

## Yapılmayanlar

**Kayıplar hâlâ toplanıyor.** `spread_db` iki ışınlı iptali, kırınım da
aynı zemini sayıyor; Tavsiye'nin kendi yapısı (P.452, P.1812) serbest
uzay + kırınım kuruyor, iki fazlalığı toplamıyor. Ölçtüm:
`max(iki ışın fazlası, kırınım)` şehir alanını 5,69 → 5,72 km²,
kullanılabilirliği %79,84 → %82,05 yapıyor. Fark küçük olduğu için
yapıyı değiştirmedim; ama çift sayım gerçek ve bir hakemin göreceği
türden. **ADR-0058 bunu yaptı.**

**Gölgeleme yok.** Konum değişkenliği (log-normal, σ ≈ 5,5 dB) hâlâ
modelde değil, yani her hücre ya geçiyor ya kalıyor. Gerçek kapsama
"konumların %X'i" diye verilir.

**Profil 64–200 örnekle okunuyor.** 1,2 km'de örnek aralığı ~19 m, bir
bina genişliği kadar. Daha sık örneklemek cevabı değiştirir ve ne yönde
değiştirdiği ölçülmedi. **ADR-0062 ölçtü:** yön tek, çünkü Bullington
örnekler üzerinden maksimum alıyor, ve kırsalda 6,32 dB eksik
okunuyormuş. Profil artık on metrede bir okunuyor.
