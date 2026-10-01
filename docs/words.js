/* Everything the page says, in both languages.
 *
 * One file rather than strings scattered through the markup and the
 * code, because the thing that goes wrong with two languages is not
 * translating badly — it is translating nine tenths of something and
 * nobody noticing the tenth. A key with one language fails a test here
 * the same way a figure with one language fails one in the engine
 * (ADR-0035).
 *
 * What this file does NOT hold: anything the engine can say for itself.
 * The figures, their notes, what each one affects, the ground's
 * description and every ready-made option come down the wire already in
 * the language the session is set to, from `defaults.toml` and from
 * `language.py`. The page asks; it does not keep a second copy.
 */

export const SAY = {
  // -- chrome ------------------------------------------------------------
  "find.placeholder": { tr: "Ayarlarda ara…  ( / )", en: "Search settings…  ( / )" },
  "find.clear": { tr: "Aramayı temizle", en: "Clear the search" },
  "find.empty": { tr: "Bu arama hiçbir ayara uymuyor.",
                  en: "Nothing here matches that." },
  "language.pick": { tr: "Dil", en: "Language" },
  "back.site": { tr: "Ana sayfa", en: "Home page" },
  "title.sim": { tr: "simülasyonu", en: "simulation" },
  "terrain.note": { tr: "{ground} · {anchors} yayın birimi",
                    en: "{ground} · {anchors|broadcast unit|broadcast units}" },

  // -- step 1, the ground -------------------------------------------------
  "step.place": { tr: "Yer", en: "Place" },
  "ground.pick": { tr: "Zemin", en: "Ground" },
  "ground.modelled": { tr: "Modellenmiş (tepeli)", en: "Modelled (rolling)" },
  "ground.real": { tr: "{site} (gerçek zemin)", en: "{site} (real ground)" },
  "ground.none": { tr: "Ölçülmüş bir zemin seçilmedi; tepeler aşağıdan modellenir.",
                   en: "No measured ground chosen; the hills are modelled below." },
  "ground.modelled.note": {
    tr: "Ölçülmüş bir zemin seçilmemişse tepeler aşağıdaki üç değerden "
        + "modellenir. Hiçbir yer düz değildir, bu yüzden düz bir seçenek yoktur.",
    en: "With no measured ground chosen, the hills come from the three "
        + "figures below. Nowhere is flat, so there is no flat option.",
  },
  "ground.buildings.note": {
    tr: "Bu zemin kendi binalarını getiriyor, dolayısıyla engel arazinin "
        + "içinde. Kilometre başına bir kayıp, arazinin gösteremediği "
        + "engelin yerine geçer; ikisinin birden sayılması aynı binaların iki "
        + "kez sayılması olur.",
    en: "This ground brings its own buildings, so the obstruction is in "
        + "the terrain. A loss per kilometre stands in for obstruction the "
        + "terrain cannot show; charging both counts the same buildings "
        + "twice.",
  },
  "ground.bore.note": {
    tr: "Bir tünel tepenin içinden geçer, üzerinden değil: tabanı iki "
        + "portal arasındaki düz çizgidir. Aşağıdaki üç değer, zemin "
        + "seçilmiş olsun ya da olmasın, bu satırda kullanılmaz.",
    en: "A bore goes through the hill rather than over it: its floor is "
        + "the straight line between two portals. The three figures below "
        + "go unread on this row, measured ground or not.",
  },
  "ground.real.note": {
    tr: "Ölçülmüş bir zemin kendi yükseklik farkını, kendi pürüzünü ve "
        + "kendi engellerini getirir, bu yüzden aşağıdaki üç değer "
        + "uygulanmaz.",
    en: "Measured ground brings its own relief, its own roughness and its "
        + "own obstructions, so the three figures below stop applying.",
  },
  "ground.photo": { tr: "Uydu görüntüsünü zeminde göster",
                    en: "Drape the photograph over the ground" },
  "ground.photo.from": { tr: "Kaynak: {source}", en: "From {source}" },
  // The photograph is under the coverage colours until they are turned
  // off, which read as a photograph that had not loaded.
  "ground.photo.plain": {
    tr: "Uydu görüntüsü kapsama renklerinin altında kalır. Renksiz görmek "
        + "için sahnenin sol üstündeki listeden «Yalnız zemin (uydu ve "
        + "yollar)» seç.",
    en: "The photograph sits under the coverage colours. To see it plain, "
        + "choose “Ground only (photograph and roads)” in the list at the "
        + "top left of the scene.",
  },
  "ground.photo.none": {
    tr: "Bu yer uydu görüntüsü olmadan getirilmiş. Yeni bir yer getirirken \"Uydu "
        + "görüntüsünü de getir\" kutusu işaretliyse görüntü de gelir.",
    en: "This place was fetched without one. Tick \"Fetch the satellite "
        + "photograph too\" when fetching somewhere new and it comes along.",
  },
  "ground.roads": { tr: "Yolları göster", en: "Show the roads" },
  "ground.buildings": { tr: "Binaları göster", en: "Show the buildings" },
  "relief.true": { tr: "Yükseklik: gerçek ölçek", en: "Height: true scale" },
  "relief.two": { tr: "Yükseklik: 2 kat abartılı", en: "Relief doubled" },
  "relief.five": { tr: "Yükseklik: 5 kat abartılı", en: "Relief five times" },
  "ground.buildings.from": {
    tr: "Getirilen binalar; model her birini aynı alanda bir blok olarak "
        + "görüyor.",
    en: "The fetched buildings; the model sees each as a block of the "
        + "same area.",
  },
  "ground.buildings.none": {
    tr: "Bu zeminde getirilmiş bina yok.",
    en: "This ground carries no fetched buildings.",
  },
  "ground.roads.from": {
    tr: "Getirilen yol ağı; araçlar kalın çizgideki güzergâhı sürüyor.",
    en: "The fetched road network; the receivers drive the route drawn thick.",
  },
  "ground.roads.none": {
    tr: "Bu zeminde getirilmiş yol yok.",
    en: "This ground carries no fetched roads.",
  },
  "ground.photo.modelled": {
    tr: "Modellenmiş zemin gerçek bir yer olmadığı için uydu görüntüsü yoktur.",
    en: "Modelled ground has no photograph: it is nowhere.",
  },
  // -- named arrangements --------------------------------------------
  "site.clipped": {
    tr: "{asked} km istendi, {held} km tutuldu: saha getirilen zeminden "
        + "büyük olamaz. Daha büyüğü için o yeri yeniden getir.",
    en: "Asked for {asked} km, held at {held} km: a site cannot be larger "
        + "than the ground fetched for it. Fetch that place again for more.",
  },
  "unit.route": { tr: "Güzergâh", en: "Route" },
  "route.no_road": {
    tr: "Bu zemin yol geometrisi taşımıyor.",
    en: "This ground carries no road geometry.",
  },
  "preset.load": { tr: "Yükle", en: "Load" },
  "preset.save": { tr: "Kaydet", en: "Save" },
  "preset.drop": { tr: "Sil", en: "Delete" },
  "preset.name": { tr: "Bu düzenlemenin adı…", en: "Name this arrangement…" },
  "preset.replaced": {
    tr: "{name} yüklendi. Bu sekmedeki her şeyin yerine geçti: zemin, "
        + "sahanın boyu ve eni, bütün yayın birimi grupları ve alıcılar, "
        + "elle taşınmış ve silinmiş yayın birimleri ve elle değiştirilmiş bütün "
        + "değerler. Diğer sekmelere dokunulmadı.",
    en: "{name} is loaded. It replaced everything in this tab: the "
        + "ground, the site's length and width, every broadcast unit group and "
        + "receiver, broadcast units moved and deleted by hand, and every figure "
        + "edited by hand. No other tab was touched.",
  },
  "preset.saved": { tr: "{name} kaydedildi → {path}",
                    en: "Saved {name} → {path}" },
  "preset.dropped": { tr: "{name} silindi", en: "Deleted {name}" },
  "preset.loaded": { tr: "{name} yüklendi", en: "Loaded {name}" },
  "preset.needs_name": {
    tr: "Kaydetmek için bir ad yaz. Hazır gelenlerin üzerine yazılmaz.",
    en: "Type a name to save under. The shipped ones are not overwritten.",
  },
  "preset.shipped_kept": {
    tr: "{name} hazır gelen bir düzenleme; silinmez ve üzerine yazılmaz. "
        + "Farklı bir ad yaz.",
    en: "{name} is a shipped arrangement; it is not deleted or overwritten. "
        + "Type a different name.",
  },
  "preset.sure_drop": { tr: "{name} silinsin mi? Dosyası da silinir.",
                        en: "Delete {name}? Its file goes from the disk." },
  "fetch.map.open": { tr: "Haritadan seç…", en: "Pick it on a map…" },
  "fetch.map.search": { tr: "Yer ara: Konya, Bolu Dağı, D100…",
                        en: "Search a place: Konya, Bolu Dağı, D100…" },
  "fetch.map.find": { tr: "Ara", en: "Search" },
  "fetch.map.draw": { tr: "Kutu çiz", en: "Draw a box" },
  "fetch.map.take": { tr: "Bu alanı al", en: "Take this ground" },
  "fetch.map.close": { tr: "Vazgeç", en: "Cancel" },
  "fetch.map.span": { tr: "{across} × {along} km · {points} ızgara noktası",
                      en: "{across} × {along} km · {points} grid points" },
  "fetch.map.hint": {
    tr: "Sürükle: kaydır · Tekerlek: yakınlaş · Kutuyu taşı, köşelerinden "
        + "çek · Shift+sürükle ya da Kutu çiz: sıfırdan kutu",
    en: "Drag to pan · Wheel to zoom · Move the box, drag its corners · "
        + "Shift-drag or Draw a box to start a new one",
  },
  "fetch.map.drop": { tr: "Bırak", en: "Drop" },
  "fetch.map.picked": { tr: "Haritadan: {across} × {along} km",
                        en: "From the map: {across} × {along} km" },
  "fetch.map.credit": { tr: "© OpenStreetMap katkıda bulunanları",
                        en: "© OpenStreetMap contributors" },
  "fetch.map.none": {
    tr: "Harita karosu adresi verilmedi (--map-tiles), o yüzden altta "
        + "harita yok. Kutuyu yine de çizebilir ve alabilirsin.",
    en: "No map tile address was given (--map-tiles), so there is no map "
        + "underneath. The box can still be drawn and taken.",
  },
  "fetch.map.searching": { tr: "Aranıyor…", en: "Searching…" },
  "fetch.map.nothing": { tr: "Bu ada uyan bir yer bulunamadı.",
                         en: "Nothing here matches that name." },
  "fetch.map.offline": {
    tr: "Arama servisine ulaşılamadı. Yeri elle bulup kutuyu çizebilirsin.",
    en: "The search service did not answer. Find the place by hand and "
        + "draw the box.",
  },
  "fetch.imagery": { tr: "Uydu görüntüsünü de getir",
                     en: "Fetch the satellite photograph too" },
  "fetch.imagery.note": {
    tr: "Uydu görüntüsü yalnız zemini boyar, hesaba girmez. Kaynak: Esri, Maxar, "
        + "Earthstar Geographics, GIS User Community.",
    en: "The ground is painted with the photograph; nothing is computed "
        + "from it. Imagery: Esri, Maxar, Earthstar Geographics, GIS User "
        + "Community.",
  },
  "fetch.open": { tr: "Yeni bir yer getir", en: "Fetch somewhere new" },
  "fetch.note": {
    tr: "Ankara ya da başka bir yer. İnternet yalnız bunun için gerekir; yer bir "
        + "kez getirilir, sonrası internetsiz çalışır.",
    en: "Ankara or anywhere else. This is the only thing that uses the "
        + "network; fetched once, everything after it runs offline.",
  },
  "fetch.name": { tr: "Ad", en: "Name" },
  "fetch.south": { tr: "Güney", en: "South" },
  "fetch.west": { tr: "Batı", en: "West" },
  "fetch.north": { tr: "Kuzey", en: "North" },
  "fetch.east": { tr: "Doğu", en: "East" },
  "fetch.centre": { tr: "Merkez (enlem, boylam)", en: "Centre (lat, lon)" },
  "fetch.size": { tr: "Kutunun bir kenarı", en: "Box across" },
  "fetch.size.out": { tr: "{km} km", en: "{km} km" },
  "fetch.box.map": {
    tr: "{points} ızgara noktası: haritadan seçilen kutu. Kaydırma çubuğunu "
        + "geri getirmek için «Bırak».",
    en: "{points} grid points: the box picked on the map. Press “Drop” to "
        + "get the slider back.",
  },
  "fetch.box": {
    tr: "{km} × {km} km, {points} ızgara noktası. Merkezi haritada sağ "
        + "tıklayarak alabilirsin.",
    en: "{km} × {km} km, {points} grid points. Right-click a map to read "
        + "the centre off it.",
  },
  "fetch.spacing": { tr: "Yükseklik noktaları arası uzaklık (m)", en: "Grid spacing (m)" },
  "fetch.buildings": { tr: "OpenStreetMap binalarını da getir",
                       en: "Fetch OpenStreetMap buildings too" },
  "fetch.go": { tr: "Getir", en: "Fetch" },
  "knob.relief": { tr: "Tepe yüksekliği", en: "Hill height" },
  "knob.hills": { tr: "Tepe aralığı", en: "Hill spacing" },
  "knob.roughness": { tr: "Yüzey pürüzü", en: "Surface roughness" },
  "knob.clutter": { tr: "Engel kaybı", en: "Clutter loss" },

  // -- step 2, the site ---------------------------------------------------
  "step.site": { tr: "Saha", en: "Site" },
  "site.rows": {
    tr: "Tablonun üç satırı üç ayrı sekmede durur. Başka sekmeye geçince "
        + "yaptığın değişiklikler silinmez; her sekme kendi yerleşimini tutar.",
    en: "All three rows are held at once. Switching tabs does not discard "
        + "your edits; each tab keeps its own arrangement.",
  },
  "knob.length": { tr: "Boy", en: "Length" },
  "knob.width": { tr: "En", en: "Width" },
  "site.shape": {
    tr: "En sıfırken saha bir koridordur: yayın birimleri yolun iki yanına "
        + "dizilir ve alıcılar düz gider. Sıfırdan büyükken saha bir alandır: "
        + "yayın birimleri kaydırmalı bir ızgaraya yayılır, alıcılar alanın "
        + "çevresini ve ortasını dolaşır. Geometri ikisinde tamamen farklıdır.",
    en: "At zero width the site is a corridor: broadcast units line the road "
        + "either side and receivers drive straight. Above zero it is an area: "
        + "broadcast units spread over a staggered grid and receivers drive a circuit round the "
        + "edge and across the middle. The geometry is not comparable.",
  },

  // -- step 3, the deployment ---------------------------------------------
  "step.layout": { tr: "Yerleşim", en: "Deployment" },
  "runs.head": { tr: "Yayın birimi grupları", en: "Broadcast unit groups" },
  "runs.add": { tr: "Grup ekle", en: "Add a group" },
  "units.head": { tr: "Alıcılar", en: "Receivers" },
  "units.add": { tr: "Alıcı ekle", en: "Add a receiver" },
  "layout.note": {
    tr: "Bir yayın birimini sürükleyerek taşı, Shift ile tıklayarak kaldır. "
        + "Her grubun kendi modülü ve montajı var; alıcı yalnız kendi "
        + "taşıdığı modülü kullanan birimleri duyar.",
    en: "Drag a broadcast unit to move it, shift-click to remove it. Each group "
        + "carries its own module and mounting; each receiver hears the "
        + "units whose modules it carries.",
  },
  "run.module": { tr: "Modül", en: "Module" },
  "run.mounting": { tr: "Montaj", en: "Mounting" },
  "run.from": { tr: "Grubun başladığı yer (m)", en: "Start (m)" },
  "run.to": { tr: "Grubun bittiği yer (m)", en: "End (m)" },
  "run.method": { tr: "Yerleştirme yöntemi", en: "Placement" },
  "run.target_dop": { tr: "Hedef HDOP", en: "Target HDOP" },
  "run.cover_k": { tr: "Her noktaya erişecek birim sayısı", en: "Units reaching each point" },
  "run.most": { tr: "En fazla yayın birimi", en: "Most broadcast units" },
  "run.spacing": { tr: "Birimler arası uzaklık (m)", en: "Spacing (m)" },
  "run.offset": { tr: "Yol eksenine uzaklık (m)", en: "From the road (m)" },
  "run.stagger": { tr: "İki yan arasındaki kaydırma (m)", en: "Stagger (m)" },
  "run.drop": { tr: "Grubu kaldır", en: "Remove the group" },
  "run.count": { tr: "{anchors} yayın birimi · menzil {reach} km", en: "{anchors|broadcast unit|broadcast units} · reach {reach} km" },
  "run.disc": {
    tr: "aramada kullanılan menzil: {metres} m, bu zeminde ölçüldü",
    en: "the search placed against {metres} m, measured on this ground",
  },
  "run.disc.ceiling": {
    tr: "aramada kullanılan menzil: {metres} m, ama ölçülemedi: en yakın "
        + "uzaklıkta bile bağlantıların onda biri kurulamıyor, gerçek "
        + "menzil bunun altında",
    en: "the search placed against {metres} m, but nothing was measured: "
        + "even the closest band loses a tenth of its links, so the reach "
        + "is somewhere below it",
  },
  "run.disc.by_hand": {
    tr: "aramada kullanılan menzil: {metres} m, elle girildi",
    en: "the search placed against {metres} m, set by hand",
  },
  "run.bar.met": {
    tr: "hedefe ulaşıldı", en: "cleared its bar",
  },
  // What the arrangement serves, beside what its method asked for. A
  // bar being met says the method got what it asked for and not that
  // the deployment works: greedy-coverage asks that a packet arrives,
  // which is one anchor, and a position needs four (ADR-0060).
  "run.bar.served": {
    tr: "dört birimin eriştiği alan: %{share}",
    en: "{share} % has four units in reach",
  },
  "run.bar.serves_nothing": {
    tr: "ama hiçbir yere dört birim erişmiyor: bu yerleşim konum vermez",
    en: "but nowhere has four: this arrangement gives no position",
  },
  "run.bar.dilution.short": {
    tr: "hedefe ulaşılamadı: sahanın bir kısmında hiç konum "
        + "alınamıyor, {short} bağlantı eksik",
    en: "did not clear its bar: part of the site cannot be fixed at all, "
        + "{short} sightings short",
  },
  "run.bar.dilution": {
    tr: "hedefe ulaşılamadı: HDOP {got}, istenen {wanted}",
    en: "did not clear its bar: HDOP {got} against {wanted} asked for",
  },
  "run.bar.anchors_in_reach": {
    tr: "hedefe ulaşılamadı: bir yerde yalnız {got} birim duyuluyor, "
        + "istenen {wanted}",
    en: "did not clear its bar: somewhere has {got} units in reach "
        + "against {wanted} asked for",
  },
  "run.bar.covered_share": {
    tr: "hedefe ulaşılamadı: {short} hücreye hiçbir birim erişmiyor",
    en: "did not clear its bar: no broadcast unit reaches {short} cells",
  },
  "run.bar.budget": {
    tr: "sınıra gelindi: {most} birim yerleştirildi", en: "budget spent, {most} placed",
  },
  "run.bar.candidates": {
    tr: "işe yarayacak yeni bir yer kalmadı", en: "nothing left to add would help",
  },
  "run.least": { tr: "En az bir yayın birimi grubu gerekli.",
                 en: "At least one broadcast unit group is needed." },
  "unit.kind": { tr: "Tür", en: "Kind" },
  "unit.vehicle": { tr: "Kara aracı alıcısı", en: "Vehicle receiver" },
  "unit.pedestrian": { tr: "Yaya alıcısı", en: "Pedestrian receiver" },
  "unit.speed": { tr: "Hız (km/sa)", en: "Speed (km/h)" },
  "unit.start": { tr: "Başlangıç noktası (m)", en: "Start (m)" },
  "unit.antenna": { tr: "Anten yüksekliği (m)", en: "Antenna (m)" },
  "unit.drop": { tr: "Alıcıyı kaldır", en: "Remove the receiver" },
  "unit.hears": { tr: "{anchors} yayın birimini duyuyor", en: "hears {anchors|broadcast unit|broadcast units}" },
  "unit.least": { tr: "En az bir alıcı gerekli.",
                  en: "At least one receiver is needed." },
  "unit.needs_module": { tr: "Alıcıda en az bir modül olmalı.",
                         en: "A receiver needs at least one module." },

  // -- step 4, the target -------------------------------------------------
  "step.target": { tr: "Hedef", en: "Target" },
  "target.setup": { tr: "Donanım kurulumu", en: "Hardware setup" },
  "target.setup.note": {
    tr: "Yayın biriminin, araç alıcısının ve yaya alıcısının modülünü, yayın birimi ve araç antenini ve uyulacak kuralı birlikte seçer. UWB grupları değişmez.",
    en: "Picks the module of the broadcast unit, the vehicle receiver and the pedestrian receiver, the broadcast unit and vehicle antennas and the rule together. UWB groups stay as they are.",
  },
  "target.pole_antenna": { tr: "Yayın birimi anteni", en: "Broadcast unit antenna" },
  "target.vehicle_antenna": { tr: "Araç anteni", en: "Vehicle antenna" },
  "antenna.pole.row": { tr: "5 dBi çubuk (Taoglas GW.22.5151)", en: "5 dBi rod (Taoglas GW.22.5151)" },
  "antenna.pole.mast": { tr: "12 dBi dış ortam anteni, kabloyla (TP-Link TL-ANT2412D)", en: "12 dBi mast antenna on a cable (TP-Link TL-ANT2412D)" },
  "antenna.vehicle.row": { tr: "5 dBi çubuk (Taoglas GW.22.5151)", en: "5 dBi rod (Taoglas GW.22.5151)" },
  "antenna.vehicle.roof": { tr: "8 dBi araç tavanı anteni, kabloyla (L-com HGV-2409U)", en: "8 dBi roof antenna on a cable (L-com HGV-2409U)" },
  "setup.custom": { tr: "Elle ayarlanmış", en: "Set by hand" },
  "setup.e28-20s": { tr: "E28-2G4M20S her birimde, FHSS ve LBT ile belgeli (tablonun)", en: "E28-2G4M20S on every unit, certified with FHSS and LBT (the table's)" },
  "setup.e28-12s": { tr: "E28-2G4M12S yalnız yayın biriminde, FHSS ve LBT ile belgeli", en: "E28-2G4M12S on the broadcast unit only, certified with FHSS and LBT" },
  "setup.e28-27s": { tr: "E28-2G4M27S yalnız yayın biriminde, FHSS ve LBT ile belgeli", en: "E28-2G4M27S on the broadcast unit only, certified with FHSS and LBT" },
  "setup.e28-12s-uncertified": { tr: "E28-2G4M12S yalnız yayın biriminde, belgesiz", en: "E28-2G4M12S on the broadcast unit only, no certificate" },
  "setup.o4": { tr: "Eski kurulum (O4): E28-2G4M12S, 12 dBi dış ortam ve 8 dBi araç tavanı anteni, belgesiz", en: "Old setup (O4): E28-2G4M12S, 12 dBi mast and 8 dBi roof antennas, no certificate" },
  "target.region": { tr: "Bölge", en: "Region" },
  "target.scheme": { tr: "Mesafe ölçme yöntemi", en: "Ranging scheme" },
  "knob.tolerance": { tr: "Mesafe ölçme toleransı", en: "Ranging tolerance" },
  "knob.journey": { tr: "Yolculuk süresi", en: "Journey" },
  "knob.sweep": { tr: "Kapsama çözünürlüğü", en: "Sweep cell" },
  "scheme.single": { tr: "Tek taraflı TWR", en: "Single-sided TWR" },
  "scheme.double": { tr: "Çift taraflı TWR", en: "Double-sided TWR" },
  "region.TR": { tr: "Türkiye, FHSS olmadan (10 mW/MHz)", en: "Türkiye, without FHSS (10 mW/MHz)" },
  "region.TR-FHSS": { tr: "Türkiye, FHSS ve LBT ile belgeli (100 mW)",
                     en: "Türkiye, certified with FHSS and LBT (100 mW)" },
  "region.EU": { tr: "Avrupa", en: "Europe" },
  "region.US": { tr: "Amerika", en: "United States" },
  "region.US-PTP": { tr: "Amerika (noktadan noktaya)",
                     en: "United States (point to point)" },
  "region.LICENSED": { tr: "Lisanslı", en: "Licensed" },

  // -- step 5, what it rests on -------------------------------------------
  "step.basis": { tr: "Dayanak", en: "Basis" },
  "options.head": { tr: "Hazır seçenekler", en: "Ready-made options" },
  "options.note": {
    tr: "Her seçenek, hesapta kullanılan birkaç değeri değiştiren kısa bir "
        + "listedir. Uygulanınca elle yaptığın değişikliklerin yanına eklenir; "
        + "hepsini geri almak için \"Değişiklikleri geri al\" yeter.",
    en: "Each option is a short list of edits to the figures. Applying "
        + "one composes with your own edits rather than replacing them; "
        + "\"Undo edits\" takes them all back.",
  },
  "options.none": { tr: "Hazır seçenek yok. «En ucuz yerleşimi ara» ile bir tane kaydedebilirsin.",
                    en: "No options yet. Save one with “Search for the cheapest layout”." },
  "options.same": { tr: "şu anki değerlerle aynı",
                    en: "the same as the current settings" },
  "options.apply": { tr: "Uygula", en: "Apply" },
  "options.applied": { tr: "{name} uygulandı.", en: "{name} applied." },
  "figures.head": { tr: "Hesapta kullanılan değerler", en: "Default figures" },
  "figures.note": {
    tr: "Hesabın dayandığı bütün değerler burada, kaynaklarıyla. Birini "
        + "değiştirdiğinde her şey yeniden hesaplanır.",
    en: "Every figure the calculation rests on is here, with its source. "
        + "Change one and everything is worked out again.",
  },
  "figures.assumed": { tr: "{total} değerin {assumed} tanesi varsayım",
                       en: "{assumed} of {total} figures are assumptions" },
  "figures.only_assumed": { tr: "Yalnız varsayımları göster",
                            en: "Show only the assumptions" },
  "figures.export": { tr: "Değerleri dosyaya kaydet", en: "Write to a file" },
  "figures.undo": { tr: "Değişiklikleri geri al", en: "Undo edits" },
  "figures.none_edited": { tr: "Değiştirilmiş değer yok.",
                           en: "No figure has been changed." },
  "figures.still_assumed": { tr: "Varsayım: kaynak gösterilmedi",
                             en: "An assumption: no source given" },
  "figures.source": { tr: "Kaynak: {source}", en: "Source: {source}" },
  "prov.datasheet": { tr: "veri sayfası", en: "datasheet" },
  "prov.measurement": { tr: "ölçüm", en: "measurement" },
  "prov.standard": { tr: "standart", en: "standard" },
  "prov.derived": { tr: "diğer değerlerden hesaplanmış", en: "derived" },
  "prov.design": { tr: "YERKON tasarım tercihi", en: "design decision" },
  "prov.assumption": { tr: "YERKON varsayımı", en: "assumption" },

  // -- step 6, running it -------------------------------------------------
  "step.run": { tr: "Çalıştır", en: "Run" },
  "run.note": {
    tr: "Tablonun satırlarını bu sayfadaki değerlerle çalıştırır, ekranda "
        + "sürüklediğin yerleşimle değil; onun için aşağıdaki "
        + "\"Simülasyonu çalıştır\" düğmesi var. Birkaç dakika sürer; "
        + "ilerlemesi aşağıda görünür.",
    en: "Runs the table's rows against the figures on this page, not "
        + "against the arrangement you dragged on screen; \"Run the "
        + "simulation\" below does that. Minutes, with progress below.",
  },
  "run.which": { tr: "Hangi satırlar", en: "Which rows" },
  "run.all_rows": { tr: "üçü birden", en: "all three" },
  "run.one_row": { tr: "yalnız {row}", en: "{row} only" },
  "run.table": { tr: "Tablo", en: "Table" },
  "run.budget": { tr: "Hata dağılımı", en: "Error budget" },
  "deliver.into": { tr: "Çıktı klasörü", en: "Deliverables folder" },
  "deliver.budget": { tr: "Hata dağılımını da yaz (yavaş)",
                      en: "Write the error budget too (slow)" },
  "deliver.go": { tr: "Markdown dosyası olarak kaydet", en: "Write as Markdown" },
  "solve.head": { tr: "En ucuz yerleşimi ara", en: "Search for the cheapest layout" },
  "solve.note": {
    tr: "Hedefi karşılayan en ucuz yerleşimi arar. Boş bıraktığın kutu "
        + "koşul sayılmaz. Bulduğu yerleşimi verdiğin adla hazır seçenek "
        + "olarak kaydeder.",
    en: "Searches for the cheapest arrangement that meets the target. A "
        + "field left empty is not a condition. Saves what it finds under "
        + "a name, as an option.",
  },
  "solve.scenario": { tr: "Tablo satırı", en: "Row" },
  "solve.availability": { tr: "Kullanılabilirlik ≥", en: "Availability ≥" },
  "solve.hpe50": { tr: "HPE P50 ≤ (m)", en: "HPE P50 ≤ (m)" },
  "solve.hpe95": { tr: "HPE P95 ≤ (m)", en: "HPE P95 ≤ (m)" },
  "solve.fixes": { tr: "Saniyedeki konum sayısı ≥", en: "Fixes a second ≥" },
  "solve.save_as": { tr: "Kaydedilecek adı", en: "Save it as" },
  "solve.go": { tr: "Ara", en: "Search" },

  // -- the placement search (ADR-0081) -------------------------------------
  "place.head": { tr: "En iyi yerleşimi bul", en: "Find the best layout" },
  "place.note": {
    tr: "Yayın birimlerini ızgaraya değil zaten yüksek olan yerlere koyar: var olan "
        + "aydınlatma direkleri ve tabelalar, yol kenarındaki direkler "
        + "(şehirde aydınlatma, kırsalda elektrik dağıtım direği) ve "
        + "tepelere dikilecek 25 m'lik direkler. Çatılar kiralık olduğu için "
        + "aday sayılmaz. Her aday bağlantı bütçesiyle "
        + "denenir; bir hücre, dört birim ona ulaştığında ve bu birimler "
        + "çevresindeki dört çeyreğin en az üçünde durduğunda sayılır. "
        + "Ölçülmüş zemin ister ve birkaç dakika sürer.",
    en: "Puts the broadcast units on places that are already high rather than on "
        + "a grid: existing lighting columns and signs, poles along the "
        + "road (lighting columns in town, electricity distribution poles in "
        + "open country) and 25 m masts to be put up on hilltops. Roofs are "
        + "rented, so they are not offered. "
        + "Every candidate is tried with the link budget; a cell counts "
        + "once four units reach it and they stand in at least three of "
        + "the four quarters around it. Needs measured ground and takes a "
        + "few minutes.",
  },
  "place.aim": { tr: "Amaç", en: "Aim" },
  "place.better": { tr: "Aynı maliyetle daha çok kapsama",
                    en: "More cover for the same cost" },
  "place.cheaper": { tr: "Aynı kapsama daha ucuza",
                     en: "The same cover for less" },
  "place.go": { tr: "Yerleştir", en: "Place" },
  "place.served": { tr: "Hizmet verilen hücre", en: "Cells served" },
  "place.cost": { tr: "Ömür boyu maliyet", en: "Lifecycle cost" },
  "place.anchors": { tr: "Yayın birimi", en: "Broadcast units" },
  "place.now": { tr: "Şimdiki yerleşim", en: "Current layout" },
  "place.found": { tr: "Aramanın bulduğu", en: "Search" },
  "place.use": { tr: "Bu yerleşimi uygula", en: "Use this layout" },
  "place.judge": {
    tr: "Bu sayılar aramanın kendi hesabı. Asıl sonucu simülasyon verir: "
        + "uyguladıktan sonra \"Simülasyonu çalıştır\" düğmesine bas.",
    en: "These are the search's own count. The simulation decides: "
        + "after applying it, press \"Run the simulation\".",
  },

  // -- the answer ---------------------------------------------------------
  "result.head": { tr: "Sonuç", en: "Result" },
  "result.run": { tr: "Simülasyonu çalıştır", en: "Run the simulation" },
  "result.running": { tr: "Çalışıyor…", en: "Running…" },
  "result.reset": { tr: "Sıfırla", en: "Reset" },
  // The fidelity toggle. Not a deployment choice, so it sits beside Run
  // rather than among the ready-made options (ADR-0063).
  "result.hurry": { tr: "Hızlı deneme", en: "Quick trial" },
  "result.hurry.on": { tr: "Hızlı deneme: açık", en: "Quick trial: on" },
  "result.hurried": {
    tr: "Bu sayılar hızlı denemeden, yayımlanacak olanlar değil",
    en: "from a quick trial, not the published figures",
  },
  "result.hurried.draws": {
    tr: "rastgele gölgeleme sekiz yerine bir kez üretiliyor",
    en: "the shadows are drawn once rather than eight times",
  },
  "result.hurried.profile": {
    tr: "arazi kesiti her 10 m yerine sabit 64 noktada okunuyor",
    en: "the profile is read at a fixed 64 samples rather than every 10 m",
  },
  "result.anchors": { tr: "Yayın birimi sayısı", en: "Broadcast units" },
  "result.units": { tr: "Alıcı sayısı", en: "Receivers" },
  "result.round": { tr: "Bir ölçüm turunun süresi", en: "Round" },
  "result.rate": { tr: "Konum sıklığı", en: "Fix rate" },
  "result.board.run": { tr: "{name} yayın birimi (1 / 100 / 1000 adet)", en: "{name} broadcast unit (1 / 100 / 1000)" },
  "result.board.unit": { tr: "{name} alıcısı (1 / 100 / 1000 adet)", en: "{name} receiver (1 / 100 / 1000)" },
  "result.unit_range": { tr: "{unit} ↔ {run}: menzil", en: "{unit} ↔ {run}: range" },
  "result.unit_range.value": {
    tr: "bağlantı {closes} km'ye, hassas ölçüm {precise} km'ye kadar",
    en: "link {closes} km, precise {precise} km",
  },
  "result.unit_range.none": { tr: "ortak modül yok", en: "no shared radio" },
  "result.capacity.one": {
    tr: "Tek kanalda en çok alıcı (saniyede 1 konum)",
    en: "Most receivers, one channel (one fix a second)",
  },
  "result.capacity.busy_km2": {
    tr: "Her birim tam doluyken en çok alıcı / km²",
    en: "Most receivers per km², every broadcast unit busy",
  },
  "result.capacity.busy_km": {
    tr: "Her birim tam doluyken en çok alıcı / km",
    en: "Most receivers per km, every broadcast unit busy",
  },
  "result.reach": { tr: "{run}: menzil", en: "{run}: reach" },
  "result.closure": { tr: "{run}: bağlantının koptuğu uzaklık", en: "{run}: closure" },
  "result.reached": { tr: "Sinyalin ulaştığı alan",
                      en: "Area a packet reaches" },
  "result.served": { tr: "Konum alınabilen alan", en: "Area with a position" },
  "result.hpe50": { tr: "Yatay hata, ortanca (HPE P50)", en: "HPE P50" },
  "result.hpe95": { tr: "Yatay hata, %95 (HPE P95)", en: "HPE P95" },
  "result.vpe95": { tr: "Dikey hata, %95 (VPE P95)", en: "VPE P95" },
  "result.draws": { tr: "Rastgele gölgeleme tekrarı", en: "Shadow draws" },
  "result.draws.first": {
    tr: "{done}/{wanted}, kalanı hesaplanıyor",
    en: "{done} of {wanted}, the rest are running",
  },
  "result.draws.pooled": {
    tr: "{wanted} tekrarın hepsi birleştirildi",
    en: "{wanted} draws pooled",
  },
  "result.pooling": { tr: "Tekrarlar birleştiriliyor…", en: "Pooling draws…" },
  "result.availability": { tr: "Kullanılabilirlik", en: "Availability" },
  "result.capex": { tr: "Kurulum maliyeti (CAPEX)", en: "CAPEX" },
  "result.opex": { tr: "Yıllık işletme maliyeti (OPEX)", en: "OPEX / year" },
  "result.capex_km2": { tr: "Kurulum maliyeti / km² (CAPEX)", en: "CAPEX / km²" },
  "result.opex_km2": { tr: "Yıllık işletme maliyeti / km² (OPEX)", en: "OPEX / km²·year" },
  "result.assumed_share": { tr: "Varsayıma dayanan pay", en: "Resting on assumptions" },

  // -- what a change also moved (ADR-0107) --------------------------------
  "notice.head": { tr: "Bu değişiklik başka değerleri de değiştirdi",
                   en: "This change moved other figures too" },
  "notice.undo": { tr: "Geri al", en: "Undo" },
  "notice.close": { tr: "Tamam", en: "OK" },
  "notice.undone": { tr: "Geri alındı.", en: "Undone." },
  "confirm.asked": { tr: "İstediğin değişiklik", en: "What you asked for" },
  "confirm.follows": { tr: "Bunlar da değişti", en: "These followed" },
  "confirm.group": { tr: "{run} grubu", en: "group {run}" },
  // The one question left: deleting a saved arrangement's file.
  "confirm.head": { tr: "Emin misin?", en: "Are you sure?" },
  "confirm.yes": { tr: "Sil", en: "Delete" },
  "confirm.no": { tr: "Vazgeç", en: "Cancel" },

  // -- the first-time path: a place, a layout, a run -----------------------
  "quick.head": { tr: "Hızlı başla: seçtiğin yer için en iyi yerleşim",
                  en: "Quick start: the best layout for a place you pick" },
  "quick.note": {
    tr: "Haritada bir yer seç. Sayfa oranın zeminini, binalarını, yollarını "
        + "ve uydu görüntüsünü getirir, yayın birimlerini var olan yüksek "
        + "yerlere en iyi biçimde yerleştirir ve hızlı bir simülasyon çalıştırır. "
        + "2 km'lik bir kutu birkaç dakika sürer; kutu büyüdükçe süre uzar.",
    en: "Pick a place on the map. The page fetches its ground, buildings, "
        + "roads and satellite photograph, puts the broadcast units on the "
        + "best of the high places already there, and runs a quick "
        + "simulation. A 2 km box takes a few minutes; a bigger one longer.",
  },
  "quick.go": { tr: "Haritadan yer seç ve başla", en: "Pick a place and start" },
  "quick.map": {
    tr: "Yeri ara ya da haritayı kaydır, kutuyu yerleştir ve «Bu alanı al» "
        + "düğmesine bas. 2-3 km önerilir.",
    en: "Search for the place or drag the map, set the box and press "
        + "“Take this ground”. 2 to 3 km is best.",
  },
  "quick.fetch": { tr: "Zemin, binalar, yollar ve uydu görüntüsü getiriliyor",
                   en: "Fetching the ground, buildings, roads and photograph" },
  "quick.ground": { tr: "Yeni zemine geçiliyor", en: "Moving onto the new ground" },
  "quick.place": { tr: "Yayın birimleri en iyi yerlere yerleştiriliyor",
                   en: "Placing the broadcast units on the best spots" },
  "quick.run": { tr: "Hızlı simülasyon çalıştırılıyor",
                 en: "Running a quick simulation" },
  "quick.done": {
    tr: "Bitti. Sonuç aşağıda. Yayımlanacak doğrulukta sayı için «Hızlı "
        + "deneme: açık» düğmesini kapatıp «Simülasyonu çalıştır»a bas.",
    en: "Done. The result is below. For publication-grade figures, turn "
        + "“Quick trial: on” off and press “Run the simulation”.",
  },
  "quick.failed": { tr: "Durdu: {why}", en: "Stopped: {why}" },
  "quick.big": {
    tr: "Bu kutu {area} km². Büyük kutularda yerleştirme uzun sürer; 2-3 km "
        + "daha hızlıdır.",
    en: "This box is {area} km². Placing takes long on big boxes; 2 to 3 km "
        + "is quicker.",
  },

  // -- the scene ----------------------------------------------------------
  "scene.drag": { tr: "Sürükle", en: "Drag" },
  "scene.turns": { tr: "döndür", en: "turn" },
  "scene.slide_keys": { tr: "Sağ tık ya da Shift+sürükle",
                        en: "Right-click or Shift+drag" },
  "scene.slides": { tr: "kaydır", en: "slide" },
  "scene.wheel": { tr: "Tekerlek", en: "Wheel" },
  "scene.zooms": { tr: "imlecin olduğu yere yaklaş",
                   en: "zoom towards the cursor" },
  "scene.walks": { tr: "gez", en: "walk" },
  "scene.tilts": { tr: "eğ", en: "tilt" },
  "scene.frames": { tr: "bütün sahneyi ekrana sığdır",
                    en: "fit the whole scene on screen" },
  "scene.frame": { tr: "Sahneyi sığdır", en: "Fit the scene" },
  "roads.forward": { tr: "Yolları öne çıkar", en: "Bring the roads forward" },
  "sweep.cell": { tr: "Kapsama çözünürlüğü: {metres} m", en: "Coverage cell: {metres} m" },
  "sweep.note": {
    tr: "Kapsamanın kaç metrede bir hesaplandığı. Küçük değer daha ayrıntılı ama daha yavaş.",
    en: "How often coverage is worked out, in metres. A smaller cell is finer and slower.",
  },
  "quality.auto": { tr: "Görüntü kalitesi: otomatik ({level})", en: "Picture quality: automatic ({level})" },
  "quality.level.low": { tr: "düşük", en: "low" },
  "quality.level.medium": { tr: "orta", en: "medium" },
  "quality.level.high": { tr: "yüksek", en: "high" },
  "quality.low": { tr: "Görüntü kalitesi: düşük", en: "Picture quality: low" },
  "quality.medium": { tr: "Görüntü kalitesi: orta", en: "Picture quality: medium" },
  "quality.high": { tr: "Görüntü kalitesi: yüksek", en: "Picture quality: high" },
  "quality.note": {
    tr: "Sahnenin bu cihazda ne kadar ayrıntılı çizileceği: ekran keskinliği, çizilen "
        + "bina ve uydu görüntüsü parçası sayısı, ayrıntılı zeminin ne kadar geniş bir "
        + "alana getirildiği ve sahne dönerken de tam çizilip çizilmediği. Otomatik "
        + "seçenek, cihazın işlemci sayısına ve belleğine bakarak seçer.",
    en: "How much this device draws: sharpness against the screen, how many buildings "
        + "and photo tiles, how wide the near ground is fetched, and whether a moving "
        + "frame keeps the exact picture. Automatic reads the device's processors and "
        + "memory.",
  },
  "scene.motion": { tr: "Telefonu çevirerek bak", en: "Look by turning the phone" },
  "scene.motion.denied": {
    tr: "Telefon hareket bilgisini vermedi; ayarlardan izin verilebilir.",
    en: "The phone did not give its motion; it can be allowed in its settings.",
  },
  // -- the tunnel, drawn flat ------------------------------------------
  "bore.plan": { tr: "Tünel, üstten", en: "The tunnel from above" },
  "bore.plan.note": {
    tr: "Tünel {width} m genişliğinde; iki duvar ayırt edilsin diye genişlik "
        + "uzunluğa göre büyütülerek çizildi.",
    en: "The bore is {width} m wide; the width is stretched against the "
        + "length so the two walls can be told apart.",
  },
  "bore.portal.in": { tr: "Giriş ağzı", en: "Entry portal" },
  "bore.portal.out": { tr: "Çıkış ağzı", en: "Exit portal" },
  "bore.section": { tr: "Boyuna kesit", en: "Long section" },
  "bore.section.note": {
    tr: "Yolun yüksekliği ve birimler; iki ağız arasında {rise} m fark var.",
    en: "The road's height and the broadcast units; the portals are {rise} m apart "
        + "in height.",
  },
  "scene.along": { tr: "tünel boyunca kaydır", en: "slide along the tunnel" },
  "scene.closer": { tr: "yaklaş ya da uzaklaş", en: "zoom in or out" },
  "scene.fits": { tr: "bütün tüneli sığdır", en: "fit the whole tunnel" },
  "scene.arrows": { tr: "Oklar", en: "Arrows" },
  // -- what the ground overlay reads (ADR-0044) ------------------------
  "layer.anchors": { tr: "Kaç yayın birimi erişiyor", en: "Broadcast units in reach" },
  "layer.margin_db": { tr: "Sinyal payı", en: "Signal margin" },
  "layer.dilution": { tr: "Yerleşim geometrisi (HDOP)", en: "Geometry (HDOP)" },
  "layer.error_m": { tr: "Beklenen konum hatası", en: "Expected position error" },
  "layer.ground": { tr: "Yalnız zemin (uydu ve yollar)",
                    en: "Ground only (photograph and roads)" },
  "layer.ground.note": {
    tr: "Kapsama renkleri kapalı; zemin, uydu görüntüsü ve yollar görünür.",
    en: "Coverage colours off, so the ground, the photograph and the "
        + "roads show.",
  },
  "layer.anchors.note": {
    tr: "Bir hücreye kaç yayın biriminin eriştiği. Konum için en az üç "
        + "gerekir; dördüncüsü konumu denetler.",
    en: "How many broadcast units reach a cell. Three is the fewest that gives a "
        + "position; a fourth checks it.",
  },
  "layer.margin_db.note": {
    tr: "En güçlü bağlantının kopmadan önce ne kadar daha zayıflayabileceği. "
        + "6 dB'nin altı az, 20 dB rahat.",
    en: "How much the strongest link has to spare before it stops "
        + "working. Under 6 dB is thin; 20 dB is comfortable.",
  },
  "layer.dilution.note": {
    tr: "Birimlerin diziliminin mesafe ölçme hatasını kaç katına "
        + "çıkardığı. Birimler tek sıra hâlindeyse sıraya dik yöndeki hata "
        + "sonsuza gider.",
    en: "How much the layout of the broadcast units multiplies a ranging "
        + "error. Units in a single line take it to infinity across that line.",
  },
  "layer.error_m.note": {
    tr: "Mesafe ölçme hatası × geometri. Bu satırın kendi toleransının "
        + "katlarıyla renklendiriliyor. Bu bir tahmin, simülasyon "
        + "değil: saat kayması, kaybolan mesaj ve gerçekten oradan geçen "
        + "bir alıcı yok. Yayımlanan sayı 'Simülasyonu çalıştır' "
        + "düğmesinden gelir.",
    en: "Ranging sigma times geometry, coloured in multiples of this "
        + "row's own tolerance. An estimate and not a simulation: no "
        + "clock drift, no lost packets, no receiver actually driving "
        + "through. The published number comes from the run.",
  },
  "legend.nothing": { tr: "boyanmayan yer: hiçbir yayın birimi erişmiyor",
                      en: "unpainted: no broadcast unit reaches" },
  "legend.served": { tr: "Konum alınabilen alan (≥4 yayın birimi)",
                     en: "Ground with a position (≥4 broadcast units)" },
  "legend.reached": { tr: "Sinyalin ulaştığı alan (≥1 yayın birimi)",
                      en: "Ground a packet reaches (≥1 broadcast unit)" },
  "legend.reach": { tr: "Grubun kullanılabilir menzili",
                    en: "The group's usable range" },
  "legend.unit": { tr: "Alıcı ve izlediği yol", en: "A receiver and its route" },

  // -- the step summaries --------------------------------------------------
  "sum.place.real": { tr: "{site} · ölçülmüş zemin",
                      en: "{site} · measured ground" },
  "sum.place.modelled": { tr: "modellenmiş · {relief} / {spacing}",
                          en: "modelled · {relief} / {spacing}" },
  "sum.site.area": { tr: "{length} × {width} alan",
                     en: "{length} × {width} area" },
  "sum.site.corridor": { tr: "{length} koridor", en: "{length} corridor" },
  "sum.layout": { tr: "{anchors} yayın birimi · {runs} grup · {units} alıcı",
                  en: "{anchors|broadcast unit|broadcast units} · {runs|group|groups} · "
                      + "{units|receiver|receivers}" },
  "sum.target": { tr: "±{tolerance} · {region} · {scheme}",
                  en: "±{tolerance} · {region} · {scheme}" },
  "sum.scheme.single": { tr: "tek taraflı", en: "single-sided" },
  "sum.scheme.double": { tr: "çift taraflı", en: "double-sided" },
  "sum.basis.edits": { tr: "{assumed} · {edits} değişiklik",
                       en: "{assumed} · {edits} edits" },
  "unit.new": { tr: "alıcı", en: "receiver" },

  // -- the numbers ---------------------------------------------------------
  "result.service_area": { tr: "Hizmet alanı", en: "Service area" },
  "result.fixes": { tr: "Konum sayısı", en: "Fixes" },

  // -- the error budget ----------------------------------------------------
  "budget.geometry": { tr: "geometri ×{gain}", en: "geometry ×{gain}" },
  "budget.source": { tr: "Hata kaynağı", en: "Error source" },
  "budget.alone": { tr: "Tek başına", en: "Alone" },
  "budget.without": { tr: "Kalkarsa", en: "Removed" },
  "budget.gain": { tr: "Kazanç", en: "Gain" },
  "budget.residue": { tr: "Modelin açıklayamadığı",
                      en: "Model residue" },
  "budget.first": { tr: "İlk iyileştirilecek yer: {remedy}.",
                    en: "Where to spend first: {remedy}." },
  "budget.no_dominant": {
    tr: "Tek bir baskın kaynak yok: en büyük ikisi birbirine yakın.",
    en: "No single source dominates: the largest two are close.",
  },
  "budget.note": {
    tr: "\"Tek başına\" o kaynak tek olsaydı kalacak hata; \"kalkarsa\" o "
        + "kaynak gidince toplamın ineceği yer. İkincisi her zaman daha "
        + "küçüktür, çünkü hatalar kareleri üzerinden toplanır; bir "
        + "parçayı iyileştirmeye değip değmeyeceğine ona bakarak karar "
        + "verilir.",
    en: "\"Alone\" is the error that would remain if that source were the "
        + "only one; \"removed\" is where the total falls to once it is "
        + "gone. The second is always the smaller, because errors add in "
        + "quadrature, and it is the one a purchase decision turns on.",
  },

  // -- the solver's search space -------------------------------------------
  "vary.drop": { tr: "Bu değeri aramadan çıkar",
                 en: "Take this figure out of the search" },
  "vary.add": { tr: "Değer ekle", en: "Add a figure" },
  "vary.reset": { tr: "Önerilen değerlere dön", en: "Back to the suggested" },
  "vary.count": {
    tr: "{candidates} yerleşim denenecek. Her biri tam bir simülasyon.",
    en: "{candidates} arrangements will be tried. Each is a full simulation.",
  },
  "vary.none": { tr: "Aranacak değer yok. Bir değer ekle ya da önerilen değerlere dön.",
                 en: "Nothing to search over. Add a figure, or go back to "
                     + "the suggested." },

  // -- what a fetch came back with ----------------------------------------
  "fetched.size": { tr: "boyut", en: "size" },
  "fetched.relief": { tr: "yükseklik farkı", en: "relief" },
  "fetched.roughness": { tr: "pürüz", en: "roughness" },
  "fetched.use": { tr: "Bu zemine geç", en: "Stand on this ground" },

  // -- what is running in the background ----------------------------------
  "act.head": { tr: "Arka planda", en: "In the background" },
  "act.together": { tr: "Arka planda: {n} iş birlikte",
                    en: "In the background: {n} at once" },
  "act.waits": { tr: "sırada: «{what}» bitince başlayacak",
                 en: "queued: starts once “{what}” finishes" },
  "act.seconds": { tr: "{n} sn", en: "{n} s" },
  "act.scene": { tr: "Sahne hesaplanıyor", en: "Working out the scene" },
  "act.apply": { tr: "Değişiklik uygulanıyor", en: "Applying the change" },
  "act.propose": { tr: "Değişikliğin etkileri hesaplanıyor",
                   en: "Working out what the change moves" },
  "act.sweep": { tr: "Kapsama hesaplanıyor", en: "Sweeping coverage" },
  "act.simulate": { tr: "Simülasyon çalışıyor", en: "Running the simulation" },
  "act.pooled": { tr: "Kalan rastgele gölgeleme tekrarları hesaplanıyor",
                  en: "Running the remaining shadow draws" },
  "act.ground": { tr: "Yakındaki zeminin ayrıntısı hesaplanıyor",
                  en: "Working out the ground close up" },
  "act.blocks": { tr: "Binalar yükleniyor", en: "Loading the buildings" },
  "act.mode": { tr: "Tablo satırına geçiliyor", en: "Switching the row" },
  "act.figures": { tr: "Değerler okunuyor", en: "Reading the figures" },
  "act.engine": { tr: "Hesap motoru çalışıyor", en: "The engine is working" },
  "act.photo": { tr: "Uydu görüntüsü indiriliyor",
                 en: "Downloading the satellite photograph" },
  "act.fine": { tr: "Yakın plan uydu görüntüsü indiriliyor",
                en: "Downloading the close-up photograph" },
  "act.run.fetch": { tr: "Yer getiriliyor", en: "Fetching the place" },
  "act.run.place": { tr: "En iyi yerleşim aranıyor",
                     en: "Searching for the best layout" },
  "act.run.table": { tr: "Tablo hesaplanıyor", en: "Running the table" },
  "act.run.budget": { tr: "Hata dağılımı hesaplanıyor",
                      en: "Working out the error budget" },
  "act.run.solve": { tr: "En ucuz yerleşim aranıyor", en: "The solver is searching" },
  "act.run.deliver": { tr: "Çıktı dosyaları yazılıyor",
                       en: "Writing the deliverables" },

  // -- what the engine is doing -------------------------------------------
  "busy.sweep": { tr: "Kapsama hesaplanıyor…", en: "Sweeping coverage…" },
  "busy.working": { tr: "Çalışıyor…", en: "Working…" },
  "busy.starting": { tr: "Başlatılıyor…", en: "Starting…" },
  "fetch.cannot": {
    tr: "Bu kurulum saha indiremiyor: {missing} eksik. Kurmak için: "
        + "pip install -e \".[dev,sites]\". Windows için docs/WINDOWS.md.",
    en: "This install cannot fetch ground: {missing} missing. Install with: "
        + "pip install -e \".[dev,sites]\". On Windows see docs/WINDOWS.md.",
  },
  "say.refused": { tr: "hesap motoru kabul etmedi", en: "the engine refused" },
};

//: The language the page is currently speaking.
let speaking = "tr";

export function speak(language) { speaking = language; }
export function speaks() { return speaking; }

/* A figure as Turkish writes it: a comma for the decimal mark and a dot
 * between thousands (1.400; 6.489,6).
 *
 * Here beside `say` because the decimal mark is a fact about a language,
 * not about a slider. */
export function decimal(value, places = 1) {
  const [whole, part] = Number(value).toFixed(places).split(".");
  const sign = whole.startsWith("-") ? "-" : "";
  const digits = sign ? whole.slice(1) : whole;
  const marked = digits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return sign + marked + (part !== undefined ? "," + part : "");
}

/* One phrase, with what it was given put where that language puts it.
 *
 * Named rather than positional. A Turkish sentence and an English one do
 * not want their pieces in the same order — "72 değerin 35 tanesi
 * varsayım" counts the total first and "35 of 72 figures are
 * assumptions" counts the assumptions first — and with `{}` in both, one
 * of them silently gets the other's numbers. It did, on the first
 * sentence that had two of them.
 */
export function say(key, fields) {
  const both = SAY[key];
  if (!both) return key;
  const text = both[speaking] || both.tr;
  if (!fields) return text;
  // `{runs|group|groups}` counts: one of them for one, the other for
  // anything else. English needs it and Turkish does not, which is
  // exactly why it belongs in the phrase rather than at the call.
  return text.replace(/\{(\w+)(?:\|([^|}]*)\|([^}]*))?\}/g,
    (whole, name, one, many) => {
      if (!(name in fields)) return whole;
      const value = fields[name];
      if (one === undefined) return value;
      return `${value} ${Number(value) === 1 ? one : many}`;
    });
}
