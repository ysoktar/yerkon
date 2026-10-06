# ADR-0023: yerleşim bir dosyadır, koda gömülmüş bir karar değil

## Durum

Kabul edildi.

## Bağlam

ADR-0016, kimsenin sağlamadığı her figürü `defaults.toml` dosyasına
taşıdı ve görüntüleyici hepsini çalışırken düzenlenebilir yaptı. Bu,
doğru kuralın sayıların yarısına uygulanmasıydı.

Diğer yarısı `scenarios.py` içinde sabit değer olarak kaldı: direkler
birbirinden ne kadar uzakta duruyor, bir satır ne kadar zemin kaplıyor,
bir tur kaç direğe soruyor, bir menzil atılmadan önce ne kadar gürültülü
olabilir, tünel ne kadar geniş. Bunların her biri yayımlanan tablonun bir
sütununa karar veriyor.

Bunun bedeli, çalışma ilginçleşir ilginçleşmez ortaya çıktı. Kırsal
satırı düzeltmek, aralıklar, direk yükseklikleri ve tur boyutları
denemek demekti — ve bu denemelerin her biri bir sabit değeri düzenleyen,
çalıştıran, yazdıran ve düzeni çöpe atan bir müsvedde betikti. Bulgular
bir ADR'de kaldı; düzenler hiç kalmadı. Kimse onları yeniden
çalıştıramazdı, görüntüleyici onları gösteremezdi ve kırsal satır için
savunulabilir iki cevap aynı anda var olamazdı, çünkü `scenarios.py` bir
seferde tek bir sayı tutabilir.

Aynı yerde bekleyen daha küçük bir sorun daha vardı. Bunları ayarlar
dosyasına yer tutucuların yanına koymak, "bu maliyetlendirmenin %99'u
kimsenin sağlamadığı figürlere dayanıyor" cümlesini sessizce yanlış
yapardı; çünkü direk aralığı bir ölçüm bekleyen bir figür değildir.
Aralığın *gerçekte ne olduğunu* kimse ölçemez. Karara bağlanan şeyin
kendisidir.

## Karar

**Üç parça.**

**Bir `DESIGN` kaynak türü.** Yerleşim geometrisi diğer her şeyle aynı
dosyaya girer — tek bir yer tablodaki her sayıyı değiştirir ve
görüntüleyici zaten o dosyadaki her şeyi düzenler — ama bir yer tutucu
olarak değil, bir seçim olarak işaretlenir. `Settings.assumed_share`
yalnızca ilkesel olarak ölçülebilecek figürleri sayar, böylece bu
çalışmanın ne kadarının tahmin olduğunu söyleyen sayı söylediği şeyi
söylemeye devam eder.

**Adlandırılmış seçenekler.** Bir seçenek, ayarlarda yapılacak kısa bir
düzenleme listesi ve birinin onları neden yaptığıdır; kendi dosyasında
durur. Hiçbir makine taşımaz: yenisi bir dosyaya mal olur, bir kod
değişikliğine değil. `--defaults` ile *birleşir*, onun yerini almaz;
böylece birinin gerçek fiyat teklifleri ve daha sık bir ızgara birlikte
ayakta kalır — dosyanın yerini alan bir seçenek, içindeki ölçülmüş her
figürü sessizce atardı.

Dördü hazır geliyor, çünkü çalışma sürekli onlara çarptı:

| seçenek | nedir |
|---|---|
| `rural-dense` | 3 km'de 49 direk, 30 m boyunda. %90'ı geçmenin en ucuz yolu |
| `rural-tall` | Aynı 33 direk, 10 m daha uzun. Eşit parada kaybeder, saha başına kazanır |
| `urban-dense` | Her iki aydınlatma direğinde bir değil, her birinde direk |
| `rural-hard-ground` | Gölbaşı tepeleri: bu tasarımın gitmesi düşünülmeyen yerde maliyeti |

İlk ikisi kasıtlı olarak birlikte duruyor. Hangisinin doğru olduğu, kıt
olan şeyin para mı saha erişimi mi olduğuna bağlıdır ve bu projede bunu
söyleyecek figürler yok.

**Bir çözücü.** `yerkon solve`, bir hedefe karşı düzenleri arar ve
kazananı yeni bir seçenek olarak kaydeder. Onu iki kural biçimlendirir:

*Gerçek benzetimi çalıştırır.* Her aday, indirilmiş zemine karşı tam bir
senaryodur; yavaş olmasının ve cevaplarının tabloya karşı
güvenilebilmesinin sebebi budur — aynı motordan gelirler. Birkaç koşuya
uydurulmuş bir vekil model, aynı şeyin ikinci bir modeli olurdu ve
tam olarak zeminin zor olduğu yerde birinciyle çelişirdi.

*En iyi değil, karşılayanların en ucuzu.* Kullanılabilirliği
enbüyükleyen bir arama, kendisine sunulan en sık ızgarayı her zaman geri
verirdi, çünkü daha çok direk her zaman biraz yardım eder. Bütçesi olan
birinin ihtiyacı, çıtayı aşan en ucuz düzendir — ADR-0015'in yapılar
için kararlaştırdığı kuralın geometriye uygulanmışı.

Ayrıca yanıltıcı bir dosya üretmek yerine iki şeyi reddeder. Hiçbir şey
hedefi karşılamıyorsa hiçbir şey döndürür, kötü bir kümenin en iyisini
değil; çünkü en az kötü başarısızlığını döndüren bir aramanın cevabının
her seferinde elle denetlenmesi gerekir. Ve ayarlar hedefi zaten
karşılıyorsa, hiçbir şeyi değiştirmeyen bir seçenek kaydetmek yerine
bunu söyler; öyle bir seçenek listede bir karar gibi görünerek dururdu.

## Sonuçlar

On altı figür `scenarios.py`'den ayarlar dosyasına taşındı ve
`scenarios.py` bir sütuna karar veren hiçbir sayı tutmaz oldu. Aşağıdaki
her şey bedavaya geldi: görüntüleyicide canlı düzenlenebilirler,
kaynaklandırılabilirler, `yerkon defaults` içinde görünürler ve
aranabilirler.

Çözücü yerini hemen hak etti. Ellinci yüzdelikte bir metrenin altında
tünel istendiğinde, 120 m'lik askı aralığının — on dört yerine on yedi
direk, 23 000 TL daha fazla — o satırı 1,81 m'den **0,48 m**'ye
taşıdığını buldu. Beşte bir fazla sermayeye karşılık neredeyse dört kat
doğruluk; üstelik kilometrekare başına maliyeti tabloda üç büyüklük
mertebesiyle zaten en büyük olan satırda. Kimse denememişti, çünkü
denemek eskiden bir sabit değeri düzenlemek demekti.

Bunun yapmadığı şey, aramayı ucuzlatmak. Otuz altı kırsal düzen, otuz
altı tam benzetim ve yarım saate yakın zaman demek. Bu, ilk kuralın
bedeli; alternatifi ise hiçbir şeye karşı denetlenemeyecek daha hızlı bir
cevaptı.
