# ADR-0084: sekme satırın kendisi; kullanılabilirlik doğruluğa bağlı; görüş dışı yanlılık bir seçenek

## Durum

Kabul edildi. Görüş dışı yanlılık kapalı olarak geliyor; hangi seçeneğin
yayımlanacağı proje sahibinin kararı.

## Bağlam

Simülasyonun mantığı kod üzerinden gözden geçirildi. Üç şey çıktı.

**1. Simülatörün sekmeleri tablonun satırlarını koşturmuyordu.** ADR-0076
simülatörün tabloyu üretmesi gerektiğini söylüyordu ve bunu yerleşim ve
yolculuk süresi üzerinden sınıyordu. Ama sekmenin senaryosu kendi
değerlerini kendisi dolduruyordu:

| | Tablo | Sekme |
|---|---|---|
| Yayın biriminin ölçüm hatası | 0,15 m | 0 |
| Paket kaybı (şehir içi, kırsal) | %15, %5 | 0 |
| Kabul eşiği (şehir, kırsal, tünel) | 15, 30, 2 m | 20, 20, 5 m |
| Turda sorulan birim (şehir, kırsal) | 12, 12 | 8, 8 |
| Tünelde yöntem | tek yönlü | çift yönlü |
| Gürültü tohumu | 101, 202, 303 | 1 |
| Kamyon anteni | 1,5 m | 2,8 m |
| Sürüş turu | kendi yardımcısı (içeri 300 m, 150 m adım) | `routes` (içeri %10, kısa kenarın yirmide biri) |
| Şehir içi tarama hücresi | 100 m | 200 m |

Hiçbiri geometri olmadığı için var olan sınama hiçbirini yakalamadı.
Sonuç: simülatörde "Çalıştır"a basan ya da simülatörden tabloyu koşturan
biri yayımlanmış satırdan farklı bir satır görüyordu.

**2. Kullanılabilirlik gevşek tanımlıydı.** Filtre başladıktan sonra tek
bir mesafe ölçümü içeren tur bile "konum var" sayılıyordu; 500 m'lik
belirsizlik sınırı hiç devreye girmiyordu. Kaba bir koşuda şehir içi
konumların %19,9'u, kırsaldakilerin %30,1'i dörtten az mesafeli
turlardan geliyordu. Sunumun dipnot 1'i kullanılabilirliği "tanımlanan
doğruluğu karşılayan" diye tanımlıyor.

**3. Çok yollu yayılım ve görüş dışı hata yoktu.** `rf.py` "kanal
modelinde eklenir" diyordu, hiçbir yerde eklenmiyordu.

## Karar

**Satırın değerleri tek yerde.** `scenarios.row_figures` ve
`row_deployment_figures` (ölçüm hatası, paket kaybı, kabul eşiği,
kullanılabilirlik çıtası, filtre kapısı, turdaki birim sayısı, yöntem),
`ROW_SEEDS`, `ROW_UNITS` (hızlar km/sa olarak, anten yükseklikleri) ve
`site_road` (tur ya da koridor, `routes` ile). Tablonun kataloğu da
simülatörün sekmesi de bunları okuyor. Sekmede kişinin değiştirebildiği
tek şey tohum ve yöntem; ikisi de sekmenin şablonunda satırın değeriyle
başlıyor. Kamyon anteni 2,8 m oldu: bir kamyonun anteni kabin üstünde.

Yeni sınama (`test_pressing_run_on_a_tab_runs_the_row_the_table_published`)
her satırı iki yoldan koşturup hataları `np.array_equal` ile
karşılaştırıyor. Sekmenin paket kaybını sıfıra geri koymak şehir içi ve
kırsal için onu kırıyor; bu denendi.

**Kullanılabilirlik doğruluğa bağlı.** Bir tur, filtrenin kendi yatay
belirsizliği (kovaryansın yatay izinin karekökü, bir sigma)
`site.fix_horizontal_sigma_m` kadar ya da daha azsa konum sayılıyor.
Değer sunumun HPE P95 < 10 m hedefinden türetildi: iki boyutlu, eksen
başına eşit bir hata için %95 yarıçapı eksen sigmasının 2,448 katı;
10 m / 2,448 = 4,08 m eksen başına, iki eksende 5,78 m. Çıtayı geçmeyen
turda alıcı izlemeyi sürdürüyor ama sunacak bir konumu yok: tur kesinti
sayılıyor ve hatası örneğe girmiyor.

**Görüş dışı yanlılık bir seçenek.** Doğrudan ışın bir engelle
kesildiğinde (`Obstruction.blocked`, zemin ya da bina), mesafeye ortalaması
`radio.<parça>.nlos_bias_mean_m` olan üstel dağılımlı pozitif bir
yanlılık ekleniyor. Fazla yol terimiyle aynı anahtara bağlı, çünkü ikisi
de sinyalin gerçekte kat ettiği fazladan yol. Ortalama sıfırsa hiçbir şey
çekilmiyor, yani seçenek kapalıyken koşu önceki koşunun kendisi. Filtre
için bir yenilik kapısı var (`estimator.gate_sigmas`): beklenenden bu
kadar sigma uzak düşen bir mesafe atılıyor.

Yayımlanmış bir SX1280 görüş dışı ölçümü bulunamadı (Semtech'in uygulama
notları, ScienceDirect ve dağıtıcılar bu ortamdan engelli). Bu yüzden
değer bir varsayım, iki düzeyde (5 m ve 15 m) koşuldu ve pilotta
ölçülecek.

## Sonuçlar

- Simülatörün her sekmesi artık tablonun satırını birebir koşturuyor.
- Kullanılabilirlik sunumun tanımıyla aynı ve daha düşük.
- Görüş dışı yanlılık kapalı geliyor. Açık ve kapalı hâlin tam tablosu
  proje sahibine sunuldu; seçilen hâl yayımlanacak.
- Yayımlanmış tablo (23 Eylül) bu ADR'den önceki modelin çıktısı. Seçim
  yapıldıktan sonra bir kez yeniden koşturulup yayımlanacak.

## Karşılaştırma

Tam okuma (sekiz çekiliş, 10 m profil), yeni kullanılabilirlik tanımıyla.
A: görüş dışı yanlılık yok. B: SX1280 için ortalama 5 m, DWM3000 için
0,5 m, filtrede 3 sigma kapısı. C: B ile aynı, SX1280 için 15 m.
Yayımlanan: 23 Eylül tablosu (eski tanım).

| Satır | Hâl | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik |
|---|---|---|---|---|---|
| Şehir içi | Yayımlanan | 2,67 | 8,84 | 64,21 | %83,98 |
| Şehir içi | A | 2,40 | 6,38 | 57,85 | %76,35 |
| Şehir içi | B | 4,80 | 12,99 | 106,34 | %72,20 |
| Şehir içi | C | 10,72 | 32,42 | 174,93 | %53,41 |
| Kırsal | Yayımlanan | 2,91 | 11,83 | 140,75 | %65,85 |
| Kırsal | A | 2,45 | 6,89 | 113,16 | %55,78 |
| Kırsal | B | 3,72 | 11,61 | 192,26 | %52,33 |
| Kırsal | C | 5,52 | 24,35 | 315,67 | %44,83 |
| Tünel | Yayımlanan | 0,78 | 2,90 | 7,60 | %98,29 |
| Tünel | A | 0,79 | 3,21 | 7,26 | %98,25 |
| Tünel | B ve C | 0,80 | 3,53 | 7,41 | %97,54 |

Alan ve maliyet sütunları üç hâlde de aynı (alan taraması mesafe
hassasiyetine bakar, yanlılığa bakmaz): şehir içi 6,68 km², kırsal
209,00 km².

Kapının ilk hâli tüneli %62'ye düşürmüştü: filtre bir turun bütün
mesafelerini atınca sürüklenmeye devam ediyor ve sonraki turu da
atıyordu. Bütün mesafeleri atılan bir turda filtre artık o turdan yeniden
başlatılıyor; sınaması var.

Yeni tanımla P95 düşüyor, çünkü belirsizliği çıtayı geçen konumlar artık
örneğe girmiyor; aynı konumlar kullanılabilirliği düşürüyor.
