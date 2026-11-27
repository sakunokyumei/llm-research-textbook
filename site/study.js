// つくってわかるLLM — Interactive Exercises, Spaced Repetition, 7-State Mastery & Course Selector.
// All learning history stays strictly inside this browser's localStorage.
(() => {
  const LEGACY_KEY = "tsukuru-llm";
  const STATE_KEY = "tsukuru-llm:study_v2";
  const COURSE_KEY = "tsukuru-llm-course";
  const DAY_MS = 24 * 60 * 60 * 1000;
  const INTERVALS = [1, 3, 7, 14, 30]; // Initial default intervals in days (transparent heuristic)

  const STAGES = {
    unstarted: { label: "未学習", rank: 0, cls: "st-unstarted" },
    read: { label: "説明を読んだ", rank: 1, cls: "st-read" },
    basic_done: { label: "基礎問題を解いた", rank: 2, cls: "st-basic" },
    applied_done: { label: "応用問題を解いた", rank: 3, cls: "st-applied" },
    impl_done: { label: "自力実装を完了した", rank: 4, cls: "st-impl" },
    needs_review: { label: "復習が必要", rank: 5, cls: "st-review-due" },
    reviewed: { label: "復習で再確認できた", rank: 6, cls: "st-reviewed" },
  };

  const LEVEL_LABELS = {
    1: "Lv.1 確認",
    2: "Lv.2 理解",
    3: "Lv.3 応用",
    4: "Lv.4 実装",
    5: "Lv.5 発展",
  };

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  function escHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function safeGet(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch (e) {
      return fallback;
    }
  }

  function safeSet(key, val) {
    try {
      localStorage.setItem(key, JSON.stringify(val));
      return true;
    } catch (e) {
      return false;
    }
  }

  function loadLegacyDone() {
    const arr = safeGet(LEGACY_KEY + ":done", []);
    return new Set(Array.isArray(arr) ? arr : []);
  }

  function loadState() {
    const s = safeGet(STATE_KEY, null);
    if (s && typeof s === "object" && s.version === 2) {
      s.readChapters = s.readChapters || {};
      s.exercises = s.exercises || {};
      return s;
    }
    return { version: 2, readChapters: {}, exercises: {} };
  }

  function saveState(state) {
    return safeSet(STATE_KEY, state);
  }

  // ---- Course mode (thorough vs standard)
  function getCourse() {
    try {
      const v = localStorage.getItem(COURSE_KEY);
      return v === "standard" ? "standard" : "thorough";
    } catch (e) {
      return "thorough";
    }
  }

  let _syncingCourse = false;
  function applyCourse(course, forceResetToggles = false) {
    const c = course === "standard" ? "standard" : "thorough";
    document.documentElement.dataset.course = c;
    try { localStorage.setItem(COURSE_KEY, c); } catch (e) {}
    $$("[data-set-course]").forEach((btn) => {
      const active = btn.dataset.setCourse === c;
      btn.setAttribute("aria-pressed", String(active));
      btn.classList.toggle("active", active);
    });
    // Adjust scaffold details boxes
    _syncingCourse = true;
    $$("details.scaffold").forEach((el) => {
      if (forceResetToggles) delete el.dataset.userToggled;
      if (!el.dataset.userToggled) {
        el.open = (c === "thorough");
      }
    });
    setTimeout(() => { _syncingCourse = false; }, 0);
    // Adjust optional thorough exercises
    $$(".exercise[data-course='thorough']").forEach((el) => {
      el.classList.toggle("ex-optional-in-standard", c === "standard");
    });
  }

  // ---- Input normalization & auto-grading
  function normalizeNumberString(raw, allowPercent) {
    let s = String(raw ?? "").trim();
    s = s.replace(/[０-９]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0xFEE0));
    s = s.replace(/[．。]/g, ".").replace(/[－−ー―]/g, "-").replace(/[＋]/g, "+").replace(/[,，\s]/g, "");
    if (allowPercent && s.endsWith("%")) {
      s = s.slice(0, -1);
    }
    return s;
  }

  function normalizeTextOutput(raw) {
    return String(raw ?? "")
      .replace(/\r\n/g, "\n")
      .trim()
      .replace(/[ \t]+\n/g, "\n")
      .replace(/\n[ \t]+/g, "\n");
  }

  function gradeVariant(ex, variant, userInput) {
    const type = ex.type;
    if (type === "choice" || (type === "predict" && Array.isArray(variant.options) && variant.options.length > 0)) {
      if (!userInput) {
        return { valid: false, message: "まず選択肢を1つ選んでから確認してください。" };
      }
      const chosen = variant.options.find((o) => o.id === userInput);
      const isCorrect = userInput === variant.answer;
      const correctOpt = variant.options.find((o) => o.id === variant.answer);
      return {
        valid: true,
        correct: isCorrect,
        wrongReason: !isCorrect && chosen ? (chosen.wrongReason || "選んだ選択肢は条件と合いません。下の考え方と途中計算を確認しましょう。") : "",
        correctDisplay: correctOpt ? correctOpt.text : String(variant.answer),
      };
    }

    if (type === "numeric") {
      const cleaned = normalizeNumberString(userInput, variant.unit === "%");
      if (!cleaned) {
        return { valid: false, message: "数値を入力してから確認してください（例：0.5 や 6）。" };
      }
      const val = Number(cleaned);
      if (!Number.isFinite(val)) {
        return { valid: false, message: `「${userInput}」は数値として読み取れませんでした。半角または全角の数字で入力してください。` };
      }
      const ansObj = typeof variant.answer === "object" ? variant.answer : { value: Number(variant.answer), tolerance: 1e-6 };
      const target = Number(ansObj.value);
      const tol = ansObj.tolerance != null ? Number(ansObj.tolerance) : 1e-6;
      const diff = val - target;
      const isCorrect = Math.abs(diff) <= tol + 1e-9;
      let wrongReason = "";
      if (!isCorrect) {
        const dir = diff > 0 ? "正解より大きい値" : "正解より小さい値";
        wrongReason = `あなたの答え <code>${escHtml(cleaned)}</code> は${dir}になっています（正解の目安：<code>${target}</code>${tol > 0.0001 ? ` ± ${tol}` : ""}）。途中計算のどの段階でずれたか確認しましょう。`;
      }
      return {
        valid: true,
        correct: isCorrect,
        wrongReason,
        correctDisplay: `${target}${variant.unit || ""}`,
      };
    }

    if (type === "predict") {
      const norm = normalizeTextOutput(userInput);
      if (!norm) {
        return { valid: false, message: "予想される出力を入力してから確認してください。" };
      }
      const accepted = Array.isArray(variant.accept) ? variant.accept : [String(variant.answer ?? "")];
      const isCorrect = accepted.some((a) => normalizeTextOutput(a) === norm);
      const canonical = accepted[0] || "";
      return {
        valid: true,
        correct: isCorrect,
        wrongReason: isCorrect
          ? ""
          : `あなたの予想：<code>${escHtml(norm)}</code> ／ 実際の出力：<code>${escHtml(canonical)}</code>。型・記号・インデックス・順番の違いを確認しましょう。`,
        correctDisplay: `<code>${escHtml(canonical)}</code>`,
      };
    }

    return { valid: false, message: "この形式は自己確認・Colab検算用です。" };
  }

  // ---- Spaced repetition scheduling
  function recordOutcome(state, ex, { correct, variantIndex, mode = "auto", now = Date.now(), note = null }) {
    const prev = state.exercises[ex.id] || {
      chapter: ex.chapter,
      concept: ex.concept,
      conceptLabel: ex.conceptLabel || ex.concept,
      level: ex.level,
      type: ex.type,
      attempts: 0,
      correct: 0,
      wrong: 0,
      streak: 0,
      lastVariant: -1,
      solvedVariants: [],
      lastResult: null,
      lastAt: null,
      intervalDays: 0,
      nextReviewAt: null,
      reviewedAfterDue: false,
      weak: false,
      note: "",
    };

    const wasDue = Boolean(prev.nextReviewAt && prev.nextReviewAt <= now && prev.attempts > 0);
    const solvedOtherDayOrDue = wasDue || Boolean(prev.lastAt && (now - prev.lastAt) >= DAY_MS && prev.correct > 0);
    const rec = { ...prev, chapter: ex.chapter, concept: ex.concept, conceptLabel: ex.conceptLabel || ex.concept, level: ex.level, type: ex.type };
    rec.attempts += 1;
    rec.lastVariant = variantIndex;
    rec.lastAt = now;
    if (note !== null) rec.note = note;

    if (correct) {
      rec.correct += 1;
      rec.streak += 1;
      if (!rec.solvedVariants.includes(variantIndex)) {
        rec.solvedVariants = [...rec.solvedVariants, variantIndex];
      }
      rec.lastResult = mode === "impl" ? "impl_verified" : (mode === "self" ? "self_checked" : "correct");
      if (solvedOtherDayOrDue || (wasDue && rec.streak >= 1)) {
        rec.reviewedAfterDue = true;
        rec.weak = false;
      } else if (rec.streak >= 2 && rec.solvedVariants.length >= 2) {
        rec.weak = false;
      }
      const idx = Math.min(Math.max(0, rec.streak - 1), INTERVALS.length - 1);
      rec.intervalDays = INTERVALS[idx];
      rec.nextReviewAt = now + rec.intervalDays * DAY_MS;
    } else {
      rec.wrong += 1;
      rec.streak = 0;
      rec.lastResult = "wrong";
      rec.weak = true;
      rec.reviewedAfterDue = false;
      rec.intervalDays = 1;
      rec.nextReviewAt = now + DAY_MS;
    }

    state.exercises[ex.id] = rec;
    saveState(state);
    return rec;
  }

  // ---- 7-state mastery calculation
  function computeChapterStatus(slug, chapterExercises, state, legacyDone, now = Date.now()) {
    const exList = chapterExercises || [];
    const recs = exList.map((e) => ({ ex: e, rec: state.exercises[e.id] || null }));
    const readFlag = Boolean(state.readChapters[slug] || legacyDone.has(slug));

    const basicEx = recs.filter((x) => x.ex.level <= 2);
    const appliedEx = recs.filter((x) => x.ex.level === 3 || x.ex.level === 5);
    const implEx = recs.filter((x) => x.ex.level === 4 || x.ex.type === "code");

    const basicSolved = basicEx.filter((x) => x.rec && x.rec.correct > 0).length;
    const appliedSolved = appliedEx.filter((x) => x.rec && x.rec.correct > 0).length;
    const implSolved = implEx.filter((x) => x.rec && (x.rec.lastResult === "impl_verified" || x.rec.correct > 0)).length;

    const dueItems = recs.filter((x) => x.rec && (x.rec.weak || (x.rec.nextReviewAt && x.rec.nextReviewAt <= now)));
    const reviewedItems = recs.filter((x) => x.rec && x.rec.reviewedAfterDue);
    const attempted = recs.filter((x) => x.rec && x.rec.attempts > 0).length;

    // Determine primary stage among the 7 explicit states
    let stage = "unstarted";
    let achieved = "unstarted";

    if (readFlag || attempted > 0) {
      achieved = "read";
    }
    if (basicEx.length > 0 && basicSolved >= Math.max(1, Math.ceil(basicEx.length * 0.5))) {
      achieved = "basic_done";
    } else if (basicEx.length === 0 && attempted > 0) {
      achieved = "basic_done";
    }
    if (appliedEx.length > 0 && appliedSolved >= 1 && STAGES[achieved].rank >= STAGES.basic_done.rank) {
      achieved = "applied_done";
    }
    if (implEx.length > 0 && implSolved >= 1) {
      achieved = "impl_done";
    }

    if (dueItems.length > 0) {
      stage = "needs_review";
    } else if (reviewedItems.length > 0 && STAGES[achieved].rank >= STAGES.basic_done.rank) {
      stage = "reviewed";
    } else {
      stage = achieved;
    }

    return {
      stage,
      achieved,
      meta: STAGES[stage],
      achievedMeta: STAGES[achieved],
      total: exList.length,
      attempted,
      basicSolved,
      basicTotal: basicEx.length,
      appliedSolved,
      appliedTotal: appliedEx.length,
      implSolved,
      implTotal: implEx.length,
      dueCount: dueItems.length,
      reviewedCount: reviewedItems.length,
      readFlag,
    };
  }

  function formatRelativeDate(ts, now = Date.now()) {
    if (!ts) return "未設定";
    const diffDays = Math.ceil((ts - now) / DAY_MS);
    if (diffDays <= 0) return "今すぐ復習可能";
    if (diffDays === 1) return "1日後";
    return `${diffDays}日後`;
  }

  // ---- Copy helper
  async function copyText(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
    } catch (e) {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); } catch (e2) {}
      ta.remove();
    }
    if (btn) {
      const old = btn.textContent;
      btn.textContent = "コピーした！";
      btn.classList.add("copied");
      setTimeout(() => { btn.textContent = old; btn.classList.remove("copied"); }, 1500);
    }
  }

  // ---- Render a single interactive exercise widget
  function mountExercise(el, payload, opts = {}) {
    const state = loadState();
    const rec = state.exercises[payload.id];
    const variants = payload.variants || [];
    if (!variants.length) return;

    let currentIdx = opts.forceVariant != null
      ? (opts.forceVariant % variants.length)
      : (opts.preferFresh && rec && rec.lastVariant >= 0 && variants.length > 1
          ? (rec.lastVariant + 1) % variants.length
          : 0);

    function draw() {
      const st = loadState();
      const r = st.exercises[payload.id];
      const v = variants[currentIdx];
      const lvlLabel = LEVEL_LABELS[payload.level] || `Lv.${payload.level}`;
      const reviewBadges = (payload.reviewOf || []).map((rv) => `<span class="ex-badge ex-badge-rev">復習連動：${escHtml(rv)}</span>`).join("");
      const courseBadge = payload.course === "thorough" ? '<span class="ex-badge ex-badge-thorough">じっくり基礎</span>' : "";
      let statusBadge = '<span class="ex-status st-unstarted">未解答</span>';
      if (r) {
        if (r.weak) {
          statusBadge = '<span class="ex-status st-review-due">要復習（誤答あり）</span>';
        } else if (r.reviewedAfterDue) {
          statusBadge = '<span class="ex-status st-reviewed">復習で再確認済</span>';
        } else if (r.lastResult === "impl_verified") {
          statusBadge = '<span class="ex-status st-impl">Colab検算済</span>';
        } else if (r.correct > 0) {
          statusBadge = `<span class="ex-status st-basic">正解 ${r.correct}回（次回：${formatRelativeDate(r.nextReviewAt)}）</span>`;
        }
      }

      const variantInfo = variants.length > 1
        ? `<span class="ex-variant-tag">問題 ${currentIdx + 1} / ${variants.length}</span>`
        : "";

      let bodyHtml = `<div class="ex-prompt">${v.prompt}</div>`;
      if (v.codeHtml) {
        bodyHtml += `<div class="codeblock code lang-python ex-code"><div class="code-head"><span>確認対象コード</span><button type="button" class="copy ex-copy-code">コピー</button></div><pre><code>${v.codeHtml}</code></pre></div>`;
      }

      const isChoiceLike = payload.type === "choice" || (payload.type === "predict" && Array.isArray(v.options) && v.options.length > 0);

      if (isChoiceLike) {
        const groupName = `ex-${payload.id}-${currentIdx}-${Math.random().toString(36).slice(2, 6)}`;
        bodyHtml += `<fieldset class="ex-options"><legend class="sr-only">選択肢</legend>` +
          v.options.map((o) =>
            `<label class="ex-opt"><input type="radio" name="${groupName}" value="${escHtml(o.id)}"><span class="ex-opt-id">${escHtml(o.id.toUpperCase())}</span><span class="ex-opt-text">${o.text}</span></label>`
          ).join("") + `</fieldset>`;
      } else if (payload.type === "numeric") {
        bodyHtml += `<div class="ex-input-row"><label class="sr-only" for="in-${payload.id}">数値の解答</label>` +
          `<input id="in-${payload.id}" class="ex-input" type="text" inputmode="decimal" autocomplete="off" placeholder="${escHtml(v.placeholder || "数値を入力（例：0.665）")}">` +
          (v.unit ? `<span class="ex-unit">${escHtml(v.unit)}</span>` : "") + `</div>`;
      } else if (payload.type === "predict") {
        bodyHtml += `<div class="ex-input-row"><label class="sr-only" for="in-${payload.id}">出力の予想</label>` +
          `<textarea id="in-${payload.id}" class="ex-textarea ex-mono" rows="2" placeholder="${escHtml(v.placeholder || "実行結果として表示される出力を予想して入力")}"></textarea></div>`;
      } else if (payload.type === "explain") {
        const savedNote = r && r.note ? r.note : "";
        bodyHtml += `<p class="ex-scope-note"><strong>検証できる範囲：</strong>自由記述の自動採点は行いません。まず自分の言葉で理由を書いてから、確認ポイントと解答例に照らして自己確認してください。</p>` +
          `<label class="sr-only" for="note-${payload.id}">自分の説明メモ</label>` +
          `<textarea id="note-${payload.id}" class="ex-textarea" rows="3" placeholder="まず自分の言葉で理由や仕組みを書いてみよう（このブラウザにメモ保存されます）">${escHtml(savedNote)}</textarea>`;
      } else if (payload.type === "code") {
        bodyHtml += `<p class="ex-scope-note"><strong>検証できる範囲：</strong>この静的サイト上ではPythonを実行しません。下のスタートコードをもとにColabで自力実装し、<strong>検算テストコード（assert）</strong>をすべて通したうえでチェックしてください。</p>`;
        if (v.starterCodeHtml) {
          bodyHtml += `<div class="codeblock code lang-python ex-code"><div class="code-head"><span>スタートコード（これをColabで完成させる）</span><button type="button" class="copy ex-copy-starter">コピー</button></div><pre><code>${v.starterCodeHtml}</code></pre></div>`;
        }
        if (v.colabCheckHtml) {
          bodyHtml += `<div class="codeblock code lang-python ex-code"><div class="code-head"><span>Colab検算用テスト（全assert通過を確認）</span><button type="button" class="copy ex-copy-check">コピー</button></div><pre><code>${v.colabCheckHtml}</code></pre></div>`;
        }
      }

      const actionsHtml = (isChoiceLike || payload.type === "numeric" || payload.type === "predict")
        ? `<div class="ex-actions">
            <button type="button" class="btn primary ex-submit">解答を確認する</button>
            ${v.hint ? '<button type="button" class="btn ex-hint-btn" aria-expanded="false">ヒントを見る</button>' : ""}
            ${variants.length > 1 ? '<button type="button" class="btn ex-switch-btn">別の類題に切り替え</button>' : ""}
          </div>`
        : `<div class="ex-actions">
            <button type="button" class="btn primary ex-reveal-btn" aria-expanded="false">${payload.type === "code" ? "解答例と確認観点を開く（まず自力で挑戦！）" : "解答例と確認ポイントを開く"}</button>
            ${v.hint ? '<button type="button" class="btn ex-hint-btn" aria-expanded="false">ヒントを見る</button>' : ""}
            ${variants.length > 1 ? '<button type="button" class="btn ex-switch-btn">別の類題に切り替え</button>' : ""}
          </div>`;

      el.innerHTML = `
        <div class="ex-head">
          <div class="ex-meta">
            <span class="ex-num">確認問題 ${payload.num || ""}</span>
            <span class="ex-badge ex-lvl-${payload.level}">${escHtml(lvlLabel)}</span>
            <span class="ex-concept">${escHtml(payload.conceptLabel || payload.concept)}</span>
            ${courseBadge}${reviewBadges}${variantInfo}
          </div>
          ${statusBadge}
        </div>
        ${bodyHtml}
        ${actionsHtml}
        ${v.hint ? `<div class="ex-hint" hidden><b>ヒント：</b>${v.hint}</div>` : ""}
        <div class="ex-feedback" aria-live="polite" hidden></div>
      `;

      // Wire copy buttons inside exercise
      const copyCode = $(".ex-copy-code", el);
      if (copyCode && v.code) copyCode.addEventListener("click", () => copyText(v.code, copyCode));
      const copyStarter = $(".ex-copy-starter", el);
      if (copyStarter && v.starterCode) copyStarter.addEventListener("click", () => copyText(v.starterCode, copyStarter));
      const copyCheck = $(".ex-copy-check", el);
      if (copyCheck && v.colabCheck) copyCheck.addEventListener("click", () => copyText(v.colabCheck, copyCheck));

      // Wire hint toggle
      const hintBtn = $(".ex-hint-btn", el);
      const hintBox = $(".ex-hint", el);
      if (hintBtn && hintBox) {
        hintBtn.addEventListener("click", () => {
          const open = hintBox.hidden;
          hintBox.hidden = !open;
          hintBtn.setAttribute("aria-expanded", String(open));
          hintBtn.textContent = open ? "ヒントを閉じる" : "ヒントを見る";
        });
      }

      // Wire variant switch
      const switchBtn = $(".ex-switch-btn", el);
      if (switchBtn && variants.length > 1) {
        switchBtn.addEventListener("click", () => {
          currentIdx = (currentIdx + 1) % variants.length;
          draw();
        });
      }

      // Wire auto-graded submission
      const submitBtn = $(".ex-submit", el);
      const fb = $(".ex-feedback", el);
      if (submitBtn) {
        const doSubmit = () => {
          let userVal = "";
          if (isChoiceLike) {
            const checked = $("input[type='radio']:checked", el);
            userVal = checked ? checked.value : "";
          } else {
            const inp = $(".ex-input, .ex-textarea", el);
            userVal = inp ? inp.value : "";
          }
          const res = gradeVariant(payload, v, userVal);
          if (!res.valid) {
            fb.hidden = false;
            fb.className = "ex-feedback fb-warn";
            fb.innerHTML = `<p>${escHtml(res.message)}</p>`;
            return;
          }
          const updated = recordOutcome(loadState(), payload, { correct: res.correct, variantIndex: currentIdx, mode: "auto" });
          const sectionHref = payload.sectionAnchor ? `${payload.chapter}.html${payload.sectionAnchor}` : `${payload.chapter}.html`;
          const sectionLink = payload.section ? `<a href="${escHtml(sectionHref)}">${escHtml(payload.section)}</a>` : `<a href="${escHtml(sectionHref)}">該当する章の解説へ</a>`;
          const stepsHtml = (v.steps && v.steps.length)
            ? `<div class="fb-block"><b>途中計算・トレース：</b><ol>${v.steps.map((s) => `<li>${s}</li>`).join("")}</ol></div>`
            : "";
          const altHtml = v.altExample
            ? `<div class="fb-block"><b>別の具体例：</b><p>${v.altExample}</p></div>`
            : "";
          const retryBtnHtml = variants.length > 1
            ? `<button type="button" class="btn primary ex-retry-variant">${res.correct ? "類題（別の条件）で定着を確かめる →" : "類題で再挑戦する →"}</button>`
            : `<button type="button" class="btn ex-retry-same">もう一度解き直す</button>`;

          fb.hidden = false;
          if (res.correct) {
            const noteMsg = updated.reviewedAfterDue
              ? "時間を空けた復習での再確認が完了しました！"
              : (updated.solvedVariants.length >= 2
                  ? "別の条件の類題でも正解できました。さらに日を空けて復習すると定着を確かめられます。"
                  : "1回目の確認をクリアしました（1回の正解だけで完全理解とはせず、類題や日を空けた復習で定着を確かめます）。");
            fb.className = "ex-feedback fb-ok";
            fb.innerHTML = `
              <p class="fb-title">✓ 正解！ <small>（次回の復習目安：${formatRelativeDate(updated.nextReviewAt)}）</small></p>
              <p class="fb-sub">${noteMsg}</p>
              <div class="fb-block"><b>正しい考え方：</b><p>${v.reasoning}</p></div>
              ${stepsHtml}
              ${altHtml}
              <div class="fb-foot">${retryBtnHtml}</div>
            `;
          } else {
            fb.className = "ex-feedback fb-ng";
            fb.innerHTML = `
              <p class="fb-title">✗ もう一度考えてみよう <small>（復習間隔を1日に短縮しました）</small></p>
              <div class="fb-block fb-where"><b>どこが間違っているか：</b><p>${res.wrongReason}</p></div>
              <div class="fb-block"><b>正しい考え方：</b><p>${v.reasoning}</p></div>
              ${stepsHtml}
              <div class="fb-block"><b>関連する教材の節：</b>${sectionLink}</div>
              ${altHtml}
              <div class="fb-foot">${retryBtnHtml}</div>
            `;
          }
          const retryVar = $(".ex-retry-variant", fb);
          if (retryVar) {
            retryVar.addEventListener("click", () => {
              currentIdx = (currentIdx + 1) % variants.length;
              draw();
              el.scrollIntoView({ behavior: "smooth", block: "nearest" });
            });
          }
          const retrySame = $(".ex-retry-same", fb);
          if (retrySame) {
            retrySame.addEventListener("click", () => draw());
          }
          // Update status badge in header + global mastery indicators
          refreshGlobalUI();
          if (typeof opts.onAnswer === "function") opts.onAnswer(updated);
        };

        submitBtn.addEventListener("click", doSubmit);
        const numInput = $(".ex-input", el);
        if (numInput) {
          numInput.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); doSubmit(); } });
        }
      }

      // Wire self-check / code implementation reveal
      const revealBtn = $(".ex-reveal-btn", el);
      if (revealBtn) {
        revealBtn.addEventListener("click", () => {
          const isOpen = !fb.hidden;
          if (isOpen) {
            fb.hidden = true;
            revealBtn.setAttribute("aria-expanded", "false");
            return;
          }
          revealBtn.setAttribute("aria-expanded", "true");
          fb.hidden = false;
          fb.className = "ex-feedback fb-self";
          const criteria = v.selfCheckCriteria || [];
          const critHtml = criteria.length
            ? `<div class="fb-block"><b>確認観点（すべて確認してチェック）：</b><ul class="ex-criteria">${criteria.map((c, idx) => `<li><label><input type="checkbox" class="ex-crit-cb" data-idx="${idx}"> <span>${c}</span></label></li>`).join("")}</ul></div>`
            : "";
          const solCodeHtml = v.solutionCodeHtml
            ? `<details class="ex-sol-details"><summary>実装例を見る（まず自分で書いてから！）</summary><div class="codeblock code lang-python"><div class="code-head"><span>実装例</span><button type="button" class="copy ex-copy-sol">コピー</button></div><pre><code>${v.solutionCodeHtml}</code></pre></div></details>`
            : "";
          const modelAnsHtml = v.modelAnswer
            ? `<div class="fb-block"><b>解答例：</b><p>${v.modelAnswer}</p></div>`
            : "";
          const stepsHtml = (v.steps && v.steps.length)
            ? `<div class="fb-block"><b>ポイント・手順：</b><ol>${v.steps.map((s) => `<li>${s}</li>`).join("")}</ol></div>`
            : "";
          const altHtml = v.altExample
            ? `<div class="fb-block"><b>別の具体例：</b><p>${v.altExample}</p></div>`
            : "";
          const sectionHref = payload.sectionAnchor ? `${payload.chapter}.html${payload.sectionAnchor}` : `${payload.chapter}.html`;
          const sectionLink = payload.section ? `<a href="${escHtml(sectionHref)}">${escHtml(payload.section)}</a>` : "";

          fb.innerHTML = `
            ${modelAnsHtml}
            <div class="fb-block"><b>考え方：</b><p>${v.reasoning}</p></div>
            ${stepsHtml}
            ${altHtml}
            ${sectionLink ? `<div class="fb-block"><b>関連する教材の節：</b>${sectionLink}</div>` : ""}
            ${solCodeHtml}
            ${critHtml}
            <div class="fb-foot ex-self-btns">
              <button type="button" class="btn primary ex-mark-ok">${payload.type === "code" ? "✓ Colabで検算テスト通過＆観点を確認した" : "✓ 確認観点どおり説明できた"}</button>
              <button type="button" class="btn ex-mark-ng">まだ自信がない（復習リストに入れる）</button>
            </div>
            <p class="ex-self-msg" aria-live="polite"></p>
          `;

          const copySol = $(".ex-copy-sol", fb);
          if (copySol && v.solutionCode) copySol.addEventListener("click", () => copyText(v.solutionCode, copySol));

          const markOk = $(".ex-mark-ok", fb);
          const markNg = $(".ex-mark-ng", fb);
          const msg = $(".ex-self-msg", fb);
          const noteEl = $(`#note-${payload.id}`, el);

          markOk.addEventListener("click", () => {
            const cbs = $$(".ex-crit-cb", fb);
            if (cbs.length && !cbs.every((c) => c.checked)) {
              msg.textContent = "上の確認観点をすべてチェックしてから完了を記録してください。";
              return;
            }
            const noteText = noteEl ? noteEl.value : null;
            const recNew = recordOutcome(loadState(), payload, {
              correct: true,
              variantIndex: currentIdx,
              mode: payload.type === "code" ? "impl" : "self",
              note: noteText,
            });
            msg.textContent = payload.type === "code"
              ? `自力実装の検算確認を記録しました（次回の復習目安：${formatRelativeDate(recNew.nextReviewAt)}）。`
              : `自己確認を記録しました（次回の復習目安：${formatRelativeDate(recNew.nextReviewAt)}）。`;
            refreshGlobalUI();
            if (typeof opts.onAnswer === "function") opts.onAnswer(recNew);
          });

          markNg.addEventListener("click", () => {
            const noteText = noteEl ? noteEl.value : null;
            recordOutcome(loadState(), payload, { correct: false, variantIndex: currentIdx, mode: "self", note: noteText });
            msg.textContent = "「復習が必要」として記録しました。関連する節を読み直して再挑戦しましょう。";
            refreshGlobalUI();
          });
        });
      }
    }

    draw();
  }

  // ---- Global UI refresh (due badges, chapter mastery strip, sidebar status dots)
  let cachedIndex = null;
  async function loadIndex() {
    if (cachedIndex) return cachedIndex;
    try {
      const res = await fetch("exercises-index.json");
      if (res.ok) cachedIndex = await res.json();
    } catch (e) {}
    return cachedIndex;
  }

  function countGlobalDue(state, now = Date.now()) {
    let n = 0;
    for (const rec of Object.values(state.exercises || {})) {
      if (rec.weak || (rec.nextReviewAt && rec.nextReviewAt <= now)) n++;
    }
    return n;
  }

  function refreshGlobalUI() {
    const state = loadState();
    const legacyDone = loadLegacyDone();
    const now = Date.now();
    const due = countGlobalDue(state, now);

    $$("[data-due-badge]").forEach((b) => {
      b.textContent = String(due);
      b.hidden = due === 0;
    });

    // Update chapter mastery strip on current chapter page
    const strip = $("[data-mastery-chapter]");
    if (strip) {
      const slug = strip.dataset.masteryChapter;
      const exEls = $$(".exercise[data-chapter='" + slug + "']");
      const exMeta = exEls.map((e) => ({
        id: e.dataset.exerciseId,
        level: Number(e.dataset.level || 1),
        type: e.dataset.type || "choice",
      }));
      const st = computeChapterStatus(slug, exMeta, state, legacyDone, now);
      const badge = $("[data-ms-stage]", strip);
      const detail = $("[data-ms-detail]", strip);
      if (badge) {
        badge.textContent = st.meta.label;
        badge.className = `ms-stage ${st.meta.cls}`;
      }
      if (detail) {
        const parts = [];
        parts.push(`基礎 ${st.basicSolved}/${st.basicTotal}`);
        if (st.appliedTotal) parts.push(`応用 ${st.appliedSolved}/${st.appliedTotal}`);
        if (st.implTotal) parts.push(`自力実装 ${st.implSolved}/${st.implTotal}`);
        if (st.dueCount) parts.push(`要復習 ${st.dueCount}件`);
        else if (st.reviewedCount) parts.push(`再確認済 ${st.reviewedCount}件`);
        detail.textContent = parts.join(" · ");
      }
    }

    // Update sidebar & home map chapter indicators using exercises-index if loaded
    if (cachedIndex) {
      const bySlug = new Map(cachedIndex.chapters.map((c) => [c.slug, c]));
      $$("a[data-slug]").forEach((a) => {
        const ch = bySlug.get(a.dataset.slug);
        if (!ch) return;
        const st = computeChapterStatus(ch.slug, ch.exercises, state, legacyDone, now);
        a.dataset.stage = st.stage;
        a.title = `${ch.title}：${st.meta.label}`;
      });
    }
  }

  // ---- Review Dashboard (review.html)
  async function initReviewDashboard() {
    const summaryEl = $("#dash-summary");
    if (!summaryEl) return;
    const index = await loadIndex();
    if (!index) {
      summaryEl.innerHTML = "<p>演習インデックス（exercises-index.json）を読み込めませんでした。</p>";
      return;
    }

    const byId = new Map();
    const bySlug = new Map();
    for (const ch of index.chapters) {
      bySlug.set(ch.slug, ch);
      for (const ex of ch.exercises) byId.set(ex.id, ex);
    }

    function renderDashboard() {
      const state = loadState();
      const legacyDone = loadLegacyDone();
      const now = Date.now();

      // 1. 7-state summary
      const counts = { unstarted: 0, read: 0, basic_done: 0, applied_done: 0, impl_done: 0, needs_review: 0, reviewed: 0 };
      const chStatuses = index.chapters.map((ch) => {
        const st = computeChapterStatus(ch.slug, ch.exercises, state, legacyDone, now);
        counts[st.stage] = (counts[st.stage] || 0) + 1;
        return { ch, st };
      });
      const totalEx = byId.size;
      const solvedEx = Object.values(state.exercises).filter((r) => r.correct > 0).length;

      summaryEl.innerHTML = `
        <div class="stage-grid">
          ${Object.entries(STAGES).map(([k, info]) =>
            `<div class="stage-card ${info.cls}"><span class="sc-num">${counts[k] || 0}</span><span class="sc-name">${info.label}</span></div>`
          ).join("")}
        </div>
        <p class="dash-totals">全 ${index.chapters.length} 章 ／ 収録確認問題 ${totalEx} 問（解答済み ${solvedEx} 問）</p>
      `;

      // 2. Due reviews
      const dueEl = $("#dash-due");
      const dueRecs = Object.entries(state.exercises)
        .filter(([id, r]) => byId.has(id) && (r.weak || (r.nextReviewAt && r.nextReviewAt <= now)))
        .sort((a, b) => (a[1].weak === b[1].weak ? (a[1].nextReviewAt || 0) - (b[1].nextReviewAt || 0) : (a[1].weak ? -1 : 1)));

      const upcomingRecs = Object.entries(state.exercises)
        .filter(([id, r]) => byId.has(id) && !r.weak && r.nextReviewAt && r.nextReviewAt > now)
        .sort((a, b) => a[1].nextReviewAt - b[1].nextReviewAt);

      if (dueRecs.length === 0) {
        dueEl.innerHTML = `<p class="empty-msg">現在、期限が来ている復習問題はありません。${upcomingRecs.length ? `（予定済み ${upcomingRecs.length} 問。次の復習は ${formatRelativeDate(upcomingRecs[0][1].nextReviewAt)} です）` : "まずは第1章の確認問題から挑戦してみましょう！"}</p>` +
          (upcomingRecs.length ? `<button type="button" class="btn" id="practice-early">予定日前の問題を類題で先取り復習する（最大3問）</button><div id="early-box"></div>` : "");
        const earlyBtn = $("#practice-early", dueEl);
        if (earlyBtn) {
          earlyBtn.addEventListener("click", () => {
            const box = $("#early-box", dueEl);
            box.innerHTML = "";
            upcomingRecs.slice(0, 3).forEach(([id], idx) => {
              const ex = { ...byId.get(id), num: idx + 1 };
              const sec = document.createElement("section");
              sec.className = "exercise";
              box.appendChild(sec);
              mountExercise(sec, ex, { preferFresh: true, onAnswer: () => renderDashboard() });
            });
          });
        }
      } else {
        dueEl.innerHTML = `<p>今すぐ復習をおすすめする問題が <strong>${dueRecs.length} 件</strong> あります（丸暗記を防ぐため、前回と異なる類題を優先表示します）。</p><div id="due-list"></div>`;
        const list = $("#due-list", dueEl);
        dueRecs.slice(0, 5).forEach(([id], idx) => {
          const ex = { ...byId.get(id), num: idx + 1 };
          const sec = document.createElement("section");
          sec.className = "exercise";
          list.appendChild(sec);
          mountExercise(sec, ex, { preferFresh: true, onAnswer: () => renderDashboard() });
        });
      }

      // 3. Weak concepts
      const weakEl = $("#dash-weak");
      const weakItems = Object.entries(state.exercises)
        .filter(([id, r]) => byId.has(id) && (r.weak || r.wrong > 0))
        .sort((a, b) => b[1].wrong - a[1].wrong);
      if (!weakItems.length) {
        weakEl.innerHTML = `<p class="empty-msg">誤答が記録された概念はまだありません。間違えた問題はここに自動集計され、該当する節へすぐ戻れます。</p>`;
      } else {
        weakEl.innerHTML = `<ul class="weak-list">` + weakItems.map(([id, r]) => {
          const ex = byId.get(id);
          const ch = bySlug.get(ex.chapter);
          const href = `${ex.chapter}.html${ex.sectionAnchor || ""}`;
          return `<li>
            <div><strong>${escHtml(ex.conceptLabel || ex.concept)}</strong> <small>（第${ch ? ch.num : "?"}章 · 誤答 ${r.wrong}回 / 正解 ${r.correct}回）</small></div>
            <div class="weak-actions"><a href="${escHtml(href)}">解説を読む</a> · <a href="${ex.chapter}.html#ex-${escHtml(id)}">問題へ</a></div>
          </li>`;
        }).join("") + `</ul>`;
      }

      // 4. Concept chains
      const chainsEl = $("#dash-chains");
      chainsEl.innerHTML = (index.reviewChains || []).map((chain) => {
        const nodes = chain.chapters.map((slug) => {
          const item = chStatuses.find((x) => x.ch.slug === slug);
          if (!item) return "";
          return `<a class="chain-node ${item.st.meta.cls}" href="${slug}.html"><b>第${item.ch.num}章 ${escHtml(item.ch.short)}</b><span>${item.st.meta.label}</span></a>`;
        }).join('<span class="chain-arrow" aria-hidden="true">→</span>');
        return `<div class="chain-row"><p class="chain-title">${escHtml(chain.title)}</p><div class="chain-nodes">${nodes}</div></div>`;
      }).join("");

      // 5. Chapter breakdown table
      const chEl = $("#dash-chapters");
      chEl.innerHTML = `<table><thead><tr><th>章</th><th>状態</th><th>基礎</th><th>応用</th><th>自力実装</th><th>要復習</th></tr></thead><tbody>` +
        chStatuses.map(({ ch, st }) => `<tr>
          <td><a href="${ch.slug}.html">第${ch.num}章 ${escHtml(ch.title)}</a></td>
          <td><span class="ms-stage ${st.meta.cls}">${st.meta.label}</span></td>
          <td>${st.basicSolved}/${st.basicTotal}</td>
          <td>${st.appliedSolved}/${st.appliedTotal}</td>
          <td>${st.implSolved}/${st.implTotal}</td>
          <td>${st.dueCount}</td>
        </tr>`).join("") + `</tbody></table>`;
    }

    renderDashboard();

    // Backup export/import/reset
    const statusMsg = $("#backup-status");
    const exportBtn = $("#export-history");
    if (exportBtn) {
      exportBtn.addEventListener("click", () => {
        const bundle = {
          exportedAt: new Date().toISOString(),
          course: getCourse(),
          legacyDone: Array.from(loadLegacyDone()),
          legacyChecks: safeGet(LEGACY_KEY + ":checks", {}),
          study: loadState(),
        };
        const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "tsukuru-llm-history.json";
        a.click();
        URL.revokeObjectURL(a.href);
        if (statusMsg) statusMsg.textContent = "学習履歴をJSONファイルとして保存しました。";
      });
    }
    const importInput = $("#import-history");
    if (importInput) {
      importInput.addEventListener("change", async () => {
        const file = importInput.files && importInput.files[0];
        if (!file) return;
        try {
          const parsed = JSON.parse(await file.text());
          if (!parsed || typeof parsed !== "object" || !parsed.study || parsed.study.version !== 2) {
            throw new Error("invalid format");
          }
          saveState(parsed.study);
          if (Array.isArray(parsed.legacyDone)) safeSet(LEGACY_KEY + ":done", parsed.legacyDone);
          if (parsed.legacyChecks && typeof parsed.legacyChecks === "object") safeSet(LEGACY_KEY + ":checks", parsed.legacyChecks);
          if (parsed.course) applyCourse(parsed.course);
          renderDashboard();
          refreshGlobalUI();
          if (statusMsg) statusMsg.textContent = "学習履歴を復元しました。";
        } catch (e) {
          if (statusMsg) statusMsg.textContent = "読み込みに失敗しました。正しいバックアップJSONファイルか確認してください。";
        }
        importInput.value = "";
      });
    }
    const resetBtn = $("#reset-history");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        if (!confirm("このブラウザに保存された確認問題の解答履歴と復習予定をリセットしますか？")) return;
        saveState({ version: 2, readChapters: {}, exercises: {} });
        renderDashboard();
        refreshGlobalUI();
        if (statusMsg) statusMsg.textContent = "学習履歴をリセットしました。";
      });
    }
  }

  // ---- Mark current chapter as read when opened & interacted / scrolled
  function initChapterReadTracking() {
    const page = document.body.dataset.page;
    if (!page || !/^\d{2}-/.test(page)) return;
    const markRead = () => {
      const state = loadState();
      const now = Date.now();
      if (!state.readChapters[page]) {
        state.readChapters[page] = { firstAt: now, lastAt: now };
      } else {
        state.readChapters[page].lastAt = now;
      }
      saveState(state);
      refreshGlobalUI();
    };
    // Sync when done button is clicked (keeps compatibility with app.js)
    $$("[data-done]").forEach((btn) => btn.addEventListener("click", () => setTimeout(refreshGlobalUI, 20)));
    // Mark as "説明を読んだ" once learner scrolls past 35% of chapter or stays on page
    let marked = false;
    const checkScroll = () => {
      if (marked) return;
      const docH = document.documentElement.scrollHeight - window.innerHeight;
      if (docH <= 0 || window.scrollY / docH >= 0.35) {
        marked = true;
        markRead();
        window.removeEventListener("scroll", checkScroll);
      }
    };
    window.addEventListener("scroll", checkScroll, { passive: true });
    // Also mark if already scrolled / short page
    setTimeout(checkScroll, 800);
  }

  // ---- Init
  document.addEventListener("DOMContentLoaded", () => {
    // Course selector buttons
    $$("[data-set-course]").forEach((btn) => {
      btn.addEventListener("click", () => applyCourse(btn.dataset.setCourse, true));
    });
    // Track manual scaffold toggles so user choice is respected
    $$("details.scaffold").forEach((el) => {
      el.addEventListener("toggle", () => {
        if (el.dataset.initDone && !_syncingCourse) el.dataset.userToggled = "1";
      });
    });
    applyCourse(getCourse(), true);
    $$("details.scaffold").forEach((el) => { el.dataset.initDone = "1"; });

    // Mount all inline exercises on chapter pages
    $$(".exercise[data-exercise-id]").forEach((el) => {
      const dataEl = $(".ex-data", el);
      if (!dataEl) return;
      try {
        const payload = JSON.parse(dataEl.textContent);
        mountExercise(el, payload);
      } catch (e) {
        el.innerHTML = "<p>演習データの読み込みに失敗しました。</p>";
      }
    });

    initChapterReadTracking();
    refreshGlobalUI();
    loadIndex().then(() => refreshGlobalUI());
    initReviewDashboard();
  });

  // Expose testable API for QA & scripts
  window.TsukuruStudy = {
    STAGES,
    INTERVALS,
    gradeVariant,
    computeChapterStatus,
    recordOutcome,
    loadState,
    saveState,
    getCourse,
    applyCourse,
    normalizeNumberString,
    normalizeTextOutput,
  };
})();
