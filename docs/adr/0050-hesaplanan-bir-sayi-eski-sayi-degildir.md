# ADR-0050: hesaplanan bir sayı, eski sayı değildir

## Durum

Kabul edildi.

## Bağlam

Şehir sekmesinden kırsala geçtim. Panel bir buçuk saniye boyunca şunu
gösterdi:

| satır | değer |
|---|---|
| Direk sayısı | **36** (şehir) |
| C: menzil | **3,82 km** (şehir) |
| Konum alınabilen alan | **219,00 km²** (kırsal) |
| Paketin ulaştığı alan | **418,00 km²** (kırsal) |

İki farklı sahanın sayıları yan yana, ikisi de yerleşmiş gibi
görünüyor. Durum çubuğunda "Kapsama taranıyor…" yazıyor ama alan
satırları bunu söylemiyor — bir sayı orada durduğu sürece cevaptır.

Aynı şey daha uzun sürende de oluyordu: `greedy-dop` 9 saniye arıyor
(ADR-0049), ve o dokuz saniye boyunca panel bir önceki düzenlemenin
her sayısını gösteriyordu. Açılır menüde "greedy-dop" yazıyor, panelde
27 direk yazıyor, hangisinin doğru olduğunu söyleyen bir şey yok.

Bir üçüncü durum daha vardı: süpürme indiğinde panel `showNumbers(latest,
null)` ile yeniden çiziliyordu. Tarama sürerken "Simülasyonu çalıştır"a
basarsan sonuç görünüyor, bir saniye sonra süpürme iniyor ve **sonuç
kayboluyor.**

## Karar

**Panelin üç durumu var, iki değil.**

| işaret | anlamı |
|---|---|
| bir sayı | yürürlükteki düzenlemenin cevabı |
| `—` | bildirilecek bir şey yok (direksiz bir düzenlemenin turu yoktur) |
| `…` | bildirilecek bir şey var, henüz bilinmiyor |

Alan satırları süpürme planlandığı anda `…` oluyor — eski alanların
doğru olmaktan çıktığı an, yenilerinin geldiği an değil; ikisi saniyeler
uzakta. Satırlar hep duruyor, çünkü gelip giden bir satır altındaki her
şeyi kaydırıyor ve cevabın değişmesi gibi okunuyor.

**Fark edilmeye değer bekleme bildiriliyor, hepsi değil.** Düzenlemelerin
çoğu milisaniye; her sürgü çekişinde kendini boşaltan bir panel hiç
boşaltmayandan daha zor okunur. Eşik 400 ms, ve beklemenin kendisi
`refreshScene` — sayfanın her yolu oradan geçiyor, `apply` de sekme
değişimi de ayar yüklemesi de.

**Bir süpürme bir simülasyonu geçersiz kılmaz.** Aynı düzenleme iki
biçimde ölçülüyor. Geçersiz kılan bir düzenlemedir, ve o zaten
`refreshScene` içinde siliniyor.

## Ek: geç gelen cevap

Bu ADR bir sayının *hesaplanırken* nasıl gösterileceğiyle ilgiliydi.
Aynı ailenin ikinci yarısı sonradan çıktı: **hesaplanan cevabın artık
sorulmayan soruya ait olması.**

Zamanlayıcıyı iptal etmek yalnızca henüz sorulmamış bir taramayı
durdurur. Uçuştaki bir tarama motor bitirdiğinde geliyor, ve
`/api/sweep` isteği aldığı andaki duruma göre cevap veriyor. Bir tarama
sürerken satır değiştirince kırsalın kapsadığı zemin tünelin paneline
indi: bir delikteki on dört direğin yanında **164,25 km²**. Sayı
gerçekti ve başkasınındı.

Dört çekirdek meşgulken bir kez görüldü — kırsalın taraması orada pencere
açacak kadar uzun sürüyor. Sonrasında cevabı sayfaya dönerken elde
tutarak kesin olarak yürünüyor.

Her tarama isteği bir sıra numarası taşıyor; sayfanın beklediği numara
değilse cevap atılıyor. Hata mesajı da öyle: kimsenin beklemediği bir
taramanın hatası da kimsenin sorusuna ait değil.

## Sonuçlar

Tarayıcıda, Kızılay üzerinde:

| an | Direk sayısı | Konum alınabilen alan |
|---|---|---|
| kırsal yerleşmiş | 28 | 8,92 km² |
| şehre geçildi, +0,6 s | 36 | **…** |
| şehir yerleşmiş | 36 | 8,92 km² |

`greedy-dop` seçilince panelin tamamı `…` ve durum çubuğu "Çalışıyor…"
diyor; 9,6 saniye sonra 60 direk yazıyor. İkinci seferde 4,2 saniye,
çünkü yerleştirme hatırlanıyor (ADR-0049).

Tarama sürerken çalıştırılan bir simülasyonun sonucu duruyor; bir
düzenleme onu siliyor.

Sınamalar kaynağı okuyor, çalıştırmıyor: `app.js` sayfanın kendisi, yüklenirken
`document`'e uzanıyor. Davranış tarayıcıda yürünüyor ve `docs/TRY-IT.md`
nasıl yürüneceğini yazıyor.
