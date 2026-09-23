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
  const english = new URLSearchParams(location.search).get("dil") === "en";
  const words = english ? {
    python: "Loading Python in your browser…",
    numpy: "Loading numpy…",
    package: "Loading the YERKON model…",
    ready: "",
    failed: "The simulator could not start in this browser: ",
    note: "Everything runs on this computer. The first load takes a while; after that the browser keeps it.",
  } : {
    python: "Python tarayıcınızda yükleniyor…",
    numpy: "numpy yükleniyor…",
    package: "YERKON modeli yükleniyor…",
    ready: "",
    failed: "Simülatör bu tarayıcıda başlatılamadı: ",
    note: "Her şey bu bilgisayarda çalışıyor. İlk açılış biraz sürer; sonra tarayıcı saklar.",
  };

  const cover = document.createElement("div");
  cover.id = "booting";
  cover.setAttribute("role", "status");
  cover.style.cssText = [
    "position:fixed", "inset:0", "z-index:1000", "display:flex",
    "flex-direction:column", "align-items:center", "justify-content:center",
    "gap:12px", "background:rgba(20,24,28,0.92)", "color:#f4f4f2",
    "font:16px/1.5 system-ui,sans-serif", "text-align:center", "padding:24px",
  ].join(";");
  const line = document.createElement("div");
  const note = document.createElement("div");
  note.style.cssText = "opacity:0.75;font-size:14px;max-width:32em";
  note.textContent = words.note;
  line.textContent = words.python;
  cover.append(line, note);
  const show = () => document.body.append(cover);
  if (document.body) show(); else addEventListener("DOMContentLoaded", show);

  const worker = new Worker("sim-worker.js", { type: "module" });
  // A worker that dies while loading says nothing on its own, and the
  // cover would promise a load that is never coming.
  worker.onerror = event => {
    line.textContent = words.failed + (event.message || "worker");
  };
  const waiting = new Map();
  let next = 1;

  worker.onmessage = event => {
    const message = event.data;
    if (message.stage) {
      if (message.stage === "ready") cover.remove();
      else if (message.stage === "failed") {
        line.textContent = words.failed + message.detail;
      } else line.textContent = words[message.stage] || message.stage;
      return;
    }
    const settle = waiting.get(message.id);
    waiting.delete(message.id);
    if (settle) settle(message);
  };

  function ask(method, path, body) {
    return new Promise(settle => {
      const id = next++;
      waiting.set(id, settle);
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
    const reply = await ask((options.method || "GET").toUpperCase(),
                            url.slice(at), options.body);
    return new Response(reply.text, {
      status: reply.status,
      headers: { "Content-Type": reply.type },
    });
  };

  addEventListener("DOMContentLoaded", () => {
    // The way back is to the site's front page in the reader's language.
    const back = document.getElementById("back");
    if (back) back.setAttribute("href", english ? "en/index.html" : "index.html");

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
