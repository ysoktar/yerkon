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

import { decimal, say, speak, speaks } from "./words.js";

/* The choices whose names are this page's to give.
 *
 * Built rather than written down, so that switching language rebuilds
 * them. Everything the engine can name for itself — the mountings, the
 * modules, the rows, the ground — is served already named (ADR-0035).
 */
const choicesNow = () => ({
  region: ["TR", "TR-FHSS", "EU", "US", "US-PTP", "LICENSED"]
    .map(code => [code, say("region." + code)]),
  scheme: [["single", say("scheme.single")], ["double", say("scheme.double")]],
});
let CHOICES = {};

/* Served by the engine rather than written here. The hardcoded version
 * drifted: it never listed the tunnel bracket, so the one mounting the
 * tunnel row uses could not be chosen and its dropdown quietly showed a
 * roadside sign instead. */
let RADIOS = [];
let LAYOUTS = [];
let ROUTES = [];
let ROUTES_LIVE = [];
/* Packages a fetch needs that this install has not got. Named by the
 * engine, like every other list here, so the page never holds a second
 * copy that can drift from it. */
let FETCH_MISSING = [];
/* The methods that search rather than lay a lattice down. They read a
 * bar and a budget instead of a spacing, so the card shows different
 * figures for them. */
const SEARCHES = ["greedy-coverage", "greedy-dop", "k-cover"];
let MOUNTINGS = [];
let TABS = [];
let LANGUAGES = [];
/* What each row is called, as the engine named it. */
const MODE_LABEL = {};
const kindsNow = () => [
  ["vehicle", say("unit.vehicle")], ["pedestrian", say("unit.pedestrian")],
];
let KINDS = [];

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

/* The line that tells you what just happened, and then stops.
 *
 * Named apart from `say`, which is the catalogue: one of them is a
 * phrase and the other is the place a phrase goes, and they read alike
 * enough that sharing a name would be a bug waiting for a long file.
 */
function flash(text, bad) {
  const el = document.getElementById("status");
  el.textContent = text;
  el.className = "on" + (bad ? " bad" : "");
  clearTimeout(flash.timer);
  if (text) flash.timer = setTimeout(() => { el.className = ""; }, 2600);
}

/* ---------- editing ---------- */

async function edit(changes, cascading) {
  if (cascading) {
    const { cascades } = await ask("/api/propose", { changes });
    if (cascades) { showConfirm(changes, cascades); return; }
  }
  await apply(changes);
}

/* The last simulation, while it still describes what is on screen.
 *
 * Kept rather than passed straight to the panel: a sweep landing after
 * a run used to redraw the numbers without it, so pressing Run while
 * coverage was still being scanned showed an answer that vanished a
 * second later. An edit does invalidate it, and clears it.
 */
let simulated = null;

/* Long enough that a slider drag never flickers, short enough that a
 * search — nine seconds over Kızılay — never looks like a finished
 * answer. */
const PATIENCE_MS = 400;

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
  tr: {
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
    width_m: ["Sahanın eni", ""],
    site: ["Zemin", ""],
    from_m: ["Grubun başlangıcı",
             "sahanın dışında kalan direk hiçbir şeyin modellemediği "
             + "zeminde durur"],
    to_m: ["Grubun bitişi",
           "sahanın dışında kalan direk hiçbir şeyin modellemediği "
           + "zeminde durur"],
    usable_range_m: ["Kullanılabilir menzil",
                     "menzil, hedeflenen hassasiyette link bütçesinin izin "
                     + "verdiği kadar"],
    closure_range_m: ["Bağlantının koptuğu mesafe",
                      "aynı bütçe bağlantının nerede çözülemez olduğunu "
                      + "belirliyor"],
  },
  // In English the engine's own label and reason are already English, so
  // this only names the two the page adds.
  en: {
    corridor_m: ["The site's length", ""],
    width_m: ["The site's width", ""],
    site: ["Ground", ""],
    from_m: ["The group's start",
             "an anchor past the end of the site stands on ground nothing "
             + "models and nothing drives past"],
    to_m: ["The group's end",
           "an anchor past the end of the site stands on ground nothing "
           + "models and nothing drives past"],
  },
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
  const found = (WORDS[speaks()] || {})[change.key];
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
      heading.textContent = say("confirm.group", { run: group.run });
      heading.style.color = "var(--accent)";
      body.appendChild(heading);
    }
    block(group.asked, say("confirm.asked"));
    block(group.follows, say("confirm.follows"));
  }
  document.getElementById("confirm").hidden = false;
}

/* One sentence and a yes/no, through the same sheet as the diff.
 *
 * Loading an arrangement is a change like any other and deserves the
 * same "here is what will happen, say yes" (ADR-0009) — but it replaces
 * a whole tab rather than moving three figures, and a sheet listing
 * forty rows says less than one sentence does. Same sheet, same buttons,
 * so there is one thing to recognise rather than two.
 */
let pendingPlainly = null;

function askPlainly(sentence) {
  return new Promise(resolve => {
    const body = document.getElementById("confirm-body");
    body.innerHTML = "";
    const line = document.createElement("p");
    line.textContent = sentence;
    body.appendChild(line);
    pendingPlainly = resolve;
    document.getElementById("confirm").hidden = false;
  });
}

document.getElementById("confirm-yes").onclick = async () => {
  document.getElementById("confirm").hidden = true;
  if (pendingPlainly) {
    const answer = pendingPlainly;
    pendingPlainly = null;
    return answer(true);
  }
  const changes = pendingChanges;
  pendingChanges = null;
  await apply(changes);
};

document.getElementById("confirm-no").onclick = () => {
  document.getElementById("confirm").hidden = true;
  if (pendingPlainly) {
    const answer = pendingPlainly;
    pendingPlainly = null;
    return answer(false);
  }
  pendingChanges = null;
  fillControls();          // put the control back where it was
  flash(say("confirm.nothing"));
};

/* ---------- controls ---------- */

const UNITS = {
  corridor_m: v => `${decimal(v / 1000, 1)} km`,
  width_m: v => (v > 0 ? `${decimal(v / 1000, 1)} km` : "koridor"),
  relief_m: v => (v > 0 ? `${v} m` : "düz"),
  hill_spacing_m: v => `${v} m`,
  roughness_m: v => `${decimal(v, 2)} m`,
  clutter_db_per_km: v => `${v} dB/km`,
  tolerance_m: v => `${decimal(v, 1)} m`,
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

/* ---------- saying the page in one language ----------
 *
 * Everything the page says for itself carries the name of what it says
 * rather than the words, and this puts the words in. Everything the
 * engine says for itself — a figure's note, what it affects, the ground's
 * description, an option's reason — arrives already in the language the
 * session is set to, because it lives beside the value it describes
 * (ADR-0035).
 */
function drawWords() {
  for (const element of document.querySelectorAll("[data-say]")) {
    element.textContent = say(element.dataset.say);
  }
  for (const element of document.querySelectorAll("[data-say-title]")) {
    element.title = say(element.dataset.sayTitle);
  }
  for (const element of document.querySelectorAll("[data-say-placeholder]")) {
    element.placeholder = say(element.dataset.sayPlaceholder);
  }
  CHOICES = choicesNow();
  KINDS = kindsNow();
  // Built in code rather than from `data-say`, so they do not come along
  // with the loops above and have to be redrawn by name. The thing that
  // goes wrong with two languages is translating nine tenths of
  // something and nobody noticing the tenth (ADR-0035).
  wireLayers();
  drawLegend();
  document.documentElement.lang = speaks();

  // The gestures, as one line. Built rather than written into the markup
  // because each is a key and a word, and the order of the two is not
  // the same in both languages.
  const gestures = document.getElementById("gestures");
  if (gestures) {
    gestures.innerHTML = [
      [say("scene.drag"), say("scene.turns")],
      [say("scene.slide_keys"), say("scene.slides")],
      [say("scene.wheel"), say("scene.zooms")],
      ["WASD", say("scene.walks")],
      ["Q/E", say("scene.turns")],
      ["R/F", say("scene.tilts")],
      ["G", say("scene.frames")],
    ].map(([key, what]) => `<b>${key}</b> ${what}`).join(" · ");
  }
}

function drawLanguages() {
  const host = document.getElementById("languages");
  if (!host || !LANGUAGES.length) return;
  host.innerHTML = "";
  for (const [code, name] of LANGUAGES) {
    const pick = document.createElement("button");
    pick.textContent = code.toUpperCase();
    pick.title = name;
    if (code === speaks()) pick.classList.add("on");
    pick.onclick = () => switchTo(code);
    host.appendChild(pick);
  }
}

/* Say the whole study in the other language.
 *
 * The engine is told first and then everything is redrawn from what it
 * sends back, rather than the page translating what it already has: the
 * notes, the options and the ground's description are the engine's
 * words, and asking it again is the only way to get them.
 */
async function switchTo(code) {
  if (code === speaks()) return;
  try {
    const { state: moved } = await ask("/api/language", { language: code });
    speak(code);
    state = moved;
    drawWords();
    drawLanguages();
    await refreshScene();
    fillControls();
    await loadFigures();
    await loadOptions();
    wireTasks();
    scheduleSweep();
  } catch (error) { flash(error.message, true); }
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
  } catch (error) { flash(error.message, true); }
}

function drawSites() {
  const select = document.getElementById("site");
  const entries = [["", say("ground.modelled")]]
    .concat(SITES.map(name => [name, say("ground.real", { site: name })]));
  select.innerHTML = options(entries, state.site || "");
  // Through the panel: a smaller fetch cannot hold a larger site, so
  // choosing ground can pull the length, the width and the anchor runs
  // in with it, and that is a change somebody should see first
  // (ADR-0009, ADR-0037).
  select.onchange = () => edit({ site: select.value }, true)
    .catch(e => flash(e.message, true));

  const real = Boolean(state.site);
  const note = document.getElementById("ground-note");
  if (note) {
    note.textContent = real
      ? (latest && latest.terrain && latest.terrain.description)
        || say("ground.none")
      : say("ground.none");
  }
  sayIfItCannotFetch();
  lockDeadKnobs();
}


/* An install that cannot fetch says so before a place is picked.
 *
 * The three packages a fetch needs are not dependencies of this one, on
 * purpose: the table is reproducible from the ground shipped inside the
 * package, with no network and no GDAL (ADR-0008). What was wrong was
 * finding that out at the end — a name typed, a box dragged on a map, a
 * fetch started, and then a sentence about a Python package. A control
 * that cannot do anything is not a control (ADR-0036, ADR-0051).
 */
function sayIfItCannotFetch() {
  const note = document.getElementById("fetch-cannot");
  const go = document.getElementById("run-fetch");
  const map = document.getElementById("open-map");
  const short = FETCH_MISSING.length > 0;
  if (note) {
    note.hidden = !short;
    if (short) note.textContent = say("fetch.cannot",
                                      { missing: FETCH_MISSING.join(", ") });
  }
  // Left in place and disabled rather than hidden, so somebody can see
  // what this page would do on a machine that has them.
  for (const button of [go, map]) if (button) button.disabled = short;
}

/* The three modelled-hill figures, and whether this state reads them.
 *
 * `ViewState.terrain` builds a bore from its portals and a fetched site
 * from its grid; either way these three go unread. A control that looks
 * live and changes nothing is worse than no control (ADR-0024).
 */
const MODELLED_HILLS = ["relief_m", "hill_spacing_m", "roughness_m"];

/* Every figure whose knob this arrangement might not read. */
const CAN_GO_UNREAD = MODELLED_HILLS.concat(["clutter_db_per_km"]);

function whyDead(key) {
  if (key === "clutter_db_per_km") {
    // A blanket loss per kilometre stands in for obstruction the terrain
    // cannot show. Where the fetch brought buildings the terrain shows
    // it, and charging both counts the same buildings twice (ADR-0038).
    const built = latest && latest.terrain && latest.terrain.buildings;
    return built ? "ground.buildings.note" : null;
  }
  if (!MODELLED_HILLS.includes(key)) return null;
  // The bore first: on the tunnel row both are true, and the reason the
  // figures go unread there is the bore rather than the mountain.
  if (state.bore) return "ground.bore.note";
  if (state.site) return "ground.real.note";
  return null;
}

/* Grey what this arrangement does not read, and say why beside it.
 *
 * Every knob is two inputs — a slider and the exact number beside it —
 * and disabling only the slider left the number box live, so measured
 * ground could still be given a relief by typing one. The whole knob is
 * locked and greyed here, from the state rather than from whichever
 * handler last ran, so it holds on a reload, a row change and a
 * language change alike.
 */
/* A site is no larger than the ground fetched for it.
 *
 * The engine refuses it either way and the panel says so, but a slider
 * that runs to forty kilometres over a three kilometre fetch invites the
 * refusal rather than showing the limit. Where the ground is modelled
 * there is no edge, so the slider goes back to its full travel.
 */
/* Why a number came back smaller than the one that was typed.
 *
 * Beside the knobs rather than in the status line, which is for what is
 * happening now: the sweep's own message replaced this one about a
 * second after it appeared, so the explanation was there and gone.
 */
function sayIfClipped(name, asked) {
  const note = document.getElementById("site-clipped");
  if (!note) return;
  const exact = document.getElementById(name + "-num");
  const ceiling = exact ? Number(exact.max) : NaN;
  if (!["corridor_m", "width_m"].includes(name)
      || !Number.isFinite(ceiling) || ceiling <= 0 || asked <= ceiling) {
    note.hidden = true;
    return;
  }
  note.hidden = false;
  note.textContent = say("site.clipped", {
    asked: decimal(asked / 1000, 2), held: decimal(ceiling / 1000, 2),
  });
}

function capSlidersToTheGround() {
  const measured = latest && latest.terrain && latest.terrain.measured_m;
  for (const [key, reach] of [["corridor_m", 0], ["width_m", 1]]) {
    const slider = document.getElementById(key);
    if (!slider) continue;
    const full = slider.dataset.fullMax || slider.max;
    slider.dataset.fullMax = full;
    const cap = measured
      ? String(Math.min(Number(full), Math.round(measured[reach])))
      : full;
    // Both halves, not just the slider. A cap on one of them is the
    // knob this project has already been caught by twice: a greyed
    // slider beside a live box, and now a capped slider beside a box
    // that accepts anything (ADR-0036, ADR-0048).
    for (const half of knobInputs(key)) half.max = cap;
  }
}

function lockDeadKnobs() {
  for (const key of CAN_GO_UNREAD) {
    const why = whyDead(key);
    for (const input of knobInputs(key)) input.disabled = Boolean(why);
    const knob = knobOf(key);
    if (knob) {
      knob.classList.toggle("dead", Boolean(why));
      // On the label rather than on the inputs: a disabled input does
      // not raise the events a tooltip waits for, so a title set there
      // is a reason nobody can read.
      knob.title = why ? say(why) : "";
    }
  }
  const modelled = document.getElementById("modelled-note");
  if (modelled) {
    // The note under step one speaks for the three hill figures; the
    // clutter knob carries its own reason on itself.
    const hills = whyDead("relief_m");
    modelled.textContent = say(hills || "ground.modelled.note");
  }
}

/* Leave room under the pinned header for anything scrolled to.
 *
 * `scrollIntoView` puts an element at the top of the scroll box, which
 * is behind the rows and the search once those are pinned — so opening
 * a step scrolled its own heading out of sight. Measured rather than
 * written down, because the header is two rows of text and its height
 * moves with the font.
 */
function keepClearOfTheHeader() {
  const panel = document.getElementById("panel");
  const top = document.getElementById("top");
  if (panel && top) {
    panel.style.scrollPaddingTop = `${Math.round(top.offsetHeight) + 8}px`;
  }
}

/* Both halves of a knob: the slider and the exact number beside it. */
function knobInputs(key) {
  return [document.getElementById(key), document.getElementById(key + "-num")]
    .filter(Boolean);
}

function knobOf(key) {
  const input = document.getElementById(key);
  return input ? input.closest("label.knob") : null;
}

function drawRuns() {
  const host = document.getElementById("runs");
  host.innerHTML = "";
  state.runs.forEach((run, index) => {
    const card = document.createElement("div");
    card.className = "card";
    card.dataset.find = `direk grup anchor group ${run.identifier} `
      + `modül montaj aralık yoldan kaydırma başlangıç bitiş `
      + `module mounting spacing stagger start end `
      + `${run.radio} ${run.mounting}`;

    const head = document.createElement("header");
    head.innerHTML =
      `<span class="swatch" style="background:${cssColour(runColour(index))}"></span>` +
      `<b>${run.identifier}</b>` +
      `<button class="drop" title="${say("run.drop")}">✕</button>`;
    head.querySelector(".drop").onclick = () => {
      const runs = state.runs.filter((_, i) => i !== index);
      if (!runs.length) { flash(say("run.least"), true); return; }
      edit({ runs }, false).catch(e => flash(e.message, true));
    };
    card.appendChild(head);

    const change = patch => {
      const runs = state.runs.map((r, i) =>
        i === index ? Object.assign({}, r, patch) : r);
      // A module or a mounting moves the link budget, so it has to be
      // confirmed. A position or a spacing does not.
      const cascading = "radio" in patch || "mounting" in patch;
      edit({ runs }, cascading).catch(e => flash(e.message, true));
    };

    for (const [key, list] of [["radio", RADIOS], ["mounting", MOUNTINGS]]) {
      const wrap = document.createElement("label");
      wrap.textContent = say(key === "radio" ? "run.module" : "run.mounting");
      const select = document.createElement("select");
      select.innerHTML = options(list, run[key]);
      select.onchange = () => change({ [key]: select.value });
      wrap.appendChild(select);
      card.appendChild(wrap);
    }

    // How this run is laid out. A lattice reads a spacing; a search
    // reads a bar to clear and a budget. Both sets stay on the run, so
    // switching the dropdown and switching back does not lose what was
    // set under the other one.
    const how = document.createElement("label");
    how.textContent = say("run.method");
    const method = document.createElement("select");
    method.innerHTML = options(LAYOUTS, run.method || "grid");
    method.onchange = () => change({ method: method.value });
    how.appendChild(method);
    card.appendChild(how);

    if (SEARCHES.includes(run.method)) {
      const bar = document.createElement("div");
      bar.className = "pair";
      if (run.method === "greedy-dop") {
        bar.appendChild(number(say("run.target_dop"), run.target_dop, 0.1,
          v => change({ target_dop: v })));
      }
      if (run.method === "k-cover") {
        bar.appendChild(number(say("run.cover_k"), run.cover_k, 1,
          v => change({ cover_k: v })));
      }
      bar.appendChild(number(say("run.most"), run.most, 5,
        v => change({ most: v })));
      card.appendChild(bar);
    }

    const pair = document.createElement("div");
    pair.className = "pair";
    pair.appendChild(number(say("run.from"), run.from_m, 100,
      v => change({ from_m: v })));
    pair.appendChild(number(say("run.to"), run.to_m, 100,
      v => change({ to_m: v })));
    if (!SEARCHES.includes(run.method)) {
      pair.appendChild(number(say("run.spacing"), run.spacing_m, 50,
        v => change({ spacing_m: v })));
    }
    pair.appendChild(number(say("run.offset"), run.offset_m, 10,
      v => change({ offset_m: v })));
    if (state.width_m > 0) {
      // Only over an area. A staggered row means nothing along a line,
      // and offering it there would suggest it did.
      pair.appendChild(number(say("run.stagger"), run.stagger_m, 25,
        v => change({ stagger_m: v })));
    }
    card.appendChild(pair);

    const found = (latest && latest.runs || []).find(
      r => r.identifier === run.identifier);
    if (found) {
      const note = document.createElement("p");
      note.className = "hint";
      note.style.margin = "4px 0 0";
      note.textContent = say("run.count", {
        anchors: found.count, reach: tr(found.reach_m / 1000),
      });
      card.appendChild(note);

      if (found.disc) {
        const disc = document.createElement("p");
        disc.className = found.disc.measured ? "hint" : "hint no-hits";
        disc.style.margin = "2px 0 0";
        disc.textContent = say(
          found.disc.by_hand ? "run.disc.by_hand"
            : found.disc.measured ? "run.disc" : "run.disc.ceiling",
          { metres: tr(found.disc.metres, 0) });
        card.appendChild(disc);
      }

      const verdict = barSaid(found.bar, run);
      if (verdict) {
        const line = document.createElement("p");
        line.className = found.bar.met ? "hint" : "hint no-hits";
        line.style.margin = "2px 0 0";
        line.textContent = verdict;
        card.appendChild(line);
      }
    }
    host.appendChild(card);
  });
}

/* What a search did against what it was asked for.
 *
 * A search stops for one of three reasons and only one of them is a
 * result: it cleared its bar, it ran out of budget, or nothing left to
 * add would help. From outside all three look the same, and over
 * Kızılay a dilution target of two cannot be met at all, so the search
 * bolted an anchor to every mountable structure on the site and read
 * exactly like one that had worked (ADR-0056).
 *
 * Nothing for a lattice. A spacing is not a target, and reporting one
 * as met would invent a claim the method never made.
 */
function barSaid(bar, run) {
  if (!bar) return "";

  // What the arrangement serves, whatever the bar was on. Said on every
  // search, because "cleared its bar" reads as "this works" and for
  // greedy-coverage it does not: over ground one disc covers it meets
  // its bar with a single mast and nowhere has the four anchors a
  // position needs (ADR-0060).
  // Anything that rounds to zero is said in words rather than printed
  // as "0 %", which reads as a rounding rather than as a finding. Over
  // Kızılay greedy-coverage serves 0,36 % of its own cells.
  const share = bar.served_share;
  const serves = share === undefined ? ""
    : (share * 100 < 0.5 ? say("run.bar.serves_nothing")
                         : say("run.bar.served", { share: tr(share * 100, 0) }));

  if (bar.met) return [say("run.bar.met"), serves].filter(Boolean).join(" · ");

  let missed;
  if (bar.name === "dilution" && bar.short > 0) {
    missed = say("run.bar.dilution.short", { short: bar.short });
  } else if (bar.name === "dilution") {
    missed = say("run.bar.dilution", {
      got: tr(bar.got), wanted: tr(bar.wanted),
    });
  } else if (bar.name === "anchors_in_reach") {
    missed = say("run.bar.anchors_in_reach", {
      got: tr(bar.got, 0), wanted: tr(bar.wanted, 0),
    });
  } else {
    missed = say("run.bar.covered_share", { short: bar.short });
  }
  // Why it stopped decides whether a larger budget would help, which is
  // the next thing somebody reaching for the budget wants to know.
  return [missed, say(
    bar.spent_the_budget ? "run.bar.budget" : "run.bar.candidates",
    { most: run.most }), serves].filter(Boolean).join(" · ");
}

function drawUnits() {
  const host = document.getElementById("units");
  host.innerHTML = "";
  state.units.forEach((unit, index) => {
    const card = document.createElement("div");
    card.className = "card";
    card.dataset.find = `alıcı receiver ${unit.identifier} ${unit.kind} `
      + `hız anten modül başlangıç speed antenna module start `
      + `güzergâh yol rota route path ${unit.route || ""} `
      + `${unit.radios.join(" ")}`;

    const head = document.createElement("header");
    head.innerHTML =
      `<span class="swatch" style="background:#b4551d;border-radius:50%"></span>` +
      `<b>${unit.identifier}</b>` +
      `<button class="drop" title="${say("unit.drop")}">✕</button>`;
    head.querySelector(".drop").onclick = () => {
      const units = state.units.filter((_, i) => i !== index);
      if (!units.length) { flash(say("unit.least"), true); return; }
      edit({ units }, false).catch(e => flash(e.message, true));
    };
    card.appendChild(head);

    const change = patch => {
      const units = state.units.map((u, i) =>
        i === index ? Object.assign({}, u, patch) : u);
      edit({ units }, false).catch(e => flash(e.message, true));
    };

    const wrap = document.createElement("label");
    wrap.textContent = say("unit.kind");
    const select = document.createElement("select");
    select.innerHTML = options(KINDS, unit.kind);
    select.onchange = () => change({ kind: select.value });
    wrap.appendChild(select);
    card.appendChild(wrap);

    // Which route this one drives. Per unit, because a van running the
    // ring road and a survey vehicle mowing the town are asking
    // different questions of the same anchors (ADR-0045).
    const where = document.createElement("label");
    where.textContent = say("unit.route");
    const route = document.createElement("select");
    route.innerHTML = options(ROUTES, unit.route || "");
    // A route this ground cannot carry is offered greyed rather than
    // hidden, so somebody can see it exists and why it is not available
    // (ADR-0036).
    for (const option of route.options) {
      if (option.value && !ROUTES_LIVE.includes(option.value)) {
        option.disabled = true;
        option.title = say("route.no_road");
      }
    }
    route.onchange = () => change({ route: route.value });
    where.appendChild(route);
    card.appendChild(where);

    const pair = document.createElement("div");
    pair.className = "pair";
    pair.appendChild(number(say("unit.speed"), unit.speed_km_h, 5,
      v => change({ speed_km_h: v })));
    pair.appendChild(number(say("unit.start"), unit.start_m, 100,
      v => change({ start_m: v })));
    pair.appendChild(number(say("unit.antenna"), unit.antenna_height_m, 0.1,
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
          flash(say("unit.needs_module"), true);
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
      note.textContent = say("unit.hears", { anchors: heard.hears });
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
  battery_life_years: "akü ömrü (amortisman)",
  battery_tl: "akü fiyatı",
  crew_size: "bakım ekibi kişi sayısı",
  crew_travels: "ekip şehir dışına gidiyor",
  off_grid_life_years: "güneş beslemesi ömrü (amortisman)",
  per_diem_tl: "harcırah, kişi başı gündelik",
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
  distribution_pole: "elektrik dağıtım direği",
  demodulation_threshold_db: "çözme eşiği",
  electricity_tl_per_kwh: "elektrik birim fiyatı",
  estimator: "kestirici",
  profile_spacing_m: "profil örnek aralığı",
  shadow_correlation_m: "gölge boyu",
  shadow_draws: "gölge çekilişi",
  shadow_seed: "gölge tohumu",
  shadow_sigma_db: "gölgeleme, yol açıkken",
  shadow_sigma_obstructed_db: "gölgeleme, yol kapalıyken",
  extent_m: "uzunluk",
  fix_horizontal_sigma_m: "konum çıtası, yatay belirsizlik",
  gate_sigmas: "filtre kapısı",
  height_aid_sigma_m: "harita yükseklik hatası",
  height_aid_correlation_m: "harita hatasının boyu",
  extra_off_grid_visits_per_year: "şebeke dışı ek ziyaret",
  ground_levels: "zemin pürüz katmanı",
  ground_patch_m: "zemin yaması",
  ground_roughness_spread: "pürüz saçılımı",
  ground_seed: "zemin tohumu",
  height_m: "yükseklik",
  junction_every: "ışıklı kavşak aralığı",
  length_m: "uzunluk",
  lighting_column: "aydınlatma direği",
  maintenance_tl_per_visit: "bakım, ziyaret başına",
  maintenance_visits_per_year: "yıllık bakım ziyareti",
  manoeuvre_m_s2: "manevra ivmesi",
  mounting: "montaj",
  noise_figure_db: "gürültü katsayısı",
  off_grid_supply_tl: "şebeke dışı besleme",
  operating: "işletme",
  nlos_bias_mean_m: "görüş dışı yanlılık, ortalama",
  packet_loss: "paket kaybı",
  payload_bytes: "paket yükü",
  rent_tl_per_year: "yıllık kira",
  rooftop: "çatı",
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

/* A figure's name, in the language the page is speaking.
 *
 * In English there is nothing to look up: the key is already English, so
 * the underscores come out and the words are the words. A glossary for
 * it would be a second list saying the same thing and drifting from the
 * first.
 */
const named = key => key.split(".").slice(1).map(
  part => (speaks() === "en" ? part.replace(/_/g, " ") : TERMS[part] || part)
).join(" · ");

const CASCADING_FIGURES = /(height_m|noise_figure_db|threshold_db|clutter|residual_ppm|tolerance_ppm|turnaround_s|payload_bytes)/;

function drawFigures() {
  const host = document.getElementById("figures");
  if (!figuresData) { host.innerHTML = ""; return; }
  host.innerHTML = "";

  document.getElementById("assumed-count").textContent =
    say("figures.assumed",
      { assumed: figuresData.assumed, total: figuresData.total });

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
      const whence = say("prov." + where);
      // Its key, its name, its group, where it came from and what it
      // affects, so the search finds it by any of them.
      row.dataset.find = `${figure.key} ${named(figure.key)} ${group.label} `
        + `${whence} ${figure.affects}`;

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
      mark.title = whence;
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
          [["", say("ground.modelled")]].concat(SITES.map(n => [n, n])),
          String(figure.value));
      } else {
        input.type = "number";
        input.value = figure.value;
        input.step = "any";
      }
      if (figure.edited) input.classList.add("edited");
      input.title = figure.assumed
        ? say("figures.still_assumed")
        : say("figures.source", { source: figure.source });
      input.onchange = () => {
        const overrides = Object.assign({}, state.overrides);
        overrides[figure.key] = figure.is_text
          ? input.value : Number(input.value);
        edit({ overrides }, CASCADING_FIGURES.test(figure.key))
          .catch(e => flash(e.message, true));
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
  } catch (error) { flash(error.message, true); }
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
  // However the figures got there: the button, a hand edit, a preset,
  // or clearing the overrides.
  drawHurry();
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
    ? say("figures.assumed",
      { assumed: figuresData.assumed, total: figuresData.total })
    : "—";
  const edits = Object.keys(state.overrides || {}).length;
  const scope = document.getElementById("task-only");

  const said = {
    "sum-place": state.site
      ? say("sum.place.real", { site: state.site })
      : say("sum.place.modelled", {
          relief: UNITS.relief_m(state.relief_m),
          spacing: UNITS.hill_spacing_m(state.hill_spacing_m),
        }),
    "sum-site": state.width_m > 0
      ? say("sum.site.area", {
          length: UNITS.corridor_m(state.corridor_m),
          width: UNITS.width_m(state.width_m),
        })
      : say("sum.site.corridor", { length: UNITS.corridor_m(state.corridor_m) }),
    "sum-layout": say("sum.layout", {
      anchors, runs: state.runs.length, units: state.units.length,
    }),
    "sum-target": say("sum.target", {
      tolerance: UNITS.tolerance_m(state.tolerance_m),
      region: state.region,
      scheme: say("sum.scheme." + state.scheme),
    }),
    "sum-basis": edits ? say("sum.basis.edits", { assumed, edits }) : assumed,
    // An empty value is every row; a named one is that row alone.
    "sum-run": scope && scope.value
      ? say("run.one_row", { row: MODE_LABEL[scope.value] || scope.value })
      : say("run.all_rows"),
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
        .catch(e => flash(e.message, true));
  }

  for (const name of Object.keys(OUTPUTS)) {
    const slider = document.getElementById(name);
    if (!slider) continue;
    const exact = document.getElementById(name + "-num");
    const send = value =>
      edit({ [name]: Number(value) }, slider.hasAttribute("data-cascades"))
        .catch(e => flash(e.message, true));

    // While the handle is moving, only the page follows. The engine is
    // asked once, when it is let go, because a sweep takes seconds.
    slider.oninput = () => showKnob(name, slider.value);
    slider.onchange = () => {
      sayIfClipped(name, Number(slider.value));
      send(slider.value);
    };
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
      exact.onchange = () => {
        // `fillControls` puts the box back to what is in force once the
        // edit lands, so a number the ground cannot hold returns to the
        // ground's own. Said as well as shown: a box that springs back
        // with no explanation reads as the page having lost the keypress
        // rather than as the site being what it is (ADR-0037).
        sayIfClipped(name, Number(exact.value));
        send(exact.value);
      };
    }
  }

  document.getElementById("add-run").onclick = () => {
    const letters = "ABCDEFGHJKLMNPQRSTUVWXYZ";
    const used = new Set(state.runs.map(r => r.identifier));
    const identifier = [...letters].find(l => !used.has(l)) || "Z";
    const last = state.runs[state.runs.length - 1];
    // Never past the end of the site.
    //
    // This used to reach a flat 3000 m whatever the site was, so on
    // Kızılay — 2970 m of measured ground — a new group put its last
    // column thirty metres past the edge. Nothing raised: the terrain
    // clamps outside itself, so the anchors simply stood on the boundary
    // row extruded into a plane (ADR-0037). It showed up as an
    // arrangement that was saved with twelve anchors and loaded with
    // nine, because loading brings a site inside its measured ground.
    const edge = Math.max(state.corridor_m, 0);
    const start = last ? Math.min(last.to_m + 500, edge) : 0;
    edit({ runs: state.runs.concat([{
      identifier,
      radio: last ? last.radio : "sx1280",
      mounting: last ? last.mounting : "mast",
      stagger_m: last ? last.stagger_m : 0,
      from_m: start,
      to_m: Math.min(last ? last.to_m + 3000 : 3000, edge),
      spacing_m: last ? last.spacing_m : 1000,
      offset_m: last ? last.offset_m : 100,
    }]) }, false).catch(e => flash(e.message, true));
  };

  document.getElementById("add-unit").onclick = () => {
    const used = new Set(state.units.map(u => u.identifier));
    let identifier = say("unit.new");
    let n = 2;
    while (used.has(identifier)) identifier = `${say("unit.new")} ${n++}`;
    edit({ units: state.units.concat([{
      identifier, kind: "vehicle", speed_km_h: 80, start_m: 0,
      antenna_height_m: 1.5, radios: ["sx1280", "dwm3000"],
    }]) }, false).catch(e => flash(e.message, true));
  };

  document.getElementById("clear-overrides").onclick = () => {
    if (!Object.keys(state.overrides || {}).length) {
      flash(say("figures.none_edited"));
      return;
    }
    edit({ overrides: {} }, true).catch(e => flash(e.message, true));
  };

  wireMap();
  wirePresets();
  wireLayers();
  drawLegend();

  document.getElementById("show-photo").onchange = event => {
    showPhotograph = event.target.checked;
    render();
  };

  document.getElementById("only-assumed").onchange = event => {
    onlyAssumed = event.target.checked;
    drawFigures();
  };

  document.getElementById("run").onclick = runSimulation;
  document.getElementById("hurry").onclick = async () => {
    const overrides = Object.assign({}, state.overrides);
    if (hurrying()) {
      for (const key of Object.keys(HURRIED)) delete overrides[key];
    } else {
      Object.assign(overrides, HURRIED);
    }
    // The figures decide how long a run takes, so the answer on screen
    // was worked out under the other setting and no longer describes
    // what pressing Run would give.
    simulated = null;
    await edit({ overrides }, false).catch(e => flash(e.message, true));
    drawHurry();
    showNumbers(latest, simulated);
  };
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

import * as draw from "./draw.js";
import * as pick from "./map.js";

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

/* The aerial photograph of the fetched ground, once it has arrived.
 *
 * Fetched as a picture and read once into an offscreen canvas, not sent
 * as colours with the scene: the mesh is twenty-two thousand nodes, and
 * putting three bytes of colour on each of them would be a quarter of a
 * megabyte on the wire every time somebody drags the camera, to say what
 * one cached PNG says once.
 *
 * Null until it loads and null where no site has one, and the painter
 * falls back to the olive it has always drawn — so the ground is never
 * waiting on a picture to appear.
 */
let photograph = null;
let photographUrl = "";
let showPhotograph = true;

function aerialOf() {
  return (latest && latest.terrain && latest.terrain.aerial) || null;
}

/* Load the site's photograph, or drop the one in hand where there is none.
 *
 * Keyed on the address, so a redraw does not refetch and changing ground
 * does. The pixels are read out of the canvas once, here, rather than
 * per quad per frame: `getImageData` is a round trip to the compositor
 * and four thousand of them a frame is not a frame.
 */
function loadPhotograph() {
  const aerial = aerialOf();
  if (!aerial) {
    photograph = null;
    photographUrl = "";
    return;
  }
  if (aerial.url === photographUrl) return;
  photographUrl = aerial.url;
  photograph = null;

  // Another site's picture may have been asked for while this one was
  // in flight; the last one asked for is the one that belongs.
  const stillWanted = () => photographUrl === aerial.url;
  const dropped = () => { if (stillWanted()) photograph = null; };

  if (aerial.tiles) {
    stitchTiles(aerial.tiles).then(sheet => {
      if (stillWanted()) takePhotograph(sheet, aerial);
    }, dropped);
    return;
  }

  const picture = new Image();
  picture.onload = () => {
    if (!stillWanted()) return;
    const sheet = document.createElement("canvas");
    sheet.width = picture.naturalWidth;
    sheet.height = picture.naturalHeight;
    sheet.getContext("2d", { willReadFrequently: true }).drawImage(picture, 0, 0);
    takePhotograph(sheet, aerial);
  };
  picture.onerror = dropped;
  // Asked for with fetch rather than handed to the image as its address.
  // On the published site there is no server behind /api/: the page's
  // fetch is answered by the worker that fetched the ground, and an
  // image's own request would go to the network and find nothing
  // (ADR-0086). Same bytes from the local server.
  fetch(aerial.url)
    .then(reply => (reply.ok ? reply.blob() : Promise.reject(reply.status)))
    .then(blob => {
      if (!stillWanted()) return;
      const address = URL.createObjectURL(blob);
      picture.addEventListener("load", () => URL.revokeObjectURL(address),
                               { once: true });
      picture.src = address;
    })
    .catch(dropped);
}

/* The pixels of a finished sheet, read out once for the painter. */
function takePhotograph(sheet, aerial) {
  const pen = sheet.getContext("2d", { willReadFrequently: true });
  let pixels;
  try {
    pixels = pen.getImageData(0, 0, sheet.width, sheet.height).data;
  } catch {
    // A canvas the browser considers tainted. Same ground, no picture.
    photograph = null;
    return;
  }
  photograph = draw.photoSampler(
    pixels, sheet.width, sheet.height, aerial.extent_m);
  render();
}

/* A photograph put together here from the provider's tiles (ADR-0087).
 *
 * The site says which tiles cover it; the browser fetches and decodes
 * them, which a plain install on the other end has no library to do.
 * Asked for as anonymous requests so the sheet can be read back, and a
 * tile that does not come is a grey square rather than no picture.
 */
function stitchTiles(tiles) {
  const side = 256;
  const columns = tiles.east_x - tiles.west_x + 1;
  const rows = tiles.south_y - tiles.north_y + 1;
  const sheet = document.createElement("canvas");
  sheet.width = columns * side;
  sheet.height = rows * side;
  const pen = sheet.getContext("2d", { willReadFrequently: true });
  pen.fillStyle = "rgb(128, 128, 128)";
  pen.fillRect(0, 0, sheet.width, sheet.height);
  const arrivals = [];
  for (let y = tiles.north_y; y <= tiles.south_y; y++) {
    for (let x = tiles.west_x; x <= tiles.east_x; x++) {
      arrivals.push(new Promise(settle => {
        const tile = new Image();
        tile.crossOrigin = "anonymous";
        tile.onload = () => {
          pen.drawImage(tile, (x - tiles.west_x) * side,
                        (y - tiles.north_y) * side, side, side);
          settle(true);
        };
        tile.onerror = () => settle(false);
        tile.src = tiles.template.replace("{z}", tiles.zoom)
          .replace("{x}", x).replace("{y}", y);
      }));
    }
  }
  return Promise.all(arrivals).then(arrived =>
    (arrived.some(Boolean) ? sheet : Promise.reject(new Error("no tiles"))));
}

/* The photograph the painter should use this frame, if any. */
function drawnPhotograph() {
  return showPhotograph ? photograph : null;
}

/* Grey the tick where this ground has no photograph, and say why.
 *
 * Modelled ground never has one; fetched ground has one only where the
 * fetch was given a tile server to ask (ADR-0036, and the same shape as
 * `lockDeadKnobs`).
 */
function lockPhotographTick() {
  const tick = document.getElementById("photo-tick");
  const box = document.getElementById("show-photo");
  if (!tick || !box) return;
  const aerial = aerialOf();
  box.disabled = !aerial;
  tick.classList.toggle("dead", !aerial);
  tick.title = aerial
    ? say("ground.photo.from", { source: aerial.source || "—" })
    : say(state.site ? "ground.photo.none" : "ground.photo.modelled");
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
    ...draw.groundFaces(view, drawnTerrain(), light, drawnPhotograph()),
    ...draw.cellFaces(view, sweepData, groundAt, bias, shownLayer),
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
      .catch(e => flash(e.message, true));
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
      apply({ moved }).catch(e => flash(e.message, true));
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

function showNumbers(drawn, result, pending) {
  const list = document.getElementById("numbers");
  const rows = [];

  const warn = say("result.assumed_share");
  const hurried = say("result.hurry");

  rows.push([say("result.anchors"), drawn.anchors.length]);
  // Per group, because a UWB bracket and a mast on one corridor do not
  // cover remotely the same ground and one number for both would say
  // they did.
  for (const run of drawn.runs || []) {
    rows.push([say("result.reach", { run: run.identifier }),
               `${tr(run.reach_m / 1000)} km`]);
    rows.push([say("result.closure", { run: run.identifier }),
               `${tr(run.closure_m / 1000)} km`]);
  }

  rows.push([say("result.units"), (drawn.units || []).length]);
  // A dash for what does not exist, rather than a number computed from
  // nothing. An arrangement with no anchors has no round and no covered
  // ground, and printing "0 ms" and a billion fixes a second states
  // both as findings (ADR-0043).
  const round = drawn.round_s;
  rows.push([say("result.round"),
             round ? `${tr(round * 1000, 0)} ms` : NOTHING]);
  rows.push([say("result.rate"), round ? `${tr(1 / round)} /s` : NOTHING]);

  // Both rows are always here, because a row that comes and goes moves
  // everything under it and reads as a change in the answer.
  rows.push([say("result.served"),
             sweepData ? area(sweepData.served_km2) : WORKING]);
  rows.push([say("result.reached"),
             sweepData ? area(sweepData.reached_km2) : WORKING]);
  if (result) {
    // Which of the figures below are still one draw of the shadows. A
    // single draw put the rural row's P95 anywhere between 9,67 and
    // 18,75 m, so a number read before the rest land is a sample and
    // the row above it says which (ADR-0055, ADR-0059).
    const done = result.draws_done || 1;
    const wanted = result.draws_wanted || 1;
    if (wanted > 1) {
      rows.push([say("result.draws"),
                 done < wanted ? say("result.draws.first", { done, wanted })
                               : say("result.draws.pooled", { wanted })]);
    }
    // Above the figures it applies to, and named so the reader knows
    // which of the two coarse readings is in force rather than only
    // that something is (ADR-0063).
    if (hurrying()) {
      const given_up = [];
      if (Number(state.overrides["site.shadow_draws"]) === 1) {
        given_up.push(say("result.hurried.draws"));
      }
      if (Number(state.overrides["site.profile_spacing_m"]) === 0) {
        given_up.push(say("result.hurried.profile"));
      }
      rows.push([hurried, `${say("result.hurried")}: ${given_up.join(", ")}`]);
    }
    rows.push([say("result.hpe50"), `${tr(result.hpe_p50_m)} m`]);
    rows.push([say("result.hpe95"), `${tr(result.hpe_p95_m)} m`]);
    rows.push([say("result.vpe95"), `${tr(result.vpe_p95_m)} m`]);
    rows.push([say("result.availability"), `%${tr(result.availability * 100)}`]);
    rows.push([say("result.capex"), `${tr(result.capex_tl, 0)} TL`]);
    rows.push([say("result.opex"), `${tr(result.opex_tl_per_year, 0)} TL`]);
    rows.push([say("result.capex_km2"), `${tr(result.capex_tl_per_km2, 0)} TL`]);
    rows.push([say("result.opex_km2"),
               `${tr(result.opex_tl_per_km2_year, 0)} TL`]);
    rows.push([warn, `%${tr(result.assumed_share * 100, 0)}`]);
  }

  // While the engine is working these rows describe the arrangement
  // before the edit, so they are not shown as if they described this
  // one. The names stay, because a panel whose rows come and go moves
  // under the reader.
  list.innerHTML = rows.map(([name, value]) =>
    `<dt>${name}</dt><dd${name === warn || name === hurried
      ? ' class="warn"' : ""}>`
    + `${pending ? WORKING : value}</dd>`
  ).join("");
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
  } catch (error) { flash(error.message, true); }
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
    card.dataset.find = `seçenek option ${option.name} ${option.title} `
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
      : `<span>${say("options.same")}</span>`;
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
    flash(say("options.applied", { name: applied }));
  } catch (error) { flash(error.message, true); }
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
  } catch (error) { return flash(error.message, true); }

  const log = logInto(target, job);
  // A second between polls. The work reports a line per simulation and
  // a simulation is tens of seconds, so anything faster is just noise
  // on the wire.
  while (!job.done) {
    await new Promise(resume => setTimeout(resume, 1000));
    try {
      ({ job } = await ask(`/api/job?id=${job.id}`));
    } catch (error) { return flash(error.message, true); }
    log.textContent = job.progress.join("\n");
    log.scrollTop = log.scrollHeight;
  }

  if (job.error) {
    flash(job.error, true);
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
      `<tr><th colspan="4">${scenario.name}: HPE P50 ` +
      `${scenario.whole_p50_m} m · bir menzil ${scenario.range_sigma_m} m · ` +
      `${say("budget.geometry", { gain: scenario.geometry_gain })}</th></tr>` +
      `<tr><th>${say("budget.source")}</th><th>${say("budget.alone")}</th>` +
      `<th>${say("budget.without")}</th><th>${say("budget.gain")}</th></tr>`;
    table.innerHTML = head + scenario.sources.map(source => {
      const width = Math.max(2, Math.round(source.share * 100));
      const shade = source.source === scenario.dominant ? " dominant" : "";
      return `<tr><td>${source.label}` +
        `<div class="bar${shade}" style="width:${width}%"></div></td>` +
        `<td>${source.alone_m}</td><td>${source.without_m}</td>` +
        `<td>${source.saves_m}</td></tr>`;
    }).join("") +
      `<tr><td>${say("budget.residue")}</td><td>${scenario.residue_m}</td>` +
      "<td></td><td></td></tr>";
    host.appendChild(table);

    const note = document.createElement("p");
    note.className = "hint";
    note.textContent = scenario.dominant
      ? `Önce harcanacak yer: ${
          scenario.sources.find(s => s.source === scenario.dominant).remedy}.`
      : say("budget.no_dominant");
    host.appendChild(note);
  }
  const why = document.createElement("p");
  why.className = "hint";
  why.textContent =
    say("budget.note");
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
    `<option value="">${say("run.all_rows")}</option>` +
    TABS.map(([name, label]) =>
      `<option value="${name}">${say("run.one_row", { row: label })}</option>`).join("");
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
    drop.title = say("vary.drop");
    drop.textContent = "✕";
    drop.onclick = () => { varying.splice(index, 1); drawSolveVary(); };

    card.append(which, values, drop);
    host.appendChild(card);
  }

  const buttons = document.createElement("div");
  buttons.className = "row";

  const add = document.createElement("button");
  add.className = "quiet";
  add.textContent = say("vary.add");
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
  reset.textContent = say("vary.reset");
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
    ? say("vary.count", { candidates })
    : say("vary.none");
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
    `<tr><td>${say("fetched.size")}</td>` +
    `<td>${result.width_m} × ${result.height_m} m</td></tr>` +
    `<tr><td>${say("fetched.relief")}</td><td>${result.relief_m} m</td></tr>` +
    `<tr><td>${say("fetched.roughness")}</td>` +
    `<td>${result.roughness_m} m</td></tr>` +
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
  use.textContent = say("fetched.use");
  // Through the panel, like the ground picker beside it: a place smaller
  // than the row standing on it pulls the length, the width and the
  // anchor runs in, and that is a change somebody should see first
  // (ADR-0009, ADR-0037). This button used to skip it, which made the
  // likeliest path — fetch, then use it — the one that resized a site
  // without saying so.
  use.onclick = () => edit({ site: result.name }, true)
    .then(() => { framed = false; return refreshScene(); })
    .then(() => fillControls())
    .catch(e => flash(e.message, true));
  host.appendChild(use);

  // And list it in the ground picker straight away. The engine finds
  // what has been fetched on every scene, so one refresh is enough —
  // without it a fetch reports success and the place it wrote is
  // nowhere on screen until something else happens to refresh.
  refreshScene().catch(e => flash(e.message, true));
}

/* What the placement search chose, beside the layout it replaces. */
function drawPlaced(result, host) {
  const table = document.createElement("table");
  table.className = "out";
  table.innerHTML =
    `<tr><th></th><th>${say("place.now")}</th><th>${say("place.found")}</th></tr>` +
    `<tr><td>${say("place.anchors")}</td><td>${result.grid_anchors}</td>` +
    `<td>${result.anchors}</td></tr>` +
    `<tr><td>${say("place.served")}</td><td>%${result.grid_share}</td>` +
    `<td>%${result.share}</td></tr>` +
    `<tr><td>${say("place.cost")}</td><td>${result.grid_lifecycle_tl} TL</td>` +
    `<td>${result.lifecycle_tl} TL</td></tr>` +
    Object.entries(result.mix).map(([origin, n]) =>
      `<tr><td>${origin}</td><td></td><td>${n}</td></tr>`).join("");
  host.appendChild(table);

  const note = document.createElement("p");
  note.className = "hint";
  note.textContent = say("place.judge");
  host.appendChild(note);

  const use = document.createElement("button");
  use.className = "quiet";
  use.textContent = say("place.use");
  // Through the panel like every other edit: it replaces every anchor
  // on the row, and that is a change somebody should see first.
  use.onclick = () => edit(result.changes, true)
    .then(() => fillControls())
    .catch(e => flash(e.message, true));
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

  document.getElementById("run-place").onclick = () =>
    watch("place", { aim: document.getElementById("place-aim").value },
          "place-out", drawPlaced);

  document.getElementById("run-deliver").onclick = () =>
    watch("deliver", {
      only: chosenRows(),
      into: document.getElementById("deliver-into").value.trim(),
      with_budget: document.getElementById("deliver-budget").checked,
    }, "task-out", drawDelivered);

  wireFetchBox();
  document.getElementById("run-fetch").onclick = () => {
    const spacing = document.getElementById("fetch-spacing").value;
    watch("fetch", {
      where: {
        name: document.getElementById("fetch-name").value.trim(),
        centre: document.getElementById("fetch-centre").value.trim(),
        size_km: Number(document.getElementById("fetch-size").value),
        spacing_m: spacing === "" ? null : Number(spacing),
        buildings: document.getElementById("fetch-buildings").checked,
        imagery: document.getElementById("fetch-imagery").checked,
        // A box drawn on the map goes as its four corners, because it is
        // whatever shape somebody dragged and a centre with one size can
        // only say "square". Absent, the centre and the size decide, the
        // way they did before there was a map.
        ...(pickedBox || {}),
      },
    }, "fetch-out", drawFetched);
  };

  document.getElementById("frame-all").onclick = frameEverything;
}

/* ---------- what the ground overlay reads ---------- */

/* Which of the sweep's four readings is painted. */
let shownLayer = "anchors";

const LAYERS = ["anchors", "margin_db", "dilution", "error_m"];

/* How each band's range is written, in the layer's own units. */
const BAND_UNITS = {
  anchors: v => `${v}`,
  margin_db: v => `${decimal(v, 0)} dB`,
  dilution: v => decimal(v, 1),
  error_m: v => `${decimal(v, 1)} m`,
};

function wireLayers() {
  const pick = document.getElementById("layer-pick");
  if (!pick) return;
  pick.innerHTML = options(LAYERS.map(k => [k, say(`layer.${k}`)]), shownLayer);
  pick.onchange = () => {
    shownLayer = pick.value;
    drawLegend();
    render();
  };
}

/* The four bands, written out with the engine's own thresholds.
 *
 * Filled from the sweep rather than from a copy here, so the colour on
 * the ground and the number beside it cannot drift apart. Blank until a
 * sweep has arrived, because until then there are no thresholds to
 * quote — the bar the error bands are multiples of is this row's own
 * tolerance and moves with it.
 */
function drawLegend() {
  const host = document.getElementById("legend-bands");
  const pick = document.getElementById("layer-pick");
  if (!host) return;
  if (pick && pick.value !== shownLayer) pick.value = shownLayer;
  if (pick) pick.title = say(`layer.${shownLayer}.note`);

  const edges = sweepData && sweepData.bands && sweepData.bands[shownLayer];
  host.innerHTML = "";
  if (!edges) return;

  const unit = BAND_UNITS[shownLayer] || (v => `${v}`);
  const rising = draw.RISING[shownLayer] !== false;
  // Read off the same function the ground is painted with, rather than
  // written out again: a legend that describes bands the painter does
  // not use is worse than no legend.
  for (let band = draw.BANDS.length - 1; band >= 0; band--) {
    const row = document.createElement("span");
    const swatch = document.createElement("i");
    swatch.style.background = draw.BANDS[band];
    const text = document.createElement("span");
    text.textContent = bandRange(band, edges, rising, unit);
    row.append(swatch, text);
    host.appendChild(row);
  }
  const note = document.createElement("p");
  note.className = "note";
  note.textContent = say("legend.nothing");
  host.appendChild(note);
}

/* What a band covers, said in the layer's units.
 *
 * Derived from the same edges and the same direction the painter uses,
 * so a change to one is a change to both.
 */
function bandRange(band, edges, rising, unit) {
  if (rising) {
    const low = edges[band];
    const high = band + 1 < edges.length ? edges[band + 1] : null;
    return high === null ? `≥ ${unit(low)}` : `${unit(low)} – ${unit(high)}`;
  }
  const index = draw.BANDS.length - 1 - band;
  if (index >= edges.length) return `> ${unit(edges[edges.length - 1])}`;
  const high = edges[index];
  const low = index > 0 ? edges[index - 1] : null;
  return low === null ? `≤ ${unit(high)}` : `${unit(low)} – ${unit(high)}`;
}

/* What the panel prints where there is no number to print.
 *
 * An em dash rather than a zero: zero is an answer, and "no anchors
 * reach anywhere because there are no anchors" is not one.
 */
const NOTHING = "—";

/* A number that is being worked out right now.
 *
 * Three states rather than two. A dash says there is nothing to report
 * — an arrangement with no anchors has no round and no covered ground.
 * This says the opposite: there is something to report and it is not
 * known yet, so the panel must not go on showing the answer to the
 * arrangement before this edit. Switching from the town to the country
 * left the country's anchor count beside the town's covered area for as
 * long as the sweep took (ADR-0050).
 */
const WORKING = "…";

function area(km2) {
  return Number.isFinite(km2) ? `${tr(km2)} km²` : NOTHING;
}

/* ---------- named arrangements ---------- */

/* Which arrangements this tab can be loaded from. */
let PRESETS = [];

function wirePresets() {
  const pick = document.getElementById("preset-pick");
  if (!pick) return;

  document.getElementById("preset-load").onclick = async () => {
    const name = pick.value;
    if (!name) return;
    const shown = PRESETS.find(p => p.name === name);
    const yes = await askPlainly(
      say("preset.replaces", { name: (shown && shown.label) || name }));
    if (!yes) return;
    try {
      await ask("/api/preset/load", { name });
      await refreshScene();
      fillControls();
      await loadFigures();
      scheduleSweep();
      // The name box follows what was loaded, so the usual next act —
      // change something, save it under a new name — starts from the
      // name it came from rather than from an empty box.
      document.getElementById("preset-name").value =
        (shown && !shown.shipped) ? name : "";
      flash(say("preset.loaded", { name: (shown && shown.label) || name }));
    } catch (error) { flash(error.message, true); }
  };

  document.getElementById("preset-save").onclick = async () => {
    const name = document.getElementById("preset-name").value.trim();
    if (!name) { flash(say("preset.needs_name"), true); return; }
    // The two shipped ones are how somebody gets back to a known
    // starting point, so they are not writable — and saying so beats
    // accepting the name and quietly not shadowing them.
    if (PRESETS.some(p => p.shipped && p.name === name)) {
      flash(say("preset.shipped_kept", { name }), true);
      return;
    }
    try {
      const { path } = await ask("/api/preset/save", { name });
      await drawPresets(name);
      flash(say("preset.saved", { name, path }));
    } catch (error) { flash(error.message, true); }
  };

  document.getElementById("preset-drop").onclick = async () => {
    const name = pick.value;
    const shown = PRESETS.find(p => p.name === name);
    if (!name) return;
    if (shown && shown.shipped) {
      flash(say("preset.shipped_kept", { name: shown.label }), true);
      return;
    }
    if (!await askPlainly(say("preset.sure_drop", { name }))) return;
    try {
      await ask("/api/preset/delete", { name });
      await drawPresets();
      flash(say("preset.dropped", { name }));
    } catch (error) { flash(error.message, true); }
  };
}

/* Redraw the picker from the engine's own list. */
async function drawPresets(keep) {
  const pick = document.getElementById("preset-pick");
  if (!pick) return;
  try {
    const { presets } = await ask("/api/presets");
    PRESETS = presets || [];
  } catch (error) { return; }
  const wanted = keep || pick.value;
  pick.innerHTML = options(
    PRESETS.map(p => [p.name, p.label]),
    PRESETS.some(p => p.name === wanted) ? wanted : "",
  );
}

/* ---------- the map somebody picks ground on ---------- */

/* The picker, and the box it last had.
 *
 * Kept after the sheet closes so that reopening it returns to the same
 * ground rather than to Ankara: somebody who takes a box, reads the
 * grid-point count and decides it is too big wants to come back to the
 * box they drew, not to the start.
 */
let picker = null;
let pickedBox = null;
/* How big that box is, which the size knob cannot say: a box drawn on a
 * map is a rectangle and the knob holds one number. */
let pickedSpan = null;
/* Redraws the size knob and the line under it. Held here because taking
 * a box from the map changes what both of them say, and the map sheet
 * and the knob are wired in two different places. */
let redrawFetchBox = () => {};
let MAP_TILES = "";

function wireMap() {
  const sheet = document.getElementById("map-sheet");
  const open = document.getElementById("open-map");
  if (!sheet || !open) return;

  open.onclick = () => {
    sheet.hidden = false;
    document.getElementById("map-credit").textContent = MAP_TILES
      ? `${say("fetch.map.hint")} · ${say("fetch.map.credit")}`
      : say("fetch.map.none");
    if (!picker) {
      picker = new pick.Picker(document.getElementById("map-canvas"), {
        url: MAP_TILES,
        centre: startingPoint(),
        sizeKm: Number(document.getElementById("fetch-size").value) || 3,
        onChange: showSpan,
      });
    }
    // No address at all is a deliberate choice somebody made with
    // `--map-tiles ""`, on a machine with no way out. The box can still
    // be dragged over an empty ground; saying so beats a grey rectangle
    // that looks like a map that failed.
    document.getElementById("map-canvas").classList.toggle(
      "mapless", !MAP_TILES);
    // A centre typed by hand since the map was last open is where the
    // map should open. Without this, somebody types Konya, presses the
    // map button and is shown Ankara with a box on it — the panel saying
    // one thing and the map another, which is the same disagreement the
    // slider and the box had.
    if (!pickedBox) {
      const typed = startingPoint();
      if (typed.typed) {
        picker.goTo(typed.lat, typed.lon,
                    Math.max(picker.zoom, 12));
      }
    }
    // The map was built while its container was hidden, so it measured
    // nothing. Redrawn now that it has a size.
    picker.draw();
    showSpan(picker.state());
  };

  const shut = () => { sheet.hidden = true; };
  document.getElementById("map-close").onclick = shut;

  document.getElementById("map-draw").onclick = event => {
    picker.drawing = !picker.drawing;
    event.target.classList.toggle("on", picker.drawing);
    picker.host.classList.toggle("drawing", picker.drawing);
  };

  document.getElementById("map-take").onclick = () => {
    const { box, span } = picker.state();
    pickedBox = box;
    pickedSpan = span;
    // The centre box is filled too, in this project's own decimal mark,
    // so the panel still shows where the ground is and a person can
    // still edit it by hand (ADR-0039).
    document.getElementById("fetch-centre").value =
      `${decimal((box.south + box.north) / 2, 5)} `
      + `${decimal((box.west + box.east) / 2, 5)}`;
    const note = document.getElementById("fetch-picked");
    note.hidden = false;
    document.getElementById("fetch-picked-what").textContent =
      say("fetch.map.picked", {
        across: decimal(span.across, 2), along: decimal(span.along, 2),
      });
    // The knob and its line describe the box that will be fetched, and
    // that is now this one.
    redrawFetchBox();
    shut();
  };

  // Typing a centre by hand drops the drawn box.
  //
  // Otherwise the panel shows one place and the fetch goes to another:
  // the corners outrank the centre on the wire, so a box drawn an hour
  // ago would quietly beat what somebody just typed. This is the same
  // class of bug as the fetch that crashed on an empty centre — the page
  // and the task disagreeing about which field decides.
  document.getElementById("fetch-centre").addEventListener("input", () => {
    pickedBox = null;
    pickedSpan = null;
    document.getElementById("fetch-picked").hidden = true;
    redrawFetchBox();
  });

  const find = () => lookForPlace();
  document.getElementById("map-find").onclick = find;
  document.getElementById("map-search").addEventListener("keydown", event => {
    if (event.key === "Enter") { event.preventDefault(); find(); }
  });
}

/* Where the map opens: whatever is in the centre box, else Ankara.
 *
 * `read_point` on the other side accepts several ways of writing a
 * point; this only has to recognise the one it wrote itself, and fall
 * back rather than argue.
 */
function startingPoint() {
  const typed = document.getElementById("fetch-centre").value.trim();
  const numbers = typed.replace(/,(?=\s)|(?<=\s),/g, " ")
    .replace(/,/g, ".").split(/[\s;]+/).map(Number).filter(Number.isFinite);
  if (numbers.length === 2 && Math.abs(numbers[0]) <= 90) {
    return { lat: numbers[0], lon: numbers[1], typed: true };
  }
  // Ankara, because this is where the four sites that ship with it are
  // and because a map has to open somewhere.
  return { lat: 39.925, lon: 32.837, typed: false };
}

/* How much ground is selected and what it will cost to sample.
 *
 * The grid-point count is the honest number here: a box is cheap to
 * drag and a 40 km one at 30 m spacing is one and a half million
 * samples. Said while the box is being drawn rather than after.
 */
function showSpan(state) {
  const shown = document.getElementById("map-span");
  if (!shown) return;
  const points = pick.gridPoints(state.span.across, state.span.along,
    Number(document.getElementById("fetch-spacing").value));
  shown.textContent = say("fetch.map.span", {
    across: decimal(state.span.across, 2),
    along: decimal(state.span.along, 2),
    points: points.toLocaleString("tr-TR"),
  });
  shown.classList.toggle("no-hits", points > 4000000);
}

async function lookForPlace() {
  const typed = document.getElementById("map-search").value.trim();
  const hits = document.getElementById("map-hits");
  if (!typed) { hits.hidden = true; return; }
  hits.hidden = false;
  hits.textContent = say("fetch.map.searching");
  try {
    const found = await pick.lookUp(typed, speaks());
    hits.textContent = "";
    if (!found.length) { hits.textContent = say("fetch.map.nothing"); return; }
    for (const place of found) {
      const row = document.createElement("button");
      row.innerHTML = "";
      const name = document.createElement("span");
      name.textContent = place.name;
      const where = document.createElement("span");
      where.className = "where";
      where.textContent = ` · ${place.kind}`;
      row.append(name, where);
      row.onclick = () => {
        picker.goTo(place.lat, place.lon, Math.max(picker.zoom, 12));
        hits.hidden = true;
      };
      hits.append(row);
    }
  } catch (error) {
    hits.textContent = say("fetch.map.offline");
  }
}

/* What the fetch is about to ask for, before it asks.
 *
 * A size and a spacing are two numbers whose product is the work, and a
 * spacing left at 30 m over a region rather than a town is minutes of
 * sampling and a file nobody wants. Said here rather than discovered.
 */
function wireFetchBox() {
  const size = document.getElementById("fetch-size");
  const number = document.getElementById("fetch-size-num");
  const shown = document.getElementById("fetch-size-out");
  const note = document.getElementById("fetch-box");
  const spacing = document.getElementById("fetch-spacing");
  if (!size || !note) return;

  const label = size.closest("label");

  const redraw = () => {
    const step = Math.max(Number(spacing.value) || 30, 1);

    /* A box drawn on a map outranks this knob, so while there is one the
     * knob does not describe anything.
     *
     * It used to go on reading "3 km" beside a note saying the map had
     * handed over 19,31 × 12,33 km, and the hint under it went on
     * costing the 3 km box at ten thousand grid points when the fetch
     * was about to take a quarter of a million. Two halves of one
     * control saying different things is the thing this project keeps
     * catching (ADR-0036, ADR-0048, ADR-0052).
     */
    if (pickedBox && pickedSpan) {
      const points = pick.gridPoints(pickedSpan.across, pickedSpan.along, step);
      if (shown) shown.textContent = NOTHING;
      if (label) label.classList.add("dead");
      size.disabled = true;
      if (number) { number.disabled = true; number.value = ""; }
      note.textContent = say("fetch.box.map",
                             { points: points.toLocaleString("tr-TR") });
      note.classList.toggle("no-hits", points > 4000000);
      return;
    }

    const km = Number(size.value);
    const points = pick.gridPoints(km, km, step);
    if (shown) shown.textContent = say("fetch.size.out", { km });
    if (label) label.classList.remove("dead");
    size.disabled = false;
    if (number) number.disabled = false;
    if (number && document.activeElement !== number) number.value = km;
    note.textContent = say("fetch.box", {
      km, points: points.toLocaleString("tr-TR"),
    });
    note.classList.toggle("no-hits", points > 4000000);
  };

  /* Reaching for the size slider drops a box drawn on the map.
   *
   * The two describe the same thing and only one of them can be in
   * force: the corners outrank the size on the wire, so without this the
   * slider would move, the hint under it would change, and the fetch
   * would go and get the box from twenty minutes ago. A control that
   * appears to do something and does not is the thing ADR-0036 is about.
   */
  const bySlider = () => {
    if (pickedBox) {
      pickedBox = null;
      pickedSpan = null;
      document.getElementById("fetch-picked").hidden = true;
      if (picker) picker.setSquare(Number(size.value) || 3);
    }
    redraw();
  };

  redrawFetchBox = redraw;
  const letGo = document.getElementById("fetch-picked-drop");
  if (letGo) {
    letGo.onclick = () => {
      pickedBox = null;
      pickedSpan = null;
      document.getElementById("fetch-picked").hidden = true;
      if (picker) picker.setSquare(Number(size.value) || 3);
      redraw();
    };
  }
  size.oninput = bySlider;
  spacing.oninput = () => {
    redraw();
    // The map's own count is per spacing too, and it is on screen while
    // this is being typed if the sheet is open.
    if (picker) showSpan(picker.state());
  };
  if (number) {
    number.oninput = () => {
      const km = Number(number.value);
      if (Number.isFinite(km) && km > 0) { size.value = km; bySlider(); }
    };
  }
  redraw();
}

/* ---------- the loop ---------- */

async function refreshScene() {
  // Only if it actually takes a moment: most scenes are milliseconds,
  // and a panel that blinks on every drag is harder to read than one
  // that does not. A search over a real town is nine seconds, and for
  // all nine the panel used to show the arrangement before the edit.
  const slow = setTimeout(() => {
    if (latest) showNumbers(latest, simulated, true);
    flash(say("busy.working"));
  }, PATIENCE_MS);
  try {
    latest = await ask("/api/scene");
  } finally {
    clearTimeout(slow);
  }
  state = latest.state;
  // The server finds what ground has been fetched; the page never keeps
  // its own list, so a place fetched while this is running turns up on
  // the next refresh.
  SITES = latest.terrain.sites || [];
  // Named by the engine, like every other list the page draws from, so
  // `--map-tiles` reaches the picker without a second copy anywhere.
  if (latest.map_tiles !== undefined) MAP_TILES = latest.map_tiles;
  if (latest.choices) {
    MOUNTINGS = latest.choices.mountings;
    RADIOS = latest.choices.radios;
    LAYOUTS = latest.choices.layouts || [];
    ROUTES = latest.choices.routes || [];
    ROUTES_LIVE = latest.choices.routes_live || [];
    FETCH_MISSING = latest.choices.fetch_missing || [];
    TABS = latest.choices.modes;
    LANGUAGES = latest.choices.languages || [];
    for (const [name, label] of TABS) MODE_LABEL[name] = label;
  }
  // The session's language, not the markup's. Reloading a page that was
  // switched to English used to come back with English figures under
  // Turkish headings, because the page took its language from the `lang`
  // attribute and the engine had kept its own.
  if (state.language && state.language !== speaks()) {
    speak(state.language);
    drawWords();
  }
  drawTabs();
  drawPresets();
  drawLanguages();
  keepClearOfTheHeader();
  capSlidersToTheGround();
  drawSites();
  document.getElementById("terrain-note").textContent = say("terrain.note", {
    ground: latest.terrain.description, anchors: latest.anchors.length,
  });
  terrainData = latest.terrain;
  // The photograph of the ground, where the fetch brought one. Asked for
  // here beside the mesh and for the same reason: both describe the site
  // this scene just became.
  loadPhotograph();
  lockPhotographTick();
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
  // The arrangement changed, so the last simulation described something
  // else.
  simulated = null;
  showNumbers(latest, null);
}

let sweepTimer = null;
/* Which sweep the page is waiting for.
 *
 * Cancelling the timer only stops a sweep that has not been asked for
 * yet. One already in flight arrives whenever the engine finishes it,
 * and `/api/sweep` answers about the state the server held when it
 * picked the request up — so switching rows while one was running put
 * the country's covered ground in the tunnel's panel: 164,25 km²
 * against fourteen anchors in a bore. The number was real and it was
 * somebody else's (ADR-0050).
 */
let sweepWanted = 0;

function scheduleSweep() {
  sweepData = null;
  const mine = ++sweepWanted;
  render();
  // Said the moment the old areas stop being true, rather than when the
  // new ones arrive: the two are seconds apart and in between the panel
  // was showing this arrangement's anchors beside the last one's ground.
  if (latest) showNumbers(latest, simulated);
  clearTimeout(sweepTimer);
  sweepTimer = setTimeout(async () => {
    try {
      flash(say("busy.sweep"));
      const swept = await ask("/api/sweep");
      // Anything but the newest answer is an answer to a question the
      // page has stopped asking.
      if (mine !== sweepWanted) return;
      sweepData = swept;
      // The bands travel with the sweep, so the legend is redrawn with
      // it: the error bands are multiples of this row's own tolerance
      // and move when that does.
      drawLegend();
      render();
      showNumbers(latest, simulated);
      flash("");
    } catch (error) {
      if (mine === sweepWanted) flash(error.message, true);
    }
  }, 250);
}

/* ---------- reading it coarsely, for trying things ----------
 *
 * Two figures decide how long a run takes rather than what it is about,
 * and both are reversible: the model does not change, it is read more
 * coarsely. Kept here as the page's copy of `settings.HURRIED`, and a
 * test pins the two against each other so they cannot drift (ADR-0063).
 */
const HURRIED = { "site.shadow_draws": 1, "site.profile_spacing_m": 0 };

/* Whether the figures on screen are the coarse ones, however they got
 * that way. Asked of the figures rather than of the button, so a person
 * who edits the draws to one by hand is told the same thing. */
function hurrying() {
  const set = state && state.overrides ? state.overrides : {};
  return Object.entries(HURRIED).some(([key, value]) =>
    key in set && Number(set[key]) === value);
}

function drawHurry() {
  const button = document.getElementById("hurry");
  if (!button) return;
  const on = hurrying();
  button.textContent = say(on ? "result.hurry.on" : "result.hurry");
  button.classList.toggle("on", on);
}

//: Which press of the button the answers on screen belong to.
//:
//: The pooled pass runs with the button live again, so a press while
//: one is in flight leaves two of them running and the older can land
//: last. Same guard as the sweep's: an answer whose press has been
//: superseded is dropped rather than shown.
let simulationWanted = 0;

async function runSimulation() {
  const button = document.getElementById("run");
  const mine = ++simulationWanted;
  button.disabled = true;
  button.textContent = say("result.running");
  let first;
  try {
    first = await ask("/api/simulate");
    if (mine !== simulationWanted) return;
    sweepData = sweepData || { served_km2: first.served_km2,
                               reached_km2: first.reached_km2 };
    simulated = first;
    showNumbers(latest, simulated);
  } catch (error) {
    if (mine === simulationWanted) flash(error.message, true);
    return;
  } finally {
    if (mine === simulationWanted) {
      button.disabled = false;
      button.textContent = say("result.run");
    }
  }

  // One draw of the shadows is on screen. The rest cost about twice as
  // long again, and on the open-country row that is minutes, so they
  // run with the button live and replace the figures when they land
  // (ADR-0059). The row above them says which of the two is showing.
  if ((first.draws_wanted || 1) <= (first.draws_done || 1)) return;
  try {
    const every = await ask("/api/simulate/pooled");
    if (mine !== simulationWanted) return;
    simulated = every;
    showNumbers(latest, simulated);
  } catch (error) {
    if (mine === simulationWanted) flash(error.message, true);
  }
}

(async function start() {
  // The language the session is in, before anything is drawn in it.
  speak(document.documentElement.lang === "en" ? "en" : "tr");
  drawWords();
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
