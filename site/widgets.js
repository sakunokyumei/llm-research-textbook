// Interactive demos. Each widget is a <div class="widget" data-widget="name">.
(() => {
  const h = (tag, attrs = {}, ...kids) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") el.className = v; else if (k.startsWith("on")) el.addEventListener(k.slice(2), v); else el.setAttribute(k, v);
    }
    for (const kid of kids) el.append(kid);
    return el;
  };
  const fmt = (x, d = 3) => Number(x).toFixed(d);
  const softmax = (z, T = 1) => {
    const s = z.map((v) => v / T); const m = Math.max(...s);
    const e = s.map((v) => Math.exp(v - m)); const sum = e.reduce((a, b) => a + b, 0);
    return e.map((v) => v / sum);
  };
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  const W = {};

  // ---- UTF-8 bytes of what you type
  W.utf8 = (root) => {
    const input = h("input", { type: "text", value: "猫はAIが好き🐈", "aria-label": "文字を入力" });
    const out = h("div", { class: "chips" });
    const sum = h("p", { class: "note" });
    const enc = new TextEncoder();
    const draw = () => {
      out.innerHTML = "";
      let bytes = 0; const chars = Array.from(input.value);
      for (const ch of chars) {
        const b = Array.from(enc.encode(ch)).map((x) => x.toString(16).toUpperCase().padStart(2, "0"));
        bytes += b.length;
        out.append(h("span", { class: "chip", title: b.length + "バイト" }, `${ch} → ${b.join(" ")}`));
      }
      sum.textContent = `文字数 ${chars.length} 文字 ／ UTF-8 で ${bytes} バイト。日本語1文字はたいてい3バイト、英数字は1バイト、絵文字は4バイト。`;
    };
    input.addEventListener("input", draw); draw();
    root.append(h("p", { class: "w-title" }, "文字 → バイト変換機（UTF-8）"), input, out, sum);
  };

  // ---- softmax with temperature (and optional top-k / top-p)
  W.softmax = (root) => {
    const full = root.dataset.mode === "full";
    const words = ["猫", "犬", "人間", "名前", "机"];
    const logits = [3.0, 1.6, 1.2, 0.4, -1.0];
    const T = h("input", { type: "range", min: "0.05", max: "3", step: "0.05", value: "1", "aria-label": "温度" });
    const tLabel = h("span");
    const K = h("input", { type: "range", min: "1", max: "5", step: "1", value: "5", "aria-label": "top-k" });
    const P = h("input", { type: "range", min: "0.1", max: "1", step: "0.05", value: "1", "aria-label": "top-p" });
    const kLabel = h("span"), pLabel = h("span");
    const bars = h("div", { class: "bars" });
    const result = h("p", { class: "note" });
    const editors = h("div", { class: "chips" });
    const inputs = logits.map((v, i) => {
      const el = h("input", { type: "number", step: "0.1", value: String(v), style: "width:5.2em", "aria-label": words[i] + "のロジット" });
      el.addEventListener("input", draw);
      editors.append(h("label", { class: "chip" }, words[i] + " ", el));
      return el;
    });
    function probs() {
      const z = inputs.map((el) => parseFloat(el.value) || 0);
      let p = softmax(z, parseFloat(T.value));
      if (full) {
        const order = p.map((v, i) => [v, i]).sort((a, b) => b[0] - a[0]);
        const keep = new Set(); let acc = 0;
        for (const [v, i] of order) {
          if (keep.size >= parseInt(K.value)) break;
          if (acc >= parseFloat(P.value) && keep.size > 0) break;
          keep.add(i); acc += v;
        }
        p = p.map((v, i) => (keep.has(i) ? v : 0));
        const s = p.reduce((a, b) => a + b, 0); p = p.map((v) => v / s);
      }
      return p;
    }
    function draw(hit = -1) {
      tLabel.textContent = ` 温度 T = ${fmt(T.value, 2)}`;
      kLabel.textContent = ` top-k = ${K.value}`; pLabel.textContent = ` top-p = ${fmt(P.value, 2)}`;
      const p = probs(); bars.innerHTML = "";
      p.forEach((v, i) => bars.append(h("div", { class: "bar-row" + (i === hit ? " hit" : "") }, h("span", {}, words[i]),
        h("span", { class: "b" }, h("span", { style: `width:${(v * 100).toFixed(1)}%` })), h("span", {}, (v * 100).toFixed(1) + "%"))));
    }
    const roll = () => {
      const p = probs(); let r = Math.random(), i = 0;
      while (i < p.length - 1 && r > p[i]) { r -= p[i]; i++; }
      result.textContent = `🎲 サイコロの結果：「吾輩は${words[i]}である」`; draw(i);
    };
    const many = () => {
      const p = probs(); const count = new Array(p.length).fill(0);
      for (let n = 0; n < 1000; n++) { let r = Math.random(), i = 0; while (i < p.length - 1 && r > p[i]) { r -= p[i]; i++; } count[i]++; }
      result.textContent = "1000回振った結果：" + words.map((w, i) => `${w} ${count[i]}回`).join("、");
    };
    [T, K, P].forEach((el) => el.addEventListener("input", () => draw()));
    root.append(h("p", { class: "w-title" }, "「吾輩は○○である」の○○を選ぶサイコロ"),
      h("p", { class: "note" }, "数字（ロジット）を書き換えたり、温度を動かしたりしてみよう。"), editors,
      h("label", {}, tLabel, T));
    if (full) root.append(h("label", {}, kLabel, K), h("label", {}, pLabel, P));
    root.append(bars, h("button", { type: "button", onclick: roll }, "サイコロを1回振る"),
      h("button", { type: "button", class: "ghost", onclick: many }, "1000回振る"), result);
    draw();
  };

  // ---- gradient descent on a 1-D loss
  W.gd = (root) => {
    const f = (w) => 0.5 * (w - 3) ** 2 + 0.6 * Math.sin(2.2 * w) + 1.2;
    const df = (w) => (w - 3) + 1.32 * Math.cos(2.2 * w);
    let w = -1.5, hist = [];
    const canvas = h("canvas", { width: "640", height: "300", "aria-label": "損失の坂とボール" });
    const lr = h("input", { type: "range", min: "0.01", max: "2.2", step: "0.01", value: "0.3", "aria-label": "学習率" });
    const lrLabel = h("span"); const info = h("p", { class: "note mono" });
    const x0 = -2.5, x1 = 8;
    function draw() {
      const ctx = canvas.getContext("2d"), Wd = canvas.width, Ht = canvas.height;
      const ink = css("--ink") || "#222", acc = css("--accent") || "#c50", tip = css("--tip") || "#276";
      ctx.clearRect(0, 0, Wd, Ht);
      const X = (x) => (x - x0) / (x1 - x0) * Wd, Y = (y) => Ht - 20 - y / 14 * (Ht - 40);
      ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.beginPath();
      for (let i = 0; i <= 300; i++) { const x = x0 + (x1 - x0) * i / 300; i ? ctx.lineTo(X(x), Y(f(x))) : ctx.moveTo(X(x), Y(f(x))); }
      ctx.stroke();
      ctx.strokeStyle = tip; ctx.lineWidth = 1.5; ctx.beginPath();
      hist.forEach((v, i) => (i ? ctx.lineTo(X(v), Y(f(v))) : ctx.moveTo(X(v), Y(f(v))))); ctx.stroke();
      ctx.fillStyle = acc; ctx.beginPath(); ctx.arc(X(w), Y(f(w)), 9, 0, Math.PI * 2); ctx.fill();
      const g = df(w); ctx.strokeStyle = acc; ctx.setLineDash([5, 4]); ctx.beginPath();
      ctx.moveTo(X(w - 0.8), Y(f(w) - 0.8 * g)); ctx.lineTo(X(w + 0.8), Y(f(w) + 0.8 * g)); ctx.stroke(); ctx.setLineDash([]);
      lrLabel.textContent = ` 学習率 = ${fmt(lr.value, 2)}`;
      info.textContent = `w = ${fmt(w)}   損失 = ${fmt(f(w))}   傾き(勾配) = ${fmt(g)}   ステップ数 = ${Math.max(0, hist.length - 1)}`;
    }
    const step = () => { if (!hist.length) hist.push(w); w = w - parseFloat(lr.value) * df(w); w = Math.max(-50, Math.min(50, w)); hist.push(w); draw(); };
    let timer = null;
    const run = () => { if (timer) { clearInterval(timer); timer = null; return; } let n = 0; timer = setInterval(() => { step(); if (++n >= 30) { clearInterval(timer); timer = null; } }, 120); };
    const reset = () => { w = -1.5 + Math.random() * 9; hist = []; draw(); };
    lr.addEventListener("input", draw);
    root.append(h("p", { class: "w-title" }, "ボールを坂の一番下へ：勾配降下法"), canvas, h("label", {}, lrLabel, lr),
      h("button", { type: "button", onclick: step }, "1歩進む"), h("button", { type: "button", onclick: run }, "30歩まとめて"),
      h("button", { type: "button", class: "ghost", onclick: reset }, "別の場所から"), info,
      h("p", { class: "note" }, "点線は「いまの場所の傾き」。傾きと逆向きに、学習率ぶん進みます。学習率を2近くにすると…？"));
    draw();
    new MutationObserver(draw).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  };

  // ---- causal self-attention on a toy sentence
  W.attention = (root) => {
    const toks = ["吾輩", "は", "猫", "で", "ある"];
    const q = [[1, 0, 0.2], [0.1, 1, 0], [1.2, 0.1, 0.4], [0, 0.8, 0.3], [0.9, 0.2, 1]];
    const k = [[1.1, 0, 0.1], [0, 1, 0], [1, 0.2, 0.5], [0.1, 0.9, 0], [0.5, 0.3, 1]];
    const mask = h("input", { type: "checkbox", checked: "" });
    const scale = h("input", { type: "range", min: "0.2", max: "5", step: "0.1", value: "1.7", "aria-label": "鋭さ" });
    const sLabel = h("span"); const table = h("table", { class: "att" }); const note = h("p", { class: "note" });
    function draw() {
      sLabel.textContent = ` 鋭さ（スコアに掛ける数）= ${fmt(scale.value, 1)}`;
      table.innerHTML = "";
      const head = h("tr", {}, h("th", {}, "注目する側＼される側"));
      toks.forEach((t) => head.append(h("th", {}, t))); table.append(head);
      toks.forEach((t, i) => {
        const scores = toks.map((_, j) => q[i].reduce((s, v, d) => s + v * k[j][d], 0) * parseFloat(scale.value));
        const masked = scores.map((s, j) => (mask.checked && j > i ? -Infinity : s));
        const p = softmax(masked.map((s) => (s === -Infinity ? -1e9 : s)));
        const row = h("tr", {}, h("th", {}, t));
        p.forEach((v, j) => {
          const hidden = mask.checked && j > i;
          row.append(h("td", { style: hidden ? "color:var(--muted)" : `background:color-mix(in srgb, var(--accent) ${Math.round(v * 90)}%, transparent)` }, hidden ? "×" : fmt(v, 2)));
        });
        table.append(row);
      });
      note.textContent = mask.checked ? "×は「未来の単語」。カンニング防止のマスクで見えないようにしてあります。各行の合計はいつも1。" : "マスクなし：未来の単語まで見えてしまう状態。テストで答えを見ながら解くのと同じです。";
    }
    [mask, scale].forEach((el) => el.addEventListener("input", draw));
    root.append(h("p", { class: "w-title" }, "Attentionの重み（各行が「誰にどれだけ注目するか」）"),
      h("label", {}, mask, " 未来を隠すマスク（causal mask）"), h("label", {}, sLabel, scale), table, note);
    draw();
  };

  // ---- byte-pair encoding, one merge at a time
  W.bpe = (root) => {
    const input = h("input", { type: "text", value: "あいうあいうあいえあいえ", "aria-label": "BPEにかける文字列" });
    const chips = h("div", { class: "chips" }); const rules = h("ol", { class: "mono" }); const note = h("p", { class: "note" });
    let toks = [], merges = [];
    const reset = () => { toks = Array.from(input.value); merges = []; draw(); };
    function draw(newTok) {
      chips.innerHTML = ""; toks.forEach((t) => chips.append(h("span", { class: "chip" + (t === newTok ? " new" : "") }, t)));
      rules.innerHTML = ""; merges.forEach((m) => rules.append(h("li", {}, `「${m[0]}」+「${m[1]}」→「${m[0] + m[1]}」`)));
      note.textContent = `トークン数 ${toks.length}（最初は ${Array.from(input.value).length}）／ 覚えた合体ルール ${merges.length} 個 ／ 語彙の種類 ${new Set(toks).size}`;
    }
    const step = () => {
      const count = new Map();
      for (let i = 0; i + 1 < toks.length; i++) { const key = toks[i] + "\u0000" + toks[i + 1]; count.set(key, (count.get(key) || 0) + 1); }
      let best = null, n = 1;
      for (const [key, c] of count) if (c > n) { best = key; n = c; }
      if (!best) { note.textContent = "もう2回以上出てくるペアがありません。おしまい！"; return; }
      const [a, b] = best.split("\u0000"); const out = [];
      for (let i = 0; i < toks.length; i++) { if (i + 1 < toks.length && toks[i] === a && toks[i + 1] === b) { out.push(a + b); i++; } else out.push(toks[i]); }
      toks = out; merges.push([a, b]); draw(a + b);
    };
    input.addEventListener("input", reset);
    root.append(h("p", { class: "w-title" }, "BPE：よく出る隣どうしを合体させる"), input, chips,
      h("button", { type: "button", onclick: step }, "1回合体"), h("button", { type: "button", class: "ghost", onclick: reset }, "最初から"), note, rules);
    reset();
  };

  // ---- the tiny Soseki GPT running in this browser
  W.minigpt = (root) => {
    const seed = h("input", { type: "text", value: "吾輩は", "aria-label": "書き出し" });
    const temp = h("input", { type: "range", min: "0.2", max: "1.5", step: "0.05", value: "0.8", "aria-label": "温度" });
    const tl = h("span"); const out = h("div", { class: "gen", "aria-live": "polite" }); const note = h("p", { class: "note" });
    const btn = h("button", { type: "button" }, "続きを書かせる");
    root.append(h("p", { class: "w-title" }, root.dataset.title || "このページで動くミニ漱石GPT"), h("label", {}, "書き出し", seed),
      h("label", {}, tl, temp), btn, out, note);
    const showT = () => (tl.textContent = ` 温度 = ${fmt(temp.value, 2)}`); temp.addEventListener("input", showT); showT();
    let model = null;
    note.textContent = "モデルを読み込み中…";
    import("./minigpt.js").then((m) => m.load("model/soseki-gpt.json")).then((m) => {
      model = m; note.textContent = `パラメータ ${m.nParams.toLocaleString()} 個・語彙 ${m.vocab.length} 文字の小さなGPT（第13章のコードでCPU学習→第24章の方法でブラウザへ）。`;
    }).catch(() => { note.textContent = "モデルを読み込めませんでした（オフライン表示では動きません）。"; });
    btn.addEventListener("click", async () => {
      if (!model) return;
      btn.disabled = true; out.innerHTML = "";
      const s = h("span", { class: "seed" }, seed.value); const rest = h("span"); out.append(s, rest);
      await model.generate(seed.value, 120, parseFloat(temp.value), (ch) => { rest.textContent += ch; });
      btn.disabled = false;
    });
  };

  document.querySelectorAll(".widget[data-widget]").forEach((el) => {
    const make = W[el.dataset.widget];
    if (make) { el.innerHTML = ""; make(el); }
  });
})();
