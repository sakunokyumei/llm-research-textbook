// ブラウザで動くミニGPT（第24章）。第12章の minigpt.py と同じ計算を JavaScript で書いたもの。
// 使い方： const model = await load("model/soseki-gpt.json");
//         await model.generate("吾輩は", 100, 0.8, ch => ..., Math.random, { signal, onInfo });

const nowMs = () => (typeof performance !== "undefined" && typeof performance.now === "function" ? performance.now() : Date.now());
const yieldFrame = () => new Promise((r) => setTimeout(r, 0));

function b64ToBytes(b64) {
  if (typeof atob === "function") {
    const s = atob(b64);
    const out = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
    return out;
  }
  return new Uint8Array(Buffer.from(b64, "base64"));   // Node.js でテストするとき
}

// 量子化された重み（int8 ＋ 行ごとの縮尺）を Float32Array に戻す
function dequantize(w) {
  if (w.f32) return { shape: w.shape, data: new Float32Array(b64ToBytes(w.f32).buffer) };
  const q = new Int8Array(b64ToBytes(w.i8).buffer);
  const scale = new Float32Array(b64ToBytes(w.scale).buffer);
  const [rows, cols] = w.shape;
  const data = new Float32Array(rows * cols);
  for (let r = 0; r < rows; r++) {
    const off = r * cols;
    const sc = scale[r];
    for (let c = 0; c < cols; c++) data[off + c] = q[off + c] * sc;
  }
  return { shape: w.shape, data };
}

// y = W x + b（W は [出力, 入力] の形。PyTorch の nn.Linear と同じ向き）
function linear(W, b, x) {
  const [rows, cols] = W.shape;
  const y = new Float32Array(rows);
  const wData = W.data;
  const bData = b ? b.data : null;
  for (let r = 0; r < rows; r++) {
    let s = bData ? bData[r] : 0;
    const off = r * cols;
    for (let c = 0; c < cols; c++) s += wData[off + c] * x[c];
    y[r] = s;
  }
  return y;
}

function layerNorm(x, w, b, eps = 1e-5) {
  const n = x.length;
  let mean = 0;
  for (let i = 0; i < n; i++) mean += x[i];
  mean /= n;
  let vari = 0;
  for (let i = 0; i < n; i++) {
    const d = x[i] - mean;
    vari += d * d;
  }
  vari /= n;
  const inv = 1 / Math.sqrt(vari + eps);
  const out = new Float32Array(n);
  const wd = w.data;
  const bd = b.data;
  for (let i = 0; i < n; i++) out[i] = (x[i] - mean) * inv * wd[i] + bd[i];
  return out;
}

// GELU（PyTorch の nn.GELU と同じ、誤差関数 erf を使う版）
function erf(x) {
  const s = Math.sign(x), a = Math.abs(x), t = 1 / (1 + 0.3275911 * a);
  const y = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-a * a);
  return s * y;
}
const gelu = (x) => 0.5 * x * (1 + erf(x / Math.SQRT2));

function buildModel(cfg, vocab, W) {
  if (!cfg || !Array.isArray(vocab) || vocab.length === 0) {
    throw new Error("モデルデータの形式が不正です。");
  }
  const stoi = new Map(vocab.map((ch, i) => [ch, i]));
  const C = cfg.n_embd, H = cfg.n_head, hs = C / H, L = cfg.n_layer, T = cfg.block_size;
  const invSqrtHs = 1 / Math.sqrt(hs);
  const nParams = Object.values(W).reduce((s, w) => s + w.data.length, 0);

  // 安全なフォールバック開始文字（「。」が無いカスタムモデルでも NaN にならない）
  const fallbackCandidates = ["。", "\n", " "];
  let fallbackId = 0;
  for (const ch of fallbackCandidates) {
    if (stoi.has(ch)) { fallbackId = stoi.get(ch); break; }
  }
  const fallbackChar = vocab[fallbackId];

  function analyzeInput(start) {
    const chars = Array.from(String(start ?? ""));
    const keptChars = [];
    const droppedChars = [];
    const ids = [];
    for (const ch of chars) {
      if (stoi.has(ch)) {
        keptChars.push(ch);
        ids.push(stoi.get(ch));
      } else {
        droppedChars.push(ch);
      }
    }
    const usedFallback = ids.length === 0;
    if (usedFallback) ids.push(fallbackId);
    const truncated = ids.length > T;
    return {
      ids: ids.slice(-T),
      keptChars,
      droppedChars,
      usedFallback,
      fallbackChar,
      truncated,
    };
  }

  // 1トークン分の計算。cache[layer][head] = {k: [], v: []} に過去の Key と Value を貯める（第16章のKVキャッシュ）
  function step(id, pos, cache) {
    const tokData = W["tok_emb.weight"].data;
    const posData = W["pos_emb.weight"].data;
    const x = new Float32Array(C);
    const tokOff = id * C;
    const posOff = pos * C;
    for (let i = 0; i < C; i++) x[i] = tokData[tokOff + i] + posData[posOff + i];
    for (let l = 0; l < L; l++) {
      const p = `blocks.${l}.`;
      const h = layerNorm(x, W[p + "ln1.weight"], W[p + "ln1.bias"]);
      const heads = new Float32Array(C);
      for (let j = 0; j < H; j++) {
        const hp = `${p}attn.heads.${j}.`;
        const q = linear(W[hp + "query.weight"], null, h);
        const k = linear(W[hp + "key.weight"], null, h);
        const v = linear(W[hp + "value.weight"], null, h);
        const c = cache[l][j];
        c.k.push(k); c.v.push(v);
        const len = c.k.length;
        const scores = new Float32Array(len);
        let maxS = -Infinity;
        for (let t = 0; t < len; t++) {
          const kk = c.k[t];
          let s = 0;
          for (let i = 0; i < hs; i++) s += q[i] * kk[i];
          s *= invSqrtHs;
          scores[t] = s;
          if (s > maxS) maxS = s;
        }
        let sum = 0;
        for (let t = 0; t < len; t++) {
          const ev = Math.exp(scores[t] - maxS);
          scores[t] = ev;
          sum += ev;
        }
        const hOff = j * hs;
        for (let t = 0; t < len; t++) {
          const w = scores[t] / sum;
          const vv = c.v[t];
          for (let i = 0; i < hs; i++) heads[hOff + i] += w * vv[i];
        }
      }
      const a = linear(W[p + "attn.proj.weight"], W[p + "attn.proj.bias"], heads);
      for (let i = 0; i < C; i++) x[i] += a[i];                          // 残差接続
      const h2 = layerNorm(x, W[p + "ln2.weight"], W[p + "ln2.bias"]);
      const f1 = linear(W[p + "ffwd.net.0.weight"], W[p + "ffwd.net.0.bias"], h2);
      for (let i = 0; i < f1.length; i++) f1[i] = gelu(f1[i]);
      const f2 = linear(W[p + "ffwd.net.2.weight"], W[p + "ffwd.net.2.bias"], f1);
      for (let i = 0; i < C; i++) x[i] += f2[i];                         // 残差接続
    }
    const out = layerNorm(x, W["ln_f.weight"], W["ln_f.bias"]);
    return linear(W["lm_head.weight"], W["lm_head.bias"], out);         // 次の文字の点数（ロジット）
  }

  const newCache = () => Array.from({ length: L }, () => Array.from({ length: H }, () => ({ k: [], v: [] })));

  // ids をまとめて流し込み、最後の位置のロジットを返す（同期API・テスト互換）
  function run(ids) {
    const cache = newCache();
    let logits = null;
    for (let pos = 0; pos < ids.length; pos++) {
      logits = step(ids[pos], pos, cache);
    }
    return { logits, cache };
  }

  // メインスレッドを固めない非同期 prefill（進捗中に定期的に制御を戻し、中断も即座に検知）
  async function runAsync(ids, signal) {
    const cache = newCache();
    let logits = null;
    let lastYield = nowMs();
    for (let pos = 0; pos < ids.length; pos++) {
      if (signal && signal.aborted) return { logits, cache, aborted: true };
      logits = step(ids[pos], pos, cache);
      if (nowMs() - lastYield >= 12) {
        await yieldFrame();
        lastYield = nowMs();
      }
    }
    return { logits, cache, aborted: false };
  }

  function sample(logits, temperature, rand) {
    const safeTemp = Number.isFinite(temperature) && temperature > 0 ? Math.max(0.01, temperature) : 0.8;
    const len = logits.length;
    const z = new Float32Array(len);
    let m = -Infinity;
    for (let i = 0; i < len; i++) {
      const v = logits[i] / safeTemp;
      z[i] = v;
      if (v > m) m = v;
    }
    let sum = 0;
    for (let i = 0; i < len; i++) {
      const ev = Math.exp(z[i] - m);
      z[i] = ev;
      sum += ev;
    }
    let r = rand() * sum;
    for (let i = 0; i < len; i++) {
      r -= z[i];
      if (r <= 0) return i;
    }
    return len - 1;
  }

  async function generate(start, n, temperature = 0.8, onToken = () => {}, randOrOpts = Math.random, maybeOpts = {}) {
    const rand = typeof randOrOpts === "function" ? randOrOpts : (randOrOpts && typeof randOrOpts.rand === "function" ? randOrOpts.rand : Math.random);
    const opts = typeof randOrOpts === "function" ? (maybeOpts || {}) : (randOrOpts || {});
    const signal = opts.signal || null;

    const info = analyzeInput(start);
    if (typeof opts.onInfo === "function") opts.onInfo(info);

    let ids = info.ids.slice();
    let text = "";
    if (signal && signal.aborted) return text;

    let state = await runAsync(ids, signal);
    if (state.aborted || !state.logits) return text;
    let { logits, cache } = state;

    let lastYield = nowMs();
    for (let i = 0; i < n; i++) {
      if (signal && signal.aborted) break;
      const id = sample(logits, temperature, rand);
      const ch = vocab[id];
      text += ch;
      onToken(ch);
      ids.push(id);
      if (ids.length > T) {                       // 窓（block_size）を超えたら、後ろ半分で非同期に計算し直す
        ids = ids.slice(-Math.floor(T / 2));
        state = await runAsync(ids, signal);
        if (state.aborted) break;
        ({ logits, cache } = state);
        lastYield = nowMs();
      } else {
        logits = step(id, ids.length - 1, cache);
        if (i % 2 === 1 || nowMs() - lastYield >= 12) {
          await yieldFrame();                     // モバイルでも画面・停止ボタンが固まらないように制御を戻す
          lastYield = nowMs();
        }
      }
    }
    return text;
  }

  return { vocab, nParams, run, generate, analyzeInput, config: cfg };
}

export function fromJSON(json) {
  const W = {};
  for (const [name, w] of Object.entries(json.weights)) W[name] = dequantize(w);
  return buildModel(json.config, json.chars, W);
}

export async function fromJSONAsync(json, opts = {}) {
  const signal = opts.signal || null;
  const W = {};
  let lastYield = nowMs();
  for (const [name, w] of Object.entries(json.weights)) {
    if (signal && signal.aborted) throw new Error("モデルの読み込みが中断されました。");
    W[name] = dequantize(w);
    if (nowMs() - lastYield >= 12) {
      await yieldFrame();
      lastYield = nowMs();
    }
  }
  return buildModel(json.config, json.chars, W);
}

export async function load(url, opts = {}) {
  const res = await fetch(url, opts.signal ? { signal: opts.signal } : undefined);
  if (!res.ok) throw new Error(`モデルを読み込めませんでした（HTTP ${res.status}）`);
  const json = await res.json();
  return fromJSONAsync(json, opts);
}
