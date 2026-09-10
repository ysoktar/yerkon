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

const VERTICAL = 6;          // ground relief is exaggerated, or hills vanish
const CHOICES = {
  region: [["TR", "Türkiye"], ["EU", "Avrupa"], ["US", "Amerika"],
           ["US-PTP", "Amerika (noktadan noktaya)"], ["LICENSED", "Lisanslı"]],
  scheme: [["single", "Tek yönlü TWR"], ["double", "Çift yönlü TWR"]],
};

const RADIOS = [["sx1280", "SX1280 (şehir içi)"], ["e28", "E28-2G4M27S (kırsal)"],
                ["dwm3000", "DWM3000 UWB (tünel)"]];
const MOUNTINGS = [["sign", "Levha (3 m)"], ["gantry", "Portal (6 m)"],
                   ["billboard", "Pano (10 m)"],
                   ["column", "Aydınlatma direği (12 m)"], ["mast", "Direk (25 m)"]];
const KINDS = [["vehicle", "Kara aracı alıcısı"], ["pedestrian", "Yaya alıcısı"]];

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
  relief_m: v => (v > 0 ? `${v} m` : "düz"),
  hill_spacing_m: v => `${v} m`,
  roughness_m: v => `${Number(v).toFixed(2).replace(".", ",")} m`,
  clutter_db_per_km: v => `${v} dB/km`,
  tolerance_m: v => `${Number(v).toFixed(1).replace(".", ",")} m`,
  journey_s: v => `${v} s`,
  sweep_m: v => `${v} m`,
};

const OUTPUTS = {
  corridor_m: "corridor-out",
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

function drawRuns() {
  const host = document.getElementById("runs");
  host.innerHTML = "";
  state.runs.forEach((run, index) => {
    const card = document.createElement("div");
    card.className = "card";

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

const CASCADING_FIGURES = /(height_m|noise_figure_db|threshold_db|clutter|residual_ppm|tolerance_ppm|turnaround_s|payload_bytes)/;

function drawFigures() {
  const host = document.getElementById("figures");
  if (!figuresData) { host.innerHTML = ""; return; }
  host.innerHTML = "";

  document.getElementById("assumed-count").textContent =
    `${figuresData.total} değerin ${figuresData.assumed} tanesi varsayım`;

  for (const group of figuresData.groups) {
    const heading = document.createElement("div");
    heading.className = "group";
    heading.textContent = group.label;
    host.appendChild(heading);

    for (const figure of figuresData.figures.filter(f => f.group === group.key)) {
      const row = document.createElement("div");
      row.className = "figure";

      const name = document.createElement("div");
      name.className = "name";
      const short = figure.key.split(".").slice(1).join(" · ");
      name.innerHTML = `<b></b><span></span>`;
      name.querySelector("b").textContent = short;
      name.querySelector("span").textContent = figure.affects;
      name.title = figure.note + (
        figure.sensitivity ? `\n\n${figure.sensitivity}` : "");
      row.appendChild(name);

      const input = document.createElement("input");
      input.type = "number";
      input.value = figure.value;
      input.step = "any";
      if (figure.edited) input.classList.add("edited");
      input.title = figure.assumed
        ? "Hâlâ varsayım — kaynağı defaults.toml'a yaz"
        : `Kaynak: ${figure.source}`;
      input.onchange = () => {
        const overrides = Object.assign({}, state.overrides);
        overrides[figure.key] = Number(input.value);
        edit({ overrides }, CASCADING_FIGURES.test(figure.key))
          .catch(e => say(e.message, true));
      };
      row.appendChild(input);

      const unit = document.createElement("div");
      unit.className = "unit";
      unit.textContent = figure.unit;
      row.appendChild(unit);

      host.appendChild(row);
    }
  }
}

async function loadFigures() {
  try {
    figuresData = await ask("/api/figures");
    drawFigures();
  } catch (error) { say(error.message, true); }
}

function fillControls() {
  for (const [name, id] of Object.entries(OUTPUTS)) {
    const input = document.getElementById(name);
    if (!input) continue;
    input.value = state[name];
    document.getElementById(id).textContent = UNITS[name](state[name]);
  }
  for (const name of Object.keys(CHOICES)) {
    document.getElementById(name).value = state[name];
  }
  document.getElementById("mode").value = state.scenario;
  drawRuns();
  drawUnits();
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
    const input = document.getElementById(name);
    if (!input) continue;
    // While the handle is moving, only the label follows. The engine is
    // asked once, when it is let go, because a sweep takes seconds.
    input.oninput = () => {
      document.getElementById(OUTPUTS[name]).textContent =
        UNITS[name](Number(input.value));
    };
    input.onchange = () =>
      edit({ [name]: Number(input.value) },
           input.hasAttribute("data-cascades"))
        .catch(e => say(e.message, true));
  }

  document.getElementById("mode").onchange = async event => {
    try {
      const { state: loaded } = await ask("/api/mode", { mode: event.target.value });
      state = loaded;
      framed = false;
      await refreshScene();
      fillControls();
      await loadFigures();
      scheduleSweep();
    } catch (error) { say(error.message, true); }
  };

  document.getElementById("add-run").onclick = () => {
    const letters = "ABCDEFGHJKLMNPQRSTUVWXYZ";
    const used = new Set(state.runs.map(r => r.identifier));
    const identifier = [...letters].find(l => !used.has(l)) || "Z";
    const last = state.runs[state.runs.length - 1];
    edit({ runs: state.runs.concat([{
      identifier,
      radio: last ? last.radio : "sx1280",
      mounting: last ? last.mounting : "mast",
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

function groundAt(x, y) {
  // Nearest sample from the mesh the engine sent. Good enough to sit a
  // coverage cell on; the elevation itself came from the engine.
  if (!terrainData) return 0;
  const { xs, ys, heights } = terrainData;
  const column = Math.min(xs.length - 1, Math.max(0, Math.round(
    ((x - xs[0]) / (xs[xs.length - 1] - xs[0])) * (xs.length - 1))));
  const row = Math.min(ys.length - 1, Math.max(0, Math.round(
    ((y - ys[0]) / (ys[ys.length - 1] - ys[0])) * (ys.length - 1))));
  return heights[row][column];
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

function render() {
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

  const items = [
    ...draw.groundFaces(view, latest.terrain, light),
    ...draw.cellFaces(view, sweepData, groundAt),
    ...draw.masts(view, latest.anchors, colourOf),
    ...draw.polyline(
      view,
      latest.road.map(p => [p.x, p.y, p.z * draw.VERTICAL + 10]),
      "#22282e", 2,
    ),
  ];

  // Each group's reach, in its own colour. A UWB bracket and a mast on
  // one corridor cover nothing like the same ground, and one ring size
  // for all of them would say they did.
  for (const anchor of latest.anchors) {
    if (!anchor.reach_m) continue;
    items.push(...draw.ring(
      view,
      [anchor.x, anchor.y, anchor.ground_z * draw.VERTICAL + 6],
      anchor.reach_m,
      colourOf(anchor.run).replace("rgb(", "rgba(").replace(")", ",0.45)"),
    ));
  }

  for (const unit of latest.units || []) {
    items.push(...draw.polyline(
      view,
      unit.trail.map(p => [p[0], p[1], p[2] * draw.VERTICAL + 20]),
      "rgba(180,85,29,0.55)", 1.5,
    ));
  }
  items.push(...draw.units(view, latest.units || []));

  markers = items.filter(item => item.kind === "mast");
  draw.paint(context, width, height, items);
}

/* ---------- dragging an anchor ---------- */

let dragging = null;
let spinning = null;

function pixel(event) {
  const box = canvas.getBoundingClientRect();
  return [event.clientX - box.left, event.clientY - box.top];
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

canvas.addEventListener("pointerdown", event => {
  const [px, py] = pixel(event);
  const hit = markerAt(px, py);
  if (hit && event.shiftKey) {
    apply({ removed: (state.removed || []).concat([hit.id]) })
      .catch(e => say(e.message, true));
    return;
  }
  if (hit) { dragging = hit.id; canvas.setPointerCapture(event.pointerId); return; }
  spinning = { x: event.clientX, y: event.clientY, yaw: orbit.yaw, pitch: orbit.pitch };
});

canvas.addEventListener("pointermove", event => {
  if (dragging) {
    const [px, py] = pixel(event);
    const view = draw.camera(orbit, container.clientWidth, container.clientHeight);
    const point = view.onPlane(px, py, groundAt(0, 0) * draw.VERTICAL);
    if (point) {
      const anchor = latest.anchors.find(a => a.id === dragging);
      if (anchor) { anchor.x = point[0]; anchor.y = point[1]; render(); }
    }
    return;
  }
  if (spinning) {
    orbit.yaw = spinning.yaw + (event.clientX - spinning.x) * 0.006;
    orbit.pitch = Math.min(1.45, Math.max(0.06,
      spinning.pitch + (event.clientY - spinning.y) * 0.005));
    render();
  }
});

window.addEventListener("pointerup", () => {
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
  spinning = null;
});

canvas.addEventListener("wheel", event => {
  event.preventDefault();
  orbit.distance = Math.min(220000, Math.max(1200,
    orbit.distance * (1 + Math.sign(event.deltaY) * 0.12)));
  render();
}, { passive: false });

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

/* ---------- the loop ---------- */

async function refreshScene() {
  latest = await ask("/api/scene");
  state = latest.state;
  document.getElementById("terrain-note").textContent =
    `${latest.terrain.description} · ${latest.anchors.length} direk`;
  terrainData = latest.terrain;
  orbit.target = [state.corridor_m / 2, 0, 0];
  if (!framed) {
    // Frame the whole corridor the first time, then leave the camera
    // where the person put it.
    orbit.distance = Math.max(6000, state.corridor_m * 1.5);
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
  resize();
  await refreshScene();
  fillControls();
  await loadFigures();
  scheduleSweep();
})();
