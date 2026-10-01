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
    tr: { title: "Koyu ve açık arasında geç", close: "Kapat" },
    en: { title: "Switch dark and light", close: "Close" },
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

  /* Any picture in a figure opens to the whole screen. */
  document.addEventListener("click", function (event) {
    var picture = event.target.closest && event.target.closest("figure img");
    if (!picture) return;
    var box = document.createElement("div");
    box.className = "lightbox";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-label", said.close);
    var big = document.createElement("img");
    big.src = picture.currentSrc || picture.src;
    big.alt = picture.alt;
    box.appendChild(big);
    function close() {
      box.remove();
      document.removeEventListener("keydown", onKey);
    }
    function onKey(key) { if (key.key === "Escape") close(); }
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

  /* A strip of slides gets its arrows: each moves it by what is in
     view, and an arrow with nowhere to go is greyed out. */
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
      back.addEventListener("click", function () {
        strip.scrollBy({ left: -strip.clientWidth, behavior: "smooth" });
      });
      on.addEventListener("click", function () {
        strip.scrollBy({ left: strip.clientWidth, behavior: "smooth" });
      });
      strip.addEventListener("scroll", mark, { passive: true });
      window.addEventListener("resize", mark);
      mark();
      draggable(strip);
    });

  /* A strip a mouse can throw, the way a finger throws it on a phone:
     press, drag, let go, and it glides on and settles on the nearest
     card. Touch is left to the browser, which already does this; only
     a mouse is handled here. A drag is not a click, so letting go over
     a card after moving the strip does not open it. */
  function draggable(strip) {
    var still = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var down = null, moved = false, gliding = 0, lastX = 0, lastT = 0, speed = 0;
    strip.classList.add("draggable");

    function settle() {
      // The card whose start is nearest where the strip stopped, its
      // left edge kept clear of the cut by the strip's own padding.
      var edge = strip.getBoundingClientRect().left;
      var best = 0, gap = Infinity;
      Array.prototype.forEach.call(strip.children, function (card) {
        var at = strip.scrollLeft + card.getBoundingClientRect().left - edge - 2;
        if (Math.abs(at - strip.scrollLeft) < gap) {
          gap = Math.abs(at - strip.scrollLeft); best = at;
        }
      });
      strip.classList.remove("dragging");
      strip.scrollTo({ left: Math.max(0, best), behavior: still ? "auto" : "smooth" });
    }

    function glide() {
      cancelAnimationFrame(gliding);
      if (still || Math.abs(speed) < 0.05) { settle(); return; }
      var then = performance.now();
      (function step(now) {
        var dt = Math.min(32, now - then); then = now;
        var before = strip.scrollLeft;
        strip.scrollLeft -= speed * dt;
        speed *= Math.pow(0.994, dt);
        if (Math.abs(speed) < 0.05 || strip.scrollLeft === before) settle();
        else gliding = requestAnimationFrame(step);
      })(then);
    }

    strip.addEventListener("pointerdown", function (event) {
      if (event.pointerType !== "mouse" || event.button !== 0) return;
      cancelAnimationFrame(gliding);
      down = { x: event.clientX, left: strip.scrollLeft, id: event.pointerId };
      moved = false; speed = 0; lastX = event.clientX; lastT = performance.now();
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
      if (now > lastT) {
        speed = 0.8 * speed + 0.2 * (event.clientX - lastX) / (now - lastT);
      }
      lastX = event.clientX; lastT = now;
      strip.scrollLeft = down.left - dx;
    });
    function release(event) {
      if (!down || event.pointerId !== down.id) return;
      down = null;
      if (moved) glide();
    }
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
