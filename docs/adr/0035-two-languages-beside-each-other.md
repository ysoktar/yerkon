# ADR-0035: iki dil, yan yana

## Durum

Kabul edildi.

## Bağlam

Bunun cevap verdiği rapor Türkçedir ve onu denetleyecek insanlar Türkçe
çalışır. Kod, kararlar ve sınamalar İngilizcedir; çünkü yazıldıkları dil
budur ve on beş bin satır açıklamayı yeniden yazmak, kimsenin
okumayacağı büyük ve riskli bir değişiklik olurdu.

Sayfa ikisinin arasında duruyordu. Çerçevesi Türkçeydi; yetmiş iki figür
neye dayandıklarını ve neyi etkilediklerini İngilizce söylüyordu; zemin
kendini İngilizce anlatıyordu; hazır seçenekler kendi savlarını İngilizce
kuruyordu. Yani en çok ihtiyacı olan insanlar için kurulmuş tek yüzey,
karar veremeyen yüzeydi.

Onu çevirmek ilk cevaptı ve yanlış olandı: Türkçeyi eklemek yerine
İngilizceyi siler ve sayfayı, yanında kodu okuyan herkes için okunmaz
kılar.

## Karar

İki dil; ve hiçbiri, biri özgün olacak anlamda ötekinin çevirisi değil.
Arama kutusunun yanında bir seçici durur — menü değil iki düğme, çünkü
iki maddelik bir menü, içinde ne olduğunu öğrenmek için bir tıka mal
olur — ve geçiş yapmak, sayfanın elindekini çevirmek yerine motora
yeniden sorar.

Birinin **yazdığı** metin, anlattığı değerin yanında yaşar:
`defaults.toml` içinde `note`/`note_en`, `affects`/`affects_en`,
`source`/`source_en`, `sensitivity`/`sensitivity_en`; her seçenekte
`title`/`title_en`, `note`/`note_en`. İkisi de tek bir değerin yanında,
iki dosyada değil; çünkü iki dosya birbirinden kayar ve başarısızlık kötü
bir çeviri değildir — aynı sayı hakkında iki farklı iddiadır.

Projenin **kurduğu** metin `language.py` içinde, tek bir ad altında bir
biçim dizgisi çifti olarak yaşar. Sayfanın kurduğu metin `words.js`
içinde, aynı şekilde. Bir dili eksik olan bir ad, yedeğe düşmek yerine
hata yükseltir: yedek, onda dokuzu çevrilmiş ve onda birini kimsenin fark
etmediği bir sayfa demektir.

Hiçbir şey bir şeye karar vermez. Değerler, geometri ve her sonuç ikisinde
de birebir aynıdır ve bir sınama bunu söylemek için bütün tabloyu iki kez
kurar.

Sayılar ikisinde de aynı yazılır: virgüllü ondalık ayırıcı ve binlik
ayırıcı yok; raporun kullandığı budur. İngilizce, ikinci bir çalışma
değil aynı çalışmaya açılan bir yoldur ve iki yazılı biçimi olan bir
figür, birinin iki türlü alıntılayabileceği bir figürdür.

Kayda geçmiş bir olgu çevrilmez. Bir sahanın künye notları da öyle:
`fetched_at` ile ve kaynağın kendi hata metniyle birlikte, o günkü
indirmenin kaydıdır ve diskte durur; sayfanın o an hangi dile ayarlı
olduğunu değil, o gün ne olduğunu söyler. `Copernicus DEM 30 m ×2`, indirilmiş
olan şeydir ve diskteki künyede saklanır; eskiden `(2 tiles)` yazıyordu,
bu da önbellekteki sahaların sayfa ne olursa olsun İngilizce olması
demekti.

## Sonuçlar

Panel, figürler, zemin, seçenekler, çözücünün çıktısı ve uzun bir iş
sürerken sayfanın gösterdiği ilerleme kütüğü hangi dil seçilmişse onda
okunuyor ve bu sözcüklerin hiçbirini tutan tek şey motor.

İlerleme kütüğü ilk turda atlanmıştı: satırları `tell`'e verilen
İngilizce sabit dizgilerdi ve İngilizce bir satır, biri sayfayı
değiştirene kadar sıradan koddan ayırt edilemez. Şimdi kütüğün de her
satırı kataloğdaki bir addır ve bir sınama, `tell`'e sabit dizgi
verilmesini reddediyor. İlerleme geri çağrısının adı da `tell` oldu;
`say` cümleyi kuran, `tell` onu sayfaya ileten.

Yapım sırasında tutmaya değen iki şey çıktı:

`say(key, ...values)` önce konumsaldı; iki dilin parçalarını aynı sırada
istemediği düşüncesiyle. İstemiyorlar da — "72 değerin 35 tanesi
varsayım" önce toplamı sayar, "35 of 72 figures are assumptions" önce
varsayımları sayar — ve ikisinde de `{}` varken bir dil sessizce
ötekinin sayılarını alır. Aldı da; üstelik iki sayısı olan ilk cümlede.
Alanlar artık adlandırılmış ve her dil onları istediği gibi sıralıyor.

`Option` veri sınıfının ortasına `title_en`/`note_en` eklemek, onlardan
sonraki her konumsal bağımsız değişkeni kaydırdı; bu da hiç değeri
olmayan bir seçeneğin, tam olarak bunu reddetmek için var olan sınamayı
geçmesine yol açtı. Yeni alanlar sona eklenir.

## Yapılmayan

`report.py`, `deliver.py`'nin yazdığı Markdown ve komut satırı hâlâ
yalnızca Türkçe konuşur. Tablonun satır adları, sütun başlıkları ve
Markdown çıktıları raporun kendi sözcükleridir ve onları ikisi birden yapmak, aynı işin başka bir
yüzeyde yeniden yapılmasıdır. Sayfa, onları gösterdiği yerde bunu
söyler: motorun görüntüleyiciye verdiği seçilen dildedir, `yerkon table`
komutunun yazdırdığı değildir.
