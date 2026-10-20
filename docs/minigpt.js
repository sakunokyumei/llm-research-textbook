// ブラウザで動くミニGPT（第24章）。第12章の minigpt.py と同じ計算を JavaScript で書いたもの。
// 使い方： const model = await load("soseki-gpt.json"); await model.generate("吾輩は", 100, 0.8, ch => ...);

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
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) data[r * cols + c] = q[r * cols + c] * scale[r];
  return { shape: w.shape, data };
}

// y = W x + b（W は [出力, 入力] の形。PyTorch の nn.Linear と同じ向き）
function linear(W, b, x) {
  const [rows, cols] = W.shape;
  const y = new Float32Array(rows);
  for (let r = 0; r < rows; r++) {
    let s = b ? b.data[r] : 0;
    const off = r * cols;
    for (let c = 0; c < cols; c++) s += W.data[off + c] * x[c];
    y[r] = s;
  }
  return y;
}

function layerNorm(x, w, b, eps = 1e-5) {
  let mean = 0;
  for (const v of x) mean += v;
  mean /= x.length;
  let vari = 0;
  for (const v of x) vari += (v - mean) ** 2;
  vari /= x.length;
  const inv = 1 / Math.sqrt(vari + eps);
  return x.map((v, i) => (v - mean) * inv * w.data[i] + b.data[i]);
}

// GELU（PyTorch の nn.GELU と同じ、誤差関数 erf を使う版）
function erf(x) {
  const s = Math.sign(x), a = Math.abs(x), t = 1 / (1 + 0.3275911 * a);
  const y = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-a * a);
  return s * y;
}
const gelu = (x) => 0.5 * x * (1 + erf(x / Math.SQRT2));

export function fromJSON(json) {
  const cfg = json.config;
  const W = {};
  for (const [name, w] of Object.entries(json.weights)) W[name] = dequantize(w);
  const vocab = json.chars;
  const stoi = new Map(vocab.map((ch, i) => [ch, i]));
  const C = cfg.n_embd, H = cfg.n_head, hs = C / H, L = cfg.n_layer, T = cfg.block_size;
  const nParams = Object.values(W).reduce((s, w) => s + w.data.length, 0);

  // 1トークン分の計算。cache[layer][head] = {k: [], v: []} に過去の Key と Value を貯める（第16章のKVキャッシュ）
  function step(id, pos, cache) {
    let x = new Float32Array(C);
    for (let i = 0; i < C; i++) x[i] = W["tok_emb.weight"].data[id * C + i] + W["pos_emb.weight"].data[pos * C + i];
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
        const scores = c.k.map((kk) => { let s = 0; for (let i = 0; i < hs; i++) s += q[i] * kk[i]; return s / Math.sqrt(hs); });
        const m = Math.max(...scores);
        const e = scores.map((s) => Math.exp(s - m));
        const sum = e.reduce((a, b) => a + b, 0);
        for (let t = 0; t < e.length; t++) {
          const w = e[t] / sum;
          for (let i = 0; i < hs; i++) heads[j * hs + i] += w * c.v[t][i];
        }
      }
      const a = linear(W[p + "attn.proj.weight"], W[p + "attn.proj.bias"], heads);
      for (let i = 0; i < C; i++) x[i] += a[i];                          // 残差接続
      const h2 = layerNorm(x, W[p + "ln2.weight"], W[p + "ln2.bias"]);
      const f1 = linear(W[p + "ffwd.net.0.weight"], W[p + "ffwd.net.0.bias"], h2).map(gelu);
      const f2 = linear(W[p + "ffwd.net.2.weight"], W[p + "ffwd.net.2.bias"], f1);
      for (let i = 0; i < C; i++) x[i] += f2[i];                         // 残差接続
    }
    const out = layerNorm(x, W["ln_f.weight"], W["ln_f.bias"]);
    return linear(W["lm_head.weight"], W["lm_head.bias"], out);         // 次の文字の点数（ロジット）
  }

  const newCache = () => Array.from({ length: L }, () => Array.from({ length: H }, () => ({ k: [], v: [] })));

  // ids をまとめて流し込み、最後の位置のロジットを返す
  function run(ids) {
    const cache = newCache();
    let logits = null;
    ids.forEach((id, pos) => { logits = step(id, pos, cache); });
    return { logits, cache };
  }

  function sample(logits, temperature, rand) {
    const z = Array.from(logits, (v) => v / temperature);
    const m = Math.max(...z);
    const e = z.map((v) => Math.exp(v - m));
    const sum = e.reduce((a, b) => a + b, 0);
    let r = rand() * sum;
    for (let i = 0; i < e.length; i++) { r -= e[i]; if (r <= 0) return i; }
    return e.length - 1;
  }

  async function generate(start, n, temperature = 0.8, onToken = () => {}, rand = Math.random) {
    let ids = Array.from(start).filter((ch) => stoi.has(ch)).map((ch) => stoi.get(ch));
    if (ids.length === 0) ids = [stoi.get("。")];
    ids = ids.slice(-T);
    let { logits, cache } = run(ids);
    let text = "";
    for (let i = 0; i < n; i++) {
      const id = sample(logits, temperature, rand);
      const ch = vocab[id];
      text += ch; onToken(ch);
      ids.push(id);
      if (ids.length > T) {                       // 窓（block_size）を超えたら、後ろ半分で計算し直す
        ids = ids.slice(-Math.floor(T / 2));
        ({ logits, cache } = run(ids));
      } else {
        logits = step(id, ids.length - 1, cache);
      }
      if (i % 4 === 3) await new Promise((r) => setTimeout(r, 0));   // 画面が固まらないように一息つく
    }
    return text;
  }

  return { vocab, nParams, run, generate, config: cfg };
}

export async function load(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error("モデルを読み込めませんでした：" + res.status);
  return fromJSON(await res.json());
}
