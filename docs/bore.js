/* The tunnel, flat.
 *
 * A bore two kilometres long and twelve metres wide is a line in three
 * dimensions: seen whole, its width is under a pixel and its units sit
 * on top of each other. So the tunnel tab draws it the way a tunnel is
 * drawn on paper: a plan along its length with the width stretched so
 * the two walls and what is fixed to them can be told apart, and the
 * long section under it, where the grade and the units' height show.
 * Nothing outside the bore is drawn.
 *
 * Every position is read as a distance along the route (chainage) and
 * a distance to one side of it, so a bore that bends is drawn straight.
 */

import { BANDS, RISING, bandOf } from "./draw.js?v=b408308ed2";

/* What part of the bore is on screen, in metres along it. */
export const bore = { start: 0, span: 0, length: 0 };

const MARGIN = 28;

/* The units, in the site's own blue: bright enough on the dark road. */
const UNIT_BLUE = "#3b82f6";

/* Where the plan and the section sit in a frame of this size. */
export function layout(width, height) {
  const plotW = Math.max(100, width - 2 * MARGIN);
  // A small screen (a phone's half of one) has room for the plan only,
  // and not for the notes under the titles.
  const small = height < 520 || width < 560;
  // Clear of the key and the hint floating over the top left corner.
  const planTop = height > 700 ? 262 : (small ? 150 : 130);
  const planH = small ? Math.max(80, height - planTop - 70)
                      : Math.max(90, Math.min(220, height * 0.32));
  const sectionTop = planTop + planH + 86;
  const sectionH = Math.max(70, Math.min(180, height - sectionTop - 60));
  return { left: MARGIN, plotW, planTop, planH, sectionTop, sectionH, small };
}

/* Distance along the route and to one side of it, for every point. */
export function along(road) {
  const pts = road.map(p => [p.x, p.y, p.z]);
  const at = [0];
  for (let i = 1; i < pts.length; i++) {
    at.push(at[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  }
  function place(x, y) {
    let best = null;
    for (let i = 1; i < pts.length; i++) {
      const [ax, ay] = pts[i - 1];
      const dx = pts[i][0] - ax;
      const dy = pts[i][1] - ay;
      const long = dx * dx + dy * dy || 1;
      const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / long));
      const px = ax + t * dx;
      const py = ay + t * dy;
      const off = Math.hypot(x - px, y - py);
      if (!best || off < best.off) {
        // Left of the direction of travel is positive.
        const side = Math.sign(dx * (y - ay) - dy * (x - ax)) || 1;
        best = { s: at[i - 1] + t * Math.sqrt(long), off, d: side * off };
      }
    }
    return best || { s: 0, d: 0, off: 0 };
  }
  return { length: at[at.length - 1] || 0, place, at, pts };
}

/* The whole bore on screen, with a little room at either portal. */
export function fit(length) {
  bore.length = length;
  bore.span = length * 1.04;
  bore.start = -length * 0.02;
}

/* Keep the view on the bore: never past a portal by more than a tenth. */
export function clamp() {
  const most = bore.length * 1.2 || 1;
  bore.span = Math.max(30, Math.min(most, bore.span));
  const slack = bore.length * 0.1;
  bore.start = Math.max(-slack, Math.min(bore.length + slack - bore.span, bore.start));
}

/* A round step between chainage marks at least `apart` pixels wide. */
function step(span, plotW, apart) {
  const raw = span * apart / plotW;
  const power = 10 ** Math.floor(Math.log10(raw));
  for (const k of [1, 2, 5, 10]) if (power * k >= raw) return power * k;
  return power * 10;
}

function metres(value) {
  return `${Math.round(value)} m`;
}

export function paintBore(context, width, height, scene, options) {
  const { sweep, layer, say, dark } = options;
  context.clearRect(0, 0, width, height);
  const route = along(scene.road || []);
  if (!bore.length || Math.abs(bore.length - route.length) > 1) fit(route.length);
  clamp();
  const { left, plotW, planTop, planH, sectionTop, sectionH, small } =
    layout(width, height);
  const X = s => left + (s - bore.start) / bore.span * plotW;

  const ink = dark ? "#e6edf3" : "#22282e";
  const quiet = dark ? "#9aa7b3" : "#61707e";
  const rock = dark ? "#2a323b" : "#c9d1d9";

  const anchors = (scene.anchors || []).map(a => Object.assign(
    { at: route.place(a.x, a.y) }, a));
  const halfWidth = Math.max(6, ...anchors.map(a => a.at.off + 2));
  const mid = planTop + planH / 2;
  const Y = d => mid - d / halfWidth * (planH / 2);

  context.save();
  context.font = "12px 'IBM Plex Sans', system-ui, sans-serif";
  context.textBaseline = "alphabetic";

  // Titles.
  context.fillStyle = ink;
  context.font = "600 13px 'IBM Plex Sans', system-ui, sans-serif";
  context.fillText(say("bore.plan"), left, planTop - 40);
  context.fillStyle = quiet;
  context.font = "12px 'IBM Plex Sans', system-ui, sans-serif";
  if (!small) {
    context.fillText(say("bore.plan.note", { width: Math.round(halfWidth * 2) }),
                     left, planTop - 22);
  }

  // The rock around the bore, then the bore between its portals.
  const inX = X(0);
  const outX = X(route.length);
  context.fillStyle = rock;
  context.fillRect(left, planTop - 14, plotW, planH + 28);
  context.save();
  context.beginPath();
  context.rect(left, planTop - 14, plotW, planH + 28);
  context.clip();
  context.fillStyle = dark ? "#151a20" : "#3b4550";
  context.fillRect(inX, planTop, outX - inX, planH);

  // Coverage over the carriageway, where a reading was chosen.
  if (sweep && layer && layer !== "ground") {
    const values = (sweep.layers && sweep.layers[layer]) || sweep.counts;
    const edges = (sweep.bands && sweep.bands[layer]) || [1, 3, 4, 6];
    const rising = RISING[layer] !== false;
    const size = sweep.resolution_m || 10;
    context.globalAlpha = 0.6;
    for (let row = 0; row < sweep.ys.length; row++) {
      for (let column = 0; column < sweep.xs.length; column++) {
        const band = bandOf(values[row][column], edges, rising);
        if (band < 0) continue;
        const cell = route.place(sweep.xs[column], sweep.ys[row]);
        if (cell.off > halfWidth) continue;
        const x0 = X(Math.max(0, cell.s - size / 2));
        const x1 = X(Math.min(route.length, cell.s + size / 2));
        if (x1 <= x0) continue;
        if (x1 < left || x0 > left + plotW) continue;
        const y0 = Y(Math.min(halfWidth, cell.d + size / 2));
        const y1 = Y(Math.max(-halfWidth, cell.d - size / 2));
        context.fillStyle = BANDS[band];
        context.fillRect(x0, y0, x1 - x0 + 0.5, y1 - y0);
      }
    }
    context.globalAlpha = 1;
  }

  // The walls, and the line down the middle.
  context.strokeStyle = dark ? "#8b98a5" : "#1c232b";
  context.lineWidth = 3;
  for (const edge of [planTop, planTop + planH]) {
    context.beginPath();
    context.moveTo(inX, edge);
    context.lineTo(outX, edge);
    context.stroke();
  }
  context.strokeStyle = "rgba(255,255,255,0.75)";
  context.lineWidth = 1.5;
  context.setLineDash([14, 12]);
  context.beginPath();
  context.moveTo(inX, mid);
  context.lineTo(outX, mid);
  context.stroke();
  context.setLineDash([]);

  // The portals.
  context.fillStyle = dark ? "#5b6875" : "#8795a3";
  for (const at of [inX, outX]) context.fillRect(at - 3, planTop - 14, 6, planH + 28);
  context.restore();
  context.fillStyle = ink;
  context.font = "600 12px 'IBM Plex Sans', system-ui, sans-serif";
  if (inX >= left - 1) {
    context.textAlign = "left";
    context.fillText(say("bore.portal.in"), Math.max(left, inX - 3), planTop + planH + 30);
  }
  if (outX <= left + plotW + 1) {
    context.textAlign = "right";
    context.fillText(say("bore.portal.out"), Math.min(left + plotW, outX + 3), planTop + planH + 30);
  }
  context.textAlign = "left";

  // Chainage along the bottom of the plan.
  const every = step(bore.span, plotW, 80);
  context.font = "11px 'IBM Plex Sans', system-ui, sans-serif";
  context.fillStyle = quiet;
  context.strokeStyle = quiet;
  context.lineWidth = 1;
  context.textAlign = "center";
  for (let s = Math.ceil(Math.max(0, bore.start) / every) * every;
       s <= Math.min(route.length, bore.start + bore.span); s += every) {
    const x = X(s);
    context.beginPath();
    context.moveTo(x, planTop + planH + 14);
    context.lineTo(x, planTop + planH + 19);
    context.stroke();
    context.fillText(metres(s), x, planTop + planH + 48);
  }
  context.textAlign = "left";

  // The units on the walls, named where there is room to.
  const room = plotW / bore.span * (anchors.length > 1
    ? route.length / anchors.length : route.length);
  for (const anchor of anchors) {
    const x = X(anchor.at.s);
    if (x < left - 8 || x > left + plotW + 8) continue;
    const y = Y(anchor.at.d);
    context.fillStyle = UNIT_BLUE;
    context.strokeStyle = "#fff";
    context.lineWidth = 2;
    context.beginPath();
    context.arc(x, y, 6, 0, Math.PI * 2);
    context.fill();
    context.stroke();
    if (room > 34) {
      context.fillStyle = "#fff";
      context.font = "10px 'IBM Plex Sans', system-ui, sans-serif";
      context.textAlign = "center";
      context.fillText(anchor.id, x, anchor.at.d > 0 ? y + 17 : y - 10);
      context.textAlign = "left";
    }
  }

  // The receivers, where they are and the way they go.
  context.save();
  context.beginPath();
  context.rect(left, planTop - 14, plotW, planH + 28);
  context.clip();
  for (const unit of scene.units || []) {
    const trail = (unit.trail || []).map(p => route.place(p[0], p[1]));
    context.strokeStyle = "rgba(255,160,90,0.8)";
    context.lineWidth = 2;
    context.beginPath();
    trail.forEach((p, i) => {
      const x = X(p.s);
      const y = Y(p.d);
      if (i === 0) context.moveTo(x, y); else context.lineTo(x, y);
    });
    context.stroke();
    if (!unit.at) continue;
    const here = route.place(unit.at[0], unit.at[1]);
    const x = X(here.s);
    const y = Y(here.d);
    if (x < left - 8 || x > left + plotW + 8) continue;
    context.fillStyle = "#e0782f";
    context.strokeStyle = "#fff";
    context.lineWidth = 1.5;
    context.beginPath();
    if (unit.kind === "pedestrian") context.arc(x, y, 6, 0, Math.PI * 2);
    else context.rect(x - 8, y - 5, 16, 10);
    context.fill();
    context.stroke();
    context.fillStyle = "#fff";
    context.font = "600 11px 'IBM Plex Sans', system-ui, sans-serif";
    context.fillText(unit.id, x + 10, y - 8);
  }
  context.restore();

  if (small) {
    context.restore();
    return;
  }

  // The long section: the road's height along the bore, and the units
  // at their own height above it.
  const zs = route.pts.map(p => p[2]);
  const low = Math.min(...zs) - 4;
  const high = Math.max(...zs) + 6;
  const Z = z => sectionTop + sectionH - (z - low) / (high - low || 1) * sectionH;
  context.fillStyle = ink;
  context.font = "600 13px 'IBM Plex Sans', system-ui, sans-serif";
  context.fillText(say("bore.section"), left, sectionTop - 22);
  context.fillStyle = quiet;
  context.font = "12px 'IBM Plex Sans', system-ui, sans-serif";
  context.fillText(say("bore.section.note", {
    rise: Math.round(Math.max(...zs) - Math.min(...zs)),
  }), left, sectionTop - 6);
  context.save();
  context.beginPath();
  context.rect(left, sectionTop, plotW, sectionH + 8);
  context.clip();
  context.strokeStyle = quiet;
  context.lineWidth = 1;
  context.strokeRect(left + 0.5, sectionTop + 0.5, plotW - 1, sectionH);
  context.strokeStyle = dark ? "#c2cdd8" : "#3b4550";
  context.lineWidth = 2.5;
  context.beginPath();
  route.pts.forEach((p, i) => {
    const x = X(route.at[i]);
    const y = Z(p[2]);
    if (i === 0) context.moveTo(x, y); else context.lineTo(x, y);
  });
  context.stroke();
  for (const anchor of anchors) {
    const x = X(anchor.at.s);
    context.fillStyle = UNIT_BLUE;
    context.beginPath();
    context.arc(x, Z(anchor.z), 3.5, 0, Math.PI * 2);
    context.fill();
  }
  context.restore();
  // The heights on the vertical axis, highest at the top.
  context.fillStyle = quiet;
  context.font = "11px 'IBM Plex Sans', system-ui, sans-serif";
  context.fillText(metres(Math.max(...zs)), left + 6, Z(Math.max(...zs)) - 6);
  context.fillText(metres(Math.min(...zs)), left + 6, Z(Math.min(...zs)) + 16);
  context.restore();
}
