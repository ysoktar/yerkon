# Karar kayıtları (ADR)

Her dosya bir kararı, gerekçesini ve o günkü sayıları tutar. Sayılar
kararın verildiği günün modeline aittir; bugünkü değerler sitede ve
`src/yerkon/published.toml` dosyasında. Yerini başka bir karara bırakmış
kayıtlar geçmiş olarak duruyor; aşağıdaki "Durum" sütunu hangisinin
geçerli olduğunu söylüyor.

Biçim: `.claude/skills/domain-modeling/ADR-FORMAT.md`.

| ADR | Karar | Durum |
|---|---|---|
| [0001](0001-one-engine-many-front-ends.md) | Tek motor, birçok ön yüz | Geçerli |
| [0002](0002-range-is-an-outcome.md) | Menzil bir sonuçtur, bir sabit değil | Geçerli |
| [0003](0003-the-estimator-sees-only-observations.md) | Kestirici yalnızca gözlemleri görür | Geçerli |
| [0004](0004-roads-have-grade.md) | Yolların eğimi vardır | Geçerli |
| [0005](0005-the-weighted-row-combines-samples.md) | Ağırlıklı satır yüzdelikleri değil örnekleri birleştirir | Yerini aldı: ADR-0068 |
| [0006](0006-opex-from-an-inventory.md) | OPEX bir envanterden gelir, bir yüzdeden değil | Geçerli |
| [0007](0007-ground-reflection-dominates.md) | Zemin yansıması, ve erişmek ile ölçmek arasındaki fark | Geçerli |
| [0008](0008-fetch-once-run-offline.md) | Saha verisi bir kez önbelleğe getirilir, sonra çevrimdışı okunur | Geçerli |
| [0009](0009-changes-are-confirmed-as-a-batch.md) | Bir değişiklik ve zorladığı her şey birlikte onaylanır | Geçerli |
| [0010](0010-the-clock-is-part-of-the-ranging-error.md) | Saat, ölçüm hatasının parçasıdır ve ne kadarına alışveriş karar verir | Geçerli |
| [0011](0011-the-vertical-is-unobservable-from-a-road.md) | Düşey, bir yoldan gözlenemez ve cevap budur | Yerini aldı: ADR-0088 |
| [0012](0012-service-area-is-where-a-position-is-available.md) | Hizmet alanı, bir konumun alınabildiği yerdir; bir paketin vardığı yer değil | Geçerli |
| [0013](0013-the-viewer-carries-its-own-renderer.md) | Görüntüleyici üç boyutunu kendi çizer | Geçerli |
| [0014](0014-a-corridor-carries-more-than-one-of-everything.md) | Bir koridor her şeyden birden fazlasını taşır | Geçerli |
| [0015](0015-siting-searches-structures-not-parameters.md) | Yerleşim araması değiştirgeleri değil yapıları arar | Geçerli |
| [0016](0016-defaults-live-in-a-file.md) | Raporun vermediği her değer tek bir dosyada durur | Geçerli |
| [0017](0017-a-threshold-belongs-to-the-ratio-it-is-quoted-on.md) | Bir çözme eşiği, üzerinde verildiği orana aittir | Geçerli |
| [0018](0018-the-first-figure-to-stop-being-a-guess.md) | Tahmin olmayı bırakan ilk değer | Geçerli (yorumu ADR-0105'te) |
| [0019](0019-three-errors-that-do-not-average-out.md) | Ortalamayla kaybolmayan üç hata | Geçerli |
| [0020](0020-an-error-figure-nobody-can-act-on.md) | Kimsenin üzerine iş yapamayacağı bir hata değeri yarım sonuçtur | Geçerli |
| [0021](0021-nowhere-is-flat.md) | Hiçbir yer düz değildir ve bir düzlem tarafsız seçenek değildir | Geçerli |
| [0022](0022-size-the-round-by-who-answers.md) | Turu, bir sabitlemenin kaç direğe ihtiyaç duyduğuna göre değil kaçının cevap verdiğine göre boyutla | Yerini aldı: ADR-0072, ADR-0085, ADR-0099 |
| [0023](0023-a-deployment-is-a-file-not-a-decision-in-code.md) | Yerleşim bir dosyadır, koda gömülmüş bir karar değil | Geçerli |
| [0024](0024-anything-worth-doing-is-doable-without-a-terminal.md) | Yapmaya değer her şey uçbirim olmadan da yapılabilir | Geçerli |
| [0025](0025-a-closure-is-what-kept-this-on-one-core.md) | Bunu tek çekirdekte tutan şey bir kapanıştı | Geçerli |
| [0026](0026-a-slope-is-not-roughness.md) | Eğim pürüzlülük değildir, eğik bir ayna da pürüzlü bir ayna değildir | Geçerli |
| [0027](0027-a-figure-can-be-a-name.md) | Bir figür bir ad olabilir ve hiçbir şeyi değiştirmeyen seçenek bir yalandır | Geçerli |
| [0028](0028-three-rows-held-at-once.md) | Üç satır aynı anda tutulur, biri girip çıkmaz | Geçerli |
| [0029](0029-the-camera-was-aimed-at-sea-level.md) | Kamera deniz seviyesine nişanlanmıştı | Geçerli |
| [0030](0030-one-depth-per-thing-is-not-enough.md) | Şey başına tek derinlik yetmiyor | Geçerli |
| [0031](0031-the-ground-you-are-looking-at.md) | Baktığın zemin | Geçerli |
| [0032](0032-two-sliders-that-did-not-mean-the-same-kind-of-thing.md) | Aynı türden şey anlatmayan iki sürgü | Geçerli |
| [0033](0033-the-pan-was-a-loop-through-the-terrain.md) | Kaydırma, araziden geçen bir döngüydü | Geçerli |
| [0034](0034-a-panel-in-the-order-somebody-works.md) | Birinin çalıştığı sırada bir panel | Geçerli |
| [0035](0035-two-languages-beside-each-other.md) | Iki dil, yan yana | Geçerli |
| [0036](0036-a-control-that-does-nothing-is-not-a-control.md) | Hiçbir şey yapmayan bir denetim, denetim değildir | Geçerli |
| [0037](0037-a-study-stops-where-the-measurement-stops.md) | Çalışma, ölçümün bittiği yerde biter | Geçerli |
| [0038](0038-buildings-by-the-other-road.md) | Binalar, öteki yoldan | Geçerli |
| [0039](0039-a-region-somebody-else-can-add.md) | Başkasının da ekleyebileceği bir bölge | Geçerli |
| [0040](0040-a-placement-is-a-choice-with-a-name.md) | Yerleştirme, adı olan bir seçimdir | Geçerli |
| [0041](0041-bir-fotograf-veri-degildir.md) | Bir fotoğraf veri değildir | Kısmen yerini aldı: ADR-0086 |
| [0042](0042-bir-yeri-secmek-yazmak-degildir.md) | Bir yeri seçmek, koordinat yazmak değildir | Geçerli |
| [0043](0043-bir-duzenlemenin-adi-olur.md) | Bir düzenlemenin adı olur | Geçerli |
| [0044](0044-sweep-zaten-biliyordu.md) | Tarama zaten biliyordu | Geçerli |
| [0045](0045-bir-guzergah-da-bir-secimdir.md) | Bir güzergâh da bir seçimdir | Geçerli |
| [0046](0046-yollar-ve-yanlarindaki-yapilar.md) | Yollar ve yanlarındaki yapılar | Kısmen yerini aldı: ADR-0097 |
| [0047](0047-aramanin-citasi-bir-sayinin-uc-kopyasiydi.md) | Aramanın çıtası bir sayının üç kopyasıydı | Kısmen yerini aldı: ADR-0057 |
| [0048](0048-kol-bir-sey-soyluyordu-saha-baskaydi.md) | Kol bir şey söylüyordu, saha başkaydı | Geçerli |
| [0049](0049-bir-direge-kimin-diktigini-sormak.md) | Bir direği kimin diktiğini sormak, onu yeniden dikmektir | Geçerli |
| [0050](0050-hesaplanan-bir-sayi-eski-sayi-degildir.md) | Hesaplanan bir sayı, eski sayı değildir | Geçerli |
| [0051](0051-indiremeyen-kurulum-bunu-basta-soyler.md) | Indiremeyen bir kurulum bunu baştan söyler | Yerini aldı: ADR-0087 |
| [0052](0052-haritadan-gelen-kutu-bir-dikdortgendir.md) | Haritadan gelen kutu bir dikdörtgendir, kol bir sayı tutar | Geçerli |
| [0053](0053-bir-yol-tek-bir-engel-degildir.md) | Bir yol tek bir engel değildir | Geçerli |
| [0054](0054-kirpmak-yalnizca-kucultur.md) | Kırpmak yalnızca küçültür | Geçerli |
| [0055](0055-bir-kosu-bir-cekilistir.md) | Bir koşu bir çekiliştir | Geçerli |
| [0056](0056-bir-arama-uc-sebeple-durur.md) | Bir arama üç sebeple durur, ikisi sonuç değildir | Geçerli |
| [0057](0057-sekiz-bant-bir-olcum-degildi.md) | Sekiz bant bir ölçüm değildi | Geçerli |
| [0058](0058-bir-yer-parcasi-bir-kez-odenir.md) | Bir yer parçası bir kez ödenir | Geçerli |
| [0059](0059-sayfa-tek-cekilis-gosteriyordu.md) | Sayfa tek çekiliş gösteriyordu | Geçerli |
| [0060](0060-cita-tutmak-calistigi-anlamina-gelmez.md) | Çıta tutmak çalıştığı anlamına gelmez | Geçerli |
| [0061](0061-golgenin-genisligi-yola-bagli.md) | Gölgenin genişliği yola bağlı | Geçerli |
| [0062](0062-kac-metrede-bir-okundugu-zeminin-ozelligi.md) | Bir yolun kaç metrede bir okunduğu zeminin özelliği | Geçerli |
| [0063](0063-denemek-icin-kaba-okuma.md) | Denemek için kaba okuma | Geçerli |
| [0064](0064-simulatorun-onunde-bir-site.md) | Simülatörün önünde bir site | Yerini aldı: ADR-0067 |
| [0065](0065-dosya-olarak-duran-site.md) | Dosya olarak duran site | Kısmen yerini aldı: ADR-0080 |
| [0066](0066-pnt-demiyoruz.md) | PNT demiyoruz | Geçerli |
| [0067](0067-site-raporun-sitesi.md) | Site raporun sitesi, benzetim onun bir sayfası | Geçerli |
| [0068](0068-agirlikli-satir-kalkti.md) | Ağırlıklı satır kalktı | Geçerli |
| [0069](0069-tablonun-tamami.md) | Tablonun tamamı sitede | Kısmen yerini aldı: ADR-0070 |
| [0070](0070-kaynak-baglantilari.md) | Kaynak bağlantıları | Geçerli |
| [0071](0071-sitenin-dili.md) | Sitenin dili | Geçerli |
| [0072](0072-iki-ayari-yeniden-olctuk.md) | Iki yerleşim ayarını yeniden ölçtük | Yerini aldı: ADR-0085, ADR-0099 |
| [0073](0073-tunel-uzunluga-bolunur.md) | Tünel satırı uzunluğa bölünür | Geçerli |
| [0074](0074-tabloyu-cizmek.md) | Tabloyu çizmek | Geçerli |
| [0075](0075-slayta-gore-senkron.md) | Siteyi slayta göre senkronlamak | Geçerli |
| [0076](0076-simulator-tabloyu-uretmeli.md) | Simülatör tabloyu üretebilmeli | Geçerli |
| [0077](0077-sehrin-kendi-sebekesi.md) | Şehrin direkleri zaten elektrikli ve bir kısmı zaten bağlı | Geçerli |
| [0078](0078-karsilastirma-23-eylul.md) | Karşılaştırma tablosu 23 Eylül belgesine göre | Geçerli |
| [0079](0079-en-ucuz-hali.md) | Her parça ve her varsayım, en ucuz hâliyle | Fiyat yöntemi yerini aldı: ADR-0105 |
| [0080](0080-simulator-tarayicida.md) | Simülatör ziyaretçinin tarayıcısında çalışıyor | Geçerli |
| [0081](0081-yoneylem-yerlesimi.md) | Direkler zaten yüksek olan yerlere, yöneylem aramasıyla | Kısmen yerini aldı: ADR-0096, ADR-0104 |
| [0082](0082-ayni-sayi-daha-hizli.md) | Aynı sayılar, daha kısa sürede | Geçerli |
| [0083](0083-sdr-kaydindan-paket-kaybi.md) | Paket kaybı, bir SDR kaydından ölçülür | Geçerli |
| [0084](0084-sekme-satirin-kendisi-ve-kullanilabilirlik.md) | Sekme satırın kendisi; kullanılabilirlik doğruluğa bağlı; görüş dışı yanlılık bir seçenek | Geçerli |
| [0085](0085-turda-sekiz-direk.md) | Turda sekiz direk, üç satırda da | Yerini aldı: ADR-0099 |
| [0086](0086-sitede-alan-getirme.md) | Yayımlanmış sitede alan getirme; uydu görüntüsü bir onay kutusu | Geçerli |
| [0087](0087-ek-paketsiz-alan-getirme.md) | Bir yer getirmek ek paket istemiyor; uydu görüntüsünü sayfa çiziyor | Geçerli |
| [0088](0088-harita-yukseklik-kisiti.md) | Yükseklik haritadan, haritanın kendi hatasıyla | Geçerli |
| [0089](0089-harcirah-ve-amortisman.md) | Harcırah ve amortisman resmî kaynaklardan | Kısmen yerini aldı: ADR-0090 |
| [0090](0090-yerel-bakim-ekibi.md) | Bakımı yerel bir teknik firma yapıyor | Geçerli |
| [0091](0091-resmi-duyarlilik-ve-direk-antenleri.md) | SX1280'in resmî duyarlılığı ve menzili geri kazandıran antenler | Kısmen yerini aldı: ADR-0094 |
| [0092](0092-frekans-atlamali-belge-secenegi.md) | Frekans atlamalı belgelendirme bir seçenek olarak | Uygulandı: ADR-0094 |
| [0093](0093-dogrulanmis-toplu-fiyatlar.md) | 1000 adet fiyatı, doğrulandığı yerde dağıtıcının kademesinden | Yerini aldı: ADR-0105 |
| [0094](0094-o6-uyarlamali-frekans-atlama-ve-cubuk-anten.md) | Şehir içi ve kırsal O6 ile: uyarlamalı frekans atlama belgesi, 27 dBm modül ve 5 dBi çubuk anten | Geçerli |
| [0095](0095-tunel-uwb-kanal-5-ve-60-m.md) | Tünelde UWB kanal 5, yoldan 1,2 m yükseklik ve 60 m aralık | Geçerli |
| [0096](0096-gercek-yollar-ve-yerlesim-aramasi.md) | Şehir içi ve kırsalda alıcılar gerçek yollarda, direkler yerleşim aramasının yerlerinde | Geçerli |
| [0097](0097-baglanti-butcesinde-gercek-ayak-izleri.md) | Bağlantı bütçesinde binalar gerçek ayak izleriyle | Geçerli |
| [0098](0098-izgara-noktalari-sokakta-ve-tur-boyu.md) | Bina içine düşen ızgara noktaları en yakın sokakta; turda 8 ve 12 direk | Kısmen yerini aldı: ADR-0099 |
| [0099](0099-turda-on-iki-direk-ve-e28-2g4m20s.md) | Şehir içi ve kırsalda turda 12 direk; direk ve araçta E28-2G4M20S | Geçerli |
| [0100](0100-harcirah-kaynakli-maliyetler-ve-anten.md) | Harcırah kanundan, montaj ve bakım kaynaklı bileşenlerden; harici anten gerekli | Geçerli |
| [0101](0101-yapiya-gore-bakim-ve-kaynakli-isletme.md) | Bakım ziyareti yapıya göre; işletme bedelleri kaynaklı | Geçerli |
| [0102](0102-kademe-fiyati-taban.md) | Doğrulanmış kademe fiyatı küçük adette taban | Yerini aldı: ADR-0105 |
| [0103](0103-kartin-geri-kalani-ve-direk-boylari.md) | Kartın geri kalanı parça parça; direk boyları ve fiyatları kaynaklı | Fiyat yöntemi yerini aldı: ADR-0105 |
| [0104](0104-catilar-aramada-yok.md) | Çatılar aramada yok; yükseklikler 12 m ve 10 m | Geçerli |
| [0105](0105-satici-kademeleri-rapor-yok.md) | Fiyatlar satıcı kademelerinden; raporun fiyatları kullanılmıyor | Geçerli |
| [0106](0106-yasam-sinyali-ve-telsizle-aktarma.md) | Yaşam sinyali; hattı olmayan birim telsizle aktarıyor | Geçerli |
