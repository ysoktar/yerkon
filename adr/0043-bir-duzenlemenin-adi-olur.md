# ADR-0043: bir düzenlemenin adı olur

## Durum

Kabul edildi.

## Bağlam

Bir sekme baştan sona bir etüt: üzerinde durduğu zemin, sahanın boyu ve
eni, bütün direk dizileri ve alıcılar, elle taşınmış ve silinmiş
direkler, ve sevk edilen dosyadan elle değiştirilmiş her değer. Bunu bir
sürgüye kaptırmak, sekmelerin var olma sebebiydi (ADR-0028) — ama üçünü
bellekte tutmak problemi yalnızca sürecin bittiği ana erteliyor.

## Karar

**Bir düzenlemenin adı olur.** Her satır için *varsayılan* ve *boş* iki
tane hazır gelir; ikisinden birinden başlayıp kurulan her şey kendi
adıyla kaydedilebilir. Yüklemek o sekmenin yerine geçer, ötekilere
dokunmaz: satırlar ayrı etütler ve hep öyleydi.

**Çalışılan klasöre, `presets/` içine.** `defaults.toml` ile aynı mantık:
etütle birlikte tutulan, depoya işlenen, başkasına verilen şey. Paketin
içinde bir klasör yeniden kurulumda giderdi. Hiçbir şey kaydedilene
kadar hiçbir şey yazılmaz.

**Boş, boş bir sayfa; boş bir tahta değil.** Şehir içi satırı Kızılay'ın
üzerinde duruyor, tünel satırı dağın içinden geçiyor; boş şehir içi
düzenlemesini yükleyen kişi şehir içi düzenlemesi kuracak, şehir içi
zemininde. Yani boş olan, üzerinde *duran* şeyler: diziler, alıcılar,
elle taşınanlar, elle silinenler, elle değiştirilen değerler. Satırdan
türetiliyor, o an yüklü olandan değil — yoksa "boş" her yüklenişinde
başka bir şey olurdu. (İlk hâli öyleydi.)

**Preset yayımlanan tabloyu da sürebilir.** `yerkon table --preset`
sevk edilen senaryo yerine kaydedilmiş bir düzenlemeyi koşturur. Bunun
bir bedeli var ve ödendi: yazılan satır artık birinin kaydettiği bir
dosyaya dayanıyor, o yüzden **hangi dosya ve onun hangi hâli** künyeye
giriyor. `digest` bunun için — `konya` adlı bir preset iki koşu arasında
değiştirilseydi, iki farklı tablo aynı künyeyle basılırdı, ki bu tam
olarak bu projenin var olma sebebi olan izlenemez sayıdır (ADR-0001).

Hash, dosyanın baytlarının değil **kanonik JSON'un** üzerinden: yeniden
biçimlendirme, anahtar sırası ya da sondaki bir satır sonu başka bir
düzenleme gibi okunmamalı.

**Preset, kaydedildiği satır olarak koşar.** Satırın kendi `name`'i
koşunun dilinde bir cümle ("Kırsal" / "Rural"), o yüzden eşleştirme
anahtarla yapılıyor — başlıkla yapsaydı Türkçede çalışır, İngilizcede
sessizce çalışmayı bırakırdı.

**Yüklemek geri getirir, düzeltmez.** Yalnızca `on_measured_ground()`
uygulanıyor: bir saha ölçülen zeminden büyük olamaz, yoksa direkler
kimsenin almadığı bir sayının üzerinde durur (ADR-0037). `within_site()`
uygulanmıyor, çünkü bu proje bir dizinin elle yazılan ucunun *kasten*
yazıldığına zaten karar vermişti. İkisinden birini burada yapıp orada
yapmamak, aynı düzenlemenin dosyadan gelince başka anlama gelmesi
demek — ve zaten öyle oldu (aşağıya bak).

**Bir cümle ve bir evet/hayır, aynı panelden.** Düzenleme yüklemek de bir
değişiklik ve aynı "ne olacak, evet de" muamelesini hak ediyor
(ADR-0009) — ama bir sekmenin tamamının yerine geçiyor, ve kırk satırlık
bir fark listesi tek bir cümleden az şey söylüyor.

## Sonuçlar

Tarayıcıda yürüdüm: boş yükle → 0 direk, Kızılay zemini, çökme yok;
dizi ekle → 9 direk; `benimki` diye kaydet; varsayılana dön → 36 direk,
gerçek zemin; kendi düzenlememe dön → 9 direk. Hazır gelen ikisi üzerine
yazılmayı ve silinmeyi reddediyor.

Komut satırında da koştu: kırsal satırı, direk aralığı yarıya indirilmiş
bir düzenlemeden **105 direkle** koştu (sevk edilen hâlinde ~53), ve
künye düzenlemenin adını, yolunu ve içerik hash'ini yazdı.

**Boş bir düzenleme yüklenemiyordu.** "Direk yok" hatası `anchors()`
içindeydi, yani üzerinde hiçbir şey olmayan bir sekme *çizilemiyordu* —
ve üzerine bir şey kurulacak boş sayfa tam olarak budur. Hata doğruydu
ama yanlış katmandaydı: çizmek boşu kabul eder, bir sayı üretmek etmez.
Artık `deployment()`, `scenario_object()` ve `deployed()` reddediyor;
`scene()` ve `sweep()` boş bir sayfa çiziyor. Sınama, ikisini birden
çiviliyor.

**İki hata daha, ikisi de bu yüzden görüldü.** Bir düzenleme 12 direkle
kaydedilip 9 ile geri geldi:

- *Yükleme* `within_site()` uyguluyordu, yani geri getirmek yerine
  sessizce düzeltiyordu. Kaldırıldı.
- *"Grup ekle"* sahanın uzunluğuna bakmadan 3000 m'ye uzanan bir dizi
  kuruyordu. Kızılay 2970 m; yani yeni grubun son sütunu sahanın otuz
  metre dışında duruyordu ve hiçbir şey yükselmiyordu — arazi kendi
  dışında kırpar, dolayısıyla direkler sınır satırının bir düzleme
  uzatılmışının üzerinde duruyordu (ADR-0037). Artık sahanın ucunda
  duruyor.

Yuvarlak-gidiş sınaması sunucunun *gerçek* yükleme yolundan geçiyor.
Kırpmayı kasten geri koyup denedim: sınama düştü.

**Bir paketleme hatası daha yakalandı** — ADR-0042'deki gibi. Bu sefer
kod değil, sınamanın kendisi: ilk yazdığım yuvarlak-gidiş sınaması
sunucunun kodunu değil benim kopyaladığım mantığı sınıyordu, yani
sunucudaki bir gerilemeyi göremezdi. Gerçek işleyiciden geçecek şekilde
yeniden yazıldı.

## Sonraki adımlar

Sinyal renklendirmesi ve alıcı güzergâhları. Yol kenarı donanımı
Overture'ın `transportation` katmanını bekliyor (ADR-0040).
