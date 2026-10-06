/* Where the page's questions go when there is no server (ADR-0080).
 *
 * On the published site the simulator runs in this browser: a worker
 * holds Python, numpy and the project's package, and every request the
 * page makes to /api/ is answered there instead of over the network.
 * The page itself is the same file the local server sends, so it does
 * not know the difference.
 *
 * A plain script, loaded before the page's module, so the replacement
 * fetch is in place before the page asks its first question.
 */
(() => {
  // The page reads this to say how long a run takes here, where the
  // engine is several times slower than on a computer of its own.
  window.YERKON_IN_BROWSER = true;
  const english = new URLSearchParams(location.search).get("dil") === "en";
  // Said in the reader's terms: somebody opening the page does not need
  // to know what Pyodide or numpy is, only how far along it is.
  const words = english ? {
    python: "Getting the simulator ready (1 of 4): downloading the calculation engine…",
    numpy: "Getting the simulator ready (2 of 4): loading the maths library…",
    package: "Getting the simulator ready (3 of 4): unpacking the YERKON model and the Ankara maps…",
    ready: "Getting the simulator ready (4 of 4): drawing the first scene…",
    failed: "The simulator could not start in this browser. Try a current Chrome, Edge, Firefox or Safari. Detail: ",
    again: "The connection dropped while the simulator was loading; trying again…",
    note: "The simulation runs on this device; nothing is sent anywhere. The first visit can take a minute or two; later visits are quicker, because the downloaded files stay in the browser.",
    home: "Back to the site",
  } : {
    python: "Simülatör hazırlanıyor (1/4): hesap motoru indiriliyor…",
    numpy: "Simülatör hazırlanıyor (2/4): matematik kütüphanesi yükleniyor…",
    package: "Simülatör hazırlanıyor (3/4): YERKON modeli ve Ankara haritaları açılıyor…",
    ready: "Simülatör hazırlanıyor (4/4): ilk sahne çiziliyor…",
    failed: "Simülatör bu tarayıcıda açılamadı. Güncel bir Chrome, Edge, Firefox ya da Safari ile deneyiniz. Ayrıntı: ",
    again: "Simülatör yüklenirken bağlantı kesildi; yeniden deneniyor…",
    note: "Simülasyon bu cihazda çalışmakta, hiçbir veri dışarı gönderilmemektedir. İlk açılış bir iki dakika sürebilir; indirilen dosyalar tarayıcıda kaldığı için sonraki açılışlar daha hızlıdır.",
    home: "Siteye dön",
  };

  const cover = document.createElement("div");
  cover.id = "booting";
  cover.setAttribute("role", "status");
  cover.style.cssText = [
    "position:fixed", "inset:0", "z-index:1000", "display:flex",
    "flex-direction:column", "align-items:center", "justify-content:center",
    "gap:12px", "background:rgba(20,24,28,0.92)", "color:#f4f4f2",
    "font:16px/1.5 \"IBM Plex Sans\",system-ui,sans-serif", "text-align:center", "padding:24px",
  ].join(";");
  const line = document.createElement("div");
  const note = document.createElement("div");
  note.style.cssText = "opacity:0.75;font-size:14px;max-width:32em";
  note.textContent = words.note;
  line.textContent = words.python;
  // The way home, over the cover: the page's own home button is under it
  // until the first scene is drawn, and nobody should have to wait a
  // minute for the simulator only to leave it.
  const home = document.createElement("a");
  home.href = english ? "en/" : "tr/";
  home.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" '
    + 'aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" '
    + 'stroke-linecap="round" stroke-linejoin="round" '
    + 'style="vertical-align:-3px;margin-right:6px">'
    + '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 9.5V20h5v-5.5h3V20h5V9.5"/>'
    + "</svg>";
  home.append(words.home);
  home.style.cssText = [
    "position:absolute", "top:16px", "right:16px", "padding:7px 14px",
    "border:1px solid rgba(244,244,242,0.45)", "border-radius:6px",
    "color:#f4f4f2", "text-decoration:none", "font-size:14px",
    "background:rgba(255,255,255,0.06)",
  ].join(";");
  cover.append(home, line, note);
  const show = () => document.body.append(cover);
  if (document.body) show(); else addEventListener("DOMContentLoaded", show);

  // A phone drops every download when its owner switches to another app
  // and freezes the page until they return, and a worker caught loading
  // then gives up. It is started again once the page is back in sight,
  // and the questions it never answered are put to the new one.
  const STARTS = 3;
  let starts = 0;
  let worker = null;
  let up = false;
  const waiting = new Map();
  let next = 1;
  // What the worker is answering and what waits behind it, oldest first.
  // It answers one question at a time, so the page can say which of its
  // background work is running and which is queued behind it.
  const queue = [];
  const tell = () => window.dispatchEvent(
    new CustomEvent("yerkon-queue", { detail: queue.map(entry => entry.path) }));

  // The cover stays until the page has its first real answer, not just
  // until Python is up: the first scene takes seconds of its own, and a
  // blank page with a grey box in it reads as broken.
  let answered = false;
  const uncover = () => {
    if (answered) return;
    answered = true;
    cover.remove();
  };

  // Both the worker's error and its own report of the failure arrive
  // for one failed load; one new start follows them.
  let restarting = false;

  function failed(detail) {
    if (restarting) return;
    if (up || starts >= STARTS) {
      line.textContent = words.failed + detail;
      return;
    }
    restarting = true;
    line.textContent = words.again;
    const again = () => {
      if (document.hidden || !restarting) return;
      document.removeEventListener("visibilitychange", again);
      start();
    };
    document.addEventListener("visibilitychange", again);
    // Out of sight it waits for the return; in sight it tries at once.
    setTimeout(again, 1500);
  }

  function start() {
    restarting = false;
    starts += 1;
    if (worker) worker.terminate();
    worker = new Worker("sim-worker.js?v=a9f83911d9", { type: "module" });
    // A worker that dies while loading says nothing on its own, and the
    // cover would promise a load that is never coming.
    worker.onerror = event => failed(event.message || "worker");
    worker.onmessage = event => {
      const message = event.data;
      if (message.stage) {
        if (message.stage === "failed") failed(message.detail);
        else {
          if (message.stage === "ready") up = true;
          line.textContent = words[message.stage] || message.stage;
        }
        return;
      }
      const settle = waiting.get(message.id);
      waiting.delete(message.id);
      const at = queue.findIndex(entry => entry.id === message.id);
      if (at >= 0) { queue.splice(at, 1); tell(); }
      if (settle) settle(message);
    };
    // Whatever was asked of a worker that never came up, in order.
    for (const entry of queue) {
      worker.postMessage({ id: entry.id, method: entry.method, path: entry.path,
                           body: entry.body });
    }
  }
  start();

  function ask(method, path, body) {
    return new Promise(settle => {
      const id = next++;
      waiting.set(id, settle);
      queue.push({ id, method, path, body: body || "" });
      tell();
      worker.postMessage({ id, method, path, body: body || "" });
    });
  }

  // The language the person arrived in, before the page asks anything:
  // the worker answers in order, so this is settled first.
  if (english) ask("POST", "/api/language", JSON.stringify({ language: "en" }));

  const network = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const url = typeof input === "string" ? input : input.url;
    const at = url.indexOf("/api/");
    if (at < 0) return network(input, init);
    const options = init || {};
    const path = url.slice(at);
    const reply = await ask((options.method || "GET").toUpperCase(),
                            path, options.body);
    if (!path.startsWith("/api/language")) uncover();
    // The photograph of a fetched site is the one answer that is not
    // text; it crosses from the worker as base64 (ADR-0086).
    const body = reply.encoding === "base64"
      ? Uint8Array.from(atob(reply.text), c => c.charCodeAt(0))
      : reply.text;
    return new Response(body, {
      status: reply.status,
      headers: { "Content-Type": reply.type },
    });
  };

  addEventListener("DOMContentLoaded", () => {
    // The way back is to the site's front page in the reader's language.
    const back = document.getElementById("back");
    if (back) back.setAttribute("href", english ? "en/" : "tr/");

    // The figures file is a link rather than a fetch, so it would go to
    // the network and find nothing. It is made here and handed over.
    const exported = document.getElementById("export");
    if (exported) exported.addEventListener("click", async event => {
      event.preventDefault();
      const reply = await ask("GET", "/api/figures.toml");
      const file = new Blob([reply.text], { type: "application/toml" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(file);
      link.download = "defaults.toml";
      link.click();
      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    });
  });
})();
