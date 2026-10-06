# ADR-0026: eğim pürüzlülük değildir, eğik bir ayna da pürüzlü bir ayna değildir

## Durum

Kabul edildi.

## Bağlam

İstek, yansıtan zeminin bütün bir saha için tek bir sayı olmak yerine
yerden yere değişmesine izin vermekti: senaryo başına denetlenebilir, iki
ya da üç ölçekte, kendi tohumuyla. Onu kurmak altındaki iki hatayı
ortaya çıkardı ve önemli olan ikincisiydi.

**Eğim, pürüzlülük olarak sayılıyordu.** `_reflection_surface`, zeminin
saçılımını yansıtan yamanın *ortalama yüksekliği* etrafında ölçüyordu.
Bir yamaç bir yüzeydir, saçılım değil: %12 eğimli bir yama üzerinde bu
yöntem, zemin 7 cm'ye kadar düzgünken 2,8 m pürüzlülük bildiriyordu.
Kırk kat; ve düz olmayan her yerde Ament çarpanını sıfıra sürmeye yeter.

Böylece uyumlu yansıma her açık hava bağlantısında kapatılmıştı ve
yamalı desen onun altında görünmezdi — sahte 5,6 m'ye karşı 0,1 m'lik bir
değişim.

**Ve yalnızca eğilim gidermek, hatanın kendisinden kötü olurdu.** Eğim
kaldırıldığında eğik bir yama kusursuz bir aynaya dönüşürdü ve model,
fiziksel olarak üretemeyeceği bir zeminde temiz bir iki-ışın sıfırını
geri getirirdi. Ankara senaryolarında ölçüldüğünde, yansıtan yama
bağlantıların %84–96'sında bir iki derece eğiktir.

Eğik bir ayna bir ışını saçmaz. Onu başka bir yere nişanlar. Aynı
belirtiyi veren farklı bir fiziktir ve ikisini birbirine karıştırmak,
özgün hatanın bu kadar uzun süre yaşamasının sebebidir: aşağı yukarı
doğru cevabı üretiyordu.

## Karar

**Pürüzlülük, yamanın kendi düzlemi etrafında ölçülür.** Yansıma
penceresi boyunca bir doğru uydurulur ve artakalan pürüzlülüktür. `Site`
sınıfı zaten tam bu sebeple eğilim gideriyordu; bu da aynı şeydir,
yansımanın olduğu yerde yapılmış.

**Eğiklik ayrı bir terimdir: `aimed_fraction`.** τ kadar eğik bir yüzey
yansıyan ışını 2τ kadar savurur; bu, ışını ilk Fresnel yarıçapına karşı
epeyce kaydırıyorsa, ışın bir şeyi sönümleyemeyecek kadar uzağa varır.
Yumuşak bir geçişle azaltılır, çünkü bir kuşak kenarı bir duvar
değildir.

Bunu doğru yapmak bir düzeltme daha gerektirdi. İlk sürüm yansımayı orta
noktaya koyuyordu ve orada değildir: 1,5 m'deki bir alıcıyla konuşan 25
m'lik bir direk yansımayı yolun %93'üne koyar; alıcıdan kilometrelerce
değil birkaç yüz metre uzağa, dolayısıyla savrulan ışının sapmak için
çok daha az yeri olur. Orta noktayı varsaymak, tam da bu çalışmanın
kurulu olduğu geometride kaçma miktarını yedi kat abartıyordu.

**Ve yamalı desenin kendisi.** `Patchwork`, pürüzlülüğü iki ya da üç
ölçekte, senaryo başına ve ölçüm tohumundan ayrı tutulan kendi tohumuyla
konumun bir işlevi yapar. İki özellik önemlidir:

*O, yer hakkında bir olgudur, bir çekiliş değil.* Aynı noktadan aynı
direğe menzil ölçen bir alıcı her seferinde aynı zeminle karşılaşır.
Gürültü olarak çekilseydi bir tur boyunca ortalamada sönerdi; konumdan
çekildiğinde sönmez — ondan önceki ölçüm hatası ve fazla yol gibi
(ADR-0019). Karma, Python'unki yerine kararlı bir karışımdır; Python'unki
süreç başına tuzlanır ve iş yayıldığı anda farklı işçilerde farklı zemin
verirdi (ADR-0025).

*Sahanın pürüzlülüğünü ölçtüğü şey olarak bırakır.* Çarpanlar ortalama
değil ortalama kare üzerinde ortalanır, çünkü pürüzlülük denkleme karesi
üzerinden girer. Katman eklemek zemini pürüzlendirmez, aynı varyansı daha
ince böler.

## Sonuçlar

**Tablo neredeyse kımıldamadı.** Şehir içi 1,64 → 1,62 m, kırsal 2,71 →
2,69, tünel 1,81 → 1,77, ağırlıklı 2,02 → 1,93. Zemin fiziğinde üç
düzeltme ve yayımlanan figürler eskiden bulundukları yerin tohum
gürültüsü içinde, çünkü eski model aynı yere yanlış yoldan varıyordu:
uyumlu yansımayı bir eğime pürüzlü diyerek öldürüyordu, yenisi ise bir
eğime doğru biçimde eğik diyerek öldürüyor.

Bu, iki modelin de aynı dünyayı anlattığına ve ikisinden yalnızca
birinin nedenini söyleyebildiğine dair elimizdeki en iyi kanıttır.

**Değişen şey, hangi satırın yansımasını koruduğu.** Tünel gerçek bir
düzlemdir, dolayısıyla uyumlu payı 0,17'den 0,73'e çıktı ve oradaki
iki-ışın sönümlemesi artık gerçek. Açık havada sıfıra yakın kalıyor. Ders
kitabındaki iki-ışın sıfırlarının hava alanları ve durgun sular üzerinde
çıkıp kırlar üzerinde çıkmamasının sebebi budur ve model artık bunu doğru
sebeple söylüyor.

**Yamalı desen bu üç senaryoda hiçbir şeyi değiştirmiyor ve bu bir
eksiklik değil bir bulgudur.** Açık havada ışın, pürüzlülük ne olursa
olsun başka yere nişanlanır. Tünelde taban, o sıyırma açısında metrelerle
ölçülen bir ölçüte karşı 2 cm saçılımdır — optik olarak düzgün, yani onu
değiştirmek bir şey yapmaz. Düz *ve* pürüzlü zeminde önemli olurdu:
üzerinde kar olan bir pist, sürülmüş bir ova, donmuş bir göl. Bir sınama
bu boş sonucu sebebiyle birlikte sabitler, böylece onu gerçekten
çalıştıran bir senaryo sessizce geçmek yerine fark edilir.

**Sayfa artık her yeri indirebiliyor.** Bu projede ağa dokunan tek şey,
aynı zamanda görüntüleyicinin yapamadığı tek şeydi; yani dört Ankara
sahasının dışında bir yer kullanmak bir uçbirime inmek demekti. Ana giriş
yolu olması amaçlanan bir görüntüleyici için bu bir delikti.
