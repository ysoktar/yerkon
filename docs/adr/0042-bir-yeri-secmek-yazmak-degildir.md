# ADR-0042: bir yeri seçmek, koordinat yazmak değildir

## Durum

Kabul edildi.

## Bağlam

"Yeni bir yer getir" kutusu bir merkez istiyordu, metin olarak:
`39,9250 32,8370`. Yani bölge eklemek şöyle başlıyordu — uygulamadan
çık, başka bir yerde harita aç, sağ tıkla, iki sayıyı kopyala, geri gel,
yapıştır.

Bu bir yer seçmek değil, bir yeri *kopya etmek*. Ve merkez artı boyut
yalnızca bir pinin etrafındaki **kareyi** tarif edebilir. Oysa insanın
istediği zemin bir vadi, bir çevre yolu, bir otoyol kesimi olur: uzun
kenarı ve kısa kenarı olan şekiller. Kare, kimsenin çizmediği bir şey.

## Karar

**Harita uygulamanın içinde.** Tam ekran açılıyor, çünkü 340 pikselik
bir panel bir sürgü tutar ama bir yer tutmaz; pul büyüklüğünde bir
haritada zemin seçmek aynı kopya etme probleminin daha küçük bir
kutusudur.

**Kutu çiziliyor, ayarlanmıyor.** Dört köşesi var, her biri çekilebilir;
gövdesinden tutup taşınıyor; Shift+sürükle ya da **Kutu çiz** ile
sıfırdan çiziliyor. Getirme bu dört köşeyi alıyor — `build_site` zaten
herhangi bir `BoundingBox` ile çalışıyordu, eksik olan onu çizecek yerdi.

**Kütüphane değil, kendi kodumuz.** `draw.js` neden varsa bu da o
yüzden: bu, bir getirmeden sonra çevrimdışı koşacağına söz veren yerel
bir uygulama, ve bir CDN'e bakan `<script>` ikinci bir ağ bağımlılığı ve
sayfada üçüncü bir taraf demek. Kayan harita bir izdüşüm, bir resim
ızgarası ve iki harekettir.

**İzdüşüm getirmenin indirdiği izdüşüm.** Web Mercator, `tile_of` ve
`tile_bounds` ile aynı numaralandırma — bakılan karo ile inen karo aynı
karo.

**Haritaya OpenStreetMap geliyor, giydirmeye hiçbir şey.** Bu, aynı
soruya iki ayrı cevap değil. Bir yer seçmek, insan gezinirken birkaç
düzine karodur; OSM'in karo kullanım ilkesinin *olağan kullanım* diye
tarif ettiği şey budur. Bir şehri araziye giydirmek ise tek seferde
binlerce karodur — aynı ilkenin *toplu indirme* deyip yapmamanızı
istediği şey. Dolayısıyla seçici haritayla, giydirme boş kutuyla geliyor
(ADR-0041). Adres motorun adlandırdığı bir şey: `--map-tiles` kendi karo
sunucusunu gösterir, boş dize ise hiç harita çizmez ve sayfa bunu söyler.

**Aynı anda yalnızca biri geçerli.** Köşeler telde merkezi yeniyor, o
yüzden:

- Haritadan kutu alınınca merkez kutusu da dolduruluyor (virgüllü
  ondalıkla) ve panel ne alındığını yazıyor.
- Merkez elle yazılınca çizilmiş kutu **düşüyor**.
- Boyut sürgüsüne dokununca da düşüyor, ve harita o boyutta kareye
  dönüyor.
- Harita, panelde yazan yerde açılıyor.

Bunların dördü de aynı hatanın dört yüzü: panelin bir şey gösterip
getirmenin başka bir yere gitmesi. Boş merkezle çöken getirme de aynı
aileden (ADR-0039) — sayfa ile görev hangi alanın karar verdiği
konusunda anlaşamıyordu.

**Kaç ızgara noktası olduğu kutu çizilirken yazıyor**, sonradan
keşfedilmiyor. Bir kutuyu sürüklemek ucuz; 40 km'lik bir kutu 30 m
adımda bir buçuk milyon örnek.

## Sonuçlar

Tarayıcıda yürüdüm. Kaydırma kutuyu zeminle birlikte taşıyor; yakınlaşma
imlecin altındaki yeri imlecin altında tutuyor (iki adımda kutu 102
pikselden 409'a, tam dört kat); güneydoğu köşesini çekmek kutuyu
3,00 × 3,00 km'den 9,22 × 5,40 km'ye getiriyor; kuzeybatı köşesini
çekerken karşı köşe **piksel piksel yerinde duruyor** (963, 624 → 963,
624); gövdesinden taşımak boyu bozmuyor.

Telde ne gittiğini de yakaladım — istek kesilerek, hiçbir şey
indirilmeden. Beş durumun beşi doğru: harita kullanılmayınca merkez ve
boyut; kutu alınınca dört köşe; merkez elle yazılınca köşeler düşüyor;
kutu yeniden alınınca geri geliyor; sürgüye dokununca yine düşüyor.

**Aritmetik iki dilde yazılı, ve bu çivilendi.** `boxAround` ile
`box_around` aynı iki sabiti kullanıyor. Bir sınama node ile *gerçek*
`map.js`'i içe aktarıp dört enlem ve üç boyutta ikisini karşılaştırıyor;
santimetreden iyi uyuyorlar. Sınamanın gerçekten yakaladığını, boylam
sabitini kasten bozarak denedim: 13 sınama düştü. Node olmayan makinede
atlanıyor — bu projenin kullanıcısının Python'u ve bir tarayıcısı var,
başka bir şeyi olmak zorunda değil.

**Sayfadaki virgül tek bir yere alındı.** `.toFixed(n).replace(".", ",")`
elle dört yere yazılmıştı; `decimal()` artık `words.js` içinde, çünkü
ondalık ayırıcı bir dil gerçeği (ADR-0035) ve dört kopya, üçünün
unutulması için üç fazladan yer demek.

**Bir paketleme hatası çıktı.** `aerial.png` paket verisine dâhil
değildi (`places/*/*.npy`, `*.npz`, `*.json`) — kurulan bir yerkon'da
fotoğraf gelmezdi. Eklendi.

## Sonraki adımlar

Presetler, sinyal renklendirmesi ve alıcı güzergâhları. Yol kenarı
donanımı da Overture'ın `transportation` katmanını bekliyor (ADR-0040).
