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
    eye, width, height,
    /* How far in front of the eye a point is. Negative is behind it. */
    depthOf(point) { return dot(sub(point, eye), forward); },
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

/* Nothing closer to the eye than this is drawn. */
const NEAR = 2;

/* The part of a shape that is in front of the camera.
 *
 * A surface bigger than the view — a five hundred metre coverage cell
 * looked at from two hundred metres away — has corners behind the eye,
 * and a corner behind the eye cannot be projected at all. The whole
 * surface used to be dropped for it, so the ground and the coverage
 * under the camera went missing at exactly the distance where they are
 * the only thing on screen. Cut the shape at the near plane instead and
 * draw the part that is in front.
 */
function ahead(view, corners) {
  const out = [];
  for (let index = 0; index < corners.length; index++) {
    const from = corners[index];
    const to = corners[(index + 1) % corners.length];
    const here = view.depthOf(from);
    const there = view.depthOf(to);
    if (here >= NEAR) out.push(from);
    if ((here >= NEAR) !== (there >= NEAR)) {
      const share = (NEAR - here) / (there - here);
      out.push([
        from[0] + (to[0] - from[0]) * share,
        from[1] + (to[1] - from[1]) * share,
        from[2] + (to[2] - from[2]) * share,
      ]);
    }
  }
  return out;
}

/* A surface to paint: its corners, its colour, and how far away it is.
 *
 * Cut at the near plane where it straddles the eye, and dropped when it
 * is wholly off one edge of the frame. A twenty kilometre site meshed
 * finely enough to read is four thousand of these, and most of them are
 * off screen the moment anybody looks at anything closely; painting them
 * anyway is what made turning the camera cost thirty milliseconds a
 * frame.
 */
function face(view, corners, colour, alpha, grow = 0, bias = 0) {
  const whole = corners.every(point => view.depthOf(point) >= NEAR);
  const shape = whole ? corners : ahead(view, corners);
  if (shape.length < 3) return null;
  const screen = shape.map(view.project);
  if (screen.some(point => point === null)) return null;
  let depth = 0;
  let left = 0, right = 0, above = 0, below = 0;
  let midX = 0, midY = 0;
  for (const point of screen) {
    depth += point[2];
    midX += point[0];
    midY += point[1];
    if (point[0] < 0) left++;
    if (point[0] > view.width) right++;
    if (point[1] < 0) above++;
    if (point[1] > view.height) below++;
  }
  const all = screen.length;
  if (left === all || right === all || above === all || below === all) {
    return null;
  }
  // Grown by a fraction of a pixel from its own middle.
  //
  // Two quads that share an edge are antialiased independently, so the
  // ground behind shows through the join as a hairline and a mesh of
  // four thousand of them reads as a wire grid laid over the hill rather
  // than as ground. Overlapping the neighbour by half a pixel closes the
  // join; stroking each quad closes it too and costs a second pass over
  // every one of them.
  if (grow) {
    midX /= all;
    midY /= all;
    for (const point of screen) {
      const away = Math.hypot(point[0] - midX, point[1] - midY) || 1;
      point[0] += ((point[0] - midX) / away) * grow;
      point[1] += ((point[1] - midY) / away) * grow;
    }
  }
  return { screen, colour, alpha, depth: depth / all - bias, kind: "face" };
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
        1, 0.6,
      );
      if (painted) out.push(painted);
    }
  }
  return out;
}

export function cellFaces(view, sweep, groundAt, bias = 0) {
  if (!sweep) return [];
  const { xs, ys, counts, resolution_m: size } = sweep;
  const half = size / 2;
  // Over the ground it describes, by its own half-width and the mesh
  // cell under it: both surfaces sort at the depth of their middles and
  // both are wide, so the two spreads add.
  const over = bias + half;
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
      // On the ground, not above it.
      //
      // These used to be lifted sixty units clear of the mesh, which is
      // one way to stop the painter burying them in a slope and a poor
      // one: sixty units is twelve metres of real ground drawn five
      // times over, so close up the overlay hovers visibly above the
      // hill it describes. Sorting them in front on purpose says the
      // same thing without moving them, and says it at every distance.
      const z = groundAt(x, y) * VERTICAL;
      const painted = face(
        view,
        [[x - half, y - half, z], [x + half, y - half, z],
         [x + half, y + half, z], [x - half, y + half, z]],
        served ? "rgb(47,158,87)" : "rgb(216,178,74)",
        served ? 0.5 : 0.26,
        0, over,
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

/* A route, as one item per segment rather than one for the whole run.
 *
 * Everything here is sorted back to front and painted, so an item has
 * exactly one depth. A twenty kilometre road given the average depth of
 * its own hundred and sixty samples sits at one distance for painting
 * purposes, and every hill nearer than that average is painted over the
 * whole of it — including the near legs, which are in front of the hill.
 * Half the circuit disappeared that way and the half that survived made
 * an area deployment look like a straight line drawn across a field.
 *
 * Per segment, each piece sorts against the ground it is actually on, so
 * the road goes behind the hills it goes behind and stays in front of
 * the ones it crosses.
 */
export function polyline(view, points, colour, width, bias = 0) {
  const out = [];
  for (let index = 0; index < points.length - 1; index++) {
    // Cut at the near plane rather than dropped, for the same reason a
    // surface is: at a close zoom one end of a segment is often behind
    // the eye, and the part in front is the part being looked at.
    const piece = ahead(view, [points[index], points[index + 1]])
      .slice(0, 2);
    if (piece.length < 2) continue;
    const from = view.project(piece[0]);
    const to = view.project(piece[1]);
    if (!from || !to) continue;
    if (offFrame(view, from, to)) continue;
    out.push({
      kind: "line", points: [from, to], colour, width,
      // Pulled towards the camera by `bias`, which is the caller's mesh
      // cell. A line lying on the ground and the quad it lies on are the
      // same surface, and a quad sorts at the depth of its middle: seen
      // at a grazing angle its middle is most of a cell nearer than its
      // far edge, so the quad is painted over the half of the road that
      // is in front of it. That is what turned the road into a dashed
      // line — every segment on the far half of a cell disappeared.
      depth: (from[2] + to[2]) / 2 - bias,
    });
  }
  return out;
}

/* Both ends past one edge of the frame, so the segment between them is
 * too. Cheap, and it is what keeps a ring per anchor affordable. */
function offFrame(view, from, to) {
  return (from[0] < 0 && to[0] < 0)
    || (from[0] > view.width && to[0] > view.width)
    || (from[1] < 0 && to[1] < 0)
    || (from[1] > view.height && to[1] > view.height);
}

export function ring(view, centre, radius, colour, bias = 0) {
  const points = [];
  for (let step = 0; step <= 48; step++) {
    const angle = (step / 48) * Math.PI * 2;
    points.push([
      centre[0] + radius * Math.cos(angle),
      centre[1] + radius * Math.sin(angle),
      centre[2],
    ]);
  }
  return polyline(view, points, colour, 1.5, bias);
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
