# 0016. Raporun vermediği her değer tek bir dosyada durur

## Durum
Kabul edildi. ADR-0006'yı genişletir.

## Bağlam
Rapor bir malzeme listesi verdi, başka bir şey vermedi. Bu projenin ihtiyaç
duyduğu geri kalan her şey — bir direğin kurulumunun neye mal olduğu, bir
bakım ziyaretinin neye mal olduğu, SX1280'in gürültü katsayısının ne olduğu,
bir frekans kayması kestiriminin geriye ne bıraktığı — birinin yazdığı bir
vekildi.

Her biri kendi kaynağını ve kendi notunu taşıyordu; bu da bir vekilin ölçüm
diye geçmesini engellemeye yetiyordu ama birini bulunabilir kılmaya
yetmiyordu. Beş modüle dağılmışlardı. Kendini yüzde doksan dokuz varsayım
diye bildiren bir maliyetlendirme, ancak onu okuyan kişi gidip o yüzde doksan
dokuzu bulabiliyorsa işe yarar; ve bulamıyorlardı.

Daha kötüsü, hiçbir şey bir yenisinin eklenmesini engellemiyordu. Disiplin
bir alışkanlıktı ve alışkanlıklar zorlanamaz.

## Karar
Kimsenin vermediği her değer `src/yerkon/defaults.toml` içinde durur.

Varsayım değil varsayılan deniyor, çünkü kalıcı olan bu. Biri bir değere
kaynak bulunca o değer dosyadan çıkmaz, yalnızca varsayım olmayı bırakır.
Her birinin neye dayandığı kendi `provenance` alanıdır; bu da değerin bir
özelliğidir, içinde durduğu dosyanın değil.

Her girdi değerini, birimini, kaynağını, kaynağının kim olduğunu, neyi temsil
ettiğini söyleyen bir notu, neyi etkilediğini ve ölçülmüş olduğu yerde iki
katına çıkarmanın ne yaptığını taşır.

`src/` içindeki başka hiçbir şey bir tane kuramaz. Bir test her modülün
sözdizim ağacını gezer ve kodda yazılmış, ASSUMPTION işaretli bir `Sourced`
değer bulursa yapıyı düşürür. Sözcüğü değil kuruluşu arar, çünkü ASSUMPTION
ile karşılaştırmak, bir maliyetlendirmenin kendisinin ne kadarının bir
varsayıma dayandığını bildirmek için yapmak *zorunda* olduğu şeydir.

Kataloglar yazılmak yerine dosyadan kurulur: `world.mountings`,
`hardware.radios`, `ranging.clocks`, `cost.operating_rates`,
`scenarios.catalogue`. Modül düzeyindeki sabitler, o kurucuların gönderilen
dosya için döndürdükleridir; dolayısıyla zaten çalışan hiçbir şey değişmedi.

Bir değeri değiştirmek tek bir yerde üç düzenlemedir: değer, kaynak ve
provenance'ın ASSUMPTION'dan artık ne olduğuna geçmesi. Aşağıdaki her şey o
anda onu saymayı bırakır.

`yerkon defaults` geriye ne kaldığını listeler. Diğer her fiilde
`--defaults DOSYA`, bütün çalışmayı başka bir dosyaya karşı koşar.

## Sonuçlar
Bir sonucun tahmine dayandığını bildirdiği pay artık iddia edilmiyor,
dosyadan hesaplanıyor ve değerlere kaynak buldukça düşüyor. Yalnızca direk
maliyetine kaynak bulmak yerleşim cevabını yüzde doksan dört varsayımdan
yüzde altmış dokuza indiriyor.

Dosya iş listesidir ve modüle göre değil sonuca göre sıralıdır. Her birinin
üzerindeki duyarlılık satırı hangilerinin bir öğleden sonraya değdiğini
söyler.

Modelin daha önce cevaplayamadığı bir soruyu da cevaplattı. Direk maliyetini
8500 TL yap, mevcut levhalar hâlâ kazanıyor; 5000 yap, direkler on yedi
direkle 264906 TL'ye devralıyor. Maliyetlendirmenin 6588 TL'de öngördüğü
başabaş noktası artık birinin tek bir satırı düzenleyerek iki taraftan da
yürüyebileceği bir şey.

Fizik de oynuyor ve en çok önem taşıyan kısım o. Bir gürültü katsayısı bir
maliyet değildir ve onu yanlış almak çalışmadaki her bağlantıyı kısaltır.
Bir bakım ziyaretinin fiyatıyla aynı listede, çünkü aynı konumda: birisi
tahmin etti.

Hepsi görüntüleyici koşarken düzenlenebilir. Her değer, altında neyi
etkilediği yazılı olarak panelde görünür ve birini değiştirmek her şeyi ondan
yeniden kurar: montaj kataloğu, telsizler, saatler, oranlar, senaryolar. Link
bütçesini oynatan bir değer — bir montaj yüksekliği, bir gürültü katsayısı,
bir saat artığı — her ayar gibi aynı onay panelinden geçer; yalnızca bir
fiyatı oynatan hemen uygulanır.

Bir görüntüleyiciye yazılan sayı hâlâ bir tahmindir, dolayısıyla bir
düzenleme, yanında bir kaynak verilmedikçe ASSUMPTION kaynağını korur. Bu
ayrım keşfetmek ile raporlamak arasındaki farkın tamamıdır ve paneldeki
sayacın, ekrandakinin ne kadarının hiçbir şeye dayandığı konusunda doğruyu
söylemesi demektir.

Böyle bir öğleden sonrayı saklamaya değer, dolayısıyla görüntüleyici
düzenlenmiş dosyayı geri yazar. Yükleyicinin okuduğu şeklin aynısıdır,
dolayısıyla `--defaults` ile doğrudan geri girer.

Bunun yapmadığı şey varsayımları ortadan kaldırmaktır. Onları kodun bir
özelliği olmaktan çıkarıp sonlu, sıralı ve zorlanabilir bir liste yapar.
