# ADR-0071: sitenin dili

## Durum

Kabul edildi.

## Bağlam

Site, raporun ve sunumun cümlelerini büyük ölçüde olduğu gibi taşıyordu.
Rapor bir yarışmaya sunuldu, ve o metin kendi bağlamında doğru. Ama
siteyi açan kişi raporu okumuş olmak zorunda değil, ve sayfalarda
cümlenin ne dediğini anlamak için terimi önceden bilmek gereken yerler
vardı:

- *seyrüsefer*, *kentsel kanyon*, *rölyef*, *ölü hesaplama*, *yer
  gerçeği*, *link bütçesi*, *kestirici*, *etüt hatası*, *bütünlük
  referansı*. Bunların hepsi ya eski ya da doğrudan İngilizceden
  çevrilmiş; hiçbiri konuşurken kullanılan kelime değil.
- *figür*: İngilizce "figure" burada sayı demek, Türkçede figür demek
  değil. Cümle yanlıştı.
- *alışveriş*: iki telsizin karşılıklı mesajlaşmasını anlatıyordu ve
  alışveriş yapmayı çağrıştırıyordu.
- *çıta tutturuldu*: panelde bir aramanın hedefini tutturup
  tutturmadığını söylüyordu, ve atlama çıtası gibi okunuyordu.
- Fayda sayfasındaki listeler ad tamlamasıyla yazılmıştı: "tek hata
  noktasının azaltılması", "yetkinliğinin geliştirilmesi". Bunlar bir
  form doldurur gibi okunuyor, kimin ne yapacağını söylemiyor.

Bir de aynı şeyin iki adı vardı: menüde **Benzetim**, sağ üstteki
düğmede **Simülasyon**. İkisi de aynı sayfaya gidiyordu.

## Karar

**Sekiz sayfanın Türkçesi baştan yazıldı, gündelik kelimelerle.** Terim
gerektiğinde açıklanıyor, gerekmediğinde atılıyor. Örnekler:

| Önce | Sonra |
| --- | --- |
| kentsel kanyon | yüksek binaların arasında |
| seyrüsefer ve hassas zamanlama | yol tarif etmek ve saati hassas tutmak |
| Kestirici gerçeği hiç görmez | Konumu hesaplayan kod, aracın gerçekte nerede olduğunu hiç görmez |
| aynı iki figürü kabalaştırır | aynı iki ayarı kabalaştırır |
| Alışveriş ve kestirici | Mesajlaşma ve konum hesabı |
| Gürültü olmayan üç hata | Ortalamayla geçmeyen üç hata |
| çıta tutturuldu | hedef tutturuldu |

**Kısaltmalar ilk geçtikleri yerde açılıyor.** "IMU, odometri, harita
kısıtı ve Kalman füzyonu yok" cümlesi, okuyan kişiye hiçbir şey
söylemiyordu. Yerine ne olmadığı yazıldı: hareket sensörü, tekerlek
turu, harita, ve bunları birleştiren filtre.

**İngilizce, Türkçenin söylediğini söylüyor.** Türkçe değişip İngilizce
olduğu yerde kalsaydı iki dil iki farklı şey anlatırdı; bu ADR-0035'in
yazıldığı hatadır. Türkçesi değişen her cümlenin İngilizcesi de
yeniden yazıldı.

**Tek ad: simülasyon.** Menü, başlık, README ve CONTEXT aynı kelimeyi
kullanıyor. Sayfanın adresi de `benzetim.html` yerine `simulasyon.html`
oldu; `write_pages` artık çizmediği sayfayı zaten süpürüyor, ve iş akışı
`gh-pages` dalını her seferinde sıfırdan yazdığı için eski adres
kendiliğinden kalktı.

**Sağ üstteki düğme artık "Simülasyonu çalıştır".** Çünkü o düğme
sayfaya değil, çalışan simülatöre gidiyor; ikisine birden "Simülasyon"
demek yeni bir karışıklık olurdu. Bunu fark ettiren de bir hataydı:
düğmenin adresi `/simulasyon`'du, sayfanın yeni adresi de öyle oldu, ve
sunucu düğmenin adresini sayfalardan önce cevapladığı için **açıklama
sayfası sunucuda erişilemez hâle geldi**. Simülatör `/calistir`
adresine taşındı, ve iki sınama bunu tutuyor: adres hiçbir sayfanın
adresiyle çakışmasın, ve düğmenin adı menüdeki adla aynı olmasın.

## Sonuçlar

Sayfalar, YERKON'u ilk kez duyan birine okunabilir. Terim sayısı
azalmadı; terimlerin açıklanmadan bırakıldığı yer azaldı.

Bir yan kazanç: cümleleri düz Türkçeye çevirmek, bazı yerlerde ne
söylendiğini de netleştirdi. "Hizmet alanı, bir konumun alınabildiği
yerdir" cümlesine nedeni eklendi (duymak yetmiyor, dört birim
gerekiyor); tünelin km² maliyetinin neden büyük çıktığı, "aritmetik"
denip geçilmek yerine yazıldı.

**Bir de sayı hatası çıktı.** Türkçe, tünelin kapladığı yeri "yaklaşık
iki yüz dönüm" diyordu. İki yüz dönüm 0,2 km²; tablonun kendi Alan
sütununda o satır için yazan sayı 0,02 km². On kat. İngilizcesi doğruydu
("a fiftieth of a square kilometre"), yani hata yalnızca Türkçedeydi ve
iki dilin aynı şeyi söyleyip söylemediğine bakan sınama sayıları
karşılaştırmadığı için görünmemişti. Cümle tablonun kendi sayısına
bağlandı.

## Yapılmayanlar

**`defaults.toml` ve `options/*.toml` notları elden geçmedi.** Onlar
çalışmanın içindeki biri için yazılmış mühendislik notları, ve
panelin "Varsayılan değerler" sekmesinde görünüyorlar. *rölyef* gibi
kelimeler orada duruyor.

**Rapor ve sunum değişmedi.** Onlar yarışmaya sunuldu; bu ADR yalnızca
siteyi bağlar.

**ADR'ler elden geçmedi.** Her biri yazıldığı günün kaydı, ve
geçmişi düzeltmek kaydı bozmak olurdu. ADR-0069'a kadar olanlarda
*benzetim* kelimesi duruyor.
