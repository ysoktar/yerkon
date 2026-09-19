# 0013. Görüntüleyici üç boyutunu kendi çizer

## Durum
Kabul edildi.

## Bağlam
Görüntüleyici yerel bir web sayfası. Bir yükseklik alanını, birkaç direği ve
bir kapsama hücreleri ızgarasını üç boyutta çizmenin bariz yolu bir içerik
dağıtım ağından gelen bir WebGL kütüphanesidir ve ilk denenen de oydu.

Yüklenmedi. Bu projenin geliştirildiği ağ içerik dağıtım ağlarını
reddediyor; ve genel olarak bir saha ziyaretindeki makine, kurumsal bir
vekil sunucunun arkasındaki makine ve hiç bağlantısı olmayan makine de öyle
yapacaktır. Ağ yokken boş gri bir dikdörtgen gösteren bir görüntüleyici,
görüntüleyici değildir.

ADR-0008 zaten projenin bir kez getirip çevrimdışı koştuğunu söylüyor. Her
açılışta üçüncü bir tarafa uzanan bir sayfa, çalışmanın ihtiyaç duymadığı
bir kazanç için bununla çelişir.

## Karar
Görüntüleyici sahneyi kendi izdüşürüp kendi boyar; düz bir tuval üzerinde,
yaklaşık iki yüz satırda. Perspektif izdüşümü, boyacı algoritması, yüzey
normalinden düz gölgeleme ve bir direği sürüklemek için ışın-düzlem
kesişimi. Bağımlılık yok, kurulacak bir şey yok ve her makinede özdeş
davranış.

Direkler ölçekli değil, ekranda okunabilir bir uzunlukta çizilir. Yirmi dört
kilometrelik bir koridorun yanındaki yirmi beş metrelik bir direk bir
pikselden aza izdüşer ve onu dürüstçe boyamak, en çok önem taşıyan kontrolü
görülemez ve tutulamaz kılardı. Yüksekliği panelde bir sayı olarak
bildirilir; orada tahmin edilmek yerine okunabilir.

## Sonuçlar
Sahne bir WebGL sahnesinden basittir: gölge yok, yumuşak normaller yok, doku
yok. Çalışmanın göstermesi gerekeni gösterir: zeminin nerede yükseldiğini,
direklerin nerede olduğunu, her birinin ne kadar uzağa ölçtüğünü ve hangi
zeminde bir konum için yeterince direk bulunduğunu.

Boyama her karede değil etkileşimde yapılır, dolayısıyla birkaç bin yüzey
hiçbir şeye mal olmaz.

Sahne bir gün bir tuvalin etkileşimli hızda boyayabileceğinin ötesine
geçerse, çözüm birinin ağına bir bağlantı değil, paketin içine konmuş bir
kütüphane dosyasıdır.
