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

/* How much the relief is stretched. True scale by default, where a
 * building on a hillside has its real shape; the page offers more, where
 * a hill in open country otherwise reads as flat. Buildings and what
 * stands on them keep their true height whatever this is. */
export let VERTICAL = 1;

/* The height the stretch is measured from: the lowest ground in the
 * scene. Stretched from sea level, ground a thousand metres up was lifted
 * four thousand more at five times and left the camera looking at empty
 * sky; stretched from its own floor, the ground stays where it was and
 * only its hills grow. */
let DATUM = 0;

export function setVertical(times) {
  VERTICAL = Math.max(1, Number(times) || 1);
}

export function setDatum(z) {
  DATUM = Number.isFinite(z) ? z : 0;
}

/* A ground height as drawn. */
export function lift(z) {
  return DATUM + (z - DATUM) * VERTICAL;
}

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

/* What colour a photograph shows at a point in the site's own metres.
 *
 * `pixels` is a flat RGBA run as `getImageData` hands it over, and
 * `extent` is where the picture's corners fall in those metres — which
 * is not the site's own extent: a fetch asks for a box and gets back
 * whole tiles, so the picture hangs off every edge.
 *
 * Nearest pixel rather than blended, the same choice `Aerial.sample`
 * makes on the other side and for the same reason: a mix of a roof and
 * the road beside it is a colour neither of them is.
 *
 * Outside the picture it answers null rather than clamping, unlike the
 * elevation. A path grazing the boundary needs the nearest known ground
 * to keep a link budget honest; ground with no photograph over it needs
 * to be drawn as ground with no photograph over it, and clamping would
 * smear the edge row of pixels out across the countryside instead.
 */
export function photoSampler(pixels, width, height, extent, sheet = null) {
  const [west, south, east, north] = extent;
  const across = Math.max(east - west, 1e-9);
  const down = Math.max(north - south, 1e-9);
  return {
    // The picture itself, for the painter to lay across the ground once
    // the camera is still.
    image: sheet,
    pixelOf(x, y) {
      return [(x - west) / across * width, (north - y) / down * height];
    },
    colourAt(x, y) {
      const u = (x - west) / across;
      const v = (north - y) / down;           // rows run north to south
      if (u < 0 || u >= 1 || v < 0 || v >= 1) return null;
      const at = ((Math.floor(v * height) * width) + Math.floor(u * width)) * 4;
      return [pixels[at], pixels[at + 1], pixels[at + 2]];
    },
  };
}

/* The olive this project has always drawn bare ground in. */
const BARE = [126, 146, 104];

/* The ground, one quad per mesh cell, shaded by which way it faces.
 *
 * `photo`, where a site was fetched with one, is the aerial photograph:
 * each quad takes the colour of the ground under its own middle instead
 * of the olive, and the same shading is applied on top so that a hill
 * still reads as a hill rather than as a flat picture.
 *
 * One colour per quad rather than the picture mapped across each of
 * them: this painter fills flat polygons, and drawing a slice of an
 * image through four thousand of them with a transform apiece is a
 * different renderer. It costs less than it sounds like — the mesh
 * follows the camera, so the quads over a street are metres across and
 * the photograph comes through at the resolution somebody is looking at
 * it from (`ground` in scene.py).
 */
export function groundFaces(view, terrain, light, photo) {
  const { xs, ys, heights } = terrain;
  const out = [];
  for (let row = 0; row < ys.length - 1; row++) {
    for (let column = 0; column < xs.length - 1; column++) {
      const corners = [
        [xs[column], ys[row], lift(heights[row][column])],
        [xs[column + 1], ys[row], lift(heights[row][column + 1])],
        [xs[column + 1], ys[row + 1], lift(heights[row + 1][column + 1])],
        [xs[column], ys[row + 1], lift(heights[row + 1][column])],
      ];
      const normal = unit(cross(
        sub(corners[1], corners[0]), sub(corners[3], corners[0]),
      ));
      const lit = 0.45 + 0.55 * Math.max(0, dot(normal, light));
      // The finer picture of the ground under the camera, where there is
      // one and it covers the whole quad; the site's own picture otherwise.
      const sheet = photo && photo.pick ? photo.pick(corners) : photo;
      const ink = (sheet && sheet.colourAt(
        (xs[column] + xs[column + 1]) / 2, (ys[row] + ys[row + 1]) / 2,
      )) || BARE;
      const painted = face(
        view, corners,
        `rgb(${Math.round(ink[0] * lit)},${Math.round(ink[1] * lit)},${Math.round(ink[2] * lit)})`,
        1, 0.6,
      );
      if (painted && sheet && sheet.image && painted.screen.length === 4) {
        // Where the quad's corners fall on the picture, so a still frame
        // can lay the photograph itself across it rather than one colour.
        painted.texture = {
          image: sheet.image,
          source: corners.map(point => sheet.pixelOf(point[0], point[1])),
          shade: 1 - lit,
          // Triangles that follow the ground, where the whole quad is in
          // front of the eye: see `slices`. Worked out only when the
          // quad is actually laid with the picture, which a flat frame
          // never asks for.
          slice: corners.every(point => view.depthOf(point) >= NEAR)
            ? most => slices(view, corners, sheet, most) : null,
        };
      }
      if (painted) {
        painted.ground = [row, column];
        out.push(painted);
      }
    }
  }
  return out;
}

/* The ground as a few hundred large patches, for a moving frame.
 *
 * Far out, the ground is thousands of quads a few pixels across, and no
 * moving frame can lay the picture on each of them: the ones it could
 * not came out as flat squares and the drag looked like a mosaic. So
 * while moving, the ground can instead be drawn as a coarse grid over
 * the same mesh, `across` patches a side, each laid with the picture as
 * two triangles whose corners are mesh nodes and so sit on the ground.
 * Everything else is painted over it as usual; the one thing given up,
 * until the camera stops, is a hill hiding what stands behind it.
 *
 * Returns the triangles and which patches were drawn: a patch reaching
 * behind the eye is left to its own quads.
 */
export function groundPatches(view, terrain, photo, across = 16) {
  if (!terrain || !photo || !photo.image) return null;
  const { xs, ys, heights } = terrain;
  const step = Math.max(1, Math.ceil(Math.max(xs.length, ys.length) / across));
  const node = (row, column) => {
    const r = Math.min(row, ys.length - 1), c = Math.min(column, xs.length - 1);
    return [xs[c], ys[r], lift(heights[r][c])];
  };
  const triangles = [];
  const covered = new Set();
  for (let row = 0; row < ys.length - 1; row += step) {
    for (let column = 0; column < xs.length - 1; column += step) {
      const corners = [node(row, column), node(row, column + step),
                       node(row + step, column + step), node(row + step, column)];
      if (!corners.every(point => view.depthOf(point) >= NEAR)) continue;
      const sheet = photo.pick ? photo.pick(corners) : photo;
      const cut = slices(view, corners, sheet, 1);
      if (!cut) continue;
      for (const corner of cut) triangles.push({ image: sheet.image, corners: corner });
      covered.add(Math.floor(row / step) + "," + Math.floor(column / step));
    }
  }
  return { triangles, covered, step };
}

/* A ground quad cut into triangles for the photograph to lie on.
 *
 * One affine map per quad is exact at three of its corners and wrong at
 * the fourth, and a quad seen in perspective is not a parallelogram on
 * screen: close to the ground, where one quad is hundreds of pixels
 * across, neighbouring quads laid the picture down out of step and every
 * edge showed as a seam. Two triangles share their corners exactly, so
 * they meet without one; cutting a large quad into smaller ones keeps
 * the perspective from bending the picture inside each. The cut follows
 * how big the quad is on screen, so a far quad costs two triangles and
 * only the few under the camera cost more.
 */
const SLICE_PX = 64;
const MOST_SLICES = 8;
const MOVING_SLICES = 4;

function slices(view, corners, sheet, most = MOST_SLICES) {
  const onScreen = corners.map(view.project);
  if (onScreen.some(point => point === null)) return null;
  let longest = 0;
  for (let i = 0; i < 4; i++) {
    const [a, b] = [onScreen[i], onScreen[(i + 1) % 4]];
    longest = Math.max(longest, Math.hypot(b[0] - a[0], b[1] - a[1]));
  }
  const n = Math.min(most, Math.max(1, Math.ceil(longest / SLICE_PX)));
  const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                             a[2] + (b[2] - a[2]) * t];
  const grid = [];
  for (let j = 0; j <= n; j++) {
    const row = [];
    for (let i = 0; i <= n; i++) {
      const point = lerp(lerp(corners[0], corners[1], i / n),
                         lerp(corners[3], corners[2], i / n), j / n);
      const screen = view.project(point);
      if (!screen) return null;
      row.push({ screen, source: sheet.pixelOf(point[0], point[1]) });
    }
    grid.push(row);
  }
  const out = [];
  for (let j = 0; j < n; j++) {
    for (let i = 0; i < n; i++) {
      const [a, b, c, d] = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1],
                            grid[j + 1][i]];
      out.push([a, b, c], [a, c, d]);
    }
  }
  return out;
}

/* The walls' colour, a pale render. */
const WALL = [196, 190, 180];

/* Buildings as blocks standing on the bare ground.
 *
 * Each is [x, y, half side, height, lowest and highest ground under it,
 * outline] in the site's metres. The outline is the footprint the fetch
 * brought, a flat x0, y0, x1, y1... run; where there is none the block is
 * the disc the link budget reads, drawn as the square of the same area.
 * The relief is exaggerated so a hill reads as a hill; a building is
 * not, or a nine metre block stands forty five metres tall. It stands
 * from the lowest ground under it and rises its own height over the
 * highest, so on a slope it is sunk rather than hanging off the hill and
 * no hilltop pokes through its roof. The roof takes the photograph under it, like the ground, and
 * each wall the shading of the way it faces. Walls facing away from the
 * eye are left out, which is half of them and nothing a person would see.
 */
export function blocks(view, list, light, photo, bias = 0) {
  const out = [];
  for (const [x, y, half, height, low, high, outline] of list || []) {
    const base = lift(low);
    const top = lift(high ?? low) + height;
    // Sorted a little nearer than its middle, by its own size: a roof a
    // hundred metres across sits over ground quads ten metres across, and
    // at the depth of its middle it is painted before the ones under it.
    const nearer = bias + half;
    let at = [];
    if (outline && outline.length >= 6) {
      for (let i = 0; i < outline.length; i += 2) at.push([outline[i], outline[i + 1]]);
      // Anticlockwise, so each wall's outward side is on its right.
      let area = 0;
      for (let i = 0; i < at.length; i++) {
        const [ax, ay] = at[i];
        const [bx, by] = at[(i + 1) % at.length];
        area += ax * by - bx * ay;
      }
      if (area < 0) at.reverse();
    } else {
      at = [[x - half, y - half], [x + half, y - half],
            [x + half, y + half], [x - half, y + half]];
    }
    const roof = at.map(([px, py]) => [px, py, top]);
    const sheet = photo && photo.pick ? photo.pick(roof) : photo;
    const ink = (sheet && sheet.colourAt(x, y)) || WALL;
    const lit = 0.45 + 0.55 * Math.max(0, light[2]);
    const painted = face(
      view, roof,
      `rgb(${Math.round(ink[0] * lit)},${Math.round(ink[1] * lit)},${Math.round(ink[2] * lit)})`,
      1, 0.4, nearer,
    );
    if (painted && sheet && sheet.image && painted.screen.length === roof.length) {
      painted.texture = {
        image: sheet.image,
        source: roof.map(point => sheet.pixelOf(point[0], point[1])),
        shade: 1 - lit,
      };
    }
    if (painted) out.push(painted);
    for (let side = 0; side < at.length; side++) {
      const [ax, ay] = at[side];
      const [bx, by] = at[(side + 1) % at.length];
      const span = Math.hypot(bx - ax, by - ay);
      if (span < 0.5) continue;
      // Outward normal of this wall, in the ground plane.
      const normal = [(by - ay) / span, (ax - bx) / span, 0];
      const middle = [(ax + bx) / 2, (ay + by) / 2, (base + top) / 2];
      if (dot(sub(view.eye, middle), normal) <= 0) continue;
      const shade = 0.5 + 0.5 * Math.max(0, dot(normal, light));
      const wall = face(
        view,
        [[ax, ay, base], [bx, by, base], [bx, by, top], [ax, ay, top]],
        `rgb(${Math.round(WALL[0] * shade)},${Math.round(WALL[1] * shade)},${Math.round(WALL[2] * shade)})`,
        1, 0.4, nearer,
      );
      if (wall) out.push(wall);
    }
  }
  return out;
}

/* Four colours, worst to best.
 *
 * Four and no more. A continuous ramp looks like more information than a
 * swept grid holds and invites reading a boundary off a gradient; the
 * question a person asks of this picture is which band ground falls in.
 */
export const BANDS = [
  "rgb(191,86,58)",     // won't do
  "rgb(216,178,74)",    // thin
  "rgb(141,176,65)",    // fair
  "rgb(47,158,87)",     // comfortable
];

/* Which band a value falls in, or -1 for "there is no value here".
 *
 * `rising` says which way is better: more anchors and more margin are
 * better, while more dilution and more metres of error are worse, and
 * one function for both keeps the two from drifting apart.
 *
 * A rising layer is sent four thresholds — the first is the floor below
 * which nothing is painted — and a falling one three, because "nothing
 * here" reaches it as a null rather than as a small number.
 */
export function bandOf(value, edges, rising) {
  if (value === null || value === undefined || Number.isNaN(value)) return -1;
  if (rising) {
    if (value < edges[0]) return -1;        // below the first edge is nothing
    for (let i = edges.length - 1; i >= 1; i--) {
      if (value >= edges[i]) return i;
    }
    return 0;
  }
  for (let i = 0; i < edges.length; i++) {
    if (value <= edges[i]) return BANDS.length - 1 - i;
  }
  return 0;
}

//: Which layers read better as they grow.
export const RISING = { anchors: true, margin_db: true,
                        dilution: false, error_m: false };

/* `within` is the ground's own edge, [west, east, south, north]. A cell
 * is a square around its point, so the outer row reached half a cell past
 * the mesh and was painted over nothing: a ragged frame of pale squares
 * round the site. Each square is cut back to the ground instead. */
export function cellFaces(view, sweep, groundAt, bias = 0, layer = "anchors",
                          within = null) {
  if (!sweep) return [];
  const { xs, ys, resolution_m: size } = sweep;
  const values = (sweep.layers && sweep.layers[layer]) || sweep.counts;
  const edges = (sweep.bands && sweep.bands[layer]) || [1, 3, 4, 6];
  const rising = RISING[layer] !== false;
  const half = size / 2;
  // Over the ground it describes, by its own half-width and the mesh
  // cell under it: both surfaces sort at the depth of their middles and
  // both are wide, so the two spreads add.
  const over = bias + half;
  const out = [];
  for (let row = 0; row < ys.length; row++) {
    for (let column = 0; column < xs.length; column++) {
      const band = bandOf(values[row][column], edges, rising);
      // Ground with no number is left as ground. Painting it would say
      // "nothing reaches here" in the same visual language as "something
      // reaches here badly", and those are different facts.
      if (band < 0) continue;
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
      const z = lift(groundAt(x, y));
      let [x0, x1, y0, y1] = [x - half, x + half, y - half, y + half];
      if (within) {
        x0 = Math.max(x0, within[0]); x1 = Math.min(x1, within[1]);
        y0 = Math.max(y0, within[2]); y1 = Math.min(y1, within[3]);
        if (x1 <= x0 || y1 <= y0) continue;
      }
      const painted = face(
        view,
        [[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]],
        BANDS[band],
        // The better the ground, the more solidly it is stated. The
        // faint end is where the picture is least certain anyway.
        0.26 + 0.08 * band,
        0, over,
      );
      if (painted) out.push(painted);
    }
  }
  return out;
}

/* Where an anchor's foot is drawn: the bare ground exaggerated, plus
 * whatever structure under it (a roof) at its true height. */
export function standingZ(anchor) {
  const bare = anchor.bare_z ?? anchor.ground_z;
  return lift(bare) + (anchor.ground_z - bare);
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
    // On the exaggerated ground, with what it stands on (a roof) at its
    // true height, the way the buildings are drawn.
    const foot = standingZ(anchor);
    const base = view.project([anchor.x, anchor.y, foot]);
    if (!base) continue;
    const scaled = view.project([anchor.x, anchor.y, foot + anchor.z - anchor.ground_z]);
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

export function units(view, moving, named = id => id) {
  /* Each unit as a dot at its start with its route behind it. */
  const out = [];
  for (const unit of moving) {
    const at = view.project([unit.at[0], unit.at[1], lift(unit.at[2])]);
    if (!at) continue;
    out.push({
      kind: "unit", id: unit.id, label: named(unit.id),
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

/* Lay a slice of the photograph across one ground quad.
 *
 * The affine map that takes three of the quad's corners on the picture to
 * the same corners on screen, clipped to the quad. Affine rather than
 * projective: a quad is a few pixels to a few dozen across, and the
 * difference is under a pixel. Only the picture's own rectangle under
 * the quad is drawn, not the whole sheet, which is what keeps ten
 * thousand of these to a frame a person does not wait for.
 */
/* One triangle of the photograph, exact at its three corners.
 *
 * The clip is pushed out by under a pixel so that two triangles sharing
 * an edge overlap on it; clipped exactly, each edge is antialiased on
 * both sides and a faint line of the flat colour shows through. */
function triangle(context, image, corners) {
  const [s0, s1, s2] = corners.map(corner => corner.screen);
  const [t0, t1, t2] = corners.map(corner => corner.source);
  const u1 = [t1[0] - t0[0], t1[1] - t0[1]];
  const u2 = [t2[0] - t0[0], t2[1] - t0[1]];
  const det = u1[0] * u2[1] - u2[0] * u1[1];
  if (Math.abs(det) < 1e-9) return;
  const d1 = [s1[0] - s0[0], s1[1] - s0[1]];
  const d2 = [s2[0] - s0[0], s2[1] - s0[1]];
  const a = (d1[0] * u2[1] - d2[0] * u1[1]) / det;
  const c = (d2[0] * u1[0] - d1[0] * u2[0]) / det;
  const b = (d1[1] * u2[1] - d2[1] * u1[1]) / det;
  const d = (d2[1] * u1[0] - d1[1] * u2[0]) / det;
  const e = s0[0] - a * t0[0] - c * t0[1];
  const f = s0[1] - b * t0[0] - d * t0[1];
  const mx = (s0[0] + s1[0] + s2[0]) / 3;
  const my = (s0[1] + s1[1] + s2[1]) / 3;
  const out = point => {
    const dx = point[0] - mx, dy = point[1] - my;
    const length = Math.hypot(dx, dy) || 1;
    return [point[0] + dx / length * 0.7, point[1] + dy / length * 0.7];
  };
  const left = Math.max(0, Math.floor(Math.min(t0[0], t1[0], t2[0])) - 1);
  const top = Math.max(0, Math.floor(Math.min(t0[1], t1[1], t2[1])) - 1);
  const right = Math.min(image.width, Math.ceil(Math.max(t0[0], t1[0], t2[0])) + 1);
  const bottom = Math.min(image.height, Math.ceil(Math.max(t0[1], t1[1], t2[1])) + 1);
  if (right <= left || bottom <= top) return;
  context.save();
  context.beginPath();
  const [p0, p1, p2] = [out(s0), out(s1), out(s2)];
  context.moveTo(p0[0], p0[1]);
  context.lineTo(p1[0], p1[1]);
  context.lineTo(p2[0], p2[1]);
  context.closePath();
  context.clip();
  context.transform(a, b, c, d, e, f);
  context.drawImage(image, left, top, right - left, bottom - top,
                    left, top, right - left, bottom - top);
  context.restore();
}

/* How large a quad has to be on screen before a moving frame lays the
 * picture on it, and how finely it is cut then. Smaller than this a flat
 * colour and the picture cannot be told apart, and a moving frame is
 * one that has to be quick. */
const MOVING_MIN_PX = 12;

function longestSide(screen) {
  let longest = 0;
  for (let i = 0; i < screen.length; i++) {
    const [a, b] = [screen[i], screen[(i + 1) % screen.length]];
    longest = Math.max(longest, Math.hypot(b[0] - a[0], b[1] - a[1]));
  }
  return longest;
}

function textured(context, item) {
  const moving = texturing.moving && !texturing.still;
  if (moving && !item.pictured) return false;
  // A moving frame lays each quad with one draw rather than two
  // triangles: the seam that leaves is not visible while the ground is
  // moving, and the same frame time covers twice the quads.
  // Where the device can afford it, a moving frame keeps the exact
  // picture too, cut a little less finely: the one-draw quad bends the
  // photograph at its fourth corner, and that bend is what flickers.
  const triangles = (!moving || texturing.exact) && item.texture.slice
    ? item.texture.slice(moving ? MOVING_SLICES : MOST_SLICES) : null;
  if (triangles) {
    context.beginPath();
    context.moveTo(item.screen[0][0], item.screen[0][1]);
    for (const point of item.screen.slice(1)) context.lineTo(point[0], point[1]);
    context.closePath();
    context.fillStyle = item.colour;
    context.fill();
    for (const corners of triangles) {
      triangle(context, item.texture.image, corners);
    }
    texturing.drawn += triangles.length;
    if (item.texture.shade > 0.01) {
      context.beginPath();
      context.moveTo(item.screen[0][0], item.screen[0][1]);
      for (const point of item.screen.slice(1)) context.lineTo(point[0], point[1]);
      context.closePath();
      context.globalAlpha = item.texture.shade * 0.8;
      context.fillStyle = "#000";
      context.fill();
      context.globalAlpha = 1;
    }
    return true;
  }
  // Three of its corners fix the map: the first, the second and the
  // last, which for a quad are three of its four and for a roof any
  // three that are not in a line.
  const last = item.screen.length - 1;
  const [s0, s1, s3] = [item.screen[0], item.screen[1], item.screen[last]];
  const [t0, t1, t3] = [item.texture.source[0], item.texture.source[1],
                        item.texture.source[last]];
  const u1 = [t1[0] - t0[0], t1[1] - t0[1]];
  const u3 = [t3[0] - t0[0], t3[1] - t0[1]];
  const det = u1[0] * u3[1] - u3[0] * u1[1];
  if (Math.abs(det) < 1e-9) return false;
  const d1 = [s1[0] - s0[0], s1[1] - s0[1]];
  const d3 = [s3[0] - s0[0], s3[1] - s0[1]];
  const a = (d1[0] * u3[1] - d3[0] * u1[1]) / det;
  const c = (d3[0] * u1[0] - d1[0] * u3[0]) / det;
  const b = (d1[1] * u3[1] - d3[1] * u1[1]) / det;
  const d = (d3[1] * u1[0] - d1[1] * u3[0]) / det;
  const e = s0[0] - a * t0[0] - c * t0[1];
  const f = s0[1] - b * t0[0] - d * t0[1];
  const xs = item.texture.source.map(p => p[0]);
  const ys = item.texture.source.map(p => p[1]);
  const image = item.texture.image;
  const left = Math.max(0, Math.floor(Math.min(...xs)) - 1);
  const top = Math.max(0, Math.floor(Math.min(...ys)) - 1);
  const right = Math.min(image.width, Math.ceil(Math.max(...xs)) + 1);
  const bottom = Math.min(image.height, Math.ceil(Math.max(...ys)) + 1);
  if (right <= left || bottom <= top) return false;
  context.beginPath();
  context.moveTo(item.screen[0][0], item.screen[0][1]);
  for (const point of item.screen.slice(1)) context.lineTo(point[0], point[1]);
  context.closePath();
  // The quad's own colour underneath: where the fourth corner does not
  // sit where the affine map puts it (a wall, a steep slope), the slice
  // leaves a sliver, and a sliver of the page behind reads as a hole.
  context.fillStyle = item.colour;
  context.fill();
  context.save();
  context.clip();
  // Composed with the transform already on the context, not put in its
  // place. The page scales the canvas by the screen's pixel ratio, and
  // replacing that drew the picture at two thirds of its size on a
  // 150 % screen, outside the clip: every quad came out its flat colour.
  context.transform(a, b, c, d, e, f);
  context.drawImage(image, left, top, right - left, bottom - top,
                    left, top, right - left, bottom - top);
  context.restore();
  texturing.drawn += 1;
  // The same shading the flat colour carries, so a hill reads as a hill.
  if (item.texture.shade > 0.01) {
    context.globalAlpha = item.texture.shade * 0.8;
    context.fillStyle = "#000";
    context.fill();
  }
  return true;
}

/* Whether quads carrying a photograph are drawn with it.
 *
 * `still` is the frame painted once the camera stops: every quad, cut
 * as finely as it needs. `moving` is a frame during a drag, where only
 * the quads large enough to show the difference carry the picture and
 * are cut coarsely; the page turns it on where such frames prove quick
 * enough. With neither, every quad is its flat colour. */
export const texturing = {
  on: false, still: false, moving: false,
  // Whether a moving frame draws the picture exactly (a capable device)
  // or quickly; the page sets it from its quality setting.
  exact: false,
  // How many triangles a moving frame may lay the picture on, largest
  // quads first; the page sets it from how long they took to draw.
  budget: 0,
  // How many were drawn in the last frame, for the page to time.
  drawn: 0,
  // The coarse ground a moving frame may draw instead of every quad.
  patches: null,
};

/* Which quads a moving frame lays the picture on: the largest on screen
 * first, until the budget is spent. The nearest ground is where the
 * difference between a flat colour and the picture shows. */
function chooseForMoving(items) {
  const candidates = [];
  for (const item of items) {
    item.pictured = false;
    if (item.kind !== "face" || !item.texture || !item.texture.slice) continue;
    const size = longestSide(item.screen);
    if (size >= MOVING_MIN_PX) candidates.push([size, item]);
  }
  // More quads than the budget: the coarse ground covers all of it in a
  // few hundred draws, where the quads would leave most of it flat.
  // A device that draws exactly lays the picture on every quad and
  // never falls back on the coarse ground.
  if (texturing.exact) {
    for (const [, item] of candidates) item.pictured = true;
    return null;
  }
  const patches = texturing.patches;
  if (patches && candidates.length > texturing.budget
      && patches.triangles.length <= Math.max(texturing.budget, 600)) {
    return patches;
  }
  candidates.sort((a, b) => b[0] - a[0]);
  let left = texturing.budget;
  for (const [, item] of candidates) {
    if (left < 1) break;
    item.pictured = true;
    left -= 1;
  }
  return null;
}

/* How much everything but the lines is darkened, 0 to 1: the page turns
 * it up when the roads are brought forward, so the roads are what reads. */
export const shade = { dim: 0 };

function dimmed(context, screen) {
  if (!shade.dim || !screen) return;
  context.globalAlpha = shade.dim;
  context.fillStyle = "#0b1016";
  context.beginPath();
  context.moveTo(screen[0][0], screen[0][1]);
  for (const point of screen.slice(1)) context.lineTo(point[0], point[1]);
  context.closePath();
  context.fill();
}

export function paint(context, width, height, items) {
  context.clearRect(0, 0, width, height);
  items.sort((a, b) => b.depth - a.depth);
  texturing.drawn = 0;
  const coarse = texturing.on && texturing.moving && !texturing.still
    ? chooseForMoving(items) : null;
  if (coarse) {
    // The coarse ground first, under everything else in the frame.
    context.globalAlpha = 1;
    for (const piece of coarse.triangles) triangle(context, piece.image, piece.corners);
    texturing.drawn += coarse.triangles.length;
    if (shade.dim) {
      context.globalAlpha = shade.dim;
      context.fillStyle = "#0b1016";
      context.fillRect(0, 0, width, height);
    }
  }
  for (const item of items) {
    if (coarse && item.ground && coarse.covered.has(
      Math.floor(item.ground[0] / coarse.step) + ","
      + Math.floor(item.ground[1] / coarse.step))) continue;
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
      // A white edge round the stem and the head, so a unit stands out
      // on the photograph, the grey roofs and the green alike.
      context.globalAlpha = 1;
      context.lineCap = "round";
      context.strokeStyle = "#fff";
      context.lineWidth = 6;
      context.beginPath();
      context.moveTo(item.base[0], item.base[1]);
      context.lineTo(item.top[0], item.top[1]);
      context.stroke();
      context.strokeStyle = item.colour || "#3a4652";
      context.lineWidth = 3;
      context.beginPath();
      context.moveTo(item.base[0], item.base[1]);
      context.lineTo(item.top[0], item.top[1]);
      context.stroke();
      context.lineCap = "butt";
      context.fillStyle = item.colour || "#22282e";
      context.strokeStyle = "#fff";
      context.lineWidth = 2;
      context.beginPath();
      context.arc(item.top[0], item.top[1], 6.5, 0, Math.PI * 2);
      context.fill();
      context.stroke();
      continue;
    }
    if (item.kind === "face" && item.texture && texturing.on) {
      context.globalAlpha = 1;
      if (textured(context, item)) {
        dimmed(context, item.screen);
        continue;
      }
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
      dimmed(context, item.screen);
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
