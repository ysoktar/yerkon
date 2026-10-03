# ADR-0106: yaşam sinyali; hattı olmayan birim telsizle aktarıyor

## Durum

Kabul edildi (proje sahibinin kararı, 28 Eylül 2026).

## Bağlam

Maliyet sayfası, cevap vermeyen birimi telefonların ve araç alıcılarının
fark ettiğini yazıyordu. Telefon birime bağlanmıyor; bu yanlıştı. Bakım
notu ise merkezin her birimin durumunu gördüğünü ve ekibin arıza olunca
gittiğini söylüyordu; arızanın nasıl fark edildiği yazmıyordu. Kırsalda
dağıtım direğindeki birimin merkeze hangi hatla bağlandığı da belli
değildi.

## Karar

- Her birim merkeze düzenli aralıklarla kısa bir "çalışıyorum" mesajı
  (yaşam sinyali) gönderiyor. Mesajı gelmeyen birim arızalı sayılıyor ve
  ekip gönderiliyor.
- Hattı olan yapıdaki birim merkeze o hattan bağlanıyor: şehirde ışıklı
  kavşağın sinyal dolabı, tünelde tünelin haberleşme omurgası, kırsalda
  yol üzerindeki AUS noktası.
- Hattı olmayan birim (örneğin kırsalda AUS'tan uzak bir dağıtım
  direğindeki) güneş paneliyle çalışmaya devam ediyor ve mesajlarını kendi
  telsiziyle hattı olan en yakın birime iletiyor. Güç ya da hat kablosu
  çekilmiyor, SIM kartı konmuyor; maliyette değişiklik yok.
- Alıcılar GPS karıştırması ya da aldatması gördüğünde bunu yakındaki
  yayın birimine iletiyor; uyarı merkeze aynı yoldan ulaşıyor.

## Sonuç

Tablo değişmedi. Yaşam sinyali ve birimler arası aktarma simülasyona
girmiyor; Simülasyon sayfasının "Modele girmeyenler" bölümü bunu yazıyor.
