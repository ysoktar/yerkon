/* A small 3D renderer, because the viewer should not need the network.
 *
 * The scene is a heightfield, some masts, a road and a grid of coverage
 * cells. That is few enough surfaces to project by hand and paint back
 * to front, which costs nothing to install, works with the machine
 * offline, and behaves the same everywhere. A WebGL library would be
 * prettier and would also mean the viewer stopped working the moment a
 * content delivery network was unreachable, which is exactly the failure
 * ADR-0008 exists to avoid.
 *
 * World axes: x runs along the corridor, y across it, z is elevation.
 */

export const VERTICAL = 5;   // relief is exaggerated, or hills read as flat

const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const scale = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];

function unit(a) {
  const length = Math.hypot(a[0], a[1], a[2]) || 1;
  return [a[0] / length, a[1] / length, a[2] / length];
}

export function camera(orbit, width, height) {
  const { yaw, pitch, distance, target } = orbit;
  const eye = [
    target[0] + distance * Math.cos(pitch) * Math.cos(yaw),
    target[1] + distance * Math.cos(pitch) * Math.sin(yaw),
    target[2] + distance * Math.sin(pitch),
  ];
  const forward = unit(sub(target, eye));
  const right = unit(cross(forward, [0, 0, 1]));
  const up = cross(right, forward);
  const focal = 1 / Math.tan((45 * Math.PI / 180) / 2);
  const half = height / 2;

  return {
    eye,
    /* World point to screen. Null when it is behind the camera. */
    project(point) {
      const d = sub(point, eye);
      const z = dot(d, forward);
      if (z <= 1) return null;
      return [
        width / 2 + (focal * dot(d, right) / z) * half,
        half - (focal * dot(d, up) / z) * half,
        z,
      ];
    },
    /* Screen pixel to the point where its ray meets a level plane. */
    onPlane(px, py, planeZ) {
      const direction = unit(add(
        add(scale(right, (px - width / 2) / half / focal),
            scale(up, (half - py) / half / focal)),
        forward,
      ));
      if (Math.abs(direction[2]) < 1e-9) return null;
      const travel = (planeZ - eye[2]) / direction[2];
      if (travel <= 0) return null;
      return add(eye, scale(direction, travel));
    },
  };
}

/* A surface to paint: its corners, its colour, and how far away it is. */
function face(view, corners, colour, alpha) {
  const screen = corners.map(view.project);
  if (screen.some(point => point === null)) return null;
  const depth = screen.reduce((total, p) => total + p[2], 0) / screen.length;
  return { screen, colour, alpha, depth, kind: "face" };
}

export function groundFaces(view, terrain, light) {
  const { xs, ys, heights } = terrain;
  const out = [];
  for (let row = 0; row < ys.length - 1; row++) {
    for (let column = 0; column < xs.length - 1; column++) {
      const corners = [
        [xs[column], ys[row], heights[row][column] * VERTICAL],
        [xs[column + 1], ys[row], heights[row][column + 1] * VERTICAL],
        [xs[column + 1], ys[row + 1], heights[row + 1][column + 1] * VERTICAL],
        [xs[column], ys[row + 1], heights[row + 1][column] * VERTICAL],
      ];
      const normal = unit(cross(
        sub(corners[1], corners[0]), sub(corners[3], corners[0]),
      ));
      const lit = 0.45 + 0.55 * Math.max(0, dot(normal, light));
      const painted = face(
        view, corners,
        `rgb(${Math.round(126 * lit)},${Math.round(146 * lit)},${Math.round(104 * lit)})`,
        1,
      );
      if (painted) out.push(painted);
    }
  }
  return out;
}

export function cellFaces(view, sweep, groundAt) {
  if (!sweep) return [];
  const { xs, ys, counts, resolution_m: size } = sweep;
  const half = size / 2;
  const out = [];
  for (let row = 0; row < ys.length; row++) {
    for (let column = 0; column < xs.length; column++) {
      const count = counts[row][column];
      if (count < 1) continue;
      // Two bands only, because the distinction that matters is between
      // ground a packet reaches and ground where a position exists.
      const served = count >= 4;
      const x = xs[column];
      const y = ys[row];
      // Lifted clear of the mesh. The ground sample under a cell is the
      // nearest mesh node rather than the exact height, so a small offset
      // leaves cells half-buried in a slope.
      const z = groundAt(x, y) * VERTICAL + 60;
      const painted = face(
        view,
        [[x - half, y - half, z], [x + half, y - half, z],
         [x + half, y + half, z], [x - half, y + half, z]],
        served ? "rgb(47,158,87)" : "rgb(216,178,74)",
        served ? 0.5 : 0.26,
      );
      if (painted) out.push(painted);
    }
  }
  return out;
}

export function masts(view, anchors, colourOf) {
  /* Drawn in screen space, not world space.
   *
   * A twenty-five metre mast beside a twenty-four kilometre corridor is
   * a thousandth of the scene and projects to less than a pixel. Painted
   * to scale it would be invisible, which would make the one control
   * that matters most impossible to see or to grab. So the mast is drawn
   * at a legible length on screen, in its group's colour, and its height
   * is reported in the panel as a number.
   */
  const out = [];
  for (const anchor of anchors) {
    const base = view.project([anchor.x, anchor.y, anchor.ground_z * VERTICAL]);
    if (!base) continue;
    const scaled = view.project([anchor.x, anchor.y, anchor.z * VERTICAL]);
    // Mounting height still shows through, so a three metre sign reads as
    // shorter than a twenty-five metre mast without either vanishing.
    const drawn = Math.max(12, Math.min(46,
      (scaled ? base[1] - scaled[1] : 0) + 10 + anchor.height_m * 0.5));
    out.push({
      kind: "mast", id: anchor.id, moved: anchor.moved,
      colour: anchor.moved ? "#b4551d" : colourOf(anchor.run),
      base, top: [base[0], base[1] - drawn], depth: base[2],
    });
  }
  return out;
}

export function units(view, moving) {
  /* Each unit as a dot at its start with its route behind it. */
  const out = [];
  for (const unit of moving) {
    const at = view.project([unit.at[0], unit.at[1], unit.at[2] * VERTICAL]);
    if (!at) continue;
    out.push({
      kind: "unit", id: unit.id, label: unit.id,
      at, depth: at[2], pedestrian: unit.kind === "pedestrian",
    });
  }
  return out;
}

export function polyline(view, points, colour, width) {
  const screen = points.map(view.project);
  const runs = [];
  let run = [];
  for (const point of screen) {
    if (point) { run.push(point); }
    else if (run.length > 1) { runs.push(run); run = []; }
    else { run = []; }
  }
  if (run.length > 1) runs.push(run);
  return runs.map(points => ({
    kind: "line", points, colour, width,
    depth: points.reduce((t, p) => t + p[2], 0) / points.length,
  }));
}

export function ring(view, centre, radius, colour) {
  const points = [];
  for (let step = 0; step <= 64; step++) {
    const angle = (step / 64) * Math.PI * 2;
    points.push([
      centre[0] + radius * Math.cos(angle),
      centre[1] + radius * Math.sin(angle),
      centre[2],
    ]);
  }
  return polyline(view, points, colour, 1.5);
}

export function paint(context, width, height, items) {
  context.clearRect(0, 0, width, height);
  items.sort((a, b) => b.depth - a.depth);
  for (const item of items) {
    if (item.kind === "unit") {
      context.globalAlpha = 1;
      context.fillStyle = "#b4551d";
      context.beginPath();
      if (item.pedestrian) {
        context.arc(item.at[0], item.at[1], 5, 0, Math.PI * 2);
      } else {
        context.rect(item.at[0] - 6, item.at[1] - 4, 12, 8);
      }
      context.fill();
      context.fillStyle = "#22282e";
      context.font = "11px system-ui, sans-serif";
      context.fillText(item.label, item.at[0] + 9, item.at[1] + 4);
      continue;
    }
    if (item.kind === "mast") {
      context.globalAlpha = 1;
      context.strokeStyle = item.colour || "#3a4652";
      context.lineWidth = 3;
      context.beginPath();
      context.moveTo(item.base[0], item.base[1]);
      context.lineTo(item.top[0], item.top[1]);
      context.stroke();
      context.fillStyle = item.colour || "#22282e";
      context.beginPath();
      context.arc(item.top[0], item.top[1], 4.5, 0, Math.PI * 2);
      context.fill();
      continue;
    }
    if (item.kind === "face") {
      context.globalAlpha = item.alpha;
      context.fillStyle = item.colour;
      context.beginPath();
      context.moveTo(item.screen[0][0], item.screen[0][1]);
      for (const point of item.screen.slice(1)) {
        context.lineTo(point[0], point[1]);
      }
      context.closePath();
      context.fill();
    } else if (item.kind === "line") {
      context.globalAlpha = 1;
      context.strokeStyle = item.colour;
      context.lineWidth = item.width;
      context.beginPath();
      context.moveTo(item.points[0][0], item.points[0][1]);
      for (const point of item.points.slice(1)) {
        context.lineTo(point[0], point[1]);
      }
      context.stroke();
    }
  }
  context.globalAlpha = 1;
}
