# 0002. Menzil bir sonuçtur, bir sabit değil

## Durum
Kabul edildi. Önceki kod tabanının sabit link menzillerinin yerine geçer.

## Bağlam
Önceki kod tabanı erişilebilirliğe üç elle yazılmış sayıdan karar
veriyordu: şehir içi 400 m, kırsal 3000 m, tünel 150 m. Ölçüm hatasını
ölçeklemek için ayrıca bir sinyal-gürültü oranı hesaplıyordu. İkisi
birbiriyle çelişiyordu. Anten kazancındaki bir değişiklik ölçüm hatasını
oynatıyor, erişilebilirliğe dokunmuyordu; yani hiçbir anten ya da arazi
değişikliği düğüm sayısını ve maliyeti hiç değiştiremiyordu.

Rapor stok antenleri parça numarasıyla belirtiyor ve yerleşimin 5–10 km'lik
bağlantılara ihtiyacı var, 15 km'ye kadar değerlendirilmek üzere. O
bağlantıların kapanıp kapanmadığı çalışmadaki en sonuçlu tek sorudur, çünkü
düğüm sayısını, o da sermaye maliyetini belirler.

## Karar
İkisine de tek bir fonksiyon karar verir. İki telsiz, antenleri, montaj
geometrisi, aralarındaki arazi ve kanal verildiğinde bir link bütçesi
döndürür: alınan güç, gürültü, sinyal-gürültü oranı ve bunlardan çıkan varış
zamanı varyansı.

Bir bağlantı, sinyal-gürültü oranı telsizin yapılandırmasının çözme eşiğini
geçtiğinde kapanır. Aynı bütçe, bağlantının taşıdığı her ölçümün varyansını
ve bir paketin kaybolma olasılığını da belirler. Azami menzil sabiti yoktur.

## Sonuçlar
Anten kazancı, montaj yüksekliği, arazi engeli, verici gücü ve ölçüm bant
genişliği artık düğüm sayısını, hassasiyeti ve maliyeti birlikte oynatır —
çalışmanın ihtiyaç duyduğu davranış budur.

Uzun bağlantılar artık varsayılmak yerine gerekçelendirilmek zorunda. 2,4
GHz'de 10 km'lik bir bağlantı, arazinin vermeyebileceği bir Fresnel
açıklığına ihtiyaç duyar ve bütçe bunu söyler.
