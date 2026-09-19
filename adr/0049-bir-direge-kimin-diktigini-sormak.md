# ADR-0049: bir direği kimin diktiğini sormak, onu yeniden dikmektir

## Durum

Kabul edildi.

## Bağlam

Sahne, ekrandaki her direğin hangi gruba ait olduğunu bilmek zorunda:
rengi, menzil halkası ve kartın üstündeki sayı bundan çıkıyor. Bunu
şöyle buluyordu:

```python
run_of = {}
for run in state.runs:
    for identifier, _, _, _ in run.anchors(
        terrain, (mounting_of, radio_of), state.width_m
    ):
        run_of[identifier] = run.identifier
```

Yani **yerleştirmeyi ikinci kez çalıştırıyordu.** İkinci bir çağrı ikinci
bir sorudur: bu çağrıda `route` yok (koridorun izlediği yol), `furniture`
yok (aramanın üzerine cıvatalandığı, zaten ayakta duran yapılar) ve bu
zemin üzerinde ölçülmüş menzil yok (ADR-0047) — yalnızca `width_m` var.
Farklı soru, farklı cevap, farklı kimlikler.

Tarayıcıda, Kızılay üzerinde:

| yöntem | dikilen | tanınan |
|---|---|---|
| grid | 36 | 36 |
| corridor | 26 | **6** |
| greedy-coverage | 27 | **14** |
| greedy-dop | 60 | **52** |
| k-cover | 60 | **51** |

Tanınmayanlar hiçbir renge boyanmıyor, hiçbir halka almıyor ve hiçbir
kartta sayılmıyor. Kart "6 direk" diyor, sahnede 26 direk duruyor, ve
hangisinin dağıtım olduğunu söyleyen hiçbir şey yok.

Bunun ikinci bir bedeli var: `greedy-dop` Kızılay'ın 232 montaj
edilebilir yapısı üzerinde eklediği her direk için her adayı her hücreye
karşı puanlıyor — bir yerleştirme 9 saniye. Sahne iki kez yerleştiriyor,
süpürme bir kez daha soruyor, ve sayfa bir açılır menü değişiminde 22
saniye donuyordu. Donarken de bir önceki düzenlemenin sayılarını
gösteriyordu (ADR-0050).

## Karar

**Hangi direği hangi grubun diktiği yerleştirmeyle birlikte taşınır.**
`ViewState.placed(terrain)` her direği onu diken grubun adıyla birlikte
veriyor; `anchors()` onun üstünde duran ince bir kabuk. Sahne artık
sormuyor, okuyor.

**Bir düzenleme için bir kez yerleştirilir.** `_PLACED`, `_REACHES`'in
yanında ve onun kalıbında: cevabın bağlı olduğu her şeyle anahtarlanmış
bir sözlük. Anahtar, durumun kendisinden *çıkarma* ile yazılıyor — bir
direği kımıldatamayacak üç alan (dil, yolculuk süresi, süpürme hücresi)
düşülüyor — çünkü sonradan eklenen bir alan o zaman biri hatırladığı için
değil, alan olduğu için anahtarda oluyor (ADR-0035). Zemin, duruma
güvenmek yerine doğrudan üç noktadan yükseklik sorularak
parmaklanıyor: `anchors` kendisine bir terrain veriliyor ve bir çağıran
duruma ait olmayan birini verebilir.

**Ölçülen menzilin anahtarı alıcı anten yüksekliğini de taşıyor.** Menzil
sahadaki en alçak antene göre veriliyor (`_lowest_unit`), ama
`_REACHES` bunu anahtarında tutmuyordu: alıcının antenini 1,5 m'den
8 m'ye çıkarmak menzili 478 m'den 522 m'ye taşıyor ve önbellek eskisini
veriyordu.

## Sonuçlar

Her yöntemde dikilen = tanınan = kartta sayılan. Sahne `greedy-dop` için
21,8 s → ilk seferde 9,3 s, ikinci seferde 0,1 s.

Sınamalar:

- her yöntem için "ekranda çizilen her direk onu diken gruba ait"
  — hata geri konduğunda dördü de düşüyor;
- iki grup birbirine karışmıyor (tersi hatayı bekleyen sınama);
- **hatırlanan, yeniden yerleştirmenin söyleyeceğiyle aynı**: aynı soru
  bir kez eski düzenlemeyi tutan bir sözlüğe, bir kez boş bir sözlüğe
  soruluyor. Dar bir anahtar ikisini ayırıyor, ve anahtarı kasten
  daralttığımda beş durumun beşi de düştü;
- alıcı anteni yükseltmek menzili yeniden sorduruyor.

Önbellek 12 düzenlemede sınırlı. Bir öğleden sonra sürgü çeken bir
oturum bir öğleden sonra büyüyen bir sözlük bırakmasın diye; tek bir
cevabın boyutuyla ilgisi yok.
