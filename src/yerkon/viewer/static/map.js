/* A map to pick a place on, and a box to draw on it freely.
 *
 * The fetch panel used to ask for a centre as text, which means knowing
 * the coordinates before you start — so "add a region" began by leaving
 * this application, opening a map somewhere else, right-clicking, and
 * pasting two numbers back. That is not choosing a place; that is
 * transcribing one.
 *
 * And the box is drawn rather than dialled. A centre and a size can only
 * describe a square around a pin, and the ground somebody wants is a
 * valley, a ring road, a stretch of motorway — shapes with a long side
 * and a short one. So the box has four corners a person can drag, and
 * the fetch takes those corners.
 *
 * Written here rather than pulled from a mapping library, for the same
 * reason `draw.js` exists: this is a local application that promises to
 * run offline after one fetch, and a script tag pointing at a CDN is a
 * second network dependency and a third party in the page. A slippy map
 * is a projection, a grid of images and two gestures.
 *
 * The projection is the one every web map uses — Web Mercator, the same
 * numbering `tile_of` and `tile_bounds` use in `site/fetch.py`, so a
 * tile this picker shows and a tile the fetch downloads are the same
 * tile.
 */

const TILE = 256;
export const LEAST_ZOOM = 2;
export const MOST_ZOOM = 19;

/* How far a pointer may travel and still count as a click rather than a
 * drag. A click fires after a drag too, and a map that recentres on
 * wherever the finger came to rest is one that feels broken. */
const A_CLICK_PX = 5;

/* OpenStreetMap's own tiles, which is what was asked for.
 *
 * A default address here and none for the photograph is not two minds
 * about the same question. Picking a place is a few dozen tiles as a
 * person pans around, which is the ordinary use OSM's tile policy
 * describes; draping a whole city over the terrain is thousands of them
 * at once, which that policy calls bulk and asks you not to do. So the
 * picker ships with a map and the drape ships with an empty box
 * (ADR-0041, ADR-0042).
 */
export const OSM = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";

/* Where a place name is looked up. Nominatim asks for no more than one
 * call a second and a client that names itself; this calls on a typed
 * search and never while panning. */
const SEARCH_URL = "https://nominatim.openstreetmap.org/search";

// --- The projection -------------------------------------------------------
//
// World pixels: the whole earth is 256 * 2^zoom pixels across at a given
// zoom, and a tile is the 256-pixel square at (x, y). Latitude is not
// linear in this — that is what makes it Mercator — so the two axes are
// converted separately.

export function worldSize(zoom) {
  return TILE * Math.pow(2, zoom);
}

export function lonToX(longitude, zoom) {
  return (longitude + 180) / 360 * worldSize(zoom);
}

export function latToY(latitude, zoom) {
  const clamped = Math.max(-85.05112878, Math.min(85.05112878, latitude));
  const radians = clamped * Math.PI / 180;
  return (1 - Math.asinh(Math.tan(radians)) / Math.PI) / 2 * worldSize(zoom);
}

export function xToLon(x, zoom) {
  return x / worldSize(zoom) * 360 - 180;
}

export function yToLat(y, zoom) {
  const n = Math.PI * (1 - 2 * y / worldSize(zoom));
  return Math.atan(Math.sinh(n)) * 180 / Math.PI;
}

/* Ground distance per degree here, the same two constants as
 * `BoundingBox.metres_per_degree` in `site/model.py`. */
export function metresPerDegree(latitude) {
  return {
    lat: 111132.92 - 559.82 * Math.cos(2 * latitude * Math.PI / 180),
    lon: 111412.84 * Math.cos(latitude * Math.PI / 180),
  };
}

/* The box a fetch of this size around this point would ask for.
 *
 * The same arithmetic as `box_around` in `site/model.py`: a degree of
 * longitude is shorter than a degree of latitude everywhere but the
 * equator, so the half-widths differ and a box that ignores it comes out
 * a rectangle nobody asked for.
 *
 * Used to seed the box when the map opens; after that the corners are
 * wherever somebody dragged them.
 */
export function boxAround(latitude, longitude, sizeKm) {
  const halfM = sizeKm * 500;
  const per = metresPerDegree(latitude);
  return {
    south: latitude - halfM / per.lat,
    north: latitude + halfM / per.lat,
    west: longitude - halfM / per.lon,
    east: longitude + halfM / per.lon,
  };
}

/* How many kilometres across and along a box is. */
export function boxSpanKm(box) {
  const per = metresPerDegree((box.south + box.north) / 2);
  return {
    across: (box.east - box.west) * per.lon / 1000,
    along: (box.north - box.south) * per.lat / 1000,
  };
}

// --- The map --------------------------------------------------------------

/* A pannable, zoomable map inside `host`, with a box drawn on it.
 *
 * Tiles are plain `<img>` elements positioned absolutely, kept in a map
 * keyed by `z/x/y` and reused across frames: the browser already
 * decodes, caches and draws images, and a canvas here would mean doing
 * all three again by hand for no gain.
 */
export class Picker {
  constructor(host, options = {}) {
    this.host = host;
    this.url = options.url || OSM;
    this.zoom = options.zoom || 12;
    this.centre = options.centre || { lat: 39.925, lon: 32.837 };
    this.onChange = options.onChange || (() => {});
    this.drawing = false;

    host.classList.add("map");
    host.innerHTML = "";
    this.tiles = element("div", "map-tiles");
    this.box = element("div", "map-box");
    this.grips = {};
    for (const corner of ["nw", "ne", "se", "sw"]) {
      const grip = element("i", `map-grip ${corner}`);
      grip.dataset.corner = corner;
      this.box.append(grip);
      this.grips[corner] = grip;
    }
    host.append(this.tiles, this.box);

    this.selection = options.box
      || boxAround(this.centre.lat, this.centre.lon, options.sizeKm || 3);
    this.live = new Map();
    this.wire();
    this.draw();
  }

  /* Every gesture the map has, decided at pointerdown.
   *
   * A corner grip resizes, the box body moves, and the background pans —
   * unless the draw button is down or shift is held, which starts a new
   * box from nothing. One handler decides; the rest of the drag is the
   * same code whichever it chose.
   */
  wire() {
    let gesture = null;

    const start = event => {
      const grip = event.target.closest(".map-grip");
      const inBox = event.target.closest(".map-box");
      const anchor = this.at(event.clientX, event.clientY);
      if (grip) {
        gesture = { kind: "resize", corner: grip.dataset.corner };
      } else if (this.drawing || event.shiftKey) {
        gesture = { kind: "draw", from: anchor };
        this.selection = { south: anchor.lat, north: anchor.lat,
                           west: anchor.lon, east: anchor.lon };
      } else if (inBox) {
        gesture = { kind: "move", from: anchor, was: { ...this.selection } };
      } else {
        gesture = { kind: "pan" };
      }
      gesture.moved = 0;
      gesture.last = { x: event.clientX, y: event.clientY };
      this.host.setPointerCapture(event.pointerId);
      this.host.classList.add("dragging");
      event.preventDefault();
    };

    const move = event => {
      if (!gesture) return;
      const dx = event.clientX - gesture.last.x;
      const dy = event.clientY - gesture.last.y;
      gesture.moved += Math.abs(dx) + Math.abs(dy);
      gesture.last = { x: event.clientX, y: event.clientY };
      const here = this.at(event.clientX, event.clientY);

      if (gesture.kind === "pan") {
        this.panBy(dx, dy);
      } else if (gesture.kind === "draw") {
        this.selection = {
          south: Math.min(gesture.from.lat, here.lat),
          north: Math.max(gesture.from.lat, here.lat),
          west: Math.min(gesture.from.lon, here.lon),
          east: Math.max(gesture.from.lon, here.lon),
        };
      } else if (gesture.kind === "move") {
        const dLat = here.lat - gesture.from.lat;
        const dLon = here.lon - gesture.from.lon;
        this.selection = {
          south: gesture.was.south + dLat, north: gesture.was.north + dLat,
          west: gesture.was.west + dLon, east: gesture.was.east + dLon,
        };
      } else if (gesture.kind === "resize") {
        const corner = gesture.corner;
        const next = { ...this.selection };
        if (corner.includes("n")) next.north = here.lat;
        if (corner.includes("s")) next.south = here.lat;
        if (corner.includes("w")) next.west = here.lon;
        if (corner.includes("e")) next.east = here.lon;
        // Dragged past the opposite edge, which is how anybody finds out
        // a box can be turned inside out. Sorted rather than refused.
        this.selection = {
          south: Math.min(next.south, next.north),
          north: Math.max(next.south, next.north),
          west: Math.min(next.west, next.east),
          east: Math.max(next.west, next.east),
        };
      }
      this.draw();
    };

    const stop = () => {
      if (gesture && gesture.kind === "draw" && gesture.moved < A_CLICK_PX) {
        // A click in draw mode, not a drag: nobody meant a box of zero
        // kilometres, so leave the one they had.
        this.draw();
      }
      gesture = null;
      this.drawing = false;
      this.host.classList.remove("dragging", "drawing");
      this.onChange(this.state());
    };

    this.host.addEventListener("pointerdown", start);
    this.host.addEventListener("pointermove", move);
    this.host.addEventListener("pointerup", stop);
    this.host.addEventListener("pointercancel", stop);
    this.host.addEventListener("wheel", event => {
      event.preventDefault();
      this.zoomBy(event.deltaY < 0 ? 1 : -1, event.clientX, event.clientY);
    }, { passive: false });
  }

  panBy(dx, dy) {
    const size = worldSize(this.zoom);
    const x = lonToX(this.centre.lon, this.zoom) - dx;
    const y = latToY(this.centre.lat, this.zoom) - dy;
    this.centre = {
      lon: xToLon(((x % size) + size) % size, this.zoom),
      lat: yToLat(Math.max(0, Math.min(size, y)), this.zoom),
    };
    this.draw();
  }

  /* Zoom a step, keeping the ground under the cursor under the cursor.
   *
   * Zooming about the middle instead is the behaviour where you aim at
   * something, zoom, and it slides off the screen. */
  zoomBy(step, clientX, clientY) {
    const next = Math.max(LEAST_ZOOM, Math.min(MOST_ZOOM, this.zoom + step));
    if (next === this.zoom) return;
    const rect = this.host.getBoundingClientRect();
    const under = clientX === undefined
      ? this.centre : this.at(clientX, clientY);
    const offX = clientX === undefined ? 0 : clientX - rect.left - rect.width / 2;
    const offY = clientY === undefined ? 0 : clientY - rect.top - rect.height / 2;

    this.zoom = next;
    // Put `under` back where the cursor is: the centre is that point,
    // moved back by the cursor's offset from the middle.
    this.centre = {
      lon: xToLon(lonToX(under.lon, next) - offX, next),
      lat: yToLat(latToY(under.lat, next) - offY, next),
    };
    this.draw();
    this.onChange(this.state());
  }

  /* What point on the ground a point on the screen is over. */
  at(clientX, clientY) {
    const rect = this.host.getBoundingClientRect();
    const x = lonToX(this.centre.lon, this.zoom)
      + (clientX - rect.left - rect.width / 2);
    const y = latToY(this.centre.lat, this.zoom)
      + (clientY - rect.top - rect.height / 2);
    return { lon: xToLon(x, this.zoom), lat: yToLat(y, this.zoom) };
  }

  /* Move the map to a place, and take the box with it.
   *
   * The box travels because the alternative is arriving at the place you
   * searched for with your selection still over the last one, off
   * screen, quietly about to be fetched.
   */
  goTo(lat, lon, zoom) {
    const span = boxSpanKm(this.selection);
    this.centre = { lat, lon };
    if (zoom) this.zoom = Math.max(LEAST_ZOOM, Math.min(MOST_ZOOM, zoom));
    const per = metresPerDegree(lat);
    this.selection = {
      south: lat - span.along * 500 / per.lat,
      north: lat + span.along * 500 / per.lat,
      west: lon - span.across * 500 / per.lon,
      east: lon + span.across * 500 / per.lon,
    };
    this.draw();
    this.onChange(this.state());
  }

  /* Make the box a square of this many kilometres, where it stands. */
  setSquare(sizeKm) {
    const middle = {
      lat: (this.selection.south + this.selection.north) / 2,
      lon: (this.selection.west + this.selection.east) / 2,
    };
    this.selection = boxAround(middle.lat, middle.lon, sizeKm);
    this.draw();
    this.onChange(this.state());
  }

  state() {
    return {
      centre: this.centre,
      zoom: this.zoom,
      box: { ...this.selection },
      span: boxSpanKm(this.selection),
    };
  }

  /* One frame: the tiles in view, then the box over them.
   *
   * Tiles already on screen are left alone and ones that scrolled off
   * are removed, so panning moves elements rather than rebuilding them.
   */
  draw() {
    const rect = this.host.getBoundingClientRect();
    const width = rect.width || 640;
    const height = rect.height || 420;
    const leftPx = lonToX(this.centre.lon, this.zoom) - width / 2;
    const topPx = latToY(this.centre.lat, this.zoom) - height / 2;

    const count = Math.pow(2, this.zoom);
    const firstX = Math.floor(leftPx / TILE);
    const firstY = Math.floor(topPx / TILE);
    const lastX = Math.floor((leftPx + width) / TILE);
    const lastY = Math.floor((topPx + height) / TILE);

    const wanted = new Set();
    for (let y = firstY; y <= lastY; y++) {
      if (y < 0 || y >= count) continue;
      for (let x = firstX; x <= lastX; x++) {
        // Wrapped round the dateline, so panning west of -180 keeps
        // showing map instead of falling off the edge of the world.
        const wrapped = ((x % count) + count) % count;
        const key = `${this.zoom}/${wrapped}/${y}@${x}`;
        wanted.add(key);
        let tile = this.live.get(key);
        if (!tile) {
          tile = element("img", "map-tile");
          tile.decoding = "async";
          tile.alt = "";
          tile.src = this.url
            .replace("{z}", this.zoom)
            .replace("{x}", wrapped)
            .replace("{y}", y);
          // A tile that will not load leaves its square empty rather
          // than putting a broken-image glyph on the map.
          tile.addEventListener("error", () => tile.classList.add("missing"));
          this.tiles.append(tile);
          this.live.set(key, tile);
        }
        tile.style.transform =
          `translate(${x * TILE - leftPx}px, ${y * TILE - topPx}px)`;
      }
    }
    for (const [key, tile] of this.live) {
      if (!wanted.has(key)) {
        tile.remove();
        this.live.delete(key);
      }
    }

    const west = lonToX(this.selection.west, this.zoom) - leftPx;
    const east = lonToX(this.selection.east, this.zoom) - leftPx;
    const north = latToY(this.selection.north, this.zoom) - topPx;
    const south = latToY(this.selection.south, this.zoom) - topPx;
    this.box.style.transform = `translate(${west}px, ${north}px)`;
    this.box.style.width = `${Math.max(1, east - west)}px`;
    this.box.style.height = `${Math.max(1, south - north)}px`;
  }
}

function element(tag, className) {
  const made = document.createElement(tag);
  made.className = className;
  return made;
}

/* Place names to coordinates, from OpenStreetMap's own search.
 *
 * Returns whatever it finds rather than the first hit, because "Konya"
 * is a city, a province and a district and only the person asking knows
 * which one they meant.
 */
export async function lookUp(text, language = "tr") {
  const query = new URLSearchParams({
    q: text, format: "jsonv2", limit: "6", "accept-language": language,
  });
  const response = await fetch(`${SEARCH_URL}?${query}`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`search: ${response.status}`);
  return (await response.json()).map(hit => ({
    name: hit.display_name,
    lat: Number(hit.lat),
    lon: Number(hit.lon),
    kind: hit.type || "",
  }));
}
