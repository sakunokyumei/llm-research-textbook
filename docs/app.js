// つくってわかるLLM — small helpers. Everything is stored only in this browser.
(() => {
  const KEY = "tsukuru-llm";
  const store = {
    get(k, fallback) { try { const v = localStorage.getItem(KEY + ":" + k); return v === null ? fallback : JSON.parse(v); } catch (e) { return fallback; } },
    set(k, v) { try { localStorage.setItem(KEY + ":" + k, JSON.stringify(v)); } catch (e) { /* private mode etc. */ } },
  };
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  // theme
  const themeBtn = $("#theme");
  if (themeBtn) themeBtn.addEventListener("click", () => {
    const now = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = now === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("tsukuru-llm-theme", next); } catch (e) {}
  });

  // mobile menu
  const menu = $("#menu");
  if (menu) menu.addEventListener("click", () => {
    const open = document.body.classList.toggle("menu-open");
    menu.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") document.body.classList.remove("menu-open"); });

  // copy buttons
  $$(".copy").forEach((btn) => btn.addEventListener("click", async () => {
    const code = btn.closest(".codeblock").querySelector("code").innerText;
    try { await navigator.clipboard.writeText(code); } catch (e) {
      const ta = document.createElement("textarea"); ta.value = code; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); } catch (e2) {} ta.remove();
    }
    btn.textContent = "コピーした！"; btn.classList.add("copied");
    setTimeout(() => { btn.textContent = "コピー"; btn.classList.remove("copied"); }, 1600);
  }));

  // chapter progress
  const done = new Set(store.get("done", []));
  const total = $$(".nav-part a[data-slug]").length;
  function paint() {
    $$("a[data-slug]").forEach((a) => a.classList.toggle("done", done.has(a.dataset.slug)));
    const box = $("[data-progress]");
    if (box && total) {
      const n = $$(".nav-part a[data-slug]").filter((a) => done.has(a.dataset.slug)).length;
      box.hidden = n === 0;
      $(".bar span", box).style.width = (100 * n / total) + "%";
      $("small", box).textContent = `クリア ${n} / ${total} 章` + (n === total ? " ── 卒業おめでとう！🥁" : "");
    }
    $$("[data-done]").forEach((b) => {
      const on = done.has(b.dataset.done);
      b.classList.toggle("is-done", on);
      b.textContent = on ? "クリア済み ✓（もう一度押すと取り消し）" : "この章をクリアした！";
    });
  }
  $$("[data-done]").forEach((b) => b.addEventListener("click", () => {
    const s = b.dataset.done;
    if (done.has(s)) done.delete(s); else done.add(s);
    store.set("done", Array.from(done)); paint();
  }));
  paint();
  const page = document.body.dataset.page;
  if (page && page !== "index") store.set("last", { page, title: document.title, at: Date.now() });
  const resume = $("[data-resume]");
  const last = store.get("last", null);
  if (resume && last && last.page) {
    resume.hidden = false;
    const a = $("a", resume); a.href = last.page + ".html"; a.textContent = last.title.split(" | ")[0];
  }

  // checklists
  const checks = store.get("checks", {});
  $$("input[data-check]").forEach((c) => {
    c.checked = !!checks[c.dataset.check];
    c.addEventListener("change", () => { checks[c.dataset.check] = c.checked; store.set("checks", checks); });
  });

  // on-page toc highlight
  const tocLinks = $$(".toc a[href^='#s']");
  if (tocLinks.length && "IntersectionObserver" in window) {
    const map = new Map(tocLinks.map((a) => [a.getAttribute("href").slice(1), a]));
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { tocLinks.forEach((a) => a.classList.remove("active")); const a = map.get(en.target.id); if (a) a.classList.add("active"); } });
    }, { rootMargin: "-70px 0px -70% 0px" });
    $$("main h2[id]").forEach((h) => io.observe(h));
  }

  // search
  const input = $("#search"), results = $("#results");
  let records = null;
  async function load() {
    if (records) return records;
    try { records = await (await fetch("search.json")).json(); } catch (e) { records = []; }
    return records;
  }
  function score(r, q) {
    let s = 0;
    if (r.title.toLowerCase().includes(q)) s += 10;
    if (r.heads.some((h) => h.toLowerCase().includes(q))) s += 5;
    if (r.text.toLowerCase().includes(q)) s += 1;
    return s;
  }
  if (input) input.addEventListener("input", async () => {
    const q = input.value.trim().toLowerCase();
    if (!q) { results.innerHTML = ""; return; }
    const list = (await load()).map((r) => [score(r, q), r]).filter((x) => x[0] > 0).sort((a, b) => b[0] - a[0]).slice(0, 12);
    results.innerHTML = list.length ? "" : "<p>見つかりませんでした。別の言い方で試してみて！</p>";
    for (const [, r] of list) {
      const a = document.createElement("a");
      a.href = r.slug.includes(".html") ? r.slug : r.slug + ".html";
      const head = r.heads.find((h) => h.toLowerCase().includes(q));
      a.innerHTML = `<small></small><span></span>`;
      a.querySelector("small").textContent = r.label + (head ? " › " + head : "");
      a.querySelector("span").textContent = r.title;
      results.appendChild(a);
    }
  });
})();
