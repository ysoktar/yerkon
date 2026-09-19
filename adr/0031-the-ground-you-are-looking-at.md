# ADR-0031: baktığın zemin

## Durum

Kabul edildi.

## Bağlam

Bir direğe yakınlaşmak düz yeşil bir duvar gösteriyordu.

Ağ, bütün sahaya yayılmış birkaç bin örnektir. Kırsal satırda bu, her
yedi yüz metrede bir örnek demektir; yani bir yamaçtan altı kilometre
uzaktaki bir kamera onun iki yüzeyini görür. Altındaki yükseklik modeli
otuz metrelik Copernicus verisidir: o tepenin biçimi ölçülmüştür,
görüntüleyici onu hiç istememiştir.

Bu, yakınlaşmayı anlamsız kılıyordu ki "dolaşabilmenin" yarısı budur.
Tekerlek kusursuz çalışıyordu ve ucunda hiçbir şey yoktu.

## Karar

`GET /api/ground?west=&east=&south=&north=`, sahanın tek bir penceresi
üzerinde, bütünüyle aynı bütçede bir ağ döndürür. Sayfa, kamera pencere
sahanın epeyce içinde kalacak kadar yaklaştığında birini ister ve geri
çekildiğinde onu bırakır — daha kaba bir ağın ortasında bırakılmış daha
ince bir yama, ikisinden de kötüdür.

Her yeniden çizimin sıfırladığı bir zamanlayıcıyla istenir; böylece bir
sürükleme sürerken altmış kez değil durduğunda bir kez ister ve pencere
elde olana yuvarlandığında atlanır.

## Sonuçlar

Tekerlek artık bir yere çıkıyor. Altı kilometrede kırsal tepe, yedi yüz
metrede bir yerine altmış metrede bir örnekleniyor; bu da kaynak verinin
gittiği inceliğe yakındır.

Hiçbir şey uydurulmuyor. Daha ince ağ, benzetimin çağırdığı aynı
`height_at`'tir; aynı arazi nesnesi üzerinde, yani ekrandaki zemin ile
bir paketin geçtiği zemin aynı zemin olarak kalır (ADR-0001). Sorun hangi
zeminin var olduğu değil, hangi örneklerin çizildiğidir.

Bedel, yerleşen her kamera hareketi başına bir istek; sahne uç
noktasının aldığı süreye yakın bir sürede yanıtlanıyor. Bu, yerel olduğu
için karşılanabilir; bir ağ üzerinden olsa karşılanamazdı — ki bu
projenin bunu dert etmek zorunda olmamasının sebebi de budur.
