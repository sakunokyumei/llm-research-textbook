{"title": "本当に良くなった？：評価と統計", "short": "評価と統計", "subtitle": "「なんとなく良くなった」を、数字と信頼区間で言い切る", "time": "2時間", "env": "gpu", "level": 4, "builds": "ボンゴ先生LoRAを、①パープレキシティ ②自動チェック ③4択クイズ（忘れていないか） ④LLMによる審査 の4つの方法で評価し、ブートストラップで信頼区間をつけた評価レポート", "theory": ["評価の種類（自動指標・ベンチマーク・LLM審査・人間評価）", "保留データでのパープレキシティ", "選択式ベンチマークを対数尤度で解く方法", "LLM-as-a-judge と位置の偏り", "平均・標準誤差・ブートストラップ信頼区間", "データ漏洩（コンタミネーション）とグッドハートの法則"], "python": ["`random.Random` と `randrange` で復元抽出", "`.sort()` で並べて95%の範囲を取り出す", "f文字列で表を作る"]}

:::goal
第18〜19章で、モデルをボンゴ先生に変身させました。でも、「本当に良くなったの？」「元の賢さを忘れていない？」と聞かれたら、何と答えますか？ この章では、4種類の評価方法でモデルを測り、**統計**を使って「その差は偶然じゃない」と言えるかどうかを判断します。研究の世界で一番信頼されるのは、派手なデモではなく、誠実な評価です。
:::

:::review-bridge 第5章・第10章・第18章とのつながり
- **第5章（パープレキシティと検証データ）**：訓練に使っていないデータ上で損失とパープレキシティ（$e^{\text{損失}}$）を測ることで汎化性能を確かめる考え方を学びました。
- **第10章（平均と標準偏差）**：数字の「真ん中（平均）」だけでなく「どれくらいばらつくか（分散・標準偏差）」を測る発想を、ここでは標本サイズの揺らぎ（標準誤差・信頼区間）へ広げます。
- **第18章（壊滅的忘却）**：ボンゴ先生の口調を学ばせた結果、元の一般知識を忘れていないか、この章の4択クイズと統計で実際に検証します！
:::

:::minato
いくつか質問して「いい感じ！」じゃダメなんですか？
:::

:::sensei
ダメとは言わないが、それは**感想**だ。キミが試した3問が、たまたまうまくいっただけかもしれない。人間は、自分が作ったものを良く見たいものなんだ。私も、自分のダジャレは全部面白いと思っている。だから、自分をだまさない仕組みが要る。ファインマンも言っている。「第一の原則は、自分をだまさないこと。そして自分は、いちばんだまされやすい人間なのだ」と。
:::

## 準備：比べる2つのモデル

:::tip 実行環境とリソースの目安
- **環境**：無料GPU（T4）推奨です。ベースラインとボンゴLoRAの2モデルを扱うためVRAM約5〜7GBを使います。
- **ダウンロードと所要時間**：初回に `Qwen2.5-0.5B-Instruct`（約1GB）と評価データ3件を取得します。GPUなら学習から4種類の評価完了まで約2〜3分です。
- **GPUが使えない日の代替**：ブートストラップ統計と評価レポートのセルは**CPUだけで一瞬**で動きます。CPUのみで全セルを試す場合は、学習を1エポック・評価件数を `heldout_rows[:4]`、`test_questions[:4]`、`quiz[:5]` に絞ると待ち時間を減らせます。
- **ライブラリ互換性**：`dtype=` は `transformers >= 4.56` 対応（推奨環境は `requirements-book.txt` を参照）。
:::

評価には「比べる相手」が必要です。元のQwen2.5-0.5B-Instruct（**ベースライン**）と、第19章と同じ方法で作るボンゴ先生LoRAを用意します。ただし今回は、データの**最後の12問を評価用に取り分けて**から学習させます。

```python
!pip install -q peft trl
!wget -nv https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/bongo_sft.jsonl
!wget -nv https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/bongo_test.jsonl
!wget -nv https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/mini_quiz.jsonl
import json, math, os, random
for fname in ("bongo_sft.jsonl", "bongo_test.jsonl", "mini_quiz.jsonl"):
    if not os.path.exists(fname):
        raise RuntimeError(f"{fname} のダウンロードに失敗しました。ネットワーク接続を確認して再実行するか、付録E（エラー辞典）を参照してください。")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import Dataset
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig

rows = [json.loads(l) for l in open("bongo_sft.jsonl", encoding="utf-8")]
train_rows, heldout_rows = rows[:48], rows[48:]          # 最後の12問は学習に使わない
test_questions = [json.loads(l)["question"] for l in open("bongo_test.jsonl", encoding="utf-8")]
quiz = [json.loads(l) for l in open("mini_quiz.jsonl", encoding="utf-8")]
print(len(train_rows), len(heldout_rows), len(test_questions), len(quiz))
```

```output
48 12 12 20
```

```python
name = "Qwen/Qwen2.5-0.5B-Instruct"
device = "cuda" if torch.cuda.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(name)
baseline = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32).to(device).eval()

ds = Dataset.from_list([{"prompt": [{"role": "user", "content": r["question"]}],
                         "completion": [{"role": "assistant", "content": r["answer"]}]} for r in train_rows])
trainer = SFTTrainer(
    model=AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32), train_dataset=ds, processing_class=tok,
    peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", task_type="CAUSAL_LM"),
    args=SFTConfig(output_dir="eval-bongo", num_train_epochs=3, per_device_train_batch_size=4, learning_rate=2e-4,
                   report_to="none", save_strategy="no", logging_steps=100, bf16=False, fp16=torch.cuda.is_available()))
trainer.train()
bongo = trainer.model.merge_and_unload().to(device).eval()
print("準備完了")
```

```output-example
{'train_runtime': 31.2, 'train_loss': 1.74, 'epoch': 3.0}
準備完了
```

:::exercise ch20-q01
:::

## 評価1：保留データのパープレキシティ

学習に使わなかった12問の「ボンゴ先生の答え」を、それぞれのモデルがどれくらい**予想できるか**を測ります。第5章のパープレキシティです。答えの部分だけの損失を計算します。

```python
@torch.no_grad()
def answer_nll_sum(model, question, answer):
    prompt = tok.apply_chat_template([{"role": "user", "content": question}], add_generation_prompt=True, tokenize=False)
    p = tok(prompt, add_special_tokens=False)["input_ids"]
    a = tok(answer + "<|im_end|>", add_special_tokens=False)["input_ids"]
    ids = torch.tensor([p + a]).to(device)
    labels = torch.tensor([[-100] * len(p) + a]).to(device)
    mean_nll = model(input_ids=ids, labels=labels).loss.item()
    return mean_nll * len(a), len(a)

for label, m in [("ベースライン", baseline), ("ボンゴLoRA", bongo)]:
    pairs = [answer_nll_sum(m, r["question"], r["answer"]) for r in heldout_rows]
    mean = sum(s for s, _ in pairs) / sum(n for _, n in pairs)   # 全答えトークン数で重みづけしたコーパス平均NLL
    print(f"{label}：損失 {mean:.3f}  パープレキシティ {math.exp(mean):.1f}")
```

```output-example
ベースライン：損失 2.951  パープレキシティ 19.1
ボンゴLoRA：損失 2.214  パープレキシティ 9.2
```

ボンゴLoRAのほうが、見たことのないボンゴ先生の答えを、ずっと「ありそう」だと予想できています。口調を学べた証拠です。なお、答えの長さが問題ごとに違うため、1問ごとの平均をそのまま平均するのではなく、**全トークンの損失合計 ÷ 全トークン数**（トークン重みづけのコーパス平均NLL）からパープレキシティを求めています。

:::theory 保留データ
評価には、学習に**一度も使っていない**データ（**保留データ**、held-out data）を使います。学習に使ったデータで測ると、丸暗記しているだけでも良い数字が出てしまうからです（第5章の過去問の話）。今回は、データを作った段階で最後の12問を取り分けておきました。データを分けるのは、学習を始める**前**にやるのが鉄則です。
:::

:::warn パープレキシティを比べるときの3つの注意点
1. **トークナイザーが違うモデル同士は直接比べられない**（第5章・第14章）：語彙サイズや1文字あたりのトークン数が違うと「1トークンを当てる難しさ」が別物になるため、そのままパープレキシティを並べて優劣をつけてはいけません（比較するには第14章の「1文字／1バイトあたりの損失」に換算します）。
2. **評価データセットや前処理が違う数字は比べられない**：文章のジャンル・長さ・改行や記号の前処理が違うだけでパープレキシティは大きく変わるため、必ず**まったく同じ保留データと前処理**で比較します。
3. **パープレキシティが低い ≠ 指示追従や安全性が高い**：パープレキシティは「お手本に似た文章を出す確率」しか測れません。事実の正確さ・指示の遵守・安全に断る力は、この先の自動チェック・選択式ベンチマーク・LLM審査・人間評価と組み合わせて確かめる必要があります。
:::

:::exercise ch20-q02
:::

## 評価2：自動チェック（ルールで数える）

ボンゴ先生らしさには、ルールで確かめられる特徴があります。「感嘆符（！）を使う」「長すぎない」「きちんと止まる（`<|im_end|>` を出す）」。評価用の12問に答えさせて、数えてみましょう。

```python
@torch.no_grad()
def generate(model, question, n=120):
    inputs = tok.apply_chat_template([{"role": "user", "content": question}], add_generation_prompt=True,
                                     return_tensors="pt", return_dict=True).to(device)
    out = model.generate(**inputs, max_new_tokens=n, do_sample=False, pad_token_id=tok.pad_token_id)
    new = out[0][inputs["input_ids"].shape[1]:]
    return tok.decode(new, skip_special_tokens=True), (new == tok.convert_tokens_to_ids("<|im_end|>")).any().item()

def style_checks(text, stopped):
    return {"！を使う": "！" in text, "150字以内": len(text) <= 150, "きちんと止まる": stopped}

answers = {}
for label, m in [("ベースライン", baseline), ("ボンゴLoRA", bongo)]:
    answers[label] = [generate(m, q) for q in test_questions]
    results = [style_checks(t, s) for t, s in answers[label]]
    summary = "  ".join(f"{k} {sum(r[k] for r in results)}/{len(results)}" for k in results[0])
    print(f"{label}：{summary}")
```

```output-example
ベースライン：！を使う 1/12  150字以内 3/12  きちんと止まる 9/12
ボンゴLoRA：！を使う 12/12  150字以内 11/12  きちんと止まる 12/12
```

:::theory 自動チェックの長所と短所
ルールで数える評価は、**速く、安く、何度でも同じ結果**が出ます。ソフトウェアのテストと同じで、変更のたびに自動で回せます。ただし、「！を使う」はボンゴ先生らしさのごく一部で、**内容が正しいか**は分かりません。「！」を付けるだけの役立たずなモデルも満点になります。1つの指標だけを信じないことが大切です。
:::

:::exercise ch20-q03
:::

## 評価3：4択クイズ（忘れていないか）

ボンゴ先生化で、元の知識を忘れていないか（第18章の壊滅的忘却）を確かめます。20問の4択クイズを用意しました。LLMに4択を解かせるには、**各選択肢の確率**を比べる方法がよく使われます。

```python
@torch.no_grad()
def choice_logprob(model, question, choice):
    prompt = tok.apply_chat_template([{"role": "user", "content": question}], add_generation_prompt=True, tokenize=False)
    p = tok(prompt, add_special_tokens=False)["input_ids"]
    c = tok(choice, add_special_tokens=False)["input_ids"]
    ids = torch.tensor([p + c]).to(device)
    logprobs = torch.log_softmax(model(ids).logits[0, :-1].float(), dim=-1)
    targets = ids[0, 1:]
    return logprobs[len(p) - 1:, :].gather(1, targets[len(p) - 1:, None]).sum().item()

def quiz_score(model):
    correct = []
    for item in quiz:
        scores = [choice_logprob(model, item["question"], c) for c in item["choices"]]
        correct.append(int(scores.index(max(scores)) == item["answer"]))
    return correct

quiz_results = {label: quiz_score(m) for label, m in [("ベースライン", baseline), ("ボンゴLoRA", bongo)]}
for label, c in quiz_results.items():
    print(f"{label}：{sum(c)}/{len(c)} 問正解")
```

```output-example
ベースライン：17/20 問正解
ボンゴLoRA：16/20 問正解
```

:::python log_softmax と gather
`torch.log_softmax(…)` は、softmaxで確率にしてから、そのlogをとる計算を一度にやる関数です（別々にやるより、数値の誤差が出にくい）。<br>
`logprobs[…].gather(1, targets[…, None])` は、「各行（各位置）から、`targets` で指定した列（実際に来たトークン）の値だけを拾う」操作です。第8章の `probs[torch.arange(len(y)), y]` と同じことを、別の書き方でしています。拾った「各トークンの対数確率」を `.sum()` で足せば、選択肢の文字列全体の対数確率になります（第5章：確率の掛け算は、対数の足し算）。
:::

:::theory 選択肢の確率で解く
「次のトークン予測」しかできないLLMに4択を解かせるには、質問の後に各選択肢を続けたとき、**その選択肢の文字列全体の確率**（対数の合計）を計算し、一番高いものを答えとします。生成させて「答えは2番」と書かせる方法より、ぶれが少なく、小さなモデルでも測れます。有名なベンチマーク（MMLUや、その日本語版のJMMLUなど）でも、この方法がよく使われます。

選択肢の長さが違うと、長いほど確率の合計が小さくなって不利になるので、長さで割る（1トークンあたりにする）こともあります。どちらの方式で測ったかは、結果と一緒に必ず書いておきましょう。
:::

:::scaffold 対数確率（log-prob）の大小関係と長さ正規化
確率 $p$ は $0 < p \le 1$ なので、その対数 $\log p$ は**必ず0以下（マイナス）**になります。
- たとえば `A: -4.8`、`B: -1.5`、`C: -2.9`、`D: -6.1` なら、最も0に近い最大値 **`B (-1.5)`** が最高確率（$e^{-1.5} \approx 22.3\%$）です。
- 選択肢が長いと負の数（$\log p_t \le 0$）を何度も足すことになるため不利になりやすい点に注意します。

```python no-run
# 1トークンあたりの平均対数確率（長さ正規化）の例
raw_scores = [-2.0, -3.0]     # 合計では選択肢0 (-2.0) が勝ち
token_lens = [1, 3]           # でも選択肢1は3トークンある
norm_scores = [s / n for s, n in zip(raw_scores, token_lens)]  # [-2.0, -1.0] → 選択肢1が逆転！
```
:::

:::exercise ch20-q04 ch20-q05
:::

17問と16問。ボンゴLoRAは1問減りました。……これは「忘れた」のでしょうか？ それとも偶然の誤差でしょうか？

## 統計：その差は偶然か？

20問は、ほんの一部の問題です。別の20問を選んでいたら、結果は逆になったかもしれません。そこで、**ブートストラップ**という方法で、「もし問題を選び直したら、差はどれくらいばらつくか」を調べます。

```python
def bootstrap_diff(a, b, n_boot=10000, seed=0):
    """a, b：同じ問題に対する正解（1）・不正解（0）のリスト。差（b - a）の95%信頼区間を返す"""
    rng = random.Random(seed)
    n = len(a)
    diffs = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]          # 問題を「復元抽出」で選び直す
        diffs.append(sum(b[i] - a[i] for i in idx) / n)
    diffs.sort()
    return sum(b[i] - a[i] for i in range(n)) / n, diffs[int(0.025 * n_boot)], diffs[int(0.975 * n_boot)]

base_c = [1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1]     # 例：17/20
bongo_c = [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1]    # 例：16/20（得意・不得意な問題が違う）
diff, low, high = bootstrap_diff(base_c, bongo_c)
print(f"正答率の差：{diff:+.2f}  95%信頼区間：[{low:+.2f}, {high:+.2f}]")
```

```output
正答率の差：-0.05  95%信頼区間：[-0.25, +0.15]
```

:::theory ブートストラップと信頼区間
**ブートストラップ**（bootstrap）は、手元のデータから「同じ数だけ、重複を許して選び直す」（**復元抽出**）ことを何千回もくり返し、結果のばらつきを調べる方法です。数式をほとんど使わずに、どんな指標の信頼区間も計算できる、とても便利な道具です。

**95%信頼区間**は、ざっくり言うと「問題を選び直しても、差はたいていこの範囲に収まるだろう」という幅です。上の例では、ボンゴLoRAはベースラインが間違えた2問に正解し、ベースラインが正解した3問を間違えて、差し引き1問減っています。信頼区間は**0（差なし）をまたいでいる**ので、「ボンゴLoRAが知識を忘れた」とは**言い切れません**。20問は少なすぎるのです。言い切るには、問題を増やす（数百問）必要があります。

この「同じ問題で両方のモデルを比べ、差をブートストラップする」方法を **対応のあるブートストラップ**（paired bootstrap）と言います。同じ問題で比べるので、問題の難しさのばらつきが打ち消され、少ない問題数でも差を検出しやすくなります。
:::

:::math 標準誤差・95%信頼区間・ブートストラップ：8ステップで理解する
**① 解決したい問題**：20問のクイズでベースラインが 17/20（85%）、ボンゴLoRAが 16/20（80%）。この「1問（5%）の差」は本当に忘れたのか、それとも問題選びの偶然かを見分けたい。

**② 素朴な比較が危険な理由**：正答率の数字だけを見ると「85% vs 80%」は、20問テストでも1,000問テストでも同じに見えてしまう。でも20問なら1問たまたま転ぶだけで±5%動く！

**③ 発想**：テスト問題 $n$ 問は「世の中にある無限の問題」からランダムに引いた標本とみなせる。標本サイズ $n$ に応じた「正答率のぶれ幅（**標準誤差 SE**）」を数式または復元抽出（**ブートストラップ**）で見積もり、**95%信頼区間**で表す。

**④ 記号表と数式**：

$$\text{SE} = \sqrt{\frac{\hat{p}(1 - \hat{p})}{n}}, \qquad \text{95\%信頼区間（Wald近似）} = \hat{p} \pm 1.96\,\text{SE}$$

| 記号 | 意味 | Pythonでの対応 |
|---|---|---|
| $n$ | 評価した問題数 | `len(results)` |
| $\hat{p}$ | 観測された正答率（$0 \sim 1$） | `sum(results) / n` |
| $\text{SE}$ | 標準誤差（問題を引き直したときの正答率のぶれの目安） | `math.sqrt(p * (1 - p) / n)` |
| $1.96\,\text{SE}$ | 95%信頼区間の片側の幅（正規分布の両側5%境界） | `1.96 * se` |

**⑤ 小さな問題数 vs 大きな問題数で手計算（$\hat{p} = 0.80$ のとき）**：
- **$n = 20$ 問のとき**：
  $$\text{SE} = \sqrt{\frac{0.80 \times 0.20}{20}} = \sqrt{0.008} \approx 0.0894 \implies 1.96\,\text{SE} \approx 0.175$$
  95%信頼区間は **$[0.625,\; 0.975]$**（幅 35%ポイント！）。1〜2問（5〜10%）の差は完全にノイズに埋もれます。
- **$n = 400$ 問のとき**：
  $$\text{SE} = \sqrt{\frac{0.80 \times 0.20}{400}} = \sqrt{0.0004} = 0.020 \implies 1.96\,\text{SE} \approx 0.0392$$
  95%信頼区間は **$[0.761,\; 0.839]$**（±3.9%）まで一気に引き締まります！

**⑥ $\frac{1}{\sqrt{n}}$ の法則**：分母が $\sqrt{n}$ なので、**誤差の幅を半分にするには問題数を $2^2 = 4$ 倍**、3分の1にするには **$3^2 = 9$ 倍** にする必要があります。評価の精度を上げるのは地道で大変なのです。

**⑦ ブートストラップとの関係**：上の式は1モデルの正答率向けですが、**2つのモデルの差**や複雑な指標では、上のコードのように手元データから同じ $n$ 問を**復元抽出**（重複OKで引き直し）して1万回やり直す **対応のあるブートストラップ** が強力です。同じ問題番号 `idx` で両モデルの差 `b[i] - a[i]` をとるため、問題の難易度のばらつきが打ち消されます。

**⑧ 理解のための最小Pythonコード（Wald 95%信頼区間）**：

```python no-run
import math
def wald_ci95(results):
    n = len(results)
    p = sum(results) / n
    se = math.sqrt(p * (1 - p) / n)
    return p, max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)
```
:::

:::exercise ch20-q06 ch20-q07 ch20-q08
:::

自分の実験の結果（`quiz_results`）でも計算してみましょう。

```python
diff, low, high = bootstrap_diff(quiz_results["ベースライン"], quiz_results["ボンゴLoRA"])
print(f"あなたの実験：差 {diff:+.2f}  95%信頼区間 [{low:+.2f}, {high:+.2f}]")
```

```output-example
あなたの実験：差 -0.05  95%信頼区間 [-0.25, +0.15]
```

:::exercise ch20-q09 ch20-q10 ch20-q11
:::

## 評価4：LLMに審査させる（LLM-as-a-judge）

「説明が分かりやすいか」「面白いか」のような、ルールで数えにくい質は、人間が読んで判断するのが一番です。でも、毎回人間が何百件も読むのは大変です。そこで、**LLMに審査員をやってもらう**方法がよく使われます（LLM-as-a-judge）。

```python
def judge(question, answer_a, answer_b):
    prompt = (f"質問：{question}\n\n回答A：{answer_a}\n\n回答B：{answer_b}\n\n"
              "高校生にとって、分かりやすく楽しい回答はどちらですか？「A」か「B」の1文字だけで答えてください。")
    inputs = tok.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True,
                                     return_tensors="pt", return_dict=True).to(device)
    out = baseline.generate(**inputs, max_new_tokens=2, do_sample=False, pad_token_id=tok.pad_token_id)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()[:1]

wins_ab = [judge(q, a[0], b[0]) for q, a, b in zip(test_questions, answers["ボンゴLoRA"], answers["ベースライン"])]
wins_ba = [judge(q, b[0], a[0]) for q, a, b in zip(test_questions, answers["ボンゴLoRA"], answers["ベースライン"])]
print("ボンゴを「A」に置いたとき、ボンゴの勝ち：", wins_ab.count("A"), "/", len(test_questions))
print("ボンゴを「B」に置いたとき、ボンゴの勝ち：", wins_ba.count("B"), "/", len(test_questions))
both = sum(x == "A" and y == "B" for x, y in zip(wins_ab, wins_ba))   # どちらの順番でも勝った数
print("どちらの順番でもボンゴの勝ち：", both, "/", len(test_questions))
```

```output-example
ボンゴを「A」に置いたとき、ボンゴの勝ち： 10 / 12
ボンゴを「B」に置いたとき、ボンゴの勝ち： 5 / 12
どちらの順番でもボンゴの勝ち： 5 / 12
```

:::theory 審査員にもクセがある
同じ組み合わせなのに、並べる順番を入れ替えただけで、勝ち数が大きく変わりました。小さなLLMの審査員は「最初に見た回答（A）を選びがち」という **位置の偏り**（position bias）を持っていることが多いのです。ほかにも、「長い回答を好む」「自分と似た書き方を好む」などの偏りが知られています。

対策は、

- **順番を入れ替えて2回審査**し、両方で勝ったときだけ勝ちとする（上のように）
- 審査員には、評価されるモデルより**大きく賢いモデル**を使う
- 審査の基準（**ルーブリック**）を具体的に書く
- 一部を**人間も審査**して、LLM審査員と人間の判断が一致するか確かめる

LLM審査は便利ですが、審査員が0.5Bでは心もとない。本格的にやるなら、第19章の4ビット読み込み（QLoRAの節）で、7Bなどの大きめのモデルを読み込んで審査員にしましょう。
:::

:::scaffold LLM-as-a-judge の3大バイアスと対策まとめ
| バイアスの種類 | 起きる現象 | 具体的な対策 |
|---|---|---|
| **位置の偏り**（Position Bias） | 先に出された回答A（または後のB）を無意識に選びがち | A/Bの順番を入れ替えて2回審査し、**両順で勝った場合のみ勝ち**とする |
| **長さの偏り**（Verbosity Bias） | 中身が薄くても長く丁寧に見える回答を高く採点しがち | ルーブリックに「正確さと簡潔さ」を明記し、冗長な回答を減点する |
| **自己選好**（Self-Enhancement） | 審査員モデル自身と同じモデル系列の文体を好みがち | 評価対象より大きく別系統の審査モデルを使い、人間評価と一致率を照合する |
:::

:::exercise ch20-q12
:::

## 評価の落とし穴

:::warn データ漏洩（コンタミネーション）
評価に使う問題が、学習データに混ざっていると、モデルは「解いた」のではなく「覚えていた」だけになります。これを **コンタミネーション**（contamination、汚染 / リーク）と言います。

- **自分のデータ**：学習用と評価用に同じ問題が入っていないか、データを作る最初の段階で厳密に分ける
- **公開ベンチマーク**：有名なベンチマーク問題（MMLUなど）は、ネット上に答え付きでたくさん転載されているため、数兆トークンの事前学習データに丸ごと混入してしまい、暗記で満点を取ってしまう現象が問題視されています。そのため、定期的に非公開の問題に入れ替えたり、人間が2つのモデルの回答をブラインド比較して勝敗を決める「Chatbot Arena（LMSYS）」の **Elo系のレーティング（Elo rating）** のような仕組みが重視されるようになっています。

第14章で「トークナイザーを検証データ込みで作ったのは少しずる」と書いたのも、このデータの漏洩（リーク）の仲間です。
:::

:::theory グッドハートの法則
「指標が目標になると、それは良い指標ではなくなる」。経済学者グッドハートの名前で呼ばれる法則です。「！を使う割合」を目標にしてモデルを鍛えれば、「！」を連打するだけのモデルができるでしょう。ベンチマークの点数を上げること自体が目的になると、本当に欲しかった能力から離れていきます。

だから評価は、**複数の方法を組み合わせ**、最後は**実際に使う場面で人間が確かめる**のが基本です。
:::

:::exercise ch20-q13
:::

## 評価レポートを書く

最後に、結果を表にまとめます。研究でも、仕事でも、評価は「表」で語ります。下のコードの数字は、この教科書の例です。**あなたの結果の数字に書き換えて**から実行しましょう。

```python
report = [
    ("保留データのパープレキシティ（低いほど良い）", "19.1", "9.2"),
    ("「！」を使う割合", "1/12", "12/12"),
    ("きちんと止まる割合", "9/12", "12/12"),
    ("4択クイズ（20問）", "17/20", "16/20（差の95%CI [-0.25, +0.15]）"),
    ("LLM審査（順番入替の両方で勝ち）", "—", "5/12"),
]
print(f"{'指標':34s} {'ベースライン':10s} ボンゴLoRA")
for metric, a, b in report:
    print(f"{metric:30s} {a:12s} {b}")
```

```output
指標                                 ベースライン     ボンゴLoRA
保留データのパープレキシティ（低いほど良い）         19.1         9.2
「！」を使う割合                       1/12         12/12
きちんと止まる割合                      9/12         12/12
4択クイズ（20問）                     17/20        16/20（差の95%CI [-0.25, +0.15]）
LLM審査（順番入替の両方で勝ち）              —            5/12
```

（表の数値は出力例のものです。あなたの実験の数値で書き直してください。）

結論はこう書けます。「ボンゴLoRAは、口調と止まり方を大きく改善した（パープレキシティ・自動チェック）。一般知識の4択では1問減ったが、20問では統計的に区別できず、忘却の有無を判断するには問題数を増やす必要がある。LLM審査は位置の偏りが大きく、参考程度とする」。**言えることと、言えないことを分けて書く**。これが誠実な評価レポートです。

:::try 問題を増やしてみよう
`mini_quiz.jsonl` を真似して、4択クイズを自分で30問追加してみましょう（基本情報の過去問の知識問題などがおすすめ）。50問にすると、信頼区間はどれくらい狭くなるでしょう？ 予想してから試してください。
:::

:::warn よくあるつまずき
- **毎回結果が変わる**：生成に `do_sample=False`（greedy）を使い、ブートストラップの乱数の種を固定しましょう。評価は「同じ条件で何度やっても同じ結果」が理想です。
- **4択の確率がおかしい**：選択肢の前の空白やかぎかっこの有無で、トークンの区切りが変わります。全部の選択肢で同じ書き方にそろえましょう。
- **審査員が「A」「B」以外を答える**：小さなモデルでは起きがちです。回答の最初の1文字だけを見る、決まった形式で答えるようfew-shotの例を入れる、などで対処します。
:::

:::exercise ch20-q14
:::

:::checklist
- 評価用のデータを、学習の前に取り分けた
- 保留データのパープレキシティで、口調を学んだことを確かめた
- ルールによる自動チェックを作った
- 4択クイズを選択肢の確率で解かせた
- ブートストラップで差の95%信頼区間を計算し、「言い切れるか」を判断した
- LLM審査で位置の偏りを確かめた
- 言えることと言えないことを分けて、評価の結論を書いた
:::

:::recap
- 評価は**保留データ**で。複数の方法（パープレキシティ・自動チェック・ベンチマーク・LLM審査・人間）を組み合わせる
- 選択式は**選択肢の確率**で解かせる
- 少ない問題数の差は偶然かもしれない。**ブートストラップ**で**信頼区間**を出し、0を含むなら言い切らない
- LLM審査員には**位置の偏り**などのクセがある
- **コンタミネーション**と**グッドハートの法則**に注意。言えることと言えないことを分けて書く
:::

:::sensei
第5部、完走！ キミはもう、モデルを借りて、鍛えて、正しく測れる。次の第6部では、LLMを「部品」にして、もっと大きなシステムを作る。最初は **RAG**。LLMに教科書を持たせて、カンニングOKの試験を受けさせる方法だ。ハルシネーション（もっともらしい嘘）を減らす、一番実用的な技だよ。
:::
