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
    });

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
