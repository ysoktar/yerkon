# ADR-0080: simülatör ziyaretçinin tarayıcısında çalışıyor

## Durum

Kabul edildi. ADR-0065'in "Simülatör gelmiyor" kararının yerine geçiyor.

## Bağlam

Yayımlanan site bir klasör dosya (ADR-0065). "Simülasyonu çalıştır"
düğmesi orada simülasyonu açmıyor, simülasyonun nasıl kurulacağını
anlatan sayfaya gidiyordu. İstenen: düğme simülasyonu doğrudan açsın, ve
hesap ziyaretçinin bilgisayarında yapılsın ki ne bir sunucu ne de GitHub
Actions bu işi taşısın.

Paketin tek bağımlılığı numpy. Pyodide, CPython'un WebAssembly'e
derlenmiş hâli, ve numpy'ı hazır taşıyor.

## Karar

**Motor bir Web Worker'da, Pyodide ile.** `sim-worker.js` Pyodide'ı
jsdelivr'dan yüklüyor, numpy'ı ekliyor, `yerkon.zip`'i açıyor ve
`yerkon.viewer.server.answer`'ı çağırıyor. Worker, çünkü bir koşu
saniyeler sürüyor ve sayfa o arada çizmeye devam etmeli. Modül Worker,
çünkü Pyodide 314 klasik Worker'da açılmayı reddediyor (bu, sınamada
yakalandı: "Classic web workers are not supported").

**Aynı işleyici, soketsiz.** `answer(method, path, body)` sunucunun
`Handler` sınıfını olduğu gibi kullanıyor; yalnızca baytların gittiği
yer değişiyor. Tarayıcıdaki simülatör ile yerel kurulumdaki aynı soruya
iki farklı cevap veremez.

**Sayfa aynı sayfa.** `calistir.html`, sunucunun gönderdiği
`simulator.html`'in kendisi: yalnızca mutlak adresler göreli yapılıyor
(site `/yerkon/` altında duruyor) ve `app.js`'ten önce `local.js`
yükleniyor. `local.js` `fetch`'i değiştiriyor: `/api/` ile biten her
istek Worker'a gidiyor. Ayar dosyasını indirme bağlantısı da oradan
yapılıyor.

**Tarayıcıda iş parçacığı ve süreç yok.** `jobs.py` işi olduğu yerde
koşturuyor, `parallel.py` tek süreçte kalıyor. Worker zaten sayfanın
dışında olduğu için sayfa donmuyor.

**Arşiv belirlenimci.** `yerkon.zip` sıralı, sabit tarihli; paket
değişmedikçe aynı baytlar. Önbellekler, ham arazi döşemeleri (`_tiles`,
93 MB, yalnızca yeni saha indirirken gerekli) ve sunucunun statik
dosyaları içinde yok: 3,1 MB.

## Doğrulananlar

- `answer()` sunucuyla aynı cevapları veriyor (sınama).
- Arşiv, depo dışında, yalnızca kendisinden içe aktarılıp cevap
  veriyor (sınama, taze bir yorumlayıcıda).
- Python 3.14 ve numpy 2.4.6 ile (Pyodide'ın kullandığı sürümler),
  iş parçacığı ve süreç kapalıyken arşivden açılan paket sahneyi,
  şehir içi simülasyonunu (ilk çekiliş 21 s), sekme ve dil değişimini
  doğru yaptı.
- Chromium'da `calistir.html`, `local.js` ve `app.js` birlikte, aynı
  mesaj düzeniyle konuşan bir Worker üzerinden sahneyi, sekmeleri ve
  sonuç panelini çizdi; sayfa hatası yok; Türkçe ve İngilizce açılış
  doğru; geri bağlantılar doğru.
- Gerçek Worker Chromium'da Pyodide'ı açtı, Python 3.14 WebAssembly'de
  çalıştı, arşivi indirip açtı.

## Doğrulanamayan

**Numpy'ın CDN'den inmesi ve modelin WebAssembly'de koşması burada
denenemedi.** Bu oturumun ağ politikası jsdelivr'ı kapatıyor ve
numpy'ın WebAssembly derlemesi başka bir yerden alınamıyor. Worker
numpy'ı yükleyemeyince ekranda bunu açıkça yazıyor ("numpy could not be
loaded"), sessizce takılmıyor. Yayından sonra bir tarayıcıda açılıp
denenmesi gereken tek adım bu.

**Hız.** Tarayıcıda tek işlemci ve WebAssembly var; bir koşu yerel
kurulumdakinden yavaş. İlk açılış yaklaşık 20 MB indiriyor.

## Yapılmayanlar

Hava fotoğrafı tarayıcıya gönderilmiyor; istenirse 404 dönüyor ve sahne
fotoğrafsız çiziliyor. Yeni bir saha indirmek (`fetch`) tarayıcıda
çalışmaz, çünkü rasterio ve pyarrow istiyor; yerel kurulumda kalıyor.
