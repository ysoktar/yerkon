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
  "terrain.note": { tr: "{ground} · {anchors} direk",
                    en: "{ground} · {anchors|anchor|anchors}" },

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
        + "engelin yerine geçer; ikisini birden saymak aynı binaları iki "
        + "kez saymaktır.",
    en: "This ground brings its own buildings, so the obstruction is in "
        + "the terrain. A loss per kilometre stands in for obstruction the "
        + "terrain cannot show; charging both counts the same buildings "
        + "twice.",
  },
  "ground.bore.note": {
    tr: "Bir tünel tepenin içinden geçer, üzerinden değil: tabanı iki "
        + "portal arasındaki düz çizgidir. Aşağıdaki üç değer, zemin "
        + "seçilmiş olsun ya da olmasın, bu satırda okunmaz.",
    en: "A bore goes through the hill rather than over it: its floor is "
        + "the straight line between two portals. The three figures below "
        + "go unread on this row, measured ground or not.",
  },
  "ground.real.note": {
    tr: "Ölçülmüş bir zemin kendi rölyefini, kendi pürüzünü ve kendi "
        + "engellerini getirir, bu yüzden aşağıdaki üç değer uygulanmaz.",
    en: "Measured ground brings its own relief, its own roughness and its "
        + "own obstructions, so the three figures below stop applying.",
  },
  "ground.photo": { tr: "Uydu görüntüsünü zemine giydir",
                    en: "Drape the photograph over the ground" },
  "ground.photo.from": { tr: "Kaynak: {source}", en: "From {source}" },
  "ground.photo.none": {
    tr: "Bu yer fotoğrafsız getirilmiş. Yeni bir yer getirirken karo "
        + "adresi verilirse görüntü de iner.",
    en: "This place was fetched without one. Give a tile address when "
        + "fetching somewhere new and the photograph comes with it.",
  },
  "ground.photo.modelled": {
    tr: "Modellenmiş zeminin fotoğrafı yoktur: orası hiçbir yer değil.",
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
  "preset.replaces": {
    tr: "{name} yüklenecek. Bu sekmedeki her şeyin yerine geçer: zemin, "
        + "sahanın boyu ve eni, bütün direk dizileri ve alıcılar, elle "
        + "taşınmış ve silinmiş direkler, ve elle değiştirilmiş bütün "
        + "değerler. Diğer sekmelere dokunulmaz.",
    en: "{name} will be loaded. It replaces everything in this tab: the "
        + "ground, the site's length and width, every anchor run and "
        + "receiver, anchors moved and deleted by hand, and every figure "
        + "edited by hand. No other tab is touched.",
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
  "preset.sure_drop": { tr: "{name} silinsin mi? Dosyası diskten kalkar.",
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
  "fetch.imagery": { tr: "Uydu karo adresi (isteğe bağlı)",
                     en: "Tile address for the photograph (optional)" },
  "fetch.imagery.zoom": { tr: "Karo yakınlığı", en: "Tile zoom" },
  "fetch.imagery.note": {
    tr: "Boş bırakılırsa fotoğraf indirilmez; zemin düz renk çizilir. "
        + "Her sağlayıcının kendi koşulları var, bu yüzden buraya hazır "
        + "bir adres konmuyor — kullanacağınız servisin koşullarını siz "
        + "kabul edersiniz. 17 yakınlığı Ankara'da yaklaşık 0,92 m/piksel.",
    en: "Left empty, no photograph is downloaded and the ground is drawn "
        + "in flat colour. Every provider has its own terms, so no "
        + "address ships here — the terms you accept are yours. Zoom 17 "
        + "is about 0,92 m per pixel in Ankara.",
  },
  "fetch.open": { tr: "Yeni bir yer getir", en: "Fetch somewhere new" },
  "fetch.note": {
    tr: "Ankara ya da başka bir yer. Ağ kullanan tek şey budur; bir kez "
        + "getirilir, sonrası çevrimdışı koşar (ADR-0008).",
    en: "Ankara or anywhere else. This is the only thing that uses the "
        + "network; fetched once, everything after it runs offline (ADR-0008).",
  },
  "fetch.name": { tr: "Ad", en: "Name" },
  "fetch.south": { tr: "Güney", en: "South" },
  "fetch.west": { tr: "Batı", en: "West" },
  "fetch.north": { tr: "Kuzey", en: "North" },
  "fetch.east": { tr: "Doğu", en: "East" },
  "fetch.centre": { tr: "Merkez (enlem, boylam)", en: "Centre (lat, lon)" },
  "fetch.size": { tr: "Kutunun boyu", en: "Box across" },
  "fetch.size.out": { tr: "{km} km", en: "{km} km" },
  "fetch.box": {
    tr: "{km} × {km} km, {points} ızgara noktası. Merkezi haritada sağ "
        + "tıklayarak alabilirsin.",
    en: "{km} × {km} km, {points} grid points. Right-click a map to read "
        + "the centre off it.",
  },
  "fetch.spacing": { tr: "Izgara aralığı (m)", en: "Grid spacing (m)" },
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
    tr: "Üç satırın üçü de hazır durur. Sekmeler arasında geçmek yaptığın "
        + "düzenlemeyi silmez; her sekme kendi yerleşimini tutar.",
    en: "All three rows are held at once. Switching tabs does not discard "
        + "your edits; each tab keeps its own arrangement.",
  },
  "knob.length": { tr: "Boy", en: "Length" },
  "knob.width": { tr: "En", en: "Width" },
  "site.shape": {
    tr: "En sıfırken saha bir koridordur: direkler yolun iki yanına dizilir "
        + "ve birimler düz gider. Sıfırdan büyükken saha bir alandır: "
        + "direkler kaydırmalı bir ızgaraya yayılır, birimler alanın "
        + "çevresini ve ortasını dolaşır. Geometri ikisinde tamamen farklıdır.",
    en: "At zero width the site is a corridor: anchors line the road either "
        + "side and units drive straight. Above zero it is an area: anchors "
        + "spread over a staggered grid and units drive a circuit round the "
        + "edge and across the middle. The geometry is not comparable.",
  },

  // -- step 3, the deployment ---------------------------------------------
  "step.layout": { tr: "Yerleşim", en: "Deployment" },
  "runs.head": { tr: "Direk grupları", en: "Anchor groups" },
  "runs.add": { tr: "Grup ekle", en: "Add a group" },
  "units.head": { tr: "Alıcılar", en: "Receivers" },
  "units.add": { tr: "Alıcı ekle", en: "Add a receiver" },
  "layout.note": {
    tr: "Direği sürükleyerek taşı, Shift ile tıklayarak kaldır. Her grup "
        + "kendi modülünü ve montajını taşır; her alıcı hangi modülleri "
        + "taşıyorsa o direkleri duyar.",
    en: "Drag an anchor to move it, shift-click to remove it. Each group "
        + "carries its own module and mounting; each receiver hears the "
        + "anchors whose modules it carries.",
  },
  "run.module": { tr: "Modül", en: "Module" },
  "run.mounting": { tr: "Montaj", en: "Mounting" },
  "run.from": { tr: "Başlangıç (m)", en: "Start (m)" },
  "run.to": { tr: "Bitiş (m)", en: "End (m)" },
  "run.method": { tr: "Yerleştirme", en: "Placement" },
  "run.target_dop": { tr: "Hedef HDOP", en: "Target HDOP" },
  "run.cover_k": { tr: "Nokta başına direk", en: "Anchors per point" },
  "run.most": { tr: "En çok direk", en: "Anchor budget" },
  "run.spacing": { tr: "Aralık (m)", en: "Spacing (m)" },
  "run.offset": { tr: "Yoldan (m)", en: "From the road (m)" },
  "run.stagger": { tr: "Kaydırma (m)", en: "Stagger (m)" },
  "run.drop": { tr: "Grubu kaldır", en: "Remove the group" },
  "run.count": { tr: "{anchors} direk · menzil {reach} km", en: "{anchors} anchors · reach {reach} km" },
  "run.least": { tr: "En az bir direk grubu gerekli.",
                 en: "At least one anchor group is needed." },
  "unit.kind": { tr: "Tür", en: "Kind" },
  "unit.vehicle": { tr: "Kara aracı alıcısı", en: "Vehicle receiver" },
  "unit.pedestrian": { tr: "Yaya alıcısı", en: "Pedestrian receiver" },
  "unit.speed": { tr: "Hız (km/sa)", en: "Speed (km/h)" },
  "unit.start": { tr: "Başlangıç (m)", en: "Start (m)" },
  "unit.antenna": { tr: "Anten (m)", en: "Antenna (m)" },
  "unit.drop": { tr: "Alıcıyı kaldır", en: "Remove the receiver" },
  "unit.hears": { tr: "{anchors} direği duyuyor", en: "hears {anchors} anchors" },
  "unit.least": { tr: "En az bir alıcı gerekli.",
                  en: "At least one receiver is needed." },
  "unit.needs_module": { tr: "Alıcıda en az bir modül olmalı.",
                         en: "A receiver needs at least one module." },

  // -- step 4, the target -------------------------------------------------
  "step.target": { tr: "Hedef", en: "Target" },
  "target.region": { tr: "Bölge", en: "Region" },
  "target.scheme": { tr: "Ölçüm şeması", en: "Ranging scheme" },
  "knob.tolerance": { tr: "Menzil toleransı", en: "Ranging tolerance" },
  "knob.journey": { tr: "Yolculuk süresi", en: "Journey" },
  "knob.sweep": { tr: "Tarama hücresi", en: "Sweep cell" },
  "scheme.single": { tr: "Tek yönlü TWR", en: "Single-sided TWR" },
  "scheme.double": { tr: "Çift yönlü TWR", en: "Double-sided TWR" },
  "region.TR": { tr: "Türkiye", en: "Türkiye" },
  "region.EU": { tr: "Avrupa", en: "Europe" },
  "region.US": { tr: "Amerika", en: "United States" },
  "region.US-PTP": { tr: "Amerika (noktadan noktaya)",
                     en: "United States (point to point)" },
  "region.LICENSED": { tr: "Lisanslı", en: "Licensed" },

  // -- step 5, what it rests on -------------------------------------------
  "step.basis": { tr: "Dayanak", en: "Basis" },
  "options.head": { tr: "Hazır seçenekler", en: "Ready-made options" },
  "options.note": {
    tr: "Her seçenek, ayar dosyasında birkaç sayıyı değiştiren kısa bir "
        + "listedir. Uygulanınca elle yaptığın düzenlemelerin yanına eklenir; "
        + "geri almak için \"Geri al\" yeter.",
    en: "Each option is a short list of edits to the settings file. Applying "
        + "one composes with your own edits rather than replacing them; "
        + "\"Undo edits\" takes them all back.",
  },
  "options.none": { tr: "Hazır seçenek yok. Çözücü ile bir tane kaydet.",
                    en: "No options yet. Save one with the solver." },
  "options.same": { tr: "şu anki ayarlarla aynı",
                    en: "the same as the current settings" },
  "options.apply": { tr: "Uygula", en: "Apply" },
  "options.applied": { tr: "{name} uygulandı.", en: "{name} applied." },
  "figures.head": { tr: "Varsayılan değerler", en: "Default figures" },
  "figures.note": {
    tr: "Rapor yalnızca malzeme listesini verdi. Buradaki her sayı bir "
        + "varsayılandır; değiştirdiğinde her şey yeniden hesaplanır.",
    en: "The report gave a bill of materials and nothing else. Every figure "
        + "here is a default; change one and everything is rebuilt from it.",
  },
  "figures.assumed": { tr: "{total} değerin {assumed} tanesi varsayım",
                       en: "{assumed} of {total} figures are assumptions" },
  "figures.only_assumed": { tr: "Yalnız varsayımları göster",
                            en: "Show only the assumptions" },
  "figures.export": { tr: "Dosyaya yaz", en: "Write to a file" },
  "figures.undo": { tr: "Geri al", en: "Undo edits" },
  "figures.none_edited": { tr: "Değiştirilmiş sayı yok.",
                           en: "No figure has been changed." },
  "figures.still_assumed": { tr: "Hâlâ varsayım — kaynağı defaults.toml'a yaz",
                             en: "Still an assumption — put a source in defaults.toml" },
  "figures.source": { tr: "Kaynak: {source}", en: "Source: {source}" },
  "prov.datasheet": { tr: "veri sayfası", en: "datasheet" },
  "prov.measurement": { tr: "ölçüm", en: "measurement" },
  "prov.standard": { tr: "standart", en: "standard" },
  "prov.derived": { tr: "türetilmiş", en: "derived" },
  "prov.design": { tr: "tasarım kararı", en: "design decision" },
  "prov.assumption": { tr: "varsayım", en: "assumption" },

  // -- step 6, running it -------------------------------------------------
  "step.run": { tr: "Çalıştır", en: "Run" },
  "run.note": {
    tr: "Raporun satırlarını, bu sayfadaki sayılarla koşar — ekranda "
        + "sürüklediğin yerleşimle değil; onun için aşağıdaki "
        + "\"Simülasyonu çalıştır\" var. Dakikalar sürer; ilerlemesi "
        + "aşağıda görünür.",
    en: "Runs the report's rows against the figures on this page — not "
        + "against the arrangement you dragged on screen; \"Run the "
        + "simulation\" below does that. Minutes, with progress below.",
  },
  "run.which": { tr: "Hangi satırlar", en: "Which rows" },
  "run.all_rows": { tr: "üçü birden (+ ağırlıklı satır)",
                    en: "all three (+ the weighted row)" },
  "run.one_row": { tr: "yalnız {row}", en: "{row} only" },
  "run.table": { tr: "Tablo", en: "Table" },
  "run.budget": { tr: "Hata dağılımı", en: "Error budget" },
  "deliver.into": { tr: "Teslim klasörü", en: "Deliverables folder" },
  "deliver.budget": { tr: "Hata bütçesini de yaz (yavaş)",
                      en: "Write the error budget too (slow)" },
  "deliver.go": { tr: "Markdown olarak yaz", en: "Write as Markdown" },
  "solve.head": { tr: "Çözücü", en: "Solver" },
  "solve.note": {
    tr: "Hedefi karşılayan en ucuz yerleşimi arar. Boş bıraktığın alan "
        + "koşul sayılmaz. Bulduğunu isimlendirip seçenek olarak kaydeder.",
    en: "Searches for the cheapest arrangement that meets the target. A "
        + "field left empty is not a condition. Saves what it finds under "
        + "a name, as an option.",
  },
  "solve.scenario": { tr: "Senaryo", en: "Row" },
  "solve.availability": { tr: "Kullanılabilirlik ≥", en: "Availability ≥" },
  "solve.hpe50": { tr: "HPE P50 ≤ (m)", en: "HPE P50 ≤ (m)" },
  "solve.hpe95": { tr: "HPE P95 ≤ (m)", en: "HPE P95 ≤ (m)" },
  "solve.fixes": { tr: "Sabitleme/sn ≥", en: "Fixes a second ≥" },
  "solve.save_as": { tr: "Kaydedilecek ad", en: "Save it as" },
  "solve.go": { tr: "Ara", en: "Search" },

  // -- the answer ---------------------------------------------------------
  "result.head": { tr: "Sonuç", en: "Result" },
  "result.run": { tr: "Simülasyonu çalıştır", en: "Run the simulation" },
  "result.running": { tr: "Çalışıyor…", en: "Running…" },
  "result.reset": { tr: "Sıfırla", en: "Reset" },
  "result.anchors": { tr: "Direk sayısı", en: "Anchors" },
  "result.units": { tr: "Alıcı sayısı", en: "Receivers" },
  "result.round": { tr: "Tur süresi", en: "Round" },
  "result.rate": { tr: "Konum sıklığı", en: "Fix rate" },
  "result.reach": { tr: "{run}: menzil", en: "{run}: reach" },
  "result.closure": { tr: "{run}: kopma", en: "{run}: closure" },
  "result.reached": { tr: "Paketin ulaştığı alan", en: "Area a packet reaches" },
  "result.served": { tr: "Konum alınabilen alan", en: "Area with a position" },
  "result.hpe50": { tr: "HPE P50", en: "HPE P50" },
  "result.hpe95": { tr: "HPE P95", en: "HPE P95" },
  "result.vpe95": { tr: "VPE P95", en: "VPE P95" },
  "result.availability": { tr: "Kullanılabilirlik", en: "Availability" },
  "result.capex": { tr: "CAPEX", en: "CAPEX" },
  "result.opex": { tr: "OPEX / yıl", en: "OPEX / year" },
  "result.capex_km2": { tr: "CAPEX / km²", en: "CAPEX / km²" },
  "result.opex_km2": { tr: "OPEX / km²·yıl", en: "OPEX / km²·year" },
  "result.assumed_share": { tr: "Varsayıma dayanan pay", en: "Resting on assumptions" },

  // -- the confirmation sheet ---------------------------------------------
  "confirm.head": { tr: "Bu değişiklik başka değerleri de değiştiriyor",
                    en: "This change moves other figures too" },
  "confirm.asked": { tr: "İstediğin değişiklik", en: "What you asked for" },
  "confirm.follows": { tr: "Bunlar da değişiyor", en: "These follow" },
  "confirm.group": { tr: "{run} grubu", en: "group {run}" },
  "confirm.yes": { tr: "Uygula", en: "Apply" },
  "confirm.no": { tr: "Vazgeç", en: "Cancel" },
  "confirm.nothing": { tr: "Hiçbir şey değişmedi.", en: "Nothing changed." },

  // -- the scene ----------------------------------------------------------
  "scene.drag": { tr: "Sürükle", en: "Drag" },
  "scene.turns": { tr: "döndürür", en: "turns" },
  "scene.slide_keys": { tr: "sağ tık / Shift+sürükle",
                        en: "right-click / Shift+drag" },
  "scene.slides": { tr: "kaydırır", en: "slides" },
  "scene.wheel": { tr: "tekerlek", en: "wheel" },
  "scene.zooms": { tr: "imlece doğru yaklaşır", en: "zooms towards the cursor" },
  "scene.walks": { tr: "gezer", en: "walks" },
  "scene.tilts": { tr: "eğer", en: "tilts" },
  "scene.frames": { tr: "her şeyi çerçeveler", en: "frames everything" },
  "scene.frame": { tr: "Çerçevele", en: "Frame" },
  // -- what the ground overlay reads (ADR-0044) ------------------------
  "layer.anchors": { tr: "Kaç direk erişiyor", en: "Anchors in reach" },
  "layer.margin_db": { tr: "Sinyal marjı", en: "Signal margin" },
  "layer.dilution": { tr: "Geometri (HDOP)", en: "Geometry (HDOP)" },
  "layer.error_m": { tr: "Beklenen konum hatası", en: "Expected position error" },
  "layer.anchors.note": {
    tr: "Bir hücreye kaç direğin eriştiği. Üçü bir konum için en az; "
        + "dördüncüsü onu denetler.",
    en: "How many anchors reach a cell. Three is the fewest that gives a "
        + "position; a fourth checks it.",
  },
  "layer.margin_db.note": {
    tr: "En güçlü bağlantının çalışmayı bırakmasına ne kadar kaldığı. "
        + "6 dB'nin altı ince, 20 dB rahat.",
    en: "How much the strongest link has to spare before it stops "
        + "working. Under 6 dB is thin; 20 dB is comfortable.",
  },
  "layer.dilution.note": {
    tr: "Direk geometrisinin menzil hatasını kaç katına çıkardığı. Bir "
        + "sıra hâlindeki direkler enine yönde bunu sonsuza götürür "
        + "(ADR-0011).",
    en: "How much the anchors' geometry multiplies a ranging error. "
        + "Anchors in a line take it to infinity across that line "
        + "(ADR-0011).",
  },
  "layer.error_m.note": {
    tr: "Menzil sigması × geometri. Bu satırın kendi toleransının "
        + "katlarıyla renklendiriliyor. Bir kestirim, bir benzetim "
        + "değil: saat kayması, paket kaybı ve gerçekten oradan geçen "
        + "bir alıcı yok. Yayımlanan sayı 'Simülasyonu çalıştır'dan "
        + "gelir (ADR-0001).",
    en: "Ranging sigma times geometry, coloured in multiples of this "
        + "row's own tolerance. An estimate and not a simulation: no "
        + "clock drift, no lost packets, no receiver actually driving "
        + "through. The published number comes from the run (ADR-0001).",
  },
  "legend.nothing": { tr: "boyanmayan yer: hiçbir direk erişmiyor",
                      en: "unpainted: no anchor reaches" },
  "legend.served": { tr: "Konum alınabilen alan (≥4 direk)",
                     en: "Ground with a position (≥4 anchors)" },
  "legend.reached": { tr: "Paketin ulaştığı alan (≥1 direk)",
                      en: "Ground a packet reaches (≥1 anchor)" },
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
  "sum.layout": { tr: "{anchors} direk · {runs} grup · {units} alıcı",
                  en: "{anchors|anchor|anchors} · {runs|group|groups} · "
                      + "{units|receiver|receivers}" },
  "sum.target": { tr: "±{tolerance} · {region} · {scheme}",
                  en: "±{tolerance} · {region} · {scheme}" },
  "sum.scheme.single": { tr: "tek yönlü", en: "single-sided" },
  "sum.scheme.double": { tr: "çift yönlü", en: "double-sided" },
  "sum.basis.edits": { tr: "{assumed} · {edits} düzenleme",
                       en: "{assumed} · {edits} edits" },
  "unit.new": { tr: "alıcı", en: "receiver" },

  // -- the numbers ---------------------------------------------------------
  "result.service_area": { tr: "Hizmet alanı", en: "Service area" },
  "result.fixes": { tr: "Sabitleme", en: "Fixes" },

  // -- the error budget ----------------------------------------------------
  "budget.geometry": { tr: "geometri ×{gain}", en: "geometry ×{gain}" },
  "budget.source": { tr: "Hata kaynağı", en: "Error source" },
  "budget.alone": { tr: "Tek başına", en: "Alone" },
  "budget.without": { tr: "Kalkarsa", en: "Removed" },
  "budget.gain": { tr: "Kazanç", en: "Gain" },
  "budget.residue": { tr: "Model artığı", en: "Model residue" },
  "budget.no_dominant": {
    tr: "Tek bir baskın kaynak yok: en büyük ikisi birbirine yakın.",
    en: "No single source dominates: the largest two are close.",
  },
  "budget.note": {
    tr: "\"Tek başına\" o kaynak tek olsaydı kalacak hata; \"kalkarsa\" o "
        + "kaynak gidince toplamın ineceği yer. İkincisi her zaman daha "
        + "küçüktür, çünkü hatalar kareli toplanır — ve satın alma kararı "
        + "olan odur.",
    en: "\"Alone\" is the error that would remain if that source were the "
        + "only one; \"removed\" is where the total falls to once it is "
        + "gone. The second is always the smaller, because errors add in "
        + "quadrature — and it is the one a purchase decision turns on.",
  },

  // -- the solver's search space -------------------------------------------
  "vary.drop": { tr: "Bu sayıyı aramadan çıkar",
                 en: "Take this figure out of the search" },
  "vary.add": { tr: "Sayı ekle", en: "Add a figure" },
  "vary.reset": { tr: "Önerilene dön", en: "Back to the suggested" },
  "vary.count": {
    tr: "{candidates} yerleşim denenecek. Her biri tam bir simülasyon.",
    en: "{candidates} arrangements will be tried. Each is a full simulation.",
  },
  "vary.none": { tr: "Aranacak sayı yok. Ekle, ya da önerilene dön.",
                 en: "Nothing to search over. Add a figure, or go back to "
                     + "the suggested." },

  // -- what a fetch came back with ----------------------------------------
  "fetched.size": { tr: "boyut", en: "size" },
  "fetched.relief": { tr: "yükselti farkı", en: "relief" },
  "fetched.roughness": { tr: "pürüz", en: "roughness" },
  "fetched.use": { tr: "Bu zemine geç", en: "Stand on this ground" },

  // -- what the engine is doing -------------------------------------------
  "busy.sweep": { tr: "Kapsama taranıyor…", en: "Sweeping coverage…" },
  "busy.working": { tr: "Çalışıyor…", en: "Working…" },
  "fetch.cannot": {
    tr: "Bu kurulum saha indiremiyor: {missing} eksik. Kurmak için: "
        + "pip install -e \".[dev,sites]\" — Windows'ta docs/WINDOWS.md.",
    en: "This install cannot fetch ground: {missing} missing. Install with: "
        + "pip install -e \".[dev,sites]\" — on Windows see docs/WINDOWS.md.",
  },
  "say.refused": { tr: "motor kabul etmedi", en: "the engine refused" },
};

//: The language the page is currently speaking.
let speaking = "tr";

export function speak(language) { speaking = language; }
export function speaks() { return speaking; }

/* A number as this project writes one: comma for the decimal mark, no
 * thousands separator (ADR-0035).
 *
 * Here beside `say` because the decimal mark is a fact about a language,
 * not about a slider. The page had four copies of
 * `.toFixed(n).replace(".", ",")` written out by hand, which is three
 * more places for one of them to be forgotten.
 */
export function decimal(value, places = 1) {
  return Number(value).toFixed(places).replace(".", ",");
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
