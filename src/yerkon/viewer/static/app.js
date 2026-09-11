/* The viewer's browser half.
 *
 * It draws and it asks. It does not compute: every number on screen came
 * from the Python engine that builds the report, so the picture and the
 * table cannot disagree (ADR-0001).
 *
 * The one rule about editing is ADR-0009. A control marked data-cascades
 * changes something the link budget reads, so it goes through the
 * confirmation sheet first and the whole batch is answered once. Anything
 * else applies immediately.
 */

const CHOICES = {
  region: [["TR", "Türkiye"], ["EU", "Avrupa"], ["US", "Amerika"],
           ["US-PTP", "Amerika (noktadan noktaya)"], ["LICENSED", "Lisanslı"]],
  scheme: [["single", "Tek yönlü TWR"], ["double", "Çift yönlü TWR"]],
};

/* Served by the engine rather than written here. The hardcoded version
 * drifted: it never listed the tunnel bracket, so the one mounting the
 * tunnel row uses could not be chosen and its dropdown quietly showed a
 * roadside sign instead. */
let RADIOS = [];
let MOUNTINGS = [];
let TABS = [];
/* What each row is called, as the engine named it. */
const MODE_LABEL = {};
const KINDS = [["vehicle", "Kara aracı alıcısı"], ["pedestrian", "Yaya alıcısı"]];

/* What ground is on hand. The server finds it rather than listing it, so
 * a fourth `yerkon fetch` turns up here without any of this changing.
 * The empty option is modelled ground, never flat ground: nowhere is
 * flat, and this page does not offer a surface that is. */
let SITES = [];

/* One colour per anchor group, so a run in the panel and its masts in
 * the scene are recognisably the same thing. */
export const RUN_COLOURS = [
  [58, 70, 82], [31, 111, 235], [47, 158, 87], [180, 85, 29], [122, 63, 158],
];
const runColour = index => RUN_COLOURS[index % RUN_COLOURS.length];
const cssColour = rgb => `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;

let state = null;
let latest = null;
let sweepData = null;
let pendingChanges = null;

/* ---------- talking to the engine ---------- */

async function ask(path, body) {
  const options = body
    ? { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body) }
    : {};
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "engine refused");
  return payload;
}

function say(text, bad) {
  const el = document.getElementById("status");
  el.textContent = text;
  el.className = "on" + (bad ? " bad" : "");
  clearTimeout(say.timer);
  if (text) say.timer = setTimeout(() => { el.className = ""; }, 2600);
}

/* ---------- editing ---------- */

async function edit(changes, cascading) {
  if (cascading) {
    const { cascades } = await ask("/api/propose", { changes });
    if (cascades) { showConfirm(changes, cascades); return; }
  }
  await apply(changes);
}

async function apply(changes) {
  const { state: updated } = await ask("/api/apply", { changes });
  state = updated;
  // The scene first. The cards quote each group's reach and each unit's
  // anchor count, and those only exist once the engine has recomputed
  // them; drawing the cards first shows the previous run's numbers.
  await refreshScene();
  fillControls();
  await loadFigures();
  scheduleSweep();
}

/* The engine speaks one language and the page speaks another.
 *
 * Each change carries the field's own name as a key, so the wording is
 * looked up here rather than matched on English text. Anything without a
 * translation falls back to what the engine said, which is worse than a
 * translation and much better than a blank.
 */
const WORDS = {
  region: ["Bölge", ""],
  anchor_radio: ["Modül", ""],
  mounting: ["Montaj", ""],
  receiver_height_m: ["Alıcı anten yüksekliği", ""],
  surface_roughness_m: ["Yüzey pürüzü", ""],
  target_ranging_sigma_m: ["Menzil toleransı", ""],
  eirp_dbm: ["Yasal yayın gücü",
             "gücü bölgenin tavanı ve antenin kazancı belirliyor"],
  anchor_height_m: ["Direk yüksekliği",
                    "montaj yapısı direğin ne kadar yükseldiğini belirliyor"],
  corridor_m: ["Sahanın boyu", ""],
  from_m: ["Grubun başlangıcı",
           "sahanın dışında kalan direk hiçbir şeyin modellemediği "
           + "zeminde durur"],
  to_m: ["Grubun bitişi",
         "sahanın dışında kalan direk hiçbir şeyin modellemediği "
         + "zeminde durur"],
  usable_range_m: ["Kullanılabilir menzil",
                   "menzil, hedeflenen hassasiyette link bütçesinin izin verdiği kadar"],
  closure_range_m: ["Bağlantının koptuğu mesafe",
                    "aynı bütçe bağlantının nerede çözülemez olduğunu belirliyor"],
};

/* Values, where the engine names a thing rather than a number. Regions
 * and modules already read the same in both languages; structures do not.
 */
const VALUE_WORDS = {
  "roadside sign": "levha (3 m)",
  "sign gantry": "portal (6 m)",
  "billboard": "pano (10 m)",
  "lighting column": "aydınlatma direği (12 m)",
  "tall mast": "direk (25 m)",
  "tunnel bracket": "tünel askısı (4,5 m)",
};

const value = text => VALUE_WORDS[text] || text;

function words(change) {
  const found = WORDS[change.key];
  return {
    label: found ? found[0] : change.label,
    because: found && found[1] ? found[1] : change.because,
  };
}

function showConfirm(changes, cascades) {
  pendingChanges = changes;
  const body = document.getElementById("confirm-body");
  body.innerHTML = "";

  const block = (items, heading) => {
    if (!items.length) return;
    const h = document.createElement("h2");
    h.textContent = heading;
    body.appendChild(h);
    for (const change of items) {
      const said = words(change);
      const row = document.createElement("div");
      row.className = "change";
      row.innerHTML =
        `<span class="name"></span><span class="move"></span>` +
        (said.because ? `<span class="why"></span>` : "");
      row.querySelector(".name").textContent = said.label;
      row.querySelector(".move").textContent =
        `${value(change.before)} → ${value(change.after)}`;
      if (said.because) row.querySelector(".why").textContent = said.because;
      body.appendChild(row);
    }
  };

  // A corridor carries several groups of anchors and a change can move
  // more than one of them, so the sheet is grouped the way the engine
  // grouped it and each group says which anchors it is about.
  const groups = cascades.groups || [];
  const several = groups.length > 1;
  for (const group of groups) {
    if (several || groups.length === 0) {
      const heading = document.createElement("h2");
      heading.textContent = `${group.run} grubu`;
      heading.style.color = "var(--accent)";
      body.appendChild(heading);
    }
    block(group.asked, "İstediğin değişiklik");
    block(group.follows, "Bunlar da değişiyor");
  }
  document.getElementById("confirm").hidden = false;
}

document.getElementById("confirm-yes").onclick = async () => {
  document.getElementById("confirm").hidden = true;
  const changes = pendingChanges;
  pendingChanges = null;
  await apply(changes);
};

document.getElementById("confirm-no").onclick = () => {
  document.getElementById("confirm").hidden = true;
  pendingChanges = null;
  fillControls();          // put the control back where it was
  say("Hiçbir şey değişmedi.");
};

/* ---------- controls ---------- */

const UNITS = {
  corridor_m: v => `${(v / 1000).toFixed(1).replace(".", ",")} km`,
  width_m: v => (v > 0 ? `${(v / 1000).toFixed(1).replace(".", ",")} km` : "koridor"),
  relief_m: v => (v > 0 ? `${v} m` : "düz"),
  hill_spacing_m: v => `${v} m`,
  roughness_m: v => `${Number(v).toFixed(2).replace(".", ",")} m`,
  clutter_db_per_km: v => `${v} dB/km`,
  tolerance_m: v => `${Number(v).toFixed(1).replace(".", ",")} m`,
  journey_s: v => `${v} s`,
  sweep_m: v => `${v} m`,
};

const OUTPUTS = {
  corridor_m: "corridor-out", width_m: "width-out",
  relief_m: "relief-out", hill_spacing_m: "hill-out", roughness_m: "rough-out",
  clutter_db_per_km: "clutter-out", tolerance_m: "tol-out",
  journey_s: "journey-out", sweep_m: "sweep-out",
};

/* Anchor groups and units are lists, not sliders, so they get their own
 * cards. Editing one rebuilds the whole list and posts it: the engine
 * holds the state, and the page never keeps a second copy of it.
 */

function options(list, selected) {
  return list.map(([value, label]) =>
    `<option value="${value}"${value === selected ? " selected" : ""}>${label}</option>`
  ).join("");
}

function number(label, value, step, onChange) {
  const wrap = document.createElement("label");
  wrap.textContent = label;
  const input = document.createElement("input");
  input.type = "number";
  input.step = step;
  input.value = value;
  input.onchange = () => onChange(Number(input.value));
  wrap.appendChild(input);
  return wrap;
}

/* The three rows. Switching keeps what each one holds (ADR-0028). */
function drawTabs() {
  const host = document.getElementById("tabs");
  if (!host || !TABS.length) return;
  host.innerHTML = "";
  for (const [name, label] of TABS) {
    const tab = document.createElement("button");
    tab.textContent = label;
    if (name === state.scenario) tab.classList.add("on");
    tab.onclick = () => showRow(name);
    host.appendChild(tab);
  }
}

async function showRow(name) {
  if (name === state.scenario) return;
  try {
    const { state: loaded } = await ask("/api/mode", { mode: name });
    state = loaded;
    framed = false;
    await refreshScene();
    fillControls();
    await loadFigures();
    scheduleSweep();
  } catch (error) { say(error.message, true); }
}

function drawSites() {
  const select = document.getElementById("site");
  const entries = [["", "Modellenmiş (tepeli)"]]
    .concat(SITES.map(name => [name, `${name} (gerçek zemin)`]));
  select.innerHTML = options(entries, state.site || "");
  select.onchange = () => edit({ site: select.value }, false)
    .catch(e => say(e.message, true));

  // A fetched grid brings its own relief and its own roughness, so the
  // three sliders under it stop meaning anything. Saying so beats
  // leaving them looking live.
  const real = Boolean(state.site);
  for (const id of ["relief_m", "hill_spacing_m", "roughness_m"]) {
    const input = document.getElementById(id);
    if (input) input.disabled = real;
  }
  const note = document.getElementById("ground-note");
  if (note) {
    note.textContent = real
      ? (latest && latest.terrain && latest.terrain.description) || "gerçek zemin"
      : "Ölçülmüş bir zemin seçilmedi; tepeler aşağıdan modellenir.";
  }
  // Say that the three sliders stopped applying, beside the three
  // sliders, rather than leaving them greyed out with no reason given.
  const modelled = document.getElementById("modelled-note");
  if (modelled) {
    modelled.textContent = real
      ? "Ölçülmüş bir zemin kendi rölyefini, kendi pürüzünü ve kendi "
        + "engellerini getirir, bu yüzden aşağıdaki üç değer uygulanmaz."
      : "Ölçülmüş bir zemin seçilmemişse tepeler aşağıdaki üç değerden "
        + "modellenir. Hiçbir yer düz değildir, bu yüzden düz bir seçenek "
        + "yoktur.";
  }
}

function drawRuns() {
  const host = document.getElementById("runs");
  host.innerHTML = "";
  state.runs.forEach((run, index) => {
    const card = document.createElement("div");
    card.className = "card";
    card.dataset.find = `direk grup ${run.identifier} modül montaj aralık `
      + `yoldan kaydırma başlangıç bitiş ${run.radio} ${run.mounting}`;

    const head = document.createElement("header");
    head.innerHTML =
      `<span class="swatch" style="background:${cssColour(runColour(index))}"></span>` +
      `<b>${run.identifier}</b>` +
      `<button class="drop" title="Grubu kaldır">✕</button>`;
    head.querySelector(".drop").onclick = () => {
      const runs = state.runs.filter((_, i) => i !== index);
      if (!runs.length) { say("En az bir direk grubu gerekli.", true); return; }
      edit({ runs }, false).catch(e => say(e.message, true));
    };
    card.appendChild(head);

    const change = patch => {
      const runs = state.runs.map((r, i) =>
        i === index ? Object.assign({}, r, patch) : r);
      // A module or a mounting moves the link budget, so it has to be
      // confirmed. A position or a spacing does not.
      const cascading = "radio" in patch || "mounting" in patch;
      edit({ runs }, cascading).catch(e => say(e.message, true));
    };

    for (const [key, list] of [["radio", RADIOS], ["mounting", MOUNTINGS]]) {
      const wrap = document.createElement("label");
      wrap.textContent = key === "radio" ? "Modül" : "Montaj";
      const select = document.createElement("select");
      select.innerHTML = options(list, run[key]);
      select.onchange = () => change({ [key]: select.value });
      wrap.appendChild(select);
      card.appendChild(wrap);
    }

    const pair = document.createElement("div");
    pair.className = "pair";
    pair.appendChild(number("Başlangıç (m)", run.from_m, 100,
      v => change({ from_m: v })));
    pair.appendChild(number("Bitiş (m)", run.to_m, 100, v => change({ to_m: v })));
    pair.appendChild(number("Aralık (m)", run.spacing_m, 50,
      v => change({ spacing_m: v })));
    pair.appendChild(number("Yoldan (m)", run.offset_m, 10,
      v => change({ offset_m: v })));
    if (state.width_m > 0) {
      // Only over an area. A staggered row means nothing along a line,
      // and offering it there would suggest it did.
      pair.appendChild(number("Kaydırma (m)", run.stagger_m, 25,
        v => change({ stagger_m: v })));
    }
    card.appendChild(pair);

    const found = (latest && latest.runs || []).find(
      r => r.identifier === run.identifier);
    if (found) {
      const note = document.createElement("p");
      note.className = "hint";
      note.style.margin = "4px 0 0";
      note.textContent =
        `${found.count} direk · menzil ${tr(found.reach_m / 1000)} km`;
      card.appendChild(note);
    }
    host.appendChild(card);
  });
}

function drawUnits() {
  const host = document.getElementById("units");
  host.innerHTML = "";
  state.units.forEach((unit, index) => {
    const card = document.createElement("div");
    card.className = "card";
    card.dataset.find = `alıcı ${unit.identifier} ${unit.kind} hız anten `
      + `modül başlangıç ${unit.radios.join(" ")}`;

    const head = document.createElement("header");
    head.innerHTML =
      `<span class="swatch" style="background:#b4551d;border-radius:50%"></span>` +
      `<b>${unit.identifier}</b>` +
      `<button class="drop" title="Alıcıyı kaldır">✕</button>`;
    head.querySelector(".drop").onclick = () => {
      const units = state.units.filter((_, i) => i !== index);
      if (!units.length) { say("En az bir alıcı gerekli.", true); return; }
      edit({ units }, false).catch(e => say(e.message, true));
    };
    card.appendChild(head);

    const change = patch => {
      const units = state.units.map((u, i) =>
        i === index ? Object.assign({}, u, patch) : u);
      edit({ units }, false).catch(e => say(e.message, true));
    };

    const wrap = document.createElement("label");
    wrap.textContent = "Tür";
    const select = document.createElement("select");
    select.innerHTML = options(KINDS, unit.kind);
    select.onchange = () => change({ kind: select.value });
    wrap.appendChild(select);
    card.appendChild(wrap);

    const pair = document.createElement("div");
    pair.className = "pair";
    pair.appendChild(number("Hız (km/sa)", unit.speed_km_h, 5,
      v => change({ speed_km_h: v })));
    pair.appendChild(number("Başlangıç (m)", unit.start_m, 100,
      v => change({ start_m: v })));
    pair.appendChild(number("Anten (m)", unit.antenna_height_m, 0.1,
      v => change({ antenna_height_m: v })));
    card.appendChild(pair);

    const modules = document.createElement("div");
    modules.className = "hint";
    modules.style.margin = "4px 0 0";
    RADIOS.forEach(([value, label]) => {
      const box = document.createElement("label");
      box.style.display = "inline-block";
      box.style.marginRight = "8px";
      const tick = document.createElement("input");
      tick.type = "checkbox";
      tick.checked = unit.radios.includes(value);
      tick.onchange = () => {
        const radios = tick.checked
          ? unit.radios.concat([value])
          : unit.radios.filter(r => r !== value);
        if (!radios.length) {
          say("Alıcıda en az bir modül olmalı.", true);
          tick.checked = true;
          return;
        }
        change({ radios });
      };
      box.appendChild(tick);
      box.appendChild(document.createTextNode(" " + label.split(" ")[0]));
      modules.appendChild(box);
    });
    card.appendChild(modules);

    const heard = (latest && latest.units || []).find(u => u.id === unit.identifier);
    if (heard) {
      const note = document.createElement("p");
      note.className = "hint";
      note.style.margin = "4px 0 0";
      note.textContent = `${heard.hears} direği duyuyor`;
      card.appendChild(note);
    }
    host.appendChild(card);
  });
}

/* Every default the report did not supply, editable while the study runs.
 *
 * The report gave a bill of materials and nothing else, so between
 * seventy-nine and ninety-nine percent of what this produces rests on
 * placeholders. Editing one here rebuilds everything from it — the
 * mounting catalogue, the radios, the clocks, the rates, the scenarios —
 * which is the only way to find out which of them is worth an afternoon
 * of somebody's time (ADR-0016).
 *
 * A figure that moves the link budget cascades like any other setting
 * and goes through the confirmation sheet. One that only moves a price
 * does not, and applies at once.
 */

let figuresData = null;
let onlyAssumed = false;

/* What each part of a settings key is called in the language the rest of
 * the page is written in.
 *
 * `clock.crystal.residual_ppm` is what goes in `defaults.toml` and it is
 * what somebody editing the file needs to see, but it is not a name — a
 * list of seventy-two of them reads as a dump of variables rather than as
 * the set of things this study is resting on. The key stays, in the
 * tooltip and in what the search matches; the line says what it is.
 *
 * A fragment nobody has translated falls through as itself, so a figure
 * added to the settings file turns up here readable enough and never
 * disappears.
 */
const TERMS = {
  accept_sigma_m: "kabul eşiği",
  anchor_kwh_per_year: "yıllık elektrik",
  anchor_offset_m: "yoldan uzaklık",
  anchor_spacing_m: "direk aralığı",
  anchor_stagger_m: "sıra kaydırması",
  anchor_survey_sigma_m: "direk ölçüm hatası",
  anchors_per_round: "turdaki direk sayısı",
  anchors_sharing_central_operation: "merkezi işletmeyi paylaşan direk",
  billboard: "pano",
  central_operation_tl_per_year: "merkezi işletme, yıllık",
  clock: "saat",
  connectivity_tl_per_year: "hat ücreti, yıllık",
  crystal: "kristal",
  demodulation_threshold_db: "çözme eşiği",
  electricity_tl_per_kwh: "elektrik birim fiyatı",
  estimator: "kestirici",
  extent_m: "uzunluk",
  extra_off_grid_visits_per_year: "şebeke dışı ek ziyaret",
  ground_levels: "zemin pürüz katmanı",
  ground_patch_m: "zemin yaması",
  ground_roughness_spread: "pürüz saçılımı",
  ground_seed: "zemin tohumu",
  height_m: "yükseklik",
  length_m: "uzunluk",
  lighting_column: "aydınlatma direği",
  maintenance_tl_per_visit: "bakım, ziyaret başına",
  maintenance_visits_per_year: "yıllık bakım ziyareti",
  manoeuvre_m_s2: "manevra ivmesi",
  mounting: "montaj",
  noise_figure_db: "gürültü katsayısı",
  off_grid_supply_tl: "şebeke dışı besleme",
  operating: "işletme",
  packet_loss: "paket kaybı",
  payload_bytes: "paket yükü",
  radio: "modül",
  ranging: "ölçüm",
  residual_ppm: "düzeltme sonrası kalan sapma",
  roadside_sign: "yol levhası",
  rural: "kırsal",
  rural_relief_m: "kırsal tepe yüksekliği",
  rural_relief_wavelength_m: "kırsal tepe aralığı",
  service_life_years: "hizmet ömrü",
  sign_gantry: "portal",
  site: "saha",
  site_cost_tl: "saha maliyeti",
  tall_mast: "direk",
  tolerance_ppm: "toleransı",
  tunnel: "tünel",
  tunnel_bracket: "tünel askısı",
  tunnel_grade: "tünel eğimi",
  turnaround_s: "dönüş süresi",
  urban: "şehir içi",
  urban_clutter_db_per_km: "şehir içi engel kaybı",
  urban_packet_loss: "şehir içi paket kaybı",
  urban_relief_m: "şehir içi tepe yüksekliği",
  urban_relief_wavelength_m: "şehir içi tepe aralığı",
  width_m: "genişlik",
};

/* Where a figure came from, as the panel says it. */
const PROVENANCE = {
  datasheet: "veri sayfası",
  measurement: "ölçüm",
  standard: "standart",
  derived: "türetilmiş",
  design: "tasarım kararı",
  assumption: "varsayım",
};

const named = key =>
  key.split(".").slice(1).map(part => TERMS[part] || part).join(" · ");

const CASCADING_FIGURES = /(height_m|noise_figure_db|threshold_db|clutter|residual_ppm|tolerance_ppm|turnaround_s|payload_bytes)/;

function drawFigures() {
  const host = document.getElementById("figures");
  if (!figuresData) { host.innerHTML = ""; return; }
  host.innerHTML = "";

  document.getElementById("assumed-count").textContent =
    `${figuresData.total} değerin ${figuresData.assumed} tanesi varsayım`;

  for (const group of figuresData.groups) {
    // Heading and rows together, so a search that empties a group takes
    // its heading with it rather than leaving ten titles over nothing.
    const block = document.createElement("div");
    block.className = "figures-group";
    host.appendChild(block);

    const heading = document.createElement("div");
    heading.className = "group";
    heading.textContent = group.label;
    block.appendChild(heading);

    for (const figure of figuresData.figures.filter(f => f.group === group.key)) {
      if (onlyAssumed && !figure.assumed) continue;
      const row = document.createElement("div");
      row.className = "figure";
      // Its key, its group and what it affects, so the search box finds
      // it by any of them.
      const where = String(figure.provenance).toLowerCase();
      // Its key, its name, its group, where it came from and what it
      // affects, so the search finds it by any of them.
      row.dataset.find = `${figure.key} ${named(figure.key)} ${group.label} `
        + `${PROVENANCE[where] || where} ${figure.affects}`;

      const name = document.createElement("div");
      name.className = "name";
      name.innerHTML = `<i class="prov"></i><b></b><span></span>`;
      // Where the number came from, as a mark rather than as a tooltip.
      //
      // Thirty-five of sixty-nine are still guesses, and which thirty-five
      // is the single most useful thing this list can say. It said it in
      // a title attribute, which is to say it said it to nobody.
      const mark = name.querySelector(".prov");
      mark.classList.add(where);
      mark.title = PROVENANCE[where] || where;
      name.querySelector("b").textContent = named(figure.key);
      name.querySelector("span").textContent = figure.affects;
      name.title = `${figure.key}\n\n${figure.note}` + (
        figure.sensitivity ? `\n\n${figure.sensitivity}` : "");
      row.appendChild(name);

      // A figure may be a name rather than a quantity — which ground a
      // row stands on (ADR-0027). Offered as the sites actually fetched,
      // because typing a directory name that is not there is the one
      // mistake this can make.
      const input = document.createElement(
        figure.is_text ? "select" : "input");
      if (figure.is_text) {
        input.innerHTML = options(
          [["", "modellenmiş"]].concat(SITES.map(n => [n, n])),
          String(figure.value));
      } else {
        input.type = "number";
        input.value = figure.value;
        input.step = "any";
      }
      if (figure.edited) input.classList.add("edited");
      input.title = figure.assumed
        ? "Hâlâ varsayım — kaynağı defaults.toml'a yaz"
        : `Kaynak: ${figure.source}`;
      input.onchange = () => {
        const overrides = Object.assign({}, state.overrides);
        overrides[figure.key] = figure.is_text
          ? input.value : Number(input.value);
        edit({ overrides }, CASCADING_FIGURES.test(figure.key))
          .catch(e => say(e.message, true));
      };
      row.appendChild(input);

      const unit = document.createElement("div");
      unit.className = "unit";
      unit.textContent = figure.unit;
      row.appendChild(unit);

      block.appendChild(row);
    }
    // A group the assumption filter emptied takes its heading with it.
    if (!block.querySelector(".figure")) block.remove();
  }
}

async function loadFigures() {
  try {
    figuresData = await ask("/api/figures");
    drawFigures();
    drawSummary();
  } catch (error) { say(error.message, true); }
}

/* A ranged setting is shown three ways at once: what it means, where it
 * sits, and what it is.
 *
 * A slider alone cannot be given 4000 exactly when its step is 500, and a
 * number alone gives no sense of the range it lives in. The pair costs a
 * line and removes the whole class of "I know the value I want and this
 * control will not let me say it".
 */
function showKnob(name, value) {
  const slider = document.getElementById(name);
  if (!slider) return;
  slider.value = value;
  const exact = document.getElementById(name + "-num");
  if (exact) exact.value = value;
  const said = document.getElementById(OUTPUTS[name]);
  if (said) said.textContent = UNITS[name](Number(value));
}

function fillControls() {
  for (const name of Object.keys(OUTPUTS)) showKnob(name, state[name]);
  for (const name of Object.keys(CHOICES)) {
    document.getElementById(name).value = state[name];
  }
  drawSites();
  drawRuns();
  drawUnits();
  drawSummary();
}

/* ---------- the six steps, each collapsed to its own state ----------
 *
 * The panel used to be one column of every control the engine has, in the
 * order the engine grew them, about three thousand pixels of it. Nobody
 * reads that; they scroll it looking for the one thing they came for, and
 * they cannot see what the other five sections are currently set to
 * without opening all five.
 *
 * So each step carries a line of its own state, and that line is enough
 * to know whether the step needs opening at all.
 */
function drawSummary() {
  if (!state) return;
  const anchors = latest ? latest.anchors.length : 0;
  const assumed = figuresData
    ? `${figuresData.total} değerin ${figuresData.assumed} tanesi varsayım`
    : "—";
  const edits = Object.keys(state.overrides || {}).length;
  const scope = document.getElementById("task-only");

  const said = {
    "sum-place": state.site
      ? `${state.site} · ölçülmüş zemin`
      : `modellenmiş · ${UNITS.relief_m(state.relief_m)} / `
        + `${UNITS.hill_spacing_m(state.hill_spacing_m)}`,
    "sum-site": state.width_m > 0
      ? `${UNITS.corridor_m(state.corridor_m)} × ${UNITS.width_m(state.width_m)} alan`
      : `${UNITS.corridor_m(state.corridor_m)} koridor`,
    "sum-layout": `${anchors} direk · ${state.runs.length} grup · `
      + `${state.units.length} alıcı`,
    "sum-target": `±${UNITS.tolerance_m(state.tolerance_m)} · ${state.region}`
      + ` · ${state.scheme === "double" ? "çift yönlü" : "tek yönlü"}`,
    "sum-basis": assumed + (edits ? ` · ${edits} düzenleme` : ""),
    // An empty value is every row; a named one is that row alone.
    "sum-run": scope && scope.value
      ? `yalnız ${MODE_LABEL[scope.value] || scope.value}`
      : "üç satır ve ağırlıklı ortalama",
  };
  for (const [id, text] of Object.entries(said)) {
    const line = document.getElementById(id);
    if (line) line.textContent = text;
  }
}

/* ---------- finding one setting among a hundred ----------
 *
 * Between the deployment controls and the sixty-nine figures nobody
 * supplied, this page holds more settings than fit in anybody's head.
 * Every row carries the words somebody might look for it by, so typing
 * two of them opens the step it lives in and hides everything else.
 */
/* Turkish, folded to the letters a keyboard reaches without thinking.
 *
 * Somebody hunting for the noise figure types "gurultu" as often as
 * "gürültü", and a search that answers only one of them is a search
 * people stop using. Both sides are folded, so either spelling finds it.
 */
const FOLD = { "ı": "i", "İ": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o",
               "ç": "c", "â": "a", "î": "i", "û": "u" };

const folded = text => text.toLocaleLowerCase("tr")
  .replace(/[ıİşğüöçâîû]/g, letter => FOLD[letter] || letter);

function wireFind() {
  const box = document.getElementById("find");
  const clear = document.getElementById("find-clear");
  const steps = () => [...document.querySelectorAll("details.step")];
  // Which steps were open before the search opened more of them. A
  // search that leaves six sections hanging open once it is cleared has
  // undone the thing the steps are for.
  let before = null;

  const apply = () => {
    const wanted = folded(box.value.trim());
    document.body.classList.toggle("finding", Boolean(wanted));
    let hits = 0;
    for (const row of document.querySelectorAll("[data-find]")) {
      const match = !wanted
        || folded(row.dataset.find).includes(wanted)
        || folded(row.textContent).includes(wanted);
      row.hidden = !match;
      if (match && wanted) hits++;
    }
    // Everything a step holds that is not a searchable row — its
    // headings, its button rows, its explanations — goes with the rows
    // it belongs to. Without this, searching for one figure still showed
    // the whole of the ready-made options above it and the match was two
    // screens down.
    for (const empty of document.querySelectorAll(".figures-group")) {
      empty.hidden = Boolean(wanted)
        && !empty.querySelector("[data-find]:not([hidden])");
    }
    for (const step of steps()) {
      for (const block of step.children) {
        if (block.tagName === "SUMMARY") continue;
        block.hidden = Boolean(wanted) && !(
          (block.matches("[data-find]") && !block.hidden)
          || block.querySelector("[data-find]:not([hidden])")
        );
      }
    }

    if (wanted && before === null) before = steps().map(step => step.open);
    // While searching, a step is open exactly when it holds a hit. Open
    // is the only way a match is visible at all, and leaving the others
    // open puts the thing somebody searched for behind two screens of
    // the things they did not.
    steps().forEach((step, index) => {
      if (!wanted) {
        step.classList.remove("empty");
        if (before) step.open = before[index];
        return;
      }
      const found = step.querySelector(
        "[data-find]:not([hidden])") !== null;
      step.classList.toggle("empty", !found);
      step.open = found;
    });
    if (!wanted) before = null;
    document.getElementById("find-empty").hidden = !wanted || hits > 0;
  };

  box.oninput = apply;
  clear.onclick = () => { box.value = ""; apply(); box.focus(); };
  box.onkeydown = event => {
    if (event.key === "Escape") { box.value = ""; apply(); box.blur(); }
  };
  // One key to reach it, because the alternative is reaching for a mouse
  // to find a control you are about to type a number into anyway.
  window.addEventListener("keydown", event => {
    if (event.key !== "/" || event.ctrlKey || event.metaKey) return;
    const typing = /^(INPUT|SELECT|TEXTAREA)$/.test(
      (document.activeElement || {}).tagName || "");
    if (typing) return;
    event.preventDefault();
    box.focus();
    box.select();
  });
  apply();
}

/* One step open at a time, and brought into view when it opens.
 *
 * Closing a step loses nothing, because its summary carries its state,
 * and keeping one open is what holds the panel to a screen. Without the
 * scroll, opening the fifth step puts its contents below the fold and
 * the click reads as having done nothing.
 */
function wireSteps() {
  const steps = [...document.querySelectorAll("details.step")];
  for (const step of steps) {
    step.addEventListener("toggle", () => {
      if (!step.open || document.body.classList.contains("finding")) return;
      for (const other of steps) if (other !== step) other.open = false;
      step.scrollIntoView({ block: "start", behavior: "smooth" });
    });
  }
}

function wireControls() {
  for (const [name, options] of Object.entries(CHOICES)) {
    const select = document.getElementById(name);
    select.innerHTML = options
      .map(([value, label]) => `<option value="${value}">${label}</option>`)
      .join("");
    select.onchange = () =>
      edit({ [name]: select.value }, select.hasAttribute("data-cascades"))
        .catch(e => say(e.message, true));
  }

  for (const name of Object.keys(OUTPUTS)) {
    const slider = document.getElementById(name);
    if (!slider) continue;
    const exact = document.getElementById(name + "-num");
    const send = value =>
      edit({ [name]: Number(value) }, slider.hasAttribute("data-cascades"))
        .catch(e => say(e.message, true));

    // While the handle is moving, only the page follows. The engine is
    // asked once, when it is let go, because a sweep takes seconds.
    slider.oninput = () => showKnob(name, slider.value);
    slider.onchange = () => send(slider.value);
    if (exact) {
      // The number may say what the slider cannot reach — a corridor of
      // 42 km, a tolerance of 0,05 m. The slider then sits at its end
      // and the value is still the value; clamping it here would be the
      // control quietly changing a setting by being looked at.
      exact.oninput = () => {
        const said = document.getElementById(OUTPUTS[name]);
        if (said) said.textContent = UNITS[name](Number(exact.value));
        slider.value = exact.value;
      };
      exact.onchange = () => send(exact.value);
    }
  }

  document.getElementById("add-run").onclick = () => {
    const letters = "ABCDEFGHJKLMNPQRSTUVWXYZ";
    const used = new Set(state.runs.map(r => r.identifier));
    const identifier = [...letters].find(l => !used.has(l)) || "Z";
    const last = state.runs[state.runs.length - 1];
    edit({ runs: state.runs.concat([{
      identifier,
      radio: last ? last.radio : "sx1280",
      mounting: last ? last.mounting : "mast",
      stagger_m: last ? last.stagger_m : 0,
      from_m: last ? last.to_m + 500 : 0,
      to_m: last ? last.to_m + 3000 : 3000,
      spacing_m: last ? last.spacing_m : 1000,
      offset_m: last ? last.offset_m : 100,
    }]) }, false).catch(e => say(e.message, true));
  };

  document.getElementById("add-unit").onclick = () => {
    const used = new Set(state.units.map(u => u.identifier));
    let identifier = "alıcı";
    let n = 2;
    while (used.has(identifier)) identifier = `alıcı ${n++}`;
    edit({ units: state.units.concat([{
      identifier, kind: "vehicle", speed_km_h: 80, start_m: 0,
      antenna_height_m: 1.5, radios: ["sx1280", "dwm3000"],
    }]) }, false).catch(e => say(e.message, true));
  };

  document.getElementById("clear-overrides").onclick = () => {
    if (!Object.keys(state.overrides || {}).length) {
      say("Değiştirilmiş sayı yok.");
      return;
    }
    edit({ overrides: {} }, true).catch(e => say(e.message, true));
  };

  document.getElementById("only-assumed").onchange = event => {
    onlyAssumed = event.target.checked;
    drawFigures();
  };

  document.getElementById("run").onclick = runSimulation;
  document.getElementById("reset").onclick = async () => {
    const { state: fresh } = await ask("/api/reset", {});
    state = fresh;
    await refreshScene();
    fillControls();
    await loadFigures();
    scheduleSweep();
  };
}

/* ---------- the scene ---------- */

import * as draw from "/draw.js";

const container = document.getElementById("scene");
const canvas = document.createElement("canvas");
container.appendChild(canvas);
const context = canvas.getContext("2d");

let orbit = { yaw: -1.9, pitch: 0.72, distance: 34000, target: [0, 0, 0] };
let framed = false;
let terrainData = null;
let markers = [];

/* A finer mesh over the ground actually on screen, when there is one.
 *
 * The site's own mesh is a fixed few thousand samples spread over
 * everything there is, which over a forty kilometre site is one every
 * seven hundred metres. Zoomed in on a mast, the hill it stands on was
 * two flat facets — under a thirty metre elevation model, so the shape
 * was measured and merely never asked for. This holds the answer to
 * asking for it. Null at any distance where the site's own mesh is
 * already as fine as the window would be.
 */
let detail = null;

function drawnTerrain() {
  return detail || terrainData;
}

/* The mesh's height at a point, between its samples as well as on them.
 *
 * This used to take the nearest sample, which makes it a staircase: the
 * height jumps by whatever the relief does between two samples, seven
 * hundred metres apart on a large site. That was tolerable while it only
 * placed coverage cells, and became a bug the moment the camera's pivot
 * started riding on it, because the pan is a loop through this function
 * — the pivot's height moves the eye, the eye moves where the cursor's
 * ray lands, and that moves the pivot. A staircase has an infinite slope
 * at every step, so the loop found one and oscillated: the scene lurched
 * forward and back on alternate frames for as long as the drag lasted.
 *
 * Interpolated, the slope of this function is the slope of the ground,
 * the loop's gain is that slope, and a hillside is not a cliff.
 */
function sampleAt(mesh, x, y) {
  const { xs, ys, heights } = mesh;
  const at = (values, value) => {
    const last = values.length - 1;
    const step = (value - values[0]) / (values[last] - values[0]) * last;
    const low = Math.min(last, Math.max(0, Math.floor(step)));
    return [low, Math.min(last, low + 1), Math.min(1, Math.max(0, step - low))];
  };
  const [west, east, alongX] = at(xs, x);
  const [south, north, alongY] = at(ys, y);
  const lower = heights[south][west]
    + (heights[south][east] - heights[south][west]) * alongX;
  const upper = heights[north][west]
    + (heights[north][east] - heights[north][west]) * alongX;
  return lower + (upper - lower) * alongY;
}

function within(mesh, x, y) {
  const { xs, ys } = mesh;
  return x >= xs[0] && x <= xs[xs.length - 1]
    && y >= ys[0] && y <= ys[ys.length - 1];
}

function groundAt(x, y) {
  // Nearest sample from the mesh the engine sent, from the finer one
  // where it covers this point. Good enough to sit a coverage cell on;
  // the elevation itself came from the engine either way.
  if (detail && within(detail, x, y)) return sampleAt(detail, x, y);
  if (!terrainData) return 0;
  return sampleAt(terrainData, x, y);
}

/* How wide one quad of the ground mesh is, in metres.
 *
 * The engine picks the mesh to suit the site, so this is asked rather
 * than assumed; it is the scale at which a painted quad's single depth
 * stops describing the whole of it.
 */
function meshCell() {
  const mesh = drawnTerrain();
  if (!mesh) return 0;
  const { xs, ys } = mesh;
  if (xs.length < 2 || ys.length < 2) return 0;
  return (Math.abs(xs[1] - xs[0]) + Math.abs(ys[1] - ys[0])) / 2;
}

function resize() {
  const ratio = window.devicePixelRatio || 1;
  canvas.width = container.clientWidth * ratio;
  canvas.height = container.clientHeight * ratio;
  canvas.style.width = container.clientWidth + "px";
  canvas.style.height = container.clientHeight + "px";
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  render();
}
window.addEventListener("resize", resize);

/* Paint once per frame, however many gestures arrived.
 *
 * A pointer reports at the rate of the device, which on a trackpad is
 * well over a hundred times a second, and one frame of this scene costs
 * about a sixtieth of a second to draw. Painting on every event meant
 * the queue grew for as long as a drag lasted and the picture ran behind
 * the hand — the camera arithmetic was right the whole time and moving
 * still felt broken. The browser is asked for a frame instead and the
 * events in between collapse into it.
 */
let framePending = false;

function render() {
  // Every path that redraws also reconsiders how fine the ground under
  // the camera should be. Cheap: it only resets a timer, and the window
  // it would ask for is compared with the one already in hand.
  scheduleDetail();
  if (framePending) return;
  framePending = true;
  requestAnimationFrame(() => { framePending = false; paintScene(); });
}

function paintScene() {
  if (!latest) return;
  const width = container.clientWidth;
  const height = container.clientHeight;
  const view = draw.camera(orbit, width, height);
  const light = [-0.4, -0.5, 0.77];

  const colourIndex = {};
  (latest.runs || []).forEach((run, index) => {
    colourIndex[run.identifier] = cssColour(runColour(index));
  });
  const colourOf = id => colourIndex[id] || "#3a4652";

  // How far something drawn on the ground has to be pulled towards the
  // camera to sort in front of the quad it lies on: one mesh cell, which
  // is how much a quad's own depth varies across itself.
  const bias = meshCell();

  const items = [
    ...draw.groundFaces(view, drawnTerrain(), light),
    ...draw.cellFaces(view, sweepData, groundAt, bias),
    ...draw.masts(view, latest.anchors, colourOf),
    ...draw.polyline(
      view,
      latest.road.map(p => [p.x, p.y, p.z * draw.VERTICAL + 10]),
      "#22282e", 2, bias,
    ),
  ];

  // Each group's reach, in its own colour, once for the group.
  //
  // A UWB bracket and a mast on one corridor cover nothing like the same
  // ground, so the ring is per run — but every anchor within a run has
  // the same reach, and drawing one each put forty-nine copies of a
  // single fact over each other. The legend has always called it the
  // group's range; the code drew each anchor's. The one being dragged
  // gets its own, because that is the anchor a person is reasoning
  // about while they drag it.
  const rings = new Map();
  for (const anchor of latest.anchors) {
    if (!anchor.reach_m || !anchor.run) continue;
    if (!rings.has(anchor.run)) rings.set(anchor.run, []);
    rings.get(anchor.run).push(anchor);
  }
  const shown = [...rings.values()].map(group => group[group.length >> 1]);
  const held = latest.anchors.find(a => a.id === dragging && a.reach_m);
  if (held && !shown.includes(held)) shown.push(held);
  for (const anchor of shown) {
    items.push(...draw.ring(
      view,
      [anchor.x, anchor.y, anchor.ground_z * draw.VERTICAL + 6],
      anchor.reach_m,
      colourOf(anchor.run).replace("rgb(", "rgba(").replace(")", ",0.45)"),
      bias,
    ));
  }

  for (const unit of latest.units || []) {
    items.push(...draw.polyline(
      view,
      unit.trail.map(p => [p[0], p[1], p[2] * draw.VERTICAL + 20]),
      "rgba(180,85,29,0.55)", 1.5, bias,
    ));
  }
  items.push(...draw.units(view, latest.units || []));

  markers = items.filter(item => item.kind === "mast");
  draw.paint(context, width, height, items);
}

/* ---------- moving the camera, and dragging an anchor ----------
 *
 * Three things move: the camera turns around a point, that point slides
 * over the ground, and the distance to it changes. A viewer with only
 * the first is unusable over a twenty kilometre site, because there is
 * no way to look at a corner of it.
 *
 * Every gesture is captured on the canvas, so a drag that leaves the
 * window keeps working until the button comes up. Losing a turn halfway
 * because the pointer crossed into the panel is the kind of thing that
 * makes a scene feel broken when the maths is fine.
 */

let dragging = null;
let spinning = null;
let panning = null;
const pinch = new Map();
let pinchSpan = null;

/* How far the camera can get from what it is looking at. The lower bound
 * is close enough to stand between two tunnel brackets a hundred and
 * fifty metres apart; the upper is a rural region with room around it.
 * Four hundred metres was the old floor, and at that distance a bore is
 * a thin line whatever the wheel is told. */
const NEAREST_M = 25;
const FURTHEST_M = 400000;

/* How far up and down the camera may look.
 *
 * Not flat along the ground: below about seven degrees a ray meets the
 * terrain so far away that grabbing it slides the site off the screen,
 * and the horizon fills the frame with quads a kilometre deep.
 */
const LOWEST_PITCH = 0.12;
const HIGHEST_PITCH = 1.50;

function pixel(event) {
  const box = canvas.getBoundingClientRect();
  return [event.clientX - box.left, event.clientY - box.top];
}

function view() {
  return draw.camera(orbit, container.clientWidth, container.clientHeight);
}

function markerAt(px, py) {
  let best = null;
  for (const marker of markers) {
    const distance = Math.hypot(marker.top[0] - px, marker.top[1] - py);
    if (distance < 14 && (!best || distance < best.distance)) {
      best = { id: marker.id, distance };
    }
  }
  return best;
}

/* Where a pixel lands on the ground, following the terrain rather than
 * one flat plane. One pass over the level plane to find roughly where we
 * are, then again at that place's real height: over rolling ground the
 * two differ by more than a mast is tall, and a drag that used the first
 * would drop an anchor visibly away from the cursor. */
function groundUnder(px, py) {
  const camera = view();
  const flat = camera.onPlane(px, py, groundAt(0, 0) * draw.VERTICAL);
  if (!flat) return null;
  const settled = camera.onPlane(
    px, py, groundAt(flat[0], flat[1]) * draw.VERTICAL);
  return settled || flat;
}

/* The point the camera turns around, put back on the ground under it.
 *
 * The pivot used to keep whatever height it was given when the scene was
 * first framed, so sliding across four hundred metres of relief left it
 * buried under the hill or hanging in the air above it — and turning
 * about a buried pivot swings the whole site past the screen instead of
 * rotating the thing being looked at. Following the ground is what makes
 * turning feel like walking round something.
 */
function onGround(x, y) {
  return [x, y, groundAt(x, y) * draw.VERTICAL];
}

function frameOn(target, distance) {
  orbit.target = target;
  if (distance) {
    orbit.distance = Math.min(FURTHEST_M, Math.max(NEAREST_M, distance));
  }
  render();
}

/* ---------- asking for the ground you are actually looking at ----------
 *
 * A window around what the camera is aimed at, clipped to the site. Only
 * worth asking for when it is a good deal smaller than the site itself;
 * otherwise the mesh already in hand is the same mesh, and asking for it
 * again is a round trip that changes nothing on screen.
 */

//: How much of the site has to be off screen before a finer mesh is worth it.
const DETAIL_SHARE = 0.6;

let detailTimer = null;
let detailAsked = null;

function visibleGround() {
  if (!terrainData) return null;
  const { xs, ys } = terrainData;
  const reach = orbit.distance;
  const west = Math.max(xs[0], orbit.target[0] - reach);
  const east = Math.min(xs[xs.length - 1], orbit.target[0] + reach);
  const south = Math.max(ys[0], orbit.target[1] - reach);
  const north = Math.min(ys[ys.length - 1], orbit.target[1] + reach);
  if (east - west < 1 || north - south < 1) return null;
  const enough =
    (east - west) < (xs[xs.length - 1] - xs[0]) * DETAIL_SHARE
    || (north - south) < (ys[ys.length - 1] - ys[0]) * DETAIL_SHARE;
  return enough ? { west, east, south, north } : null;
}

function scheduleDetail() {
  clearTimeout(detailTimer);
  detailTimer = setTimeout(async () => {
    const box = visibleGround();
    if (!box) {
      // Pulled back far enough that the site's own mesh is the finer of
      // the two. Dropping it keeps one mesh on screen rather than a
      // sharp patch left behind in the middle of a coarse one.
      if (detail) { detail = null; detailAsked = null; paintScene(); }
      return;
    }
    const key = [box.west, box.east, box.south, box.north]
      .map(edge => Math.round(edge / 25)).join(",");
    if (key === detailAsked) return;
    detailAsked = key;
    try {
      const query = new URLSearchParams(
        Object.entries(box).map(([edge, at]) => [edge, String(at)]));
      detail = await ask("/api/ground?" + query.toString());
      paintScene();
    } catch (error) {
      detail = null;
      detailAsked = null;
    }
  }, 220);
}

/* -- turning, sliding and zooming -- */

canvas.addEventListener("pointerdown", event => {
  if (event.pointerType === "touch") {
    pinch.set(event.pointerId, [event.clientX, event.clientY]);
    if (pinch.size === 2) { spinning = panning = null; return; }
  }
  const [px, py] = pixel(event);
  const hit = markerAt(px, py);

  if (hit && event.shiftKey) {
    apply({ removed: (state.removed || []).concat([hit.id]) })
      .catch(e => say(e.message, true));
    return;
  }
  canvas.setPointerCapture(event.pointerId);
  if (hit && event.button === 0) { dragging = hit.id; return; }

  // Right button, middle button, or a held modifier slides the ground.
  // Left alone turns. Both are on the canvas, so neither is lost when
  // the pointer crosses the panel.
  const slide = event.button === 1 || event.button === 2 ||
                event.ctrlKey || event.metaKey || event.shiftKey;
  const seat = { x: event.clientX, y: event.clientY, target: orbit.target.slice() };
  if (slide) {
    // The camera as it stood when the ground was grabbed, kept for the
    // length of the gesture.
    //
    // A slide asks where the cursor lands on the ground and moves the
    // pivot by the difference. The pivot rides on the ground, so its
    // height moves the eye, which moves where the cursor lands, which
    // moves the pivot — a loop, and over real relief its gain is above
    // one. It oscillated: the scene lurched forward and back on
    // alternate frames for as long as the drag lasted, which is what
    // the flicker was.
    //
    // Reading every later cursor position against the grab-time camera
    // breaks the loop outright, and it is also what a rigid drag means:
    // the mapping from pixels to ground is the one that was on screen
    // when the ground was taken hold of.
    panning = Object.assign(seat, { at: groundUnder(px, py), from: view() });
  } else {
    panning = null;
    spinning = Object.assign(seat, { yaw: orbit.yaw, pitch: orbit.pitch });
  }
});

canvas.addEventListener("contextmenu", event => event.preventDefault());

canvas.addEventListener("pointermove", event => {
  if (event.pointerType === "touch" && pinch.has(event.pointerId)) {
    pinch.set(event.pointerId, [event.clientX, event.clientY]);
    if (pinch.size === 2) return twoFingers();
  }

  if (dragging) {
    const point = groundUnder(...pixel(event));
    if (point) {
      const anchor = latest.anchors.find(a => a.id === dragging);
      if (anchor) { anchor.x = point[0]; anchor.y = point[1]; render(); }
    }
    return;
  }

  if (panning) {
    // Slide by however far the ground has moved under the cursor, so
    // the point grabbed stays under it. Falls back to a distance-scaled
    // nudge when the ray misses the ground, which happens near the
    // horizon.
    // Refused when the slide is wilder than the distance being looked
    // from. Near the horizon a ray meets the ground kilometres away and
    // a pixel of movement throws the site off screen; that is a grab
    // that should never have been honoured, not a slide.
    const [atX, atY] = pixel(event);
    const here = panning.at && panning.from
      ? panning.from.onPlane(atX, atY, panning.at[2])
      : null;
    const far = here && panning.at
      && Math.hypot(panning.at[0] - here[0], panning.at[1] - here[1])
         > orbit.distance * 3;
    if (panning.at && here && !far) {
      orbit.target = onGround(
        panning.target[0] + (panning.at[0] - here[0]),
        panning.target[1] + (panning.at[1] - here[1]),
      );
    } else {
      const pace = orbit.distance * 0.0014;
      const along = -(event.clientX - panning.x) * pace;
      const across = (event.clientY - panning.y) * pace;
      orbit.target = onGround(
        panning.target[0] + along * Math.cos(orbit.yaw + Math.PI / 2)
          + across * Math.cos(orbit.yaw),
        panning.target[1] + along * Math.sin(orbit.yaw + Math.PI / 2)
          + across * Math.sin(orbit.yaw),
      );
    }
    render();
    return;
  }

  if (spinning) {
    orbit.yaw = spinning.yaw + (event.clientX - spinning.x) * 0.006;
    orbit.pitch = Math.min(HIGHEST_PITCH, Math.max(LOWEST_PITCH,
      spinning.pitch + (event.clientY - spinning.y) * 0.005));
    render();
  }
});

function twoFingers() {
  const [a, b] = [...pinch.values()];
  const span = Math.hypot(a[0] - b[0], a[1] - b[1]);
  if (pinchSpan && span > 1) {
    orbit.distance = Math.min(FURTHEST_M, Math.max(NEAREST_M,
      orbit.distance * (pinchSpan / span)));
    render();
  }
  pinchSpan = span;
}

function letGo(event) {
  if (event && pinch.has(event.pointerId)) {
    pinch.delete(event.pointerId);
    if (pinch.size < 2) pinchSpan = null;
  }
  if (dragging) {
    const anchor = latest.anchors.find(a => a.id === dragging);
    if (anchor) {
      const moved = Object.assign({}, state.moved);
      moved[dragging] = [anchor.x, anchor.y];
      // Moving an anchor forces no other setting to change, so it goes
      // straight through rather than to the confirmation sheet.
      apply({ moved }).catch(e => say(e.message, true));
    }
    dragging = null;
  }
  spinning = panning = null;
}

canvas.addEventListener("pointerup", letGo);
canvas.addEventListener("pointercancel", letGo);
window.addEventListener("blur", () => letGo(null));

canvas.addEventListener("wheel", event => {
  event.preventDefault();
  // Scaled by how much the wheel actually turned, so a trackpad's small
  // deltas creep and a mouse notch steps. The old fixed twelve percent
  // per event made a trackpad unusable and a mouse imprecise.
  const notches = Math.max(-4, Math.min(4, event.deltaY / 100));
  const was = orbit.distance;
  orbit.distance = Math.min(FURTHEST_M, Math.max(NEAREST_M,
    orbit.distance * Math.exp(notches * 0.18)));

  // Zoom towards the cursor rather than towards the middle. Without
  // this, getting close to one anchor means zooming in and then
  // hunting for it again.
  const under = groundUnder(...pixel(event));
  if (under && was > 0) {
    const share = 1 - orbit.distance / was;
    orbit.target = onGround(
      orbit.target[0] + (under[0] - orbit.target[0]) * share,
      orbit.target[1] + (under[1] - orbit.target[1]) * share,
    );
  }
  render();
}, { passive: false });

/* -- the keyboard, for anyone who would rather not drag -- */

const NUDGE = {
  ArrowLeft: [-1, 0], a: [-1, 0], ArrowRight: [1, 0], d: [1, 0],
  ArrowUp: [0, 1], w: [0, 1], ArrowDown: [0, -1], s: [0, -1],
};

window.addEventListener("keydown", event => {
  const typing = /^(INPUT|SELECT|TEXTAREA)$/.test(
    (document.activeElement || {}).tagName || "");
  if (typing || event.altKey || event.ctrlKey || event.metaKey) return;

  const nudge = NUDGE[event.key];
  if (nudge) {
    event.preventDefault();
    // Along the way the camera is facing, not along the world's axes,
    // which is what "forward" means to somebody looking at a screen.
    const pace = orbit.distance * (event.shiftKey ? 0.16 : 0.05);
    const [sideways, forward] = nudge;
    orbit.target = onGround(
      orbit.target[0] + pace * (forward * Math.cos(orbit.yaw)
        - sideways * Math.sin(orbit.yaw)),
      orbit.target[1] + pace * (forward * Math.sin(orbit.yaw)
        + sideways * Math.cos(orbit.yaw)),
    );
    return render();
  }

  if (event.key === "q" || event.key === "e") {
    orbit.yaw += event.key === "q" ? -0.12 : 0.12;
    return render();
  }
  // Tilting had no key at all, so the one gesture that cannot be done
  // with a trackpad's single button was also the one gesture the
  // keyboard could not do.
  if (event.key === "r" || event.key === "f") {
    orbit.pitch = Math.min(HIGHEST_PITCH, Math.max(LOWEST_PITCH,
      orbit.pitch + (event.key === "r" ? 0.1 : -0.1)));
    return render();
  }
  if (event.key === "+" || event.key === "=" || event.key === "-") {
    orbit.distance = Math.min(FURTHEST_M, Math.max(NEAREST_M,
      orbit.distance * (event.key === "-" ? 1.2 : 1 / 1.2)));
    return render();
  }
  if (event.key === "g" || event.key === "0") {
    frameEverything();
    return;
  }
});

/* Put the whole deployment back on screen. The one gesture a person
 * needs after getting lost, and getting lost is the price of being able
 * to go anywhere.
 *
 * The height matters as much as the middle. Ground in Ankara is 700 to
 * 1900 m above sea level and the relief is drawn five times over, so a
 * camera aimed at z = 0 looks at a point nearly six thousand units below
 * everything there is — which is a blank screen, and was one. Modelled
 * terrain averages zero and hid this until the scenarios moved onto real
 * ground.
 */
function frameEverything() {
  if (!latest || !latest.anchors.length) return;
  // The route counts. A corridor longer than its anchor run drives off
  // past the last mast, and framing on the masts alone left the far half
  // of the journey off screen.
  const route = latest.road || [];
  const xs = latest.anchors.map(a => a.x).concat(route.map(p => p.x));
  const ys = latest.anchors.map(a => a.y).concat(route.map(p => p.y));
  const zs = latest.anchors.map(a => a.ground_z);
  const span = Math.max(
    Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys), 1000);
  frameOn(
    [(Math.min(...xs) + Math.max(...xs)) / 2,
     (Math.min(...ys) + Math.max(...ys)) / 2,
     (zs.reduce((total, z) => total + z, 0) / zs.length) * draw.VERTICAL],
    span * 1.6,
  );
}

/* ---------- numbers ---------- */

const tr = (value, places = 2) =>
  Number(value).toFixed(places).replace(".", ",");

function showNumbers(drawn, result) {
  const list = document.getElementById("numbers");
  const rows = [];

  rows.push(["Direk sayısı", drawn.anchors.length]);
  // Per group, because a UWB bracket and a mast on one corridor do not
  // cover remotely the same ground and one number for both would say
  // they did.
  for (const run of drawn.runs || []) {
    rows.push([`${run.identifier}: menzil`, `${tr(run.reach_m / 1000)} km`]);
    rows.push([`${run.identifier}: kopma`, `${tr(run.closure_m / 1000)} km`]);
  }

  rows.push(["Alıcı sayısı", (drawn.units || []).length]);
  rows.push(["Tur süresi", `${tr(drawn.round_s * 1000, 0)} ms`]);
  rows.push(["Konum sıklığı", `${tr(1 / Math.max(drawn.round_s, 1e-9))} /s`]);

  if (sweepData) {
    rows.push(["Hizmet alanı", `${tr(sweepData.served_km2)} km²`]);
    rows.push(["Paketin ulaştığı alan", `${tr(sweepData.reached_km2)} km²`]);
  }
  if (result) {
    rows.push(["HPE P50", `${tr(result.hpe_p50_m)} m`]);
    rows.push(["HPE P95", `${tr(result.hpe_p95_m)} m`]);
    rows.push(["VPE P95", `${tr(result.vpe_p95_m)} m`]);
    rows.push(["Kullanılabilirlik", `%${tr(result.availability * 100)}`]);
    rows.push(["CAPEX", `${tr(result.capex_tl, 0)} TL`]);
    rows.push(["OPEX", `${tr(result.opex_tl_per_year, 0)} TL/yıl`]);
    rows.push(["CAPEX / km²", `${tr(result.capex_tl_per_km2, 0)} TL`]);
    rows.push(["OPEX / km²", `${tr(result.opex_tl_per_km2_year, 0)} TL/yıl`]);
    rows.push(["Varsayıma dayanan pay",
               `%${tr(result.assumed_share * 100, 0)}`]);
  }

  list.innerHTML = rows.map(([name, value]) =>
    `<dt>${name}</dt><dd${
      name === "Varsayıma dayanan pay" ? ' class="warn"' : ""
    }>${value}</dd>`).join("");
}


/* ---------- named options, and the work that takes minutes ----------
 *
 * Everything the command line can do, started from here. The page still
 * holds no physics: it posts what it wants, polls a task identifier, and
 * renders what comes back (ADR-0024).
 */

let optionsData = null;

async function loadOptions() {
  try {
    optionsData = await ask("/api/options");
    drawOptions();
    drawSolveScenarios();
  } catch (error) { say(error.message, true); }
}

function drawOptions() {
  const host = document.getElementById("options");
  if (!host || !optionsData) return;
  host.innerHTML = "";
  if (!optionsData.options.length) {
    host.innerHTML =
      '<p class="hint">Hazır seçenek yok. Çözücü ile bir tane kaydet.</p>';
    return;
  }
  for (const option of optionsData.options) {
    const card = document.createElement("div");
    card.className = "option";
    // Searchable by its name, its title and the figures it moves — a
    // ready-made option is a setting like any other.
    card.dataset.find = `seçenek ${option.name} ${option.title} `
      + (option.moves || []).map(move => `${move.key} ${named(move.key)}`)
        .join(" ");

    const head = document.createElement("header");
    head.innerHTML = `<b>${option.title}</b>`;
    const use = document.createElement("button");
    use.className = "quiet";
    use.textContent = "Uygula";
    use.onclick = () => applyOption(option.name);
    head.appendChild(use);
    card.appendChild(head);

    const moves = document.createElement("div");
    moves.className = "moves";
    // Named the way the figures list names them, so a person reading an
    // option and a person reading the figure it moves read the same
    // words. The key itself is a hover away.
    moves.innerHTML = option.moves.length
      ? option.moves.map(m =>
          `<span title="${m.key}">${named(m.key)}: ` +
          `${m.from} → ${m.to}</span>`).join("")
      : "<span>şu anki ayarlarla aynı</span>";
    card.appendChild(moves);

    const why = document.createElement("p");
    why.className = "why";
    why.textContent = option.note.split("\n")[0];
    card.appendChild(why);

    host.appendChild(card);
  }
}

async function applyOption(name) {
  try {
    const { applied } = await ask("/api/option", { name });
    await refreshScene();
    fillControls();
    await loadFigures();
    await loadOptions();
    say(`${applied} uygulandı.`);
  } catch (error) { say(error.message, true); }
}

/* -- watching a long task -- */

function logInto(host, job) {
  host.innerHTML = "";
  const log = document.createElement("div");
  log.className = "log";
  log.textContent = job.progress.join("\n");
  log.scrollTop = log.scrollHeight;
  host.appendChild(log);
  return log;
}

async function watch(kind, body, host, render) {
  const target = document.getElementById(host);
  target.innerHTML = '<p class="hint">Başlatılıyor…</p>';
  let job;
  try {
    ({ job } = await ask("/api/run", Object.assign({ kind }, body)));
  } catch (error) { return say(error.message, true); }

  const log = logInto(target, job);
  // A second between polls. The work reports a line per simulation and
  // a simulation is tens of seconds, so anything faster is just noise
  // on the wire.
  while (!job.done) {
    await new Promise(resume => setTimeout(resume, 1000));
    try {
      ({ job } = await ask(`/api/job?id=${job.id}`));
    } catch (error) { return say(error.message, true); }
    log.textContent = job.progress.join("\n");
    log.scrollTop = log.scrollHeight;
  }

  if (job.error) {
    say(job.error, true);
    const trouble = document.createElement("p");
    trouble.className = "hint";
    trouble.textContent = job.error;
    target.appendChild(trouble);
    return;
  }
  render(job.result, target);
}

/* -- the table -- */

function drawTable(result, host) {
  const table = document.createElement("table");
  table.className = "out";
  table.innerHTML =
    "<tr>" + result.columns.map(c => `<th>${c}</th>`).join("") + "</tr>" +
    result.rows.map(row =>
      `<tr><td>${row.system}</td>` +
      row.cells.map(c => `<td>${c}</td>`).join("") + "</tr>").join("");
  host.appendChild(table);
}

/* -- where the error came from -- */

function drawBudget(result, host) {
  for (const scenario of result.scenarios) {
    const table = document.createElement("table");
    table.className = "out";
    const head =
      `<tr><th colspan="4">${scenario.name} — HPE P50 ` +
      `${scenario.whole_p50_m} m · bir menzil ${scenario.range_sigma_m} m · ` +
      `geometri ×${scenario.geometry_gain}</th></tr>` +
      "<tr><th>Hata kaynağı</th><th>Tek başına</th><th>Kalkarsa</th>" +
      "<th>Kazanç</th></tr>";
    table.innerHTML = head + scenario.sources.map(source => {
      const width = Math.max(2, Math.round(source.share * 100));
      const shade = source.source === scenario.dominant ? " dominant" : "";
      return `<tr><td>${source.label}` +
        `<div class="bar${shade}" style="width:${width}%"></div></td>` +
        `<td>${source.alone_m}</td><td>${source.without_m}</td>` +
        `<td>${source.saves_m}</td></tr>`;
    }).join("") +
      `<tr><td>Model artığı</td><td>${scenario.residue_m}</td>` +
      "<td></td><td></td></tr>";
    host.appendChild(table);

    const note = document.createElement("p");
    note.className = "hint";
    note.textContent = scenario.dominant
      ? `Önce harcanacak yer: ${
          scenario.sources.find(s => s.source === scenario.dominant).remedy}.`
      : "Tek bir baskın kaynak yok: en büyük ikisi birbirine yakın.";
    host.appendChild(note);
  }
  const why = document.createElement("p");
  why.className = "hint";
  why.textContent =
    '"Tek başına" o kaynak tek olsaydı kalacak hata; "kalkarsa" o kaynak ' +
    "gidince toplamın ineceği yer. İkincisi her zaman daha küçüktür, çünkü " +
    "hatalar kareli toplanır — ve satın alma kararı olan odur.";
  host.appendChild(why);
}

/* -- the solver -- */

function drawSolveScenarios() {
  const select = document.getElementById("solve-scenario");
  if (!select || !optionsData) return;
  const names = Object.keys(optionsData.searchable);
  select.innerHTML = names
    .map(name => `<option value="${name}">${name}</option>`).join("");
  select.value = names.includes(state.scenario) ? state.scenario
    : names.includes("rural") ? "rural" : names[0];
  select.onchange = () => {
    varying = suggestedFor(select.value);
    drawSolveVary();
  };
  if (!varying.length) varying = suggestedFor(select.value);
  drawSolveVary();

  // Which rows the table and the dissection run. Derived from the mode
  // before, which meant the mixed corridor — not one of the report's
  // rows — quietly expanded to all three and took twelve minutes.
  const rows = document.getElementById("task-only");
  rows.innerHTML =
    `<option value="">üçü birden (+ ağırlıklı satır)</option>` +
    TABS.map(([name, label]) =>
      `<option value="${name}">yalnız ${label}</option>`).join("");
  rows.value = state.scenario;
  rows.onchange = drawSummary;
}

/* What the search may move, and what is worth trying.
 *
 * The short list per scenario is a starting point, not the search space.
 * Any figure in the settings file can be searched — the engine validates
 * the key and refuses one it has no entry for — so this lets a person
 * add, drop and retune rows rather than choosing from a menu somebody
 * else wrote (ADR-0025).
 */

let varying = [];

function suggestedFor(scenario) {
  const knobs = (optionsData && optionsData.searchable[scenario]) || {};
  return Object.entries(knobs).map(([key, values]) => ({ key, values }));
}

function drawSolveVary() {
  const host = document.getElementById("solve-vary");
  if (!host) return;
  host.innerHTML = "";

  for (const [index, row] of varying.entries()) {
    const card = document.createElement("div");
    card.className = "vary-row";

    const which = document.createElement("select");
    which.innerHTML = (figuresData ? figuresData.figures : [])
      .map(figure =>
        `<option value="${figure.key}"` +
        `${figure.key === row.key ? " selected" : ""}>` +
        `${figure.key}</option>`).join("");
    which.onchange = () => {
      varying[index].key = which.value;
      drawSolveVary();
    };

    const values = document.createElement("input");
    values.type = "text";
    values.className = "vary";
    values.value = row.values.join(", ");
    values.onchange = () => { varying[index].values = readValues(values.value); };

    const drop = document.createElement("button");
    drop.className = "drop";
    drop.title = "Bu sayıyı aramadan çıkar";
    drop.textContent = "✕";
    drop.onclick = () => { varying.splice(index, 1); drawSolveVary(); };

    card.append(which, values, drop);
    host.appendChild(card);
  }

  const buttons = document.createElement("div");
  buttons.className = "row";

  const add = document.createElement("button");
  add.className = "quiet";
  add.textContent = "Sayı ekle";
  add.onclick = () => {
    const first = figuresData && figuresData.figures[0];
    if (!first) return;
    // Seeded around whatever the figure is now, because a row that
    // starts empty is a row that searches nothing.
    const now = first.value;
    varying.push({ key: first.key, values: [now * 0.5, now, now * 1.5] });
    drawSolveVary();
  };

  const reset = document.createElement("button");
  reset.className = "quiet";
  reset.textContent = "Önerilene dön";
  reset.onclick = () => {
    varying = suggestedFor(document.getElementById("solve-scenario").value);
    drawSolveVary();
  };

  buttons.append(add, reset);
  host.appendChild(buttons);

  const size = document.createElement("p");
  size.className = "hint";
  const candidates = varying.reduce(
    (total, row) => total * Math.max(row.values.length, 1), 1);
  size.textContent = varying.length
    ? `${candidates} yerleşim denenecek. Her biri tam bir simülasyon.`
    : "Aranacak sayı yok. Ekle, ya da önerilene dön.";
  host.appendChild(size);
}

function readValues(text) {
  return text.split(",")
    .map(part => Number(part.trim()))
    .filter(value => Number.isFinite(value));
}

/* Read the rows back. A row with no usable numbers is dropped rather
 * than searched over nothing. */
function varyingNow() {
  const over = {};
  for (const row of varying) {
    if (row.values.length) over[row.key] = row.values;
  }
  return Object.keys(over).length ? over : null;
}

function drawDelivered(result, host) {
  const list = document.createElement("table");
  list.className = "out";
  list.innerHTML =
    `<tr><th colspan="2">${result.into}</th></tr>` +
    result.files.map(file =>
      `<tr><td>${file.name}</td><td>${file.about}</td></tr>`).join("");
  host.appendChild(list);
}

function drawFetched(result, host) {
  const table = document.createElement("table");
  table.className = "out";
  table.innerHTML =
    `<tr><th colspan="2">${result.name}</th></tr>` +
    `<tr><td>boyut</td><td>${result.width_m} × ${result.height_m} m</td></tr>` +
    `<tr><td>yükselti farkı</td><td>${result.relief_m} m</td></tr>` +
    `<tr><td>pürüz</td><td>${result.roughness_m} m</td></tr>` +
    `<tr><td>bina</td><td>${result.buildings}</td></tr>`;
  host.appendChild(table);

  for (const note of result.notes || []) {
    const line = document.createElement("p");
    line.className = "hint";
    line.textContent = note;
    host.appendChild(line);
  }

  const use = document.createElement("button");
  use.className = "quiet";
  use.textContent = "Bu zemine geç";
  use.onclick = () => edit({ site: result.name }, false)
    .then(() => { framed = false; return refreshScene(); })
    .then(() => fillControls())
    .catch(e => say(e.message, true));
  host.appendChild(use);
}

function wireTasks() {
  const chosenRows = () => {
    const picked = document.getElementById("task-only").value;
    return picked ? [picked] : [];
  };

  document.getElementById("run-table").onclick = () =>
    watch("table", { only: chosenRows() }, "task-out", drawTable);

  document.getElementById("run-budget").onclick = () =>
    watch("budget", { only: chosenRows() }, "task-out", drawBudget);

  document.getElementById("run-solve").onclick = () => {
    const number = id => {
      const raw = document.getElementById(id).value;
      return raw === "" ? null : Number(raw);
    };
    watch("solve", {
      scenario: document.getElementById("solve-scenario").value,
      target: {
        availability: number("solve-availability"),
        hpe_p50_m: number("solve-hpe50"),
        hpe_p95_m: number("solve-hpe95"),
        fixes_per_second: number("solve-fixes"),
      },
      vary: varyingNow(),
      save: document.getElementById("solve-save").value.trim(),
    }, "solve-out", drawSolved);
  };

  document.getElementById("run-deliver").onclick = () =>
    watch("deliver", {
      only: chosenRows(),
      into: document.getElementById("deliver-into").value.trim(),
      with_budget: document.getElementById("deliver-budget").checked,
    }, "task-out", drawDelivered);

  document.getElementById("run-fetch").onclick = () => {
    const box = id => {
      const raw = document.getElementById(id).value;
      return raw === "" ? null : Number(raw);
    };
    watch("fetch", {
      where: {
        name: document.getElementById("fetch-name").value.trim(),
        south: box("fetch-south"), west: box("fetch-west"),
        north: box("fetch-north"), east: box("fetch-east"),
        spacing_m: box("fetch-spacing"),
        buildings: document.getElementById("fetch-buildings").checked,
      },
    }, "fetch-out", drawFetched);
  };

  document.getElementById("frame-all").onclick = frameEverything;
}

/* ---------- the loop ---------- */

async function refreshScene() {
  latest = await ask("/api/scene");
  state = latest.state;
  // The server finds what ground has been fetched; the page never keeps
  // its own list, so a place fetched while this is running turns up on
  // the next refresh.
  SITES = latest.terrain.sites || [];
  if (latest.choices) {
    MOUNTINGS = latest.choices.mountings;
    RADIOS = latest.choices.radios;
    TABS = latest.choices.modes;
    for (const [name, label] of TABS) MODE_LABEL[name] = label;
  }
  drawTabs();
  drawSites();
  document.getElementById("terrain-note").textContent =
    `${latest.terrain.description} · ${latest.anchors.length} direk`;
  terrainData = latest.terrain;
  // The finer mesh described the ground before this edit. Dropped rather
  // than kept, or a change of site leaves the old hill drawn in the
  // middle of the new one.
  detail = null;
  detailAsked = null;
  if (!framed) {
    // Frame everything the first time, then leave the camera exactly
    // where the person put it. Re-centring on every refresh is what made
    // panning pointless: any slide was undone by the next edit.
    frameEverything();
    framed = true;
  }
  render();
  showNumbers(latest, null);
}

let sweepTimer = null;
function scheduleSweep() {
  sweepData = null;
  render();
  clearTimeout(sweepTimer);
  sweepTimer = setTimeout(async () => {
    try {
      say("Kapsama taranıyor…");
      sweepData = await ask("/api/sweep");
      render();
      showNumbers(latest, null);
      say("");
    } catch (error) { say(error.message, true); }
  }, 250);
}

async function runSimulation() {
  const button = document.getElementById("run");
  button.disabled = true;
  button.textContent = "Çalışıyor…";
  try {
    const result = await ask("/api/simulate");
    sweepData = sweepData || { served_km2: result.served_km2,
                               reached_km2: result.reached_km2 };
    showNumbers(latest, result);
  } catch (error) {
    say(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "Simülasyonu çalıştır";
  }
}

(async function start() {
  wireControls();
  wireTasks();
  wireSteps();
  wireFind();
  resize();
  await refreshScene();
  fillControls();
  await loadFigures();
  await loadOptions();
  scheduleSweep();
})();
