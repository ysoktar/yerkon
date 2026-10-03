# 0012. Hizmet alanı, bir konumun alınabildiği yerdir; bir paketin vardığı yer değil

## Durum
Kabul edildi. `CONTEXT.md`'deki **hizmet alanı** tanımını inceltir.

## Bağlam
Karşılaştırma tablosu maliyeti hizmet alanına böler, dolayısıyla neyin
hizmet verildiği sayıldığı kilometrekare başına maliyete karar verir. Yanında
durduğu GNSS satırları hizmet alanıyla, bir alıcının konumunu
belirleyebildiği zemini kastediyor.

`CONTEXT.md`, YERKON hizmet alanını direklerin eriştiği alanların birleşimi
olarak tanımlıyordu. Bir koridor yerleşiminde bu iki okuma birbirine yakın
bile değil. Yirmi beş metrelik direklerde her dört kilometrede bir direkle
gerçek bir tarama üzerinden ölçüldüğünde, bir direk 392,5 km²'ye, dört direk
15,2 km²'ye erişiyor. Birincisini bildirmek kilometrekare başına maliyeti
yirmi altı kat olduğundan az gösterirdi.

Fark bir yapaylık değil. Bir konum dört menzile ihtiyaç duyar. Bir direkten
kullanılabilir menzil, bir direkte yaklaşık beş buçuk kilometredir;
dolayısıyla bir direkten dört kilometre uzaktaki bir alıcı tipik olarak üç
direğin erişimindedir, yani bir eksik.

## Karar
Hizmet alanı, bir konum üretmeye yetecek kadar direğin kullanılabilir ölçüm
hassasiyetinde erişilebilir olduğu zemindir. Gerçek arazi üzerinde bir
ızgara taranarak ve her hücrede link bütçesine sorularak ölçülür; onu yolun
etrafına çizilmiş bir koridor değil, menzilin gerçekten kapsadığı alan yapan
da budur.

Ulaşılan alan yanında hesaplanır ve yanında bildirilir. İkisi asla
birbirinden ayrı yazdırılmaz, çünkü aralarındaki fark bulgunun kendisidir.

## Sonuçlar
Direk aralığı bir menzil sorusu olmaktan çıkıp bir geometri sorusu olur.
Dört kilometre telsizin erişiminin içinde ve bir konumun gerektirdiğinin
dışındadır; bir tarama üzerinden ölçüldüğünde aralığı bin beş yüz metreye
yarılamak hizmet alanını 15,2'den 75,2 km²'ye, medyan yatay hatayı 5,22'den
2,64 m'ye götürür.

Kilometrekare başına maliyet artık menzilin bir kısmında direk eklendikçe
düşer, çünkü örtüşme tamamlanana kadar her direk maliyetinden fazla hizmet
alanı ekler. Ulaşılan alanı kullanan bir model, kilometrekare başına
maliyeti tekdüze yükseliyor gösterir ve bunu gizlerdi.

`CONTEXT.md` buna uyacak şekilde değiştirildi. Önceki okuma silinmek yerine
burada kaydediliyor, çünkü ondan alıntılanmış bir hizmet alanı bir
mertebeden fazla yanlış olur ve biri hâlâ öylesine bir değerle
karşılaşabilir.
