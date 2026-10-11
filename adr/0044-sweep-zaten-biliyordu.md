# ADR-0044: tarama zaten biliyordu

## Durum

Kabul edildi.

## Bağlam

Zemin örtüsü iki renkti: paketin ulaştığı yer ve konum alınabilen yer.
Bu ayrım önemli ve ADR-0012 onun için var — ama sorulabilecek tek soru
değil.

Asıl mesele şuydu: tarama her hücrede her direk için **tam link
bütçesini koşturuyor** — projedeki en yavaş şey olmasının sebebi bu — ve
sonucu bir boolean'a indirip gerisini atıyordu. Marj dB cinsinden
oradaydı, menzil sigması oradaydı, erişen direklerin geometrisi oradaydı.
Hepsi hesaplanıp çöpe atılıyordu.

## Karar

**Atılanı tut.** Dört okuma, aynı taramadan:

| Katman | Ne sorar |
|---|---|
| Kaç direk erişiyor | Bugünkü sayım. Üç bir konum için en az, dördüncüsü onu denetler. |
| Sinyal marjı (dB) | En güçlü bağlantının çalışmayı bırakmasına ne kadar kaldığı. |
| Geometri (HDOP) | Direk dizilişinin menzil hatasını kaç katına çıkardığı. |
| Beklenen konum hatası (m) | Menzil sigması × geometri. |

**Bedeli %3.** Ölçtüm: kırsal satırda 13,09 s → 13,48 s, şehir içinde
2,19 s → 2,20 s. Link bütçesi hâkim; defter tutmak yanında hiçbir şey.

**Hata bir kestirimdir, benzetim değildir — ve bu yazılı.** İçinde saat
kayması yok, paket kaybı yok, oturmayan bir çözücü yok, gerçekten oradan
geçen bir alıcı yok. `yerkon table`'ın dördü de var. Bu, hangi zeminin
zor olduğunu gösteren bir resim; yayımlanan sayı koşudan gelir
(ADR-0001). Katmanın kendi notunda böyle yazıyor.

Yine de birbirini tutuyorlar, ki tutması gerekirdi: kırsal zeminde
kestirimin ortancası 3,02 m, yayımlanan HPE P50 3,11 m.

**Sayı olmayan yer boyanmıyor, sıfır boyanmıyor.** Sıfır dB marj bir
cevaptır — kılpayı kapanan bir bağlantı — ve "buraya hiçbir direk
erişmiyor" bambaşka bir olgudur. Izgarada NaN, telde `null`. (NaN JSON
değil: `json.dumps` çıplak `NaN` yazar, `JSON.parse` reddeder, yani tek
bir erişilemeyen hücre güncellemeyi durduran bir sayfa ederdi.)

**Üç direk erişene kadar geometri yoktur.** İki menzil alıcıyı iki
noktadan birine koyar; bildirilecek bir seyreltme yoktur ve yine de
bildirmek, birinin sonuç diye okuyabileceği bir sayı olurdu (ADR-0040).

**Dört bant, daha fazlası değil.** Sürekli bir renk geçişi, taranmış bir
ızgaranın taşıdığından fazla bilgi varmış gibi görünür ve insanı bir
sınırı gradyandan okumaya davet eder. Eşikler birinin gerçekten
adlandıracağı yerler: marjda 6 dB ince / 20 dB rahat, seyreltmede GNSS
geleneği, ve **hatada bu satırın kendi toleransının katları** — çünkü bu
projenin sorduğu soru zeminin çıtayı karşılayıp karşılamadığı, soyut bir
ölçekte kaç aldığı değil (ADR-0015). Çıtayı oynat, resim onunla oynar.

**Efsane motorun kendi eşiklerinden yazılıyor**, sayfadaki bir kopyadan
değil — ve boyayıcının kullandığı aynı işlevden okunuyor. Boyayıcının
kullanmadığı bantları tarif eden bir efsane, efsanesizlikten kötüdür.

**Yükselen katman dört eşik alır, düşen üç.** Yükselende ilki, altında
hiçbir şeyin boyanmadığı tabandır; düşende buna gerek yok, çünkü "burada
bir şey yok" null olarak geliyor. İlk hâlinde ikisi de dört alıyordu ve
düşenlerde dördüncüsü hiçbir şey yapmıyordu — bir şey yapıyormuş gibi
duran bir sayı.

## Sonuçlar

Kızılay'da dört katman dört ayrı resim veriyor: marj haritasındaki sarı
lekeler ile hata haritasındakiler **farklı yerlerde**, ki olması gereken
bu — sinyal gücü ile konum kalitesi ayrı sorular.

`evaluate` artık `layout`'tan `dilution_at` okuyor. `layout` bir yaprak
— bu paketten hiçbir şey almıyor — dolayısıyla ne döngü ne de alıcının
gerçek konumuna bir yol açıyor (`test_architecture` denetliyor).
Seyreltme, bir aday direği puanlarken de bir hücreyi boyarken de aynı
aritmetik.

Kod kendi kuralını hatırlattı: sigmayı koşulsuz istemiştim ve
`ranging_sigma_m` reddetti — kapanmayan bir bağlantının menzil
hassasiyeti yoktur ve `rf` büyük bir sayı uydurmaktansa reddediyor.

## Sonraki adımlar

Alıcı güzergâhları — hangi alıcı hangi yolda. Ve yol kenarı donanımı
için Overture'ın `transportation` katmanı (ADR-0040).
