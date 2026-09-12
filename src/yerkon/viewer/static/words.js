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
  "ground.real.note": {
    tr: "Ölçülmüş bir zemin kendi rölyefini, kendi pürüzünü ve kendi "
        + "engellerini getirir, bu yüzden aşağıdaki üç değer uygulanmaz.",
    en: "Measured ground brings its own relief, its own roughness and its "
        + "own obstructions, so the three figures below stop applying.",
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
  "say.refused": { tr: "motor kabul etmedi", en: "the engine refused" },
};

//: The language the page is currently speaking.
let speaking = "tr";

export function speak(language) { speaking = language; }
export function speaks() { return speaking; }

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
