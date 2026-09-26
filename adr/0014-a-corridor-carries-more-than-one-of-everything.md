# 0014. Bir koridor her şeyden birden fazlasını taşır

## Durum
Kabul edildi. Tek telsizli yerleşimin yerine geçer.

## Bağlam
Model bir yerleşime bir direk modülü ve bir alıcı veriyordu; rapor ise
ikisini de böyle anlatmıyor.

Malzeme listesi üç direk modülünün adını veriyor ve onları üç yere
atıyor: şehirler için yayılı bir modül, açık arazi için bir yükselticinin
arkasındaki aynı silikon, tüneller için darbeli bir telsiz. Gerçek bir
koridor bir şehirden çıkar, açık araziyi geçer ve bir tünelden geçer;
dolayısıyla üçünü birden taşır ve tablonun tek bir satırı bile o düzeni
ölçmez.

Aynı listedeki iki alıcı da ikişer telsiz taşıyor. "Yaya alıcısı: SX1280,
DWM3000, ESP32-S3…" ve "Kara aracı alıcısı: SX1280, DWM3000, STM32…". Bu
yedeklilik değil; bir birimin yolda şehir direkleriyle, tünelin içinde
tünel direkleriyle, birimde hiçbir şey değişmeden ölçmesini sağlayan şey.

Ve bir yerleşim tek bir araca değil trafiğe hizmet eder.

## Karar
Telsiz direğe aittir. Bir yerleşim hangi türlerle kurulduysa o türden
direkleri, hangi modüllerle kurulduysa o modülleri taşıyan birimleri tutar.
Bir birim, dalga formunu paylaştığı her direkle ölçer ve gerisini sessizce
yok sayar; donanımın yaptığı da budur.

Birimler havayı paylaşır. Bir tur, her birimin alışverişlerinin uç uca
dizilmesi kadar uzundur; dolayısıyla ikinci bir birim işi yarıya indirmez,
beklemeyi ikiye katlar.

Görüntüleyici direkleri *grup* olarak düzenler — tek bir montaj üzerinde tek
bir modülü tek bir aralıkta taşıyan bir koridor kesimi — çünkü bir ağ böyle
belirtilir ve böyle kurulur. Birkaç grup üst üste binebilir.

## Sonuçlar
Kapasite kısıtı görünür oldu ve ağır. Şehirde on altı direk ve iki birim
1018 ms'lik bir tur eder, yani her birim saniyede bir kez konumlanır. Birim
eklemek sabitleme eklemez: bir yolculuk boyunca ölçüldüğünde iki birim
toplamda birinin denediği kadar tur deniyor. Hava zaten tamamen
harcanmıştı.

Bunun bedeli hemen hassasiyetten çıktı. Şehir içi HPE medyanda tek birimle
3,35 m'den iki birimle 5,06 m'ye çıktı, çünkü her süzgeç artık güncellemeler
arasında iki katı kadar boşta süzülüyor. Bu bir gerileme değil; ilk dürüst
değer, ve öncekisi tek müşterisi olan bir ağı anlatıyordu.

Paylaşılan bir ayar artık her şeyi oynatmıyor. Bölgeyi değiştirmek yayılı
grupların tavanını yükseltir ve darbeli olanınkini hiç oynatmaz, çünkü bir
ultra geniş bant sınıflandırması zaten iletilen güç değil bir yayım
sınırıdır. Onay paneli değişen grupları gösterir ve değişmeyen hakkında
susar.

Türk kuralı altında şehir içi modülü kırsal olanla değiştirmek hiçbir şeyi
değiştirmez, dolayısıyla panel hiç çıkmaz. Bu link bütçesinden zaten
biliniyordu; artık birinin deneyeceği yerde görünür.

## Ek, 2026-09-10: yalnızca tünel bir koridordur

Üç senaryo da koridor olarak kurulmuştu — tek eksende bir direk dizisi ve
onun boyunca doğuya giden bir alıcı — çünkü yazılan ilki bir karayoluydu ve
diğer ikisi ondan kopyalanmıştı. Bu, ikisi için yanlıştı ve hata küçük
değildi.

Bir şehir bir alandır. Bir açık arazi kesimi bir alandır. Direkleri kaba bir
sokak ızgarasında ya da zemine yayılmış direklerde durur ve ikisinde de bir
araç döner. Bunları çizgi olarak modellemek, bir alıcının duyabildiği her
direğe neredeyse aynı kerterizi veriyordu; bu da bir koridorun enine
doğrultusunu zar zor gözlenebilir kılan geometridir ve yatay hata, dosyanın
şeklinden başka hiçbir sebep olmadan o büyütmeyi miras alıyordu.

Şehir içi artık bir kenarı üç kilometre olan bir şehir: beş yüz metrelik bir
ızgarada aydınlatma direklerinde kırk altı direk, ardışık sıralar kaydırmalı.
Kırsal bir kenarı yirmi kilometre: dört kilometrelik bir ızgarada otuz üç
direk. İkisi de çevreyi dolaşıp ortadan geçen bir turda sürülüyor, böylece
birim döndükçe enine geometri değişiyor. Tünel değişmedi, çünkü bir tünel
gerçekten bir çizgidir.

Neyi oynattı: şehir içi HPE ellinci yüzdelikte 5,31 m'den 1,24 m'ye, kırsal
4,22 m'den 2,14 m'ye ve kırsal hizmet alanı 58 km²'den 372,50 km²'ye; bu da
kilometrekare başına sermaye maliyetini 21424 TL'den 8468 TL'ye götürdü.
Hassasiyette dört kat, maliyette iki buçuk kat; hiçbiri fizikteki bir
değişiklikten değil.

Bunu iki sonuç izler. Bir alan üzerindeki bir alıcı, ölçmeye vakti
olduğundan çok daha fazla direk duyabilir, dolayısıyla `Deployment`
`max_anchors_per_round` kazandı: en yakın sekiziyle ölçer ve gerisini yok
sayar — gerçek sistemlerin yaptığı ve bir turun iki saniye sürmesini
engelleyen şey budur. Ve `Deployed.serves_a_corridor` artık güzergâh
kilometresi başına maliyetin hiç yazdırılıp yazdırılmayacağına karar veriyor
— bir alan için o güzergâh kilometreleri hizmetin bir boyutu değil bir test
yolculuğunun uzunluğudur ve birini diğeri diye bildirmek bütün bunu ilk
etapta davet eden şeydi.
