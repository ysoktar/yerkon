/* The reader's choice of palette, kept between pages.
 *
 * site.css already follows the system setting in a media query, so a
 * page with no script running still comes up in the right palette. This
 * only adds an override. The button is written into the markup hidden
 * and shown here, because a control that does nothing is worse than no
 * control.
 */
(function () {
  var KEY = "yerkon-palette";
  var root = document.documentElement;
  var button = document.getElementById("theme");
  var words = {
    tr: { title: "Koyu ve açık arasında geç", close: "Kapat",
          back: "Önceki fotoğraf", on: "Sonraki fotoğraf" },
    en: { title: "Switch dark and light", close: "Close",
          back: "Previous picture", on: "Next picture" },
  };
  var SUN = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" '
    + 'stroke="currentColor" stroke-width="2" stroke-linecap="round">'
    + '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 '
    + '1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'
    + '</svg>';
  var MOON = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" '
    + 'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    + 'stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 '
    + '9.8 9.8z"/></svg>';
  var said = words[root.lang === "en" ? "en" : "tr"];

  function kept() {
    try {
      return localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  }

  function keep(name) {
    try {
      localStorage.setItem(KEY, name);
    } catch (e) {
      /* A reader with storage blocked still gets the switch, for this
         page only. */
    }
  }

  function dark() {
    if (root.dataset.theme) return root.dataset.theme === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function draw() {
    /* A switch: on is dark. */
    button.setAttribute("aria-checked", dark() ? "true" : "false");
  }

  var chosen = kept();
  if (chosen === "dark" || chosen === "light") root.dataset.theme = chosen;

  /* A link to another site opens in a new tab, so the page it was read
     on stays where it was. Links within this site (the menu, the pages
     on the home page, one page quoting another) and the note numbers
     stay in this tab. */
  Array.prototype.forEach.call(document.querySelectorAll("a[href]"),
    function (link) {
      if (!/^https?:/i.test(link.getAttribute("href") || "")) return;
      if (link.host === location.host) return;
      link.target = "_blank";
      link.rel = "noopener";
    });

  /* Any picture in a figure opens to the whole screen. In a strip of
     pictures the arrows beside it and the arrow keys move through the
     strip, and so does a swipe on a phone; a picture standing on its own
     opens alone. While it is open the page behind does not scroll, and
     on closing the page is where it was and the last picture looked at
     sits in the middle of the strip. */
  document.addEventListener("click", function (event) {
    var picture = event.target.closest && event.target.closest("figure img");
    if (!picture) return;
    var strip = picture.closest(".slides");
    var group = strip
      ? Array.prototype.slice.call(strip.querySelectorAll("figure img"))
      : [picture];
    var at = Math.max(0, group.indexOf(picture));
    var scrolled = window.scrollY;
    var overflow = root.style.overflow;
    root.style.overflow = "hidden";
    var box = document.createElement("div");
    box.className = "lightbox";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-label", said.close);
    var frame = document.createElement("div");
    frame.className = "frame";
    var big = document.createElement("img");
    frame.appendChild(big);
    box.appendChild(frame);
    var count = document.createElement("span");
    count.className = "count";
    function show(index) {
      at = (index + group.length) % group.length;
      var shown = group[at];
      big.src = shown.currentSrc || shown.src;
      big.alt = shown.alt;
      count.textContent = (at + 1) + " / " + group.length;
    }
    function arrow(name, step, glyph) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "step " + name;
      button.title = said[name];
      button.setAttribute("aria-label", said[name]);
      button.textContent = glyph;
      button.addEventListener("click", function (click) {
        click.stopPropagation();
        show(at + step);
      });
      frame.appendChild(button);
    }
    if (group.length > 1) {
      box.className += " group";
      arrow("back", -1, "‹");
      arrow("on", 1, "›");
      box.appendChild(count);
    }
    show(at);
    function close() {
      box.remove();
      document.removeEventListener("keydown", onKey);
      root.style.overflow = overflow;
      window.scrollTo(window.scrollX, scrolled);
      if (strip) {
        var card = group[at].closest(".slides > *") || group[at];
        strip.scrollTo({ left: centred(strip, card), behavior: "auto" });
      }
    }
    // A wheel or a finger over the picture moves nothing behind it.
    box.addEventListener("wheel", function (wheel) { wheel.preventDefault(); },
      { passive: false });
    box.addEventListener("touchmove", function (move) { move.preventDefault(); },
      { passive: false });
    function onKey(key) {
      if (key.key === "Escape") close();
      else if (group.length > 1 && key.key === "ArrowLeft") show(at - 1);
      else if (group.length > 1 && key.key === "ArrowRight") show(at + 1);
    }
    var startX = null;
    box.addEventListener("touchstart", function (touch) {
      startX = touch.touches.length === 1 ? touch.touches[0].clientX : null;
    }, { passive: true });
    box.addEventListener("touchend", function (touch) {
      if (startX === null || group.length < 2) return;
      var dx = touch.changedTouches[0].clientX - startX;
      startX = null;
      if (Math.abs(dx) > 50) {
        touch.preventDefault();
        show(at + (dx < 0 ? 1 : -1));
      }
    });
    box.addEventListener("click", close);
    document.addEventListener("keydown", onKey);
    document.body.appendChild(box);
  });

  /* The button at the end of a table row opens that row's notes over
     the page: a copy of the panel drawn hidden under the table. */
  document.addEventListener("click", function (event) {
    var opener = event.target.closest && event.target.closest("button.rowinfo");
    if (!opener) return;
    var drawn = document.querySelector(
      '.rowpanels section[data-row="' + opener.dataset.row + '"]');
    if (!drawn) return;
    var box = document.createElement("div");
    box.className = "panel";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    var section = drawn.cloneNode(true);
    var shut = document.createElement("button");
    shut.type = "button";
    shut.className = "shut";
    shut.title = said.close;
    shut.setAttribute("aria-label", said.close);
    shut.textContent = "×";
    section.insertBefore(shut, section.firstChild);
    box.appendChild(section);
    function close() {
      box.remove();
      document.removeEventListener("keydown", onKey);
      opener.focus();
    }
    function onKey(key) { if (key.key === "Escape") close(); }
    box.addEventListener("click", function (inside) {
      if (inside.target === box || inside.target === shut) close();
    });
    document.addEventListener("keydown", onKey);
    document.body.appendChild(box);
    shut.focus();
  });

  /* A strip of slides gets its arrows: each moves it by one card and the
     gap after it, and an arrow with nowhere to go is greyed out. */
  Array.prototype.forEach.call(document.querySelectorAll(".slider"),
    function (slider) {
      var strip = slider.querySelector(".slides");
      var back = slider.querySelector(".slide-back");
      var on = slider.querySelector(".slide-on");
      function mark() {
        back.disabled = strip.scrollLeft <= 2;
        on.disabled = strip.scrollLeft + strip.clientWidth >= strip.scrollWidth - 2;
      }
      back.hidden = on.hidden = false;
      function card() {
        var first = strip.children[0];
        var gap = parseFloat(getComputedStyle(strip).columnGap) || 0;
        return first ? first.getBoundingClientRect().width + gap : strip.clientWidth;
      }
      // Each click moves one card from where the strip is headed, so two
      // quick clicks go two cards rather than one and a half.
      function step(by) {
        var list = snaps(strip);
        var from = strip._target != null ? strip._target : strip.scrollLeft;
        var at = nearest(list, from) + by;
        glideTo(strip, list[Math.max(0, Math.min(list.length - 1, at))]);
      }
      back.addEventListener("click", function () { step(-1); });
      on.addEventListener("click", function () { step(1); });
      strip.addEventListener("scroll", mark, { passive: true });
      window.addEventListener("resize", mark);
      mark();
      draggable(strip, card);
      gauge(slider, strip);
    });

  var still = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Where the strip can rest: each card in the middle of the strip, the
     first and last ones clamped to the ends the strip can reach. */
  function centred(strip, card) {
    var box = strip.getBoundingClientRect(), it = card.getBoundingClientRect();
    return strip.scrollLeft + it.left + it.width / 2
      - (box.left + strip.clientLeft + strip.clientWidth / 2);
  }
  function snaps(strip) {
    var most = strip.scrollWidth - strip.clientWidth;
    var out = [];
    Array.prototype.forEach.call(strip.children, function (card) {
      var at = Math.min(most, Math.max(0, centred(strip, card)));
      if (!out.length || Math.abs(at - out[out.length - 1]) > 1) out.push(at);
    });
    return out.length ? out : [0];
  }

  function nearest(list, x) {
    var best = 0;
    for (var i = 1; i < list.length; i++) {
      if (Math.abs(list[i] - x) < Math.abs(list[best] - x)) best = i;
    }
    return best;
  }

  /* One continuous, slowing movement to a resting place. The browser's
     own snapping stays off until the strip is there: let back in early,
     it pulled the strip to its own choice in a single frame. */
  function glideTo(strip, left) {
    cancelAnimationFrame(strip._glide || 0);
    var from = strip.scrollLeft, distance = left - from;
    strip._target = left;
    strip.classList.add("dragging");
    function done() {
      strip._glide = 0;
      strip._target = null;
      strip.classList.remove("dragging");
    }
    if (still || Math.abs(distance) < 1) {
      strip.scrollLeft = left;
      done();
      return;
    }
    var duration = Math.min(560, Math.max(260, 220 + Math.abs(distance) * 0.45));
    var began = performance.now();
    (function frame(now) {
      var t = Math.min(1, (now - began) / duration);
      strip.scrollLeft = from + distance * (1 - Math.pow(1 - t, 3));
      if (t < 1) strip._glide = requestAnimationFrame(frame);
      else done();
    })(began);
  }

  /* A thin blue bar over the strip: how much of it is in view and
     where, standing in for the scroll bar a phone does not show. A click
     or a drag on it moves the strip there, and letting go lets the strip
     come to rest on the nearest card. */
  function gauge(slider, strip) {
    var bar = document.createElement("div");
    var thumb = document.createElement("i");
    bar.className = "strip-bar";
    bar.setAttribute("aria-hidden", "true");
    bar.appendChild(thumb);
    strip.parentNode.insertBefore(bar, strip);
    function paint() {
      var room = strip.scrollWidth - strip.clientWidth;
      bar.hidden = room <= 2;
      if (bar.hidden) return;
      var shown = strip.clientWidth / strip.scrollWidth;
      thumb.style.width = (shown * 100) + "%";
      thumb.style.left = (strip.scrollLeft / room * (1 - shown) * 100) + "%";
    }
    function to(event) {
      var box = bar.getBoundingClientRect();
      var at = (event.clientX - box.left) / box.width;
      var shown = strip.clientWidth / strip.scrollWidth;
      var share = Math.min(1, Math.max(0, (at - shown / 2) / (1 - shown)));
      strip.scrollLeft = share * (strip.scrollWidth - strip.clientWidth);
    }
    var held = null;
    bar.addEventListener("pointerdown", function (event) {
      held = event.pointerId;
      bar.setPointerCapture(event.pointerId);
      cancelAnimationFrame(strip._glide || 0);
      strip._target = null;
      strip.classList.add("dragging");
      to(event);
    });
    bar.addEventListener("pointermove", function (event) {
      if (held === event.pointerId) to(event);
    });
    function let_go(event) {
      if (held !== event.pointerId) return;
      held = null;
      var list = snaps(strip);
      glideTo(strip, list[nearest(list, strip.scrollLeft)]);
    }
    bar.addEventListener("pointerup", let_go);
    bar.addEventListener("pointercancel", let_go);
    strip.addEventListener("scroll", paint, { passive: true });
    window.addEventListener("resize", paint);
    paint();
  }

  /* A strip a mouse can throw, the way a finger throws it on a phone:
     press, drag, let go, and it carries on in one slowing movement to a
     card. Where it comes to rest follows the throw: a quick flick or a
     drag past a quarter of a card goes on to the next card, a slow short
     drag goes back, and a drag held still before letting go stays on the
     nearest card. A finger is handled the same way, so a phone feels
     like the computer: the strip takes sideways movement only, and an
     upward or downward swipe still scrolls the page (`touch-action` in
     the stylesheet). A drag is not a click, so letting go over a card
     after moving the strip does not open it. */
  function draggable(strip, card) {
    var down = null, moved = false, trail = [];
    strip.classList.add("draggable");

    strip.addEventListener("pointerdown", function (event) {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      cancelAnimationFrame(strip._glide || 0);
      strip._target = null;
      down = { x: event.clientX, left: strip.scrollLeft, id: event.pointerId };
      moved = false;
      trail = [[performance.now(), event.clientX]];
    });
    strip.addEventListener("pointermove", function (event) {
      if (!down || event.pointerId !== down.id) return;
      var dx = event.clientX - down.x;
      if (!moved && Math.abs(dx) > 5) {
        moved = true;
        strip.classList.add("dragging");
        strip.setPointerCapture(event.pointerId);
      }
      if (!moved) return;
      var now = performance.now();
      trail.push([now, event.clientX]);
      while (trail.length > 2 && now - trail[0][0] > 100) trail.shift();
      strip.scrollLeft = down.left - dx;
    });
    function release(event) {
      if (!down || event.pointerId !== down.id) return;
      var origin = down.left;
      down = null;
      if (!moved) return;
      // The speed of the last tenth of a second, and none at all if the
      // pointer was held still before letting go.
      var now = performance.now(), first = trail[0], last = trail[trail.length - 1];
      var speed = (now - last[0] > 90 || last[0] === first[0]) ? 0
        : (last[1] - first[1]) / (last[0] - first[0]);
      rest(origin, -speed);
    }

    // Where a throw comes to rest. `speed` is how fast the strip itself
    // was moving on, in pixels a millisecond, forwards positive.
    function rest(origin, speed) {
      var list = snaps(strip);
      var here = strip.scrollLeft;
      var start = nearest(list, origin);
      var at = nearest(list, here + speed * 300);
      var way = here > origin ? 1 : -1;
      if (at === start && (Math.abs(speed) > 0.3
          || Math.abs(here - origin) > card() * 0.25)) {
        at = Math.max(0, Math.min(list.length - 1, start + way));
      }
      glideTo(strip, list[at]);
    }

    // A sideways swipe on a touchpad, or a wheel turned with Shift held,
    // moves the strip under the fingers and, once they stop, carries it
    // on to a card the same way a throw does. Left to the browser's own
    // snapping, a short swipe sprang back and a long one jumped a card in
    // a single frame. An upward or downward wheel still scrolls the page.
    var wheelFrom = null, wheelTrail = [], wheelDone = 0;
    strip.addEventListener("wheel", function (event) {
      var across = event.deltaX || (event.shiftKey ? event.deltaY : 0);
      if (!across || (!event.shiftKey
          && Math.abs(event.deltaY) > Math.abs(event.deltaX))) return;
      event.preventDefault();
      if (event.deltaMode === 1) across *= 40;
      else if (event.deltaMode === 2) across *= strip.clientWidth;
      if (wheelFrom === null) {
        cancelAnimationFrame(strip._glide || 0);
        strip._target = null;
        wheelFrom = strip.scrollLeft;
        wheelTrail = [];
        strip.classList.add("dragging");
      }
      strip.scrollLeft += across;
      var now = performance.now();
      wheelTrail.push([now, strip.scrollLeft]);
      while (wheelTrail.length > 2 && now - wheelTrail[0][0] > 100) wheelTrail.shift();
      clearTimeout(wheelDone);
      wheelDone = setTimeout(function () {
        var first = wheelTrail[0], last = wheelTrail[wheelTrail.length - 1];
        var speed = last[0] === first[0] ? 0
          : (last[1] - first[1]) / (last[0] - first[0]);
        var origin = wheelFrom;
        wheelFrom = null;
        rest(origin, speed);
      }, 140);
    }, { passive: false });
    strip.addEventListener("pointerup", release);
    strip.addEventListener("pointercancel", release);
    // The click that ends a drag is swallowed; one that did not move is
    // an ordinary click on the card.
    strip.addEventListener("click", function (event) {
      if (moved) { event.preventDefault(); event.stopPropagation(); moved = false; }
    }, true);
    strip.addEventListener("dragstart", function (event) { event.preventDefault(); });
  }

  /* A note number in the table opens the folded notes before the page
     moves to the note. */
  function unfold(name) {
    var at = name && document.getElementById(name);
    var fold = at && at.closest && at.closest("details");
    if (fold && !fold.open) {
      fold.open = true;
      at.scrollIntoView();
    }
  }
  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest('a[href^="#"]');
    if (link) unfold(link.getAttribute("href").slice(1));
  });
  unfold(location.hash.slice(1));

  if (!button) return;
  button.hidden = false;
  button.setAttribute("role", "switch");
  button.title = said.title;
  button.setAttribute("aria-label", said.title);
  button.innerHTML = SUN + MOON + '<span class="knob"></span>';
  draw();
  button.addEventListener("click", function () {
    var next = dark() ? "light" : "dark";
    root.dataset.theme = next;
    keep(next);
    draw();
  });
})();
