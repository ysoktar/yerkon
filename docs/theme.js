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
    tr: { dark: "Koyu", light: "Açık", title: "Koyu ve açık arasında geç" },
    en: { dark: "Dark", light: "Light", title: "Switch dark and light" },
  };
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
    /* The label says where the button goes, not where the page is. */
    button.textContent = dark() ? said.light : said.dark;
    button.title = said.title;
  }

  var chosen = kept();
  if (chosen === "dark" || chosen === "light") root.dataset.theme = chosen;
  if (!button) return;
  button.hidden = false;
  draw();
  button.addEventListener("click", function () {
    var next = dark() ? "light" : "dark";
    root.dataset.theme = next;
    keep(next);
    draw();
  });
})();
