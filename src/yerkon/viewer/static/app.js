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
  radio: [["sx1280", "SX1280"], ["e28", "E28-2G4M27S"], ["dwm3000", "DWM3000 UWB"]],
  mounting: [["sign", "Levha (3 m)"], ["gantry", "Portal (6 m)"],
             ["billboard", "Pano (10 m)"], ["column", "Aydınlatma direği (12 m)"],
             ["mast", "Direk (25 m)"]],
  scheme: [["single", "Tek yönlü TWR"], ["double", "Çift yönlü TWR"]],
};

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
  fillControls();
  await refreshScene();
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
  block(cascades.asked, "İstediğin değişiklik");
  block(cascades.follows, "Bunlar da değişiyor");
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
  spacing_m: v => `${v} m`,
  offset_m: v => `${v} m`,
  relief_m: v => (v > 0 ? `${v} m` : "düz"),
  hill_spacing_m: v => `${v} m`,
  roughness_m: v => `${Number(v).toFixed(2).replace(".", ",")} m`,
  clutter_db_per_km: v => `${v} dB/km`,
  tolerance_m: v => `${Number(v).toFixed(1).replace(".", ",")} m`,
  speed_km_h: v => `${v} km/sa`,
  receiver_height_m: v => `${Number(v).toFixed(1).replace(".", ",")} m`,
  journey_s: v => `${v} s`,
  sweep_m: v => `${v} m`,
};

const OUTPUTS = {
  corridor_m: "corridor-out", spacing_m: "spacing-out", offset_m: "offset-out",
  relief_m: "relief-out", hill_spacing_m: "hill-out", roughness_m: "rough-out",
  clutter_db_per_km: "clutter-out", tolerance_m: "tol-out",
  speed_km_h: "speed-out", receiver_height_m: "rxh-out",
  journey_s: "journey-out", sweep_m: "sweep-out",
};

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

  document.getElementById("run").onclick = runSimulation;
  document.getElementById("reset").onclick = async () => {
    const { state: fresh } = await ask("/api/reset", {});
    state = fresh;
    fillControls();
    await refreshScene();
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

  const items = [
    ...draw.groundFaces(view, latest.terrain, light),
    ...draw.cellFaces(view, sweepData, groundAt),
    ...draw.masts(view, latest.anchors),
    ...draw.polyline(
      view,
      latest.road.map(p => [p.x, p.y, p.z * draw.VERTICAL + 10]),
      "#22282e", 2,
    ),
  ];

  for (const anchor of latest.anchors) {
    items.push(...draw.ring(
      view,
      [anchor.x, anchor.y, anchor.ground_z * draw.VERTICAL + 6],
      latest.reach_m,
      "rgba(31,111,235,0.55)",
    ));
  }

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

function showNumbers(scene, result) {
  const list = document.getElementById("numbers");
  const rows = [
    ["Direk sayısı", scene.anchors.length],
    ["Kullanılabilir menzil", `${tr(scene.reach_m / 1000)} km`],
    ["Bağlantının koptuğu mesafe", `${tr(scene.closure_m / 1000)} km`],
  ];
  if (sweepData) {
    rows.push(["Hizmet alanı", `${tr(sweepData.served_km2)} km²`]);
    rows.push(["Paketin ulaştığı alan", `${tr(sweepData.reached_km2)} km²`]);
  }
  if (result) {
    rows.push(["Tur süresi", `${tr(result.round_s * 1000, 0)} ms`]);
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
  scheduleSweep();
})();
