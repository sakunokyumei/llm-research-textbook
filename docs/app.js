// つくってわかるLLM — small helpers. Everything is stored only in this browser.
(() => {
  const KEY = "tsukuru-llm";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  // ---- Accessible storage error notification banner
  let storageBannerShown = false;
  function notifyStorageError(reason) {
    if (storageBannerShown) return;
    storageBannerShown = true;
    const host = $("#main") || document.body;
    if (!host) return;
    const existing = $("#storage-error-banner");
    if (existing) return;
    const banner = document.createElement("div");
    banner.id = "storage-error-banner";
    banner.className = "storage-alert";
    banner.setAttribute("role", "alert");

    const text = document.createElement("p");
    text.textContent =
      (reason || "ブラウザの保存領域（localStorage）に書き込めませんでした。") +
      " プライベートブラウジングや容量上限のため、この画面を閉じると学習履歴が失われる可能性があります。必要に応じて「学習状況・復習」ページのJSON保存機能をご利用ください。";

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "storage-alert-close";
    closeBtn.setAttribute("aria-label", "通知を閉じる");
    closeBtn.textContent = "閉じる";
    closeBtn.addEventListener("click", () => banner.remove());

    banner.append(text, closeBtn);
    host.prepend(banner);
  }
  window.TsukuruUI = Object.assign(window.TsukuruUI || {}, { notifyStorageError });

  const store = {
    get(k, fallback) {
      try {
        const v = localStorage.getItem(KEY + ":" + k);
        return v === null ? fallback : JSON.parse(v);
      } catch (e) {
        return fallback;
      }
    },
    set(k, v) {
      try {
        localStorage.setItem(KEY + ":" + k, JSON.stringify(v));
        return true;
      } catch (e) {
        notifyStorageError("学習状況の保存に失敗しました（ブラウザのストレージ制限またはプライベートモード）。");
        return false;
      }
    },
  };

  // ---- Theme toggle
  const themeBtn = $("#theme");
  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const now = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      const next = now === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      try {
        localStorage.setItem("tsukuru-llm-theme", next);
      } catch (e) {
        notifyStorageError("表示テーマの設定を保存できませんでした。");
      }
    });
  }

  // ---- Accessible mobile menu (focus management, inert, Escape, outside click)
  const menu = $("#menu");
  const sidebar = $("#sidebar");
  const mobileMQ = matchMedia("(max-width: 900px)");
  let backdrop = null;

  function syncSidebarInert() {
    if (!sidebar) return;
    const isMobile = mobileMQ.matches;
    const isOpen = document.body.classList.contains("menu-open");
    const shouldHide = isMobile && !isOpen;
    if ("inert" in sidebar) {
      sidebar.inert = shouldHide;
    }
    if (shouldHide) sidebar.setAttribute("aria-hidden", "true");
    else sidebar.removeAttribute("aria-hidden");
  }

  function closeMenu({ restoreFocus = false } = {}) {
    if (!document.body.classList.contains("menu-open")) return;
    document.body.classList.remove("menu-open");
    if (menu) {
      menu.setAttribute("aria-expanded", "false");
      menu.setAttribute("aria-label", "目次を開く");
    }
    if (backdrop) backdrop.hidden = true;
    syncSidebarInert();
    if (restoreFocus && menu) menu.focus();
  }

  function openMenu() {
    document.body.classList.add("menu-open");
    if (menu) {
      menu.setAttribute("aria-expanded", "true");
      menu.setAttribute("aria-label", "目次を閉じる");
    }
    if (!backdrop) {
      backdrop = document.createElement("div");
      backdrop.className = "menu-backdrop";
      backdrop.setAttribute("aria-hidden", "true");
      backdrop.addEventListener("click", () => closeMenu({ restoreFocus: true }));
      document.body.appendChild(backdrop);
    }
    backdrop.hidden = false;
    syncSidebarInert();
    if (sidebar) {
      const firstFocusable = sidebar.querySelector("input, button, a[href], summary, [tabindex]:not([tabindex='-1'])");
      if (firstFocusable) firstFocusable.focus();
    }
  }

  if (menu) {
    menu.addEventListener("click", () => {
      if (document.body.classList.contains("menu-open")) closeMenu({ restoreFocus: false });
      else openMenu();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (document.body.classList.contains("menu-open")) {
        closeMenu({ restoreFocus: true });
      }
      // Also dismiss hovered/focused glossary term tooltips (WCAG 1.4.13)
      $$(".term").forEach((t) => t.classList.add("tip-dismissed"));
    }
  });
  if (typeof mobileMQ.addEventListener === "function") {
    mobileMQ.addEventListener("change", () => {
      if (!mobileMQ.matches) closeMenu({ restoreFocus: false });
      syncSidebarInert();
    });
  }
  syncSidebarInert();

  // ---- Glossary tooltip WCAG 1.4.13 helpers (viewport-safe alignment & Esc re-arm)
  $$(".term[data-tip]").forEach((t) => {
    const arm = () => {
      t.classList.remove("tip-dismissed");
      const rect = t.getBoundingClientRect();
      t.classList.toggle("tip-right", rect.left + 320 > window.innerWidth - 12);
    };
    t.addEventListener("mouseenter", arm);
    t.addEventListener("focus", arm);
    t.addEventListener("mouseleave", () => t.classList.remove("tip-dismissed"));
    t.addEventListener("blur", () => t.classList.remove("tip-dismissed"));
  });

  // ---- Copy buttons
  $$(".copy").forEach((btn) => btn.addEventListener("click", async () => {
    const code = btn.closest(".codeblock").querySelector("code").innerText;
    try { await navigator.clipboard.writeText(code); } catch (e) {
      const ta = document.createElement("textarea"); ta.value = code; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); } catch (e2) {} ta.remove();
    }
    btn.textContent = "コピーした！"; btn.classList.add("copied");
    setTimeout(() => { btn.textContent = "コピー"; btn.classList.remove("copied"); }, 1600);
  }));

  // ---- Chapter progress (synced with study.js)
  let done = new Set(store.get("done", []));
  const total = $$(".nav-part a[data-slug]").length;
  function paint() {
    $$("a[data-slug]").forEach((a) => a.classList.toggle("done", done.has(a.dataset.slug)));
    const box = $("[data-progress]");
    if (box && total) {
      const n = $$(".nav-part a[data-slug]").filter((a) => done.has(a.dataset.slug)).length;
      box.hidden = n === 0;
      $(".bar span", box).style.width = (100 * n / total) + "%";
      $("small", box).textContent = `読了 ${n} / ${total} 章` + (n === total ? " ── 全章読了！復習で確認しよう" : "");
    }
    $$("[data-done]").forEach((b) => {
      const on = done.has(b.dataset.done);
      b.classList.toggle("is-done", on);
      b.setAttribute("aria-pressed", String(on));
      b.textContent = on ? "読了チェック済み ✓（もう一度押すと取り消し）" : "この章の説明を読み終えた！";
    });
  }
  $$("[data-done]").forEach((b) => b.addEventListener("click", () => {
    const s = b.dataset.done;
    const isNowDone = !done.has(s);
    if (isNowDone) done.add(s); else done.delete(s);
    store.set("done", Array.from(done));
    paint();
    window.dispatchEvent(new CustomEvent("tsukuru:done-toggle", { detail: { slug: s, done: isNowDone } }));
  }));
  paint();

  const page = document.body.dataset.page;
  if (page && page !== "index") store.set("last", { page, title: document.title, at: Date.now() });
  const resume = $("[data-resume]");
  const last = store.get("last", null);
  if (resume && last && typeof last.page === "string" && /^[a-z0-9-]+$/i.test(last.page)) {
    resume.hidden = false;
    const a = $("a", resume);
    a.href = last.page + ".html";
    a.textContent = String(last.title || last.page).split(" | ")[0];
  }

  // ---- Checklists
  let checks = store.get("checks", {});
  if (!checks || typeof checks !== "object" || Array.isArray(checks)) checks = {};
  $$("input[data-check]").forEach((c) => {
    c.checked = !!checks[c.dataset.check];
    c.addEventListener("change", () => {
      checks[c.dataset.check] = c.checked;
      store.set("checks", checks);
    });
  });

  // Listen for full reset / import sync from study.js
  window.addEventListener("tsukuru:reset-all", () => {
    done = new Set(store.get("done", []));
    checks = store.get("checks", {});
    if (!checks || typeof checks !== "object" || Array.isArray(checks)) checks = {};
    $$("input[data-check]").forEach((c) => { c.checked = !!checks[c.dataset.check]; });
    if (resume) resume.hidden = true;
    paint();
  });

  // ---- On-page TOC highlight
  const tocLinks = $$(".toc a[href^='#s']");
  if (tocLinks.length && "IntersectionObserver" in window) {
    const map = new Map(tocLinks.map((a) => [a.getAttribute("href").slice(1), a]));
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) {
          tocLinks.forEach((a) => a.classList.remove("active"));
          const a = map.get(en.target.id);
          if (a) a.classList.add("active");
        }
      });
    }, { rootMargin: "-70px 0px -70% 0px" });
    $$("main h2[id]").forEach((h) => io.observe(h));
  }

  // ---- Upgraded Full-Text & Section-Level Search (NFKC + Kana + Multi-word AND + Snippets)
  const input = $("#search"), results = $("#results");
  let records = null;
  let searchSeq = 0;

  function toHiragana(str) {
    return str.replace(/[\u30a1-\u30f6]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0x60));
  }

  function normText(s) {
    return toHiragana(String(s || "").normalize("NFKC").toLowerCase());
  }

  function prepareRecord(r) {
    const titleNorm = normText(r.title);
    const labelNorm = normText(r.label);
    const readingsRaw = Array.isArray(r.readings) ? r.readings.join(" ") : String(r.readings || "");
    const readingsNorm = normText(readingsRaw);
    const textNorm = normText(r.text);

    // Support both new `sections: [{ id, head, text }]` and legacy `heads: [...]`
    const sections = Array.isArray(r.sections) && r.sections.length
      ? r.sections.map((sec) => ({
          id: sec.id || "",
          head: String(sec.head || ""),
          text: String(sec.text || ""),
          headNorm: normText(sec.head),
          textNorm: normText(sec.text),
        }))
      : (Array.isArray(r.heads) ? r.heads.map((h) => ({ id: "", head: String(h), text: "", headNorm: normText(h), textNorm: "" })) : []);

    const allHeadNorm = sections.map((s) => s.headNorm).join(" ");
    const combinedNorm = `${titleNorm} ${labelNorm} ${readingsNorm} ${allHeadNorm} ${textNorm}`;
    return { raw: r, titleNorm, labelNorm, readingsNorm, textNorm, sections, combinedNorm };
  }

  async function loadSearch() {
    if (records) return records;
    try {
      const res = await fetch("search.json");
      if (!res.ok) throw new Error("HTTP " + res.status);
      const raw = await res.json();
      records = Array.isArray(raw) ? raw.map(prepareRecord) : [];
    } catch (e) {
      records = [];
    }
    return records;
  }

  function matchRecord(rec, terms, fullPhrase) {
    // Multi-word AND matching across combined normalized fields
    for (const t of terms) {
      if (!rec.combinedNorm.includes(t)) return null;
    }
    let score = 0;
    if (rec.titleNorm.includes(fullPhrase)) score += 30;
    if (rec.readingsNorm && rec.readingsNorm.includes(fullPhrase)) score += 20;

    let bestSec = null;
    let bestSecScore = -1;

    for (const t of terms) {
      if (rec.titleNorm.includes(t)) score += 12;
      if (rec.readingsNorm && rec.readingsNorm.includes(t)) score += 10;
      if (rec.textNorm.includes(t)) score += 2;
    }

    for (const sec of rec.sections) {
      let sScore = 0;
      let secHits = 0;
      for (const t of terms) {
        if (sec.headNorm.includes(t)) { sScore += 10; secHits++; }
        else if (sec.textNorm.includes(t)) { sScore += 3; secHits++; }
      }
      if (sec.headNorm.includes(fullPhrase)) sScore += 8;
      if (secHits > 0) {
        score += Math.min(sScore, 20);
        if (sScore > bestSecScore) {
          bestSecScore = sScore;
          bestSec = sec;
        }
      }
    }

    return { score, rec, bestSec };
  }

  function buildSnippetEl(sourceText, terms) {
    const raw = String(sourceText || "").replace(/\s+/g, " ").trim();
    if (!raw) return null;
    const norm = normText(raw);
    let hitPos = -1;
    let hitTerm = terms[0] || "";
    for (const t of terms) {
      const idx = norm.indexOf(t);
      if (idx >= 0 && (hitPos === -1 || idx < hitPos)) {
        hitPos = idx;
        hitTerm = t;
      }
    }
    if (hitPos < 0) return null;

    // Slice around hitPos safely (note: NFKC length can differ slightly on rare chars, clamp defensively)
    const start = Math.max(0, hitPos - 24);
    const end = Math.min(raw.length, hitPos + Math.max(hitTerm.length, 8) + 46);
    const chunk = (start > 0 ? "…" : "") + raw.slice(start, end) + (end < raw.length ? "…" : "");

    const p = document.createElement("span");
    p.className = "res-snip";

    // Highlight first match inside chunk safely with DOM nodes (never innerHTML)
    const chunkNorm = normText(chunk);
    const localIdx = hitTerm ? chunkNorm.indexOf(hitTerm) : -1;
    if (localIdx >= 0 && localIdx + hitTerm.length <= chunk.length) {
      p.append(document.createTextNode(chunk.slice(0, localIdx)));
      const mark = document.createElement("mark");
      mark.textContent = chunk.slice(localIdx, localIdx + hitTerm.length);
      p.append(mark);
      p.append(document.createTextNode(chunk.slice(localIdx + hitTerm.length)));
    } else {
      p.textContent = chunk;
    }
    return p;
  }

  if (input && results) {
    input.addEventListener("input", async () => {
      const seq = ++searchSeq;
      const rawQ = input.value.trim();
      const normQ = normText(rawQ);
      const terms = normQ.split(/[\s\u3000]+/).filter(Boolean);
      if (!terms.length) {
        results.textContent = "";
        return;
      }
      const list = (await loadSearch())
        .map((rec) => matchRecord(rec, terms, normQ))
        .filter(Boolean)
        .sort((a, b) => b.score - a.score)
        .slice(0, 12);

      if (seq !== searchSeq) return; // stale async result

      results.textContent = "";
      if (!list.length) {
        const empty = document.createElement("p");
        empty.textContent = "見つかりませんでした。別の言い方や短いキーワードで試してみて！";
        results.appendChild(empty);
        return;
      }

      for (const { rec, bestSec } of list) {
        const r = rec.raw;
        const a = document.createElement("a");
        const baseHref = r.slug.includes(".html") ? r.slug : r.slug + ".html";
        a.href = (!baseHref.includes("#") && bestSec && bestSec.id) ? `${baseHref}#${bestSec.id}` : baseHref;

        const sm = document.createElement("small");
        sm.textContent = r.label + (bestSec && bestSec.head ? " › " + bestSec.head : "");
        const titleEl = document.createElement("span");
        titleEl.className = "res-title";
        titleEl.textContent = r.title;
        a.append(sm, titleEl);

        const snipSource = (bestSec && bestSec.text) ? bestSec.text : r.text;
        const snipEl = buildSnippetEl(snipSource, terms);
        if (snipEl) a.append(snipEl);

        results.appendChild(a);
      }
    });
  }
})();
