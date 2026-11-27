// つくってわかるLLM — Interactive Exercises, Spaced Repetition, Mastery Engine & Course Selector.
// All learning history stays strictly inside this browser's localStorage.
(() => {
  const LEGACY_KEY = "tsukuru-llm";
  const STATE_KEY = "tsukuru-llm:study_v2";
  const COURSE_KEY = "tsukuru-llm-course";
  const DAY_MS = 24 * 60 * 60 * 1000;
  const INTERVALS = [1, 3, 7, 14, 30]; // Initial default intervals in days (transparent heuristic)
  const MAX_IMPORT_BYTES = 2 * 1024 * 1024;
  const FORBIDDEN_KEYS = new Set(["__proto__", "constructor", "prototype"]);
  const ALLOWED_RESULTS = new Set([
    "correct",
    "hinted_correct",
    "wrong",
    "self_checked",
    "impl_self_reported",
    "impl_verified", // legacy read compatibility
    null,
  ]);
  const OPT_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

  const STAGES = {
    unstarted: { label: "未学習", rank: 0, cls: "st-unstarted" },
    read: { label: "説明を読んだ", rank: 1, cls: "st-read" },
    basic_done: { label: "基礎問題を解いた", rank: 2, cls: "st-basic" },
    applied_done: { label: "応用問題を解いた", rank: 3, cls: "st-applied" },
    impl_done: { label: "自力実装を完了した（自己申告）", rank: 4, cls: "st-impl" },
    needs_review: { label: "復習が必要", rank: 5, cls: "st-review-due" },
    reviewed: { label: "間隔を空けて再確認できた", rank: 6, cls: "st-reviewed" },
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
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function isPlainObject(v) {
    return Boolean(v) && typeof v === "object" && !Array.isArray(v);
  }

  function toNonNegInt(v, fallback = 0, max = 1000000) {
    const n = Number(v);
    if (!Number.isFinite(n) || n < 0) return fallback;
    return Math.min(max, Math.floor(n));
  }

  function isValidTs(ts) {
    return typeof ts === "number" && Number.isFinite(ts) && ts >= 946684800000 && ts <= 4102444800000;
  }

  function startOfLocalDay(ts) {
    const d = new Date(ts);
    return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  }

  function sameLocalDay(a, b) {
    if (!isValidTs(a) || !isValidTs(b)) return false;
    return startOfLocalDay(a) === startOfLocalDay(b);
  }

  function isDueAt(rec, now = Date.now()) {
    if (!rec) return false;
    if (rec.weak) return true;
    if (!isValidTs(rec.nextReviewAt)) return false;
    return rec.nextReviewAt <= now;
  }

  // ---- Storage error notification (delegates to app.js banner with standalone fallback)
  let localStorageAlertShown = false;
  function notifyStorageFailure(reason) {
    if (window.TsukuruUI && typeof window.TsukuruUI.notifyStorageError === "function") {
      window.TsukuruUI.notifyStorageError(reason);
      return;
    }
    if (localStorageAlertShown) return;
    localStorageAlertShown = true;
    const host = $("#main") || document.body;
    if (!host || $("#storage-error-banner")) return;
    const banner = document.createElement("div");
    banner.id = "storage-error-banner";
    banner.className = "storage-alert";
    banner.setAttribute("role", "alert");
    const p = document.createElement("p");
    p.textContent = (reason || "学習履歴の保存に失敗しました。") + " プライベートモードや保存容量上限の可能性があります。";
    banner.appendChild(p);
    host.prepend(banner);
  }

  function safeGet(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch (e) {
      return fallback;
    }
  }

  function safeSet(key, val, { silent = false } = {}) {
    try {
      localStorage.setItem(key, JSON.stringify(val));
      return true;
    } catch (e) {
      if (!silent) notifyStorageFailure("ブラウザの保存領域（localStorage）へ学習履歴を保存できませんでした。");
      return false;
    }
  }

  function safeRemove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (e) {
      return false;
    }
  }

  function loadLegacyDone() {
    const arr = safeGet(LEGACY_KEY + ":done", []);
    return new Set(Array.isArray(arr) ? arr.filter((x) => typeof x === "string") : []);
  }

  // ---- Record sanitization & schema migration (v1 / legacy -> v2 without silent wipe)
  function sanitizeIntArray(arr, maxLen = 64) {
    if (!Array.isArray(arr)) return [];
    const out = [];
    for (const item of arr) {
      const n = Number(item);
      if (Number.isInteger(n) && n >= 0 && n < 1000 && !out.includes(n)) {
        out.push(n);
        if (out.length >= maxLen) break;
      }
    }
    return out;
  }

  function sanitizeExerciseRecord(raw) {
    if (!isPlainObject(raw)) return null;
    const correct = toNonNegInt(raw.correct, 0);
    const wrong = toNonNegInt(raw.wrong, 0);
    const attempts = Math.max(toNonNegInt(raw.attempts, correct + wrong), correct + wrong);
    const lastResult = ALLOWED_RESULTS.has(raw.lastResult) ? raw.lastResult : null;
    const solvedVariants = sanitizeIntArray(raw.solvedVariants);
    const hintedCorrect = toNonNegInt(raw.hintedCorrect, lastResult === "hinted_correct" ? Math.max(1, correct) : 0);
    const hasExplicitUnhinted = raw.unhintedCorrect != null;
    const unhintedCorrect = hasExplicitUnhinted
      ? toNonNegInt(raw.unhintedCorrect, 0)
      : (lastResult === "hinted_correct" ? Math.max(0, correct - hintedCorrect) : correct);
    const unhintedVariants = Array.isArray(raw.unhintedVariants)
      ? sanitizeIntArray(raw.unhintedVariants)
      : (unhintedCorrect > 0 ? solvedVariants.slice() : []);

    const lastAt = isValidTs(Number(raw.lastAt)) ? Number(raw.lastAt) : null;
    const nextReviewAt = isValidTs(Number(raw.nextReviewAt)) ? Number(raw.nextReviewAt) : null;
    const lastVariant = Number.isInteger(Number(raw.lastVariant)) && Number(raw.lastVariant) >= -1 ? Number(raw.lastVariant) : -1;

    return {
      chapter: typeof raw.chapter === "string" ? raw.chapter.slice(0, 80) : "",
      concept: typeof raw.concept === "string" ? raw.concept.slice(0, 120) : "",
      conceptLabel: typeof raw.conceptLabel === "string" ? raw.conceptLabel.slice(0, 120) : "",
      level: Math.min(5, Math.max(1, toNonNegInt(raw.level, 1, 5))),
      type: typeof raw.type === "string" ? raw.type.slice(0, 32) : "choice",
      attempts,
      correct,
      wrong,
      unhintedCorrect,
      hintedCorrect,
      streak: toNonNegInt(raw.streak, 0, 1000),
      lastVariant,
      solvedVariants,
      unhintedVariants,
      lastUsedHint: Boolean(raw.lastUsedHint || lastResult === "hinted_correct"),
      lastResult,
      lastAt,
      intervalDays: toNonNegInt(raw.intervalDays, 0, 3650),
      nextReviewAt,
      reviewedAfterDue: Boolean(raw.reviewedAfterDue),
      weak: Boolean(raw.weak),
      note: typeof raw.note === "string" ? raw.note.slice(0, 5000) : "",
    };
  }

  function sanitizeReadChapters(raw) {
    const out = {};
    if (!isPlainObject(raw)) return out;
    for (const [slug, val] of Object.entries(raw)) {
      if (FORBIDDEN_KEYS.has(slug) || !/^[a-z0-9-]+$/i.test(slug)) continue;
      if (isPlainObject(val)) {
        const firstAt = isValidTs(Number(val.firstAt)) ? Number(val.firstAt) : Date.now();
        const lastAt = isValidTs(Number(val.lastAt)) ? Number(val.lastAt) : firstAt;
        out[slug] = { firstAt, lastAt };
      } else if (val === true) {
        const now = Date.now();
        out[slug] = { firstAt: now, lastAt: now };
      }
    }
    return out;
  }

  function migrateState(raw) {
    const empty = { version: 2, readChapters: {}, exercises: {} };
    if (!isPlainObject(raw)) return empty;

    // Recover from v1, unversioned-but-structured, v2, or forward-compatible versions
    const srcRead = isPlainObject(raw.readChapters) ? raw.readChapters : (isPlainObject(raw.chapters) ? raw.chapters : {});
    const srcEx = isPlainObject(raw.exercises) ? raw.exercises : (isPlainObject(raw.items) ? raw.items : {});

    const readChapters = sanitizeReadChapters(srcRead);
    const exercises = {};
    for (const [id, rec] of Object.entries(srcEx)) {
      if (FORBIDDEN_KEYS.has(id) || typeof id !== "string" || !id.trim()) continue;
      const clean = sanitizeExerciseRecord(rec);
      if (clean) exercises[id] = clean;
    }

    return { version: 2, readChapters, exercises };
  }

  function loadState() {
    const raw = safeGet(STATE_KEY, null);
    if (raw) return migrateState(raw);
    // Try migrating legacy v1 key if present
    const legacyV1 = safeGet(LEGACY_KEY + ":study_v1", null) || safeGet(LEGACY_KEY + ":study", null);
    if (legacyV1 && isPlainObject(legacyV1)) {
      const migrated = migrateState(legacyV1);
      saveState(migrated);
      return migrated;
    }
    return { version: 2, readChapters: {}, exercises: {} };
  }

  function saveState(state, opts) {
    return safeSet(STATE_KEY, state, opts);
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
    try {
      localStorage.setItem(COURSE_KEY, c);
    } catch (e) {
      notifyStorageFailure("学習コースの設定を保存できませんでした。");
    }
    $$("[data-set-course]").forEach((btn) => {
      const active = btn.dataset.setCourse === c;
      btn.setAttribute("aria-pressed", String(active));
      btn.classList.toggle("active", active);
    });
    _syncingCourse = true;
    $$("details.scaffold").forEach((el) => {
      if (forceResetToggles) delete el.dataset.userToggled;
      if (!el.dataset.userToggled) {
        el.open = (c === "thorough");
      }
    });
    setTimeout(() => { _syncingCourse = false; }, 0);
    $$(".exercise[data-course='thorough']").forEach((el) => {
      el.classList.toggle("ex-optional-in-standard", c === "standard");
    });
  }

  // ---- Deterministic MCQ presentation shuffle (preserves canonical opt.id for grading)
  function hashSeed(str) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h >>> 0;
  }

  function shuffleOptionsDeterministic(options, key) {
    const arr = options.slice();
    if (arr.length <= 1) return arr;
    let state = hashSeed(String(key)) || 1;
    const nextRand = () => {
      state ^= state << 13;
      state ^= state >>> 17;
      state ^= state << 5;
      return (state >>> 0) / 4294967296;
    };
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(nextRand() * (i + 1));
      const tmp = arr[i];
      arr[i] = arr[j];
      arr[j] = tmp;
    }
    return arr;
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
      const ansObj = isPlainObject(variant.answer) ? variant.answer : { value: Number(variant.answer), tolerance: 1e-6 };
      const target = Number(ansObj.value);
      const tol = ansObj.tolerance != null ? Number(ansObj.tolerance) : 1e-6;
      const diff = val - target;
      const isCorrect = Math.abs(diff) <= tol + 1e-9;
      let wrongReason = "";
      if (!isCorrect) {
        const dir = diff > 0 ? "正解より大きい値" : "正解より小さい値";
        wrongReason = `あなたの答え <code>${escHtml(cleaned)}</code> は${dir}になっています（正解の目安：<code>${escHtml(String(target))}</code>${tol > 0.0001 ? ` ± ${escHtml(String(tol))}` : ""}）。途中計算のどの段階でずれたか確認しましょう。`;
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

  // ---- Spaced repetition scheduling (calendar-day due boundary, hint distinction, anti-gaming)
  function recordOutcome(state, ex, { correct, variantIndex, mode = "auto", usedHint = false, now = Date.now(), note = null }) {
    const safeNow = isValidTs(now) ? now : Date.now();
    const prevRaw = state.exercises[ex.id];
    const prev = prevRaw
      ? sanitizeExerciseRecord(prevRaw)
      : {
          chapter: ex.chapter,
          concept: ex.concept,
          conceptLabel: ex.conceptLabel || ex.concept,
          level: ex.level,
          type: ex.type,
          attempts: 0,
          correct: 0,
          wrong: 0,
          unhintedCorrect: 0,
          hintedCorrect: 0,
          streak: 0,
          lastVariant: -1,
          solvedVariants: [],
          unhintedVariants: [],
          lastUsedHint: false,
          lastResult: null,
          lastAt: null,
          intervalDays: 0,
          nextReviewAt: null,
          reviewedAfterDue: false,
          weak: false,
          note: "",
        };

    const wasDue = Boolean(isValidTs(prev.nextReviewAt) && prev.nextReviewAt <= safeNow && prev.attempts > 0);
    const solvedLaterDay = Boolean(isValidTs(prev.lastAt) && startOfLocalDay(safeNow) > startOfLocalDay(prev.lastAt) && prev.unhintedCorrect > 0);
    const solvedOtherDayOrDue = wasDue || solvedLaterDay;
    const sameDayRepeatSameVariant = Boolean(
      !wasDue &&
      isValidTs(prev.lastAt) &&
      sameLocalDay(prev.lastAt, safeNow) &&
      prev.solvedVariants.includes(variantIndex)
    );

    const rec = {
      ...prev,
      chapter: ex.chapter,
      concept: ex.concept,
      conceptLabel: ex.conceptLabel || ex.concept,
      level: ex.level,
      type: ex.type,
      solvedVariants: prev.solvedVariants.slice(),
      unhintedVariants: prev.unhintedVariants.slice(),
    };

    rec.attempts += 1;
    rec.lastVariant = variantIndex;
    rec.lastAt = safeNow;
    rec.lastUsedHint = Boolean(usedHint);
    if (note !== null) rec.note = String(note).slice(0, 5000);

    const dayStart = startOfLocalDay(safeNow);

    if (correct) {
      rec.correct += 1;
      if (!rec.solvedVariants.includes(variantIndex)) {
        rec.solvedVariants.push(variantIndex);
      }

      if (usedHint && mode === "auto") {
        // Hinted pass: acknowledge progress, but do NOT promote to unhinted mastery or long intervals
        rec.hintedCorrect += 1;
        rec.lastResult = "hinted_correct";
        rec.intervalDays = 1;
        rec.nextReviewAt = dayStart + DAY_MS;
        // Keep weak=true if it was weak; do NOT set reviewedAfterDue=true from a hinted answer
      } else {
        rec.unhintedCorrect += 1;
        if (!rec.unhintedVariants.includes(variantIndex)) {
          rec.unhintedVariants.push(variantIndex);
        }
        if (mode === "impl") rec.lastResult = "impl_self_reported";
        else if (mode === "self") rec.lastResult = "self_checked";
        else rec.lastResult = "correct";

        // Anti-gaming: repeating the exact same variant on the same day does NOT inflate streak/interval
        if (!sameDayRepeatSameVariant) {
          rec.streak += 1;
        } else if (rec.streak === 0) {
          rec.streak = 1;
        }

        if (solvedOtherDayOrDue) {
          rec.reviewedAfterDue = true;
          rec.weak = false;
        } else if (rec.streak >= 2 && rec.unhintedVariants.length >= 2) {
          rec.weak = false;
        }

        const idx = Math.min(Math.max(0, rec.streak - 1), INTERVALS.length - 1);
        rec.intervalDays = INTERVALS[idx];
        rec.nextReviewAt = dayStart + rec.intervalDays * DAY_MS;
      }
    } else {
      rec.wrong += 1;
      rec.streak = 0;
      rec.lastResult = "wrong";
      rec.weak = true;
      rec.reviewedAfterDue = false;
      rec.intervalDays = 1;
      rec.nextReviewAt = dayStart + DAY_MS;
    }

    state.exercises[ex.id] = rec;
    saveState(state);
    return rec;
  }

  // ---- Mastery calculation (distinguishes read / hinted / unhinted / fresh variant / spaced recall / self-report)
  function isUnhintedPass(rec) {
    if (!rec) return false;
    if (rec.unhintedCorrect > 0) return true;
    return rec.correct > 0 && rec.lastResult !== "hinted_correct" && !rec.lastUsedHint;
  }

  function isHintedOnly(rec) {
    if (!rec) return false;
    return !isUnhintedPass(rec) && (rec.hintedCorrect > 0 || rec.lastResult === "hinted_correct");
  }

  function isImplCompleted(rec) {
    if (!rec) return false;
    return rec.lastResult === "impl_self_reported" || rec.lastResult === "impl_verified" || isUnhintedPass(rec);
  }

  function computeChapterStatus(slug, chapterExercises, state, legacyDone, now = Date.now()) {
    const exList = chapterExercises || [];
    const recs = exList.map((e) => ({
      ex: { ...e, level: Number(e.level ?? e.difficulty ?? 1) },
      rec: state.exercises[e.id] || null,
    }));
    const readFlag = Boolean(state.readChapters[slug] || legacyDone.has(slug));

    const basicEx = recs.filter((x) => x.ex.level <= 2);
    const appliedEx = recs.filter((x) => x.ex.level === 3 || x.ex.level === 5);
    const implEx = recs.filter((x) => x.ex.level === 4 || x.ex.type === "code");

    const basicSolved = basicEx.filter((x) => isUnhintedPass(x.rec)).length;
    const appliedSolved = appliedEx.filter((x) => isUnhintedPass(x.rec)).length;
    const implSolved = implEx.filter((x) => isImplCompleted(x.rec)).length;

    const hintedOnlyCount = recs.filter((x) => isHintedOnly(x.rec)).length;
    const variantMasteredCount = recs.filter((x) => x.rec && Array.isArray(x.rec.unhintedVariants) && x.rec.unhintedVariants.length >= 2).length;
    const dueItems = recs.filter((x) => isDueAt(x.rec, now));
    const reviewedItems = recs.filter((x) => x.rec && x.rec.reviewedAfterDue);
    const attempted = recs.filter((x) => x.rec && x.rec.attempts > 0).length;
    const totalSolved = recs.filter((x) => isUnhintedPass(x.rec) || isImplCompleted(x.rec)).length;

    let achieved = "unstarted";
    if (readFlag || attempted > 0) {
      achieved = "read";
    }
    if (basicEx.length > 0 && basicSolved >= Math.max(1, Math.ceil(basicEx.length * 0.5))) {
      achieved = "basic_done";
    } else if (basicEx.length === 0 && totalSolved > 0) {
      achieved = "basic_done";
    }
    if (appliedEx.length > 0 && appliedSolved >= 1 && STAGES[achieved].rank >= STAGES.basic_done.rank) {
      achieved = "applied_done";
    }
    // Require basic_done (when chapter has basic exercises) so checking 1 code box doesn't skip fundamentals
    if (implEx.length > 0 && implSolved >= 1 && (basicEx.length === 0 || STAGES[achieved].rank >= STAGES.basic_done.rank)) {
      achieved = "impl_done";
    }

    let stage = achieved;
    const reviewTarget = Math.min(2, Math.max(1, totalSolved));
    if (dueItems.length > 0) {
      stage = "needs_review";
    } else if (reviewedItems.length >= reviewTarget && STAGES[achieved].rank >= STAGES.basic_done.rank) {
      stage = "reviewed";
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
      hintedOnlyCount,
      variantMasteredCount,
      dueCount: dueItems.length,
      reviewedCount: reviewedItems.length,
      readFlag,
    };
  }

  function formatRelativeDate(ts, now = Date.now()) {
    if (!isValidTs(ts)) return "未設定";
    const diffDays = Math.round((startOfLocalDay(ts) - startOfLocalDay(now)) / DAY_MS);
    if (diffDays <= 0) return "今日復習可能";
    if (diffDays === 1) return "明日（1日後）";
    return `${diffDays}日後`;
  }

  function renderExerciseStatusBadge(payload, r) {
    if (!r) return '<span class="ex-status st-unstarted">未解答</span>';
    if (r.weak) return '<span class="ex-status st-review-due">要復習（誤答あり）</span>';
    if (r.reviewedAfterDue) {
      return `<span class="ex-status st-reviewed">間隔を空けて再正解（次回：${escHtml(formatRelativeDate(r.nextReviewAt))}）</span>`;
    }
    if (payload.type === "code" && (r.lastResult === "impl_self_reported" || r.lastResult === "impl_verified")) {
      return `<span class="ex-status st-impl">自力実装・自己確認済（自己申告）</span>`;
    }
    if (payload.type === "explain" && r.lastResult === "self_checked") {
      return `<span class="ex-status st-self">自己確認済（自己申告）</span>`;
    }
    if (isHintedOnly(r)) {
      return `<span class="ex-status st-hinted">ヒント付き正解（ヒントなしで再確認推奨）</span>`;
    }
    if (Array.isArray(r.unhintedVariants) && r.unhintedVariants.length >= 2) {
      return `<span class="ex-status st-applied">初見類題で正解（自動採点済・次回：${escHtml(formatRelativeDate(r.nextReviewAt))}）</span>`;
    }
    if (isUnhintedPass(r)) {
      return `<span class="ex-status st-basic">ヒントなし正解（自動採点済・次回：${escHtml(formatRelativeDate(r.nextReviewAt))}）</span>`;
    }
    return '<span class="ex-status st-unstarted">未解答</span>';
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
      const statusBadge = renderExerciseStatusBadge(payload, r);

      const variantInfo = variants.length > 1
        ? `<span class="ex-variant-tag">問題 ${currentIdx + 1} / ${variants.length}</span>`
        : "";

      const hintsList = Array.isArray(v.hints) && v.hints.length > 0
        ? v.hints.filter(Boolean)
        : (v.hint ? [v.hint] : []);

      let bodyHtml = `<div class="ex-prompt">${v.prompt}</div>`;
      if (v.codeHtml) {
        bodyHtml += `<div class="codeblock code lang-python ex-code"><div class="code-head"><span>確認対象コード</span><button type="button" class="copy ex-copy-code">コピー</button></div><pre><code>${v.codeHtml}</code></pre></div>`;
      }

      const isChoiceLike = payload.type === "choice" || (payload.type === "predict" && Array.isArray(v.options) && v.options.length > 0);
      let displayedOptions = [];

      if (isChoiceLike) {
        displayedOptions = shuffleOptionsDeterministic(v.options, `${payload.id}:v${currentIdx}`);
        const groupName = `ex-${escHtml(payload.id)}-${currentIdx}-${Math.random().toString(36).slice(2, 6)}`;
        bodyHtml += `<fieldset class="ex-options"><legend class="sr-only">選択肢</legend>` +
          displayedOptions.map((o, idx) => {
            const dispLetter = OPT_LETTERS[idx] || String(idx + 1);
            return `<label class="ex-opt"><input type="radio" name="${groupName}" value="${escHtml(o.id)}"><span class="ex-opt-id">${dispLetter}</span><span class="ex-opt-text">${o.text}</span></label>`;
          }).join("") + `</fieldset>`;
      } else if (payload.type === "numeric") {
        const inputId = `in-${escHtml(payload.id)}-${currentIdx}`;
        bodyHtml += `<div class="ex-input-row"><label class="sr-only" for="${inputId}">数値の解答</label>` +
          `<input id="${inputId}" class="ex-input" type="text" inputmode="decimal" autocomplete="off" placeholder="${escHtml(v.placeholder || "数値を入力（例：0.665）")}">` +
          (v.unit ? `<span class="ex-unit">${escHtml(v.unit)}</span>` : "") + `</div>`;
      } else if (payload.type === "predict") {
        const inputId = `in-${escHtml(payload.id)}-${currentIdx}`;
        bodyHtml += `<div class="ex-input-row"><label class="sr-only" for="${inputId}">出力の予想</label>` +
          `<textarea id="${inputId}" class="ex-textarea ex-mono" rows="2" placeholder="${escHtml(v.placeholder || "実行結果として表示される出力を予想して入力")}"></textarea></div>`;
      } else if (payload.type === "explain") {
        const savedNote = r && r.note ? r.note : "";
        const noteId = `note-${escHtml(payload.id)}`;
        bodyHtml += `<p class="ex-scope-note"><strong>検証できる範囲（自己申告）：</strong>自由記述の自動採点は行いません。まず自分の言葉で理由を書いてから、確認ポイントと解答例に照らして自己確認してください。</p>` +
          `<label class="sr-only" for="${noteId}">自分の説明メモ</label>` +
          `<textarea id="${noteId}" class="ex-textarea" rows="3" placeholder="まず自分の言葉で理由や仕組みを書いてみよう（このブラウザにメモ保存されます）">${escHtml(savedNote)}</textarea>`;
      } else if (payload.type === "code") {
        bodyHtml += `<p class="ex-scope-note"><strong>検証できる範囲（自己申告）：</strong>この静的サイト上ではPythonを実行しません。下のスタートコードをもとにColabで自力実装し、<strong>検算テストコード（assert）</strong>をすべて通したうえで自己確認として記録してください。</p>`;
        if (v.starterCodeHtml) {
          bodyHtml += `<div class="codeblock code lang-python ex-code"><div class="code-head"><span>スタートコード（これをColabで完成させる）</span><button type="button" class="copy ex-copy-starter">コピー</button></div><pre><code>${v.starterCodeHtml}</code></pre></div>`;
        }
        if (v.colabCheckHtml) {
          bodyHtml += `<div class="codeblock code lang-python ex-code"><div class="code-head"><span>Colab検算用テスト（全assert通過を確認）</span><button type="button" class="copy ex-copy-check">コピー</button></div><pre><code>${v.colabCheckHtml}</code></pre></div>`;
        }
      }

      const hintBtnLabel = hintsList.length > 1
        ? `ヒント 1 / ${hintsList.length} を表示`
        : "ヒントを見る";

      const actionsHtml = (isChoiceLike || payload.type === "numeric" || payload.type === "predict")
        ? `<div class="ex-actions">
            <button type="button" class="btn primary ex-submit">解答を確認する</button>
            ${hintsList.length ? `<button type="button" class="btn ex-hint-btn" aria-expanded="false">${hintBtnLabel}</button>` : ""}
            ${variants.length > 1 ? '<button type="button" class="btn ex-switch-btn">別の類題に切り替え</button>' : ""}
          </div>`
        : `<div class="ex-actions">
            <button type="button" class="btn primary ex-reveal-btn" aria-expanded="false">${payload.type === "code" ? "解答例と確認観点を開く（まず自力で挑戦！）" : "解答例と確認ポイントを開く"}</button>
            ${hintsList.length ? `<button type="button" class="btn ex-hint-btn" aria-expanded="false">${hintBtnLabel}</button>` : ""}
            ${variants.length > 1 ? '<button type="button" class="btn ex-switch-btn">別の類題に切り替え</button>' : ""}
          </div>`;

      el.innerHTML = `
        <div class="ex-head">
          <div class="ex-meta">
            <span class="ex-num">確認問題 ${escHtml(String(payload.num || ""))}</span>
            <span class="ex-badge ex-lvl-${escHtml(String(payload.level || 1))}">${escHtml(lvlLabel)}</span>
            <span class="ex-concept">${escHtml(payload.conceptLabel || payload.concept)}</span>
            ${courseBadge}${reviewBadges}${variantInfo}
          </div>
          ${statusBadge}
        </div>
        ${bodyHtml}
        ${actionsHtml}
        ${hintsList.length ? '<div class="ex-hint" hidden></div>' : ""}
        <div class="ex-feedback" aria-live="polite" hidden></div>
      `;

      // Wire copy buttons inside exercise
      const copyCode = $(".ex-copy-code", el);
      if (copyCode && v.code) copyCode.addEventListener("click", () => copyText(v.code, copyCode));
      const copyStarter = $(".ex-copy-starter", el);
      if (copyStarter && v.starterCode) copyStarter.addEventListener("click", () => copyText(v.starterCode, copyStarter));
      const copyCheck = $(".ex-copy-check", el);
      if (copyCheck && v.colabCheck) copyCheck.addEventListener("click", () => copyText(v.colabCheck, copyCheck));

      // Progressive hints reveal + hint usage tracking
      let revealedHints = 0;
      let usedHintThisAttempt = false;
      const hintBtn = $(".ex-hint-btn", el);
      const hintBox = $(".ex-hint", el);
      if (hintBtn && hintBox && hintsList.length) {
        hintBtn.addEventListener("click", () => {
          if (revealedHints < hintsList.length) {
            revealedHints += 1;
            usedHintThisAttempt = true;
            hintBox.hidden = false;
            hintBox.innerHTML = hintsList.slice(0, revealedHints).map((hText, idx) => {
              const title = hintsList.length > 1 ? `ヒント ${idx + 1} / ${hintsList.length}：` : "ヒント：";
              return `<div class="ex-hint-item"><b>${title}</b>${hText}</div>`;
            }).join("");
            hintBtn.setAttribute("aria-expanded", "true");
            if (revealedHints < hintsList.length) {
              hintBtn.textContent = `ヒント ${revealedHints + 1} / ${hintsList.length} を表示`;
            } else {
              hintBtn.textContent = "ヒントを閉じる";
            }
          } else {
            const willHide = !hintBox.hidden;
            hintBox.hidden = willHide;
            hintBtn.setAttribute("aria-expanded", String(!willHide));
            hintBtn.textContent = willHide ? "ヒントをもう一度見る" : "ヒントを閉じる";
          }
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

      // Wire auto-graded submission (deduplicated per rendered view to prevent streak farming)
      const submitBtn = $(".ex-submit", el);
      const fb = $(".ex-feedback", el);
      let submittedThisView = false;
      if (submitBtn) {
        const doSubmit = () => {
          if (submittedThisView) return;
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

          submittedThisView = true;
          submitBtn.disabled = true;
          submitBtn.textContent = "確認済み";

          const updated = recordOutcome(loadState(), payload, {
            correct: res.correct,
            variantIndex: currentIdx,
            mode: "auto",
            usedHint: usedHintThisAttempt,
          });

          const sectionHref = payload.sectionAnchor ? `${payload.chapter}.html${payload.sectionAnchor}` : `${payload.chapter}.html`;
          const sectionLink = payload.section
            ? `<a href="${escHtml(sectionHref)}">${escHtml(payload.section)}</a>`
            : `<a href="${escHtml(sectionHref)}">該当する章の解説へ</a>`;
          const stepsHtml = (v.steps && v.steps.length)
            ? `<div class="fb-block"><b>途中計算・トレース：</b><ol>${v.steps.map((s) => `<li>${s}</li>`).join("")}</ol></div>`
            : "";
          const altHtml = v.altExample
            ? `<div class="fb-block"><b>別の具体例：</b><p>${v.altExample}</p></div>`
            : "";
          const retryBtnHtml = variants.length > 1
            ? `<button type="button" class="btn primary ex-retry-variant">${res.correct ? (usedHintThisAttempt ? "ヒントなしで類題に挑戦する →" : "類題（別の条件）で定着を確かめる →") : "類題で再挑戦する →"}</button>`
            : `<button type="button" class="btn ex-retry-same">もう一度解き直す</button>`;

          fb.hidden = false;
          if (res.correct && usedHintThisAttempt) {
            fb.className = "ex-feedback fb-hinted";
            fb.innerHTML = `
              <p class="fb-title">✓ 正解！（ヒント使用） <small>（次回の復習目安：${escHtml(formatRelativeDate(updated.nextReviewAt))}）</small></p>
              <p class="fb-sub">ヒント付きで正解できました。自力での定着として記録するには、ヒントを使わずに類題または翌日以降に再挑戦しましょう。</p>
              <div class="fb-block"><b>正しい考え方：</b><p>${v.reasoning}</p></div>
              ${stepsHtml}
              ${altHtml}
              <div class="fb-foot">${retryBtnHtml}</div>
            `;
          } else if (res.correct) {
            const noteMsg = updated.reviewedAfterDue
              ? "時間を空けた復習での再確認（自動採点済）が完了しました！"
              : (updated.unhintedVariants.length >= 2
                  ? "別の条件の初見類題でもヒントなしで正解できました。さらに日を空けて復習すると長期定着を確かめられます。"
                  : "ヒントなしで1回目の確認をクリアしました（1回の正解だけで完全理解とはせず、類題や日を空けた復習で定着を確かめます）。");
            fb.className = "ex-feedback fb-ok";
            fb.innerHTML = `
              <p class="fb-title">✓ 正解！（自動採点済・ヒントなし） <small>（次回の復習目安：${escHtml(formatRelativeDate(updated.nextReviewAt))}）</small></p>
              <p class="fb-sub">${escHtml(noteMsg)}</p>
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

          const headStatus = $(".ex-status", el);
          if (headStatus) headStatus.outerHTML = renderExerciseStatusBadge(payload, updated);

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
          refreshGlobalUI();
          if (typeof opts.onAnswer === "function") opts.onAnswer(updated);
        };

        submitBtn.addEventListener("click", doSubmit);
        const numInput = $(".ex-input", el);
        if (numInput) {
          numInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") { e.preventDefault(); doSubmit(); }
          });
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
              <button type="button" class="btn primary ex-mark-ok">${payload.type === "code" ? "✓ Colabで検算テスト通過＆観点を確認した（自己申告）" : "✓ 確認観点どおり説明できた（自己申告）"}</button>
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
              usedHint: usedHintThisAttempt,
              note: noteText,
            });
            msg.textContent = payload.type === "code"
              ? `自力実装の検算確認を記録しました（自己申告・次回の復習目安：${formatRelativeDate(recNew.nextReviewAt)}）。`
              : `自己確認を記録しました（自己申告・次回の復習目安：${formatRelativeDate(recNew.nextReviewAt)}）。`;
            const headStatus = $(".ex-status", el);
            if (headStatus) headStatus.outerHTML = renderExerciseStatusBadge(payload, recNew);
            refreshGlobalUI();
            if (typeof opts.onAnswer === "function") opts.onAnswer(recNew);
          });

          markNg.addEventListener("click", () => {
            const noteText = noteEl ? noteEl.value : null;
            const recNew = recordOutcome(loadState(), payload, {
              correct: false,
              variantIndex: currentIdx,
              mode: "self",
              note: noteText,
            });
            msg.textContent = "「復習が必要」として記録しました。関連する節を読み直して再挑戦しましょう。";
            const headStatus = $(".ex-status", el);
            if (headStatus) headStatus.outerHTML = renderExerciseStatusBadge(payload, recNew);
            refreshGlobalUI();
          });
        });
      }
    }

    draw();
  }

  // ---- Metadata loading: slim exercises-meta.json (~22KB) on normal pages, full exercises-index.json ONLY on review.html
  let cachedMeta = null;
  let cachedIndex = null;
  let validIdsSet = null;

  function setMetaFromIndex(index) {
    if (!index || !Array.isArray(index.chapters)) return null;
    const bySlug = {};
    const ids = [];
    for (const ch of index.chapters) {
      bySlug[ch.slug] = (ch.exercises || []).map((e) => {
        ids.push(e.id);
        return { id: e.id, level: Number(e.level ?? e.difficulty ?? 1), difficulty: Number(e.difficulty ?? e.level ?? 1), type: e.type || "choice" };
      });
    }
    cachedMeta = { version: 2, total: ids.length, ids, bySlug };
    validIdsSet = new Set(ids);
    return cachedMeta;
  }

  async function loadMeta() {
    if (cachedMeta) return cachedMeta;
    try {
      const res = await fetch("exercises-meta.json");
      if (res.ok) {
        const meta = await res.json();
        if (meta && isPlainObject(meta.bySlug) && Array.isArray(meta.ids)) {
          cachedMeta = meta;
          validIdsSet = new Set(meta.ids);
          return cachedMeta;
        }
      }
    } catch (e) {}
    // Graceful fallback if exercises-meta.json is not yet built
    const idx = await loadIndex();
    return setMetaFromIndex(idx);
  }

  async function loadIndex() {
    if (cachedIndex) return cachedIndex;
    try {
      const res = await fetch("exercises-index.json");
      if (res.ok) {
        cachedIndex = await res.json();
        setMetaFromIndex(cachedIndex);
      }
    } catch (e) {}
    return cachedIndex;
  }

  function countGlobalDue(state, now = Date.now(), allowedIds = validIdsSet) {
    let n = 0;
    for (const [id, rec] of Object.entries(state.exercises || {})) {
      if (allowedIds && !allowedIds.has(id)) continue;
      if (isDueAt(rec, now)) n++;
    }
    return n;
  }

  function refreshGlobalUI() {
    const state = loadState();
    const legacyDone = loadLegacyDone();
    const now = Date.now();
    const due = countGlobalDue(state, now, validIdsSet);

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
        parts.push(`基礎（ヒントなし） ${st.basicSolved}/${st.basicTotal}`);
        if (st.appliedTotal) parts.push(`応用 ${st.appliedSolved}/${st.appliedTotal}`);
        if (st.implTotal) parts.push(`自力実装（自己申告） ${st.implSolved}/${st.implTotal}`);
        if (st.hintedOnlyCount) parts.push(`ヒント付きのみ ${st.hintedOnlyCount}問`);
        if (st.variantMasteredCount) parts.push(`類題確認済 ${st.variantMasteredCount}問`);
        if (st.dueCount) parts.push(`要復習 ${st.dueCount}件`);
        else if (st.reviewedCount) parts.push(`間隔再確認 ${st.reviewedCount}件`);
        detail.textContent = parts.join(" · ");
      }
    }

    // Update sidebar & home map chapter indicators using slim exercises-meta.json (or exercises-index)
    if (cachedMeta && isPlainObject(cachedMeta.bySlug)) {
      $$("a[data-slug]").forEach((a) => {
        const slug = a.dataset.slug;
        const exList = cachedMeta.bySlug[slug];
        if (!Array.isArray(exList)) return;
        const st = computeChapterStatus(slug, exList, state, legacyDone, now);
        a.dataset.stage = st.stage;
        const labelText = (a.textContent || slug).trim();
        a.title = `${labelText}：${st.meta.label}`;
      });
    }
  }

  // ---- Strict JSON backup import validator (never mutates localStorage before full validation)
  function validateAndSanitizeImport(parsed) {
    if (!isPlainObject(parsed)) throw new Error("トップレベルがJSONオブジェクトではありません。");

    // Accept either backup bundle `{ study: {...} }` or direct study state `{ version, exercises }`
    const hasStudyBundle = isPlainObject(parsed.study);
    const studyRaw = hasStudyBundle ? parsed.study : parsed;

    if (!isPlainObject(studyRaw)) {
      throw new Error("study データが見つかりません。");
    }
    const ver = studyRaw.version;
    if (ver !== 2 && ver !== 1) {
      throw new Error("対応していないバックアップ形式（version）です。");
    }
    if (studyRaw.exercises != null && !isPlainObject(studyRaw.exercises)) {
      throw new Error("exercises フィールドの形式が不正です。");
    }
    if (studyRaw.readChapters != null && !isPlainObject(studyRaw.readChapters)) {
      throw new Error("readChapters フィールドの形式が不正です。");
    }

    // Validate every exercise record entry is a plain object (reject corrupt/null entries)
    for (const [k, v] of Object.entries(studyRaw.exercises || {})) {
      if (FORBIDDEN_KEYS.has(k)) throw new Error("不正なキーが含まれています。");
      if (!isPlainObject(v)) throw new Error(`演習レコード（${k}）の形式が不正です。`);
    }

    const cleanStudy = migrateState(studyRaw);

    let cleanLegacyDone = null;
    if (hasStudyBundle && parsed.legacyDone !== undefined) {
      if (!Array.isArray(parsed.legacyDone)) throw new Error("legacyDone の形式が不正です。");
      cleanLegacyDone = parsed.legacyDone.filter((s) => typeof s === "string" && /^[a-z0-9-]+$/i.test(s));
    }

    let cleanLegacyChecks = null;
    if (hasStudyBundle && parsed.legacyChecks !== undefined) {
      if (!isPlainObject(parsed.legacyChecks)) throw new Error("legacyChecks の形式が不正です。");
      cleanLegacyChecks = {};
      for (const [k, v] of Object.entries(parsed.legacyChecks)) {
        if (!FORBIDDEN_KEYS.has(k) && typeof k === "string" && k.length <= 120) {
          cleanLegacyChecks[k] = Boolean(v);
        }
      }
    }

    const cleanCourse = hasStudyBundle && (parsed.course === "standard" || parsed.course === "thorough")
      ? parsed.course
      : null;

    return {
      study: cleanStudy,
      legacyDone: cleanLegacyDone,
      legacyChecks: cleanLegacyChecks,
      course: cleanCourse,
    };
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
      const validEntries = Object.entries(state.exercises).filter(([id]) => byId.has(id));
      const solvedUnhinted = validEntries.filter(([, r]) => isUnhintedPass(r) || isImplCompleted(r)).length;
      const hintedOnlyTotal = validEntries.filter(([, r]) => isHintedOnly(r)).length;
      const variantMasteredTotal = validEntries.filter(([, r]) => Array.isArray(r.unhintedVariants) && r.unhintedVariants.length >= 2).length;

      summaryEl.innerHTML = `
        <div class="stage-grid">
          ${Object.entries(STAGES).map(([k, info]) =>
            `<div class="stage-card ${escHtml(info.cls)}"><span class="sc-num">${Number(counts[k]) || 0}</span><span class="sc-name">${escHtml(info.label)}</span></div>`
          ).join("")}
        </div>
        <p class="dash-totals">全 ${Number(index.chapters.length)} 章 ／ 収録確認問題 ${Number(totalEx)} 問（自力正解・自己確認済 ${Number(solvedUnhinted)} 問 · ヒント付きのみ ${Number(hintedOnlyTotal)} 問 · 初見類題クリア ${Number(variantMasteredTotal)} 問）</p>
      `;

      // 2. Due reviews
      const dueEl = $("#dash-due");
      const dueRecs = validEntries
        .filter(([, r]) => isDueAt(r, now))
        .sort((a, b) => (a[1].weak === b[1].weak ? (Number(a[1].nextReviewAt) || 0) - (Number(b[1].nextReviewAt) || 0) : (a[1].weak ? -1 : 1)));

      const upcomingRecs = validEntries
        .filter(([, r]) => !r.weak && isValidTs(r.nextReviewAt) && r.nextReviewAt > now)
        .sort((a, b) => a[1].nextReviewAt - b[1].nextReviewAt);

      if (dueRecs.length === 0) {
        dueEl.innerHTML = `<p class="empty-msg">現在、期限が来ている復習問題はありません。${upcomingRecs.length ? `（予定済み ${Number(upcomingRecs.length)} 問。次の復習は ${escHtml(formatRelativeDate(upcomingRecs[0][1].nextReviewAt, now))} です）` : "まずは第1章の確認問題から挑戦してみましょう！"}</p>` +
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
        dueEl.innerHTML = `<p>今すぐ復習をおすすめする問題が <strong>${Number(dueRecs.length)} 件</strong> あります（丸暗記を防ぐため、前回と異なる類題を優先表示します）。</p><div id="due-list"></div>`;
        const list = $("#due-list", dueEl);
        dueRecs.slice(0, 5).forEach(([id], idx) => {
          const ex = { ...byId.get(id), num: idx + 1 };
          const sec = document.createElement("section");
          sec.className = "exercise";
          list.appendChild(sec);
          mountExercise(sec, ex, { preferFresh: true, onAnswer: () => renderDashboard() });
        });
      }

      // 3. Weak concepts (strictly escaped & number-coerced to prevent imported DOM XSS)
      const weakEl = $("#dash-weak");
      const weakItems = validEntries
        .filter(([, r]) => r.weak || Number(r.wrong) > 0)
        .sort((a, b) => (Number(b[1].wrong) || 0) - (Number(a[1].wrong) || 0));
      if (!weakItems.length) {
        weakEl.innerHTML = `<p class="empty-msg">誤答が記録された概念はまだありません。間違えた問題はここに自動集計され、該当する節へすぐ戻れます。</p>`;
      } else {
        weakEl.innerHTML = `<ul class="weak-list">` + weakItems.map(([id, r]) => {
          const ex = byId.get(id);
          const ch = bySlug.get(ex.chapter);
          const href = `${ex.chapter}.html${ex.sectionAnchor || ""}`;
          const wrongCnt = Number(r.wrong) || 0;
          const correctCnt = Number(r.correct) || 0;
          const chNum = ch ? Number(ch.num) : "?";
          return `<li>
            <div><strong>${escHtml(ex.conceptLabel || ex.concept)}</strong> <small>（第${escHtml(String(chNum))}章 · 誤答 ${wrongCnt}回 / 正解 ${correctCnt}回）</small></div>
            <div class="weak-actions"><a href="${escHtml(href)}">解説を読む</a> · <a href="${escHtml(ex.chapter)}.html#ex-${escHtml(id)}">問題へ</a></div>
          </li>`;
        }).join("") + `</ul>`;
      }

      // 4. Concept chains
      const chainsEl = $("#dash-chains");
      chainsEl.innerHTML = (index.reviewChains || []).map((chain) => {
        const nodes = (chain.chapters || []).map((slug) => {
          const item = chStatuses.find((x) => x.ch.slug === slug);
          if (!item) return "";
          return `<a class="chain-node ${escHtml(item.st.meta.cls)}" href="${escHtml(slug)}.html"><b>第${Number(item.ch.num)}章 ${escHtml(item.ch.short)}</b><span>${escHtml(item.st.meta.label)}</span></a>`;
        }).join('<span class="chain-arrow" aria-hidden="true">→</span>');
        return `<div class="chain-row"><p class="chain-title">${escHtml(chain.title)}</p><div class="chain-nodes">${nodes}</div></div>`;
      }).join("");

      // 5. Chapter breakdown table (wrapped in .table-wrap for accessible horizontal scrolling)
      const chEl = $("#dash-chapters");
      chEl.innerHTML = `<div class="table-wrap"><table><thead><tr><th>章</th><th>状態</th><th>基礎（自力）</th><th>応用</th><th>自力実装（自己申告）</th><th>要復習</th></tr></thead><tbody>` +
        chStatuses.map(({ ch, st }) => `<tr>
          <td><a href="${escHtml(ch.slug)}.html">第${Number(ch.num)}章 ${escHtml(ch.title)}</a></td>
          <td><span class="ms-stage ${escHtml(st.meta.cls)}">${escHtml(st.meta.label)}</span></td>
          <td>${Number(st.basicSolved)}/${Number(st.basicTotal)}</td>
          <td>${Number(st.appliedSolved)}/${Number(st.appliedTotal)}</td>
          <td>${Number(st.implSolved)}/${Number(st.implTotal)}</td>
          <td>${Number(st.dueCount)}</td>
        </tr>`).join("") + `</tbody></table></div>`;
    }

    renderDashboard();

    // Backup export / import / reset
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
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "tsukuru-llm-history.json";
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000); // Defer revoke for Safari/mobile compatibility
        if (statusMsg) statusMsg.textContent = "学習履歴をJSONファイルとして保存しました。";
      });
    }

    const importInput = $("#import-history");
    if (importInput) {
      importInput.addEventListener("change", async () => {
        const file = importInput.files && importInput.files[0];
        if (!file) return;
        try {
          if (file.size > MAX_IMPORT_BYTES) {
            throw new Error("ファイルサイズが大きすぎます（上限 2MB）。");
          }
          const parsed = JSON.parse(await file.text());
          const clean = validateAndSanitizeImport(parsed);

          // Snapshot existing data so we can roll back if localStorage quota fails mid-import
          const prevStudy = safeGet(STATE_KEY, null);
          const prevDone = safeGet(LEGACY_KEY + ":done", null);
          const prevChecks = safeGet(LEGACY_KEY + ":checks", null);

          const okStudy = saveState(clean.study, { silent: true });
          const okDone = clean.legacyDone !== null ? safeSet(LEGACY_KEY + ":done", clean.legacyDone, { silent: true }) : true;
          const okChecks = clean.legacyChecks !== null ? safeSet(LEGACY_KEY + ":checks", clean.legacyChecks, { silent: true }) : true;

          if (!okStudy || !okDone || !okChecks) {
            if (prevStudy !== null) saveState(prevStudy, { silent: true });
            if (prevDone !== null) safeSet(LEGACY_KEY + ":done", prevDone, { silent: true });
            if (prevChecks !== null) safeSet(LEGACY_KEY + ":checks", prevChecks, { silent: true });
            notifyStorageFailure("復元データの保存に失敗しました（ストレージ容量上限またはプライベートモード）。");
            if (statusMsg) statusMsg.textContent = "保存領域に書き込めなかったため、復元を中止しました（元の履歴は保持されています）。";
            importInput.value = "";
            return;
          }

          if (clean.course) applyCourse(clean.course);
          window.dispatchEvent(new CustomEvent("tsukuru:reset-all"));
          renderDashboard();
          refreshGlobalUI();
          if (statusMsg) statusMsg.textContent = "学習履歴を復元しました。";
        } catch (e) {
          const detail = e && e.message ? `（${e.message}）` : "";
          if (statusMsg) statusMsg.textContent = `読み込みに失敗しました。正しいバックアップJSONファイルか確認してください${detail}。既存の履歴は変更されていません。`;
        }
        importInput.value = "";
      });
    }

    const resetBtn = $("#reset-history");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        const confirmed = confirm(
          "このブラウザに保存されたすべての学習履歴（確認問題の解答履歴・復習予定・章の読了チェック・チェックリスト・前回の続き）をリセットしますか？\n※必要な場合は、先に「学習履歴をJSONで保存」でバックアップを取ってください。"
        );
        if (!confirmed) return;
        const ok = saveState({ version: 2, readChapters: {}, exercises: {} });
        safeRemove(LEGACY_KEY + ":done");
        safeRemove(LEGACY_KEY + ":checks");
        safeRemove(LEGACY_KEY + ":last");
        safeRemove(LEGACY_KEY + ":study_v1");
        window.dispatchEvent(new CustomEvent("tsukuru:reset-all"));
        renderDashboard();
        refreshGlobalUI();
        if (statusMsg) {
          statusMsg.textContent = ok
            ? "すべての学習履歴をリセットしました。"
            : "リセットの保存に失敗しました（ブラウザのストレージ制限をご確認ください）。";
        }
      });
    }
  }

  // ---- Mark current chapter as read when opened & scrolled, synced with app.js [data-done]
  function initChapterReadTracking() {
    const page = document.body.dataset.page;
    window.addEventListener("tsukuru:done-toggle", (e) => {
      const detail = e && e.detail;
      if (!detail || typeof detail.slug !== "string") return;
      const state = loadState();
      if (detail.done) {
        const now = Date.now();
        state.readChapters[detail.slug] = state.readChapters[detail.slug]
          ? { ...state.readChapters[detail.slug], lastAt: now }
          : { firstAt: now, lastAt: now };
      } else {
        delete state.readChapters[detail.slug];
      }
      saveState(state);
      refreshGlobalUI();
    });

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
    setTimeout(checkScroll, 800);
  }

  // ---- Init
  document.addEventListener("DOMContentLoaded", () => {
    $$("[data-set-course]").forEach((btn) => {
      btn.addEventListener("click", () => applyCourse(btn.dataset.setCourse, true));
    });
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

    if ($("#dash-summary")) {
      initReviewDashboard().then(() => refreshGlobalUI());
    } else {
      loadMeta().then(() => refreshGlobalUI());
    }
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
    migrateState,
    validateAndSanitizeImport,
    shuffleOptionsDeterministic,
    getCourse,
    applyCourse,
    normalizeNumberString,
    normalizeTextOutput,
    formatRelativeDate,
  };
})();
