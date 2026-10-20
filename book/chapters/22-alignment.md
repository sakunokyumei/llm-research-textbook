{"title": "好みを教える：RLHFとDPO", "short": "RLHFとDPO", "subtitle": "「どちらの答えが良いか」だけで、モデルの性格を変える", "time": "2時間", "env": "gpu", "level": 5, "builds": "29組の「良い答え／悪い答え」のペアで、QwenをDPOで学習させる。その前にDPOの損失を数式からゼロから実装し、TRLの計算と一致することを確かめる", "theory": ["なぜSFTだけでは足りないのか", "報酬モデルとブラッドリー・テリーモデル", "シグモイド関数", "RLHF（PPO）の全体像とKLペナルティ", "DPO：報酬モデルなしで好みを直接学ぶ", "報酬ハッキング・安全性・アラインメント", "検証可能な報酬による強化学習（推論モデルへの道）"], "python": ["`F.logsigmoid`", "`trl` の `DPOTrainer`", "学習ログ（`log_history`）の読み方"]}

:::goal
第18章のSFTは「お手本をまねる」学習でした。でも、良い答え方はお手本1つでは決まりません。「この2つの答えなら、こっちのほうが良い」という**比べた好み**のほうが、人間にとって作りやすく、しかも細かいニュアンスを伝えられます。この章では、ChatGPTを丁寧で安全なアシスタントにした **RLHF** の考え方を学び、その簡単で強力な後継 **DPO** を、損失関数からゼロから実装して使います。
:::

:::minato
SFTでボンゴ先生になったのに、まだ何か足りないんですか？
:::

:::sensei
SFTは「100点のお手本」をまねる方法だ。でも世の中、100点のお手本を書くのは大変なのに、2つを比べて「こっちのほうがマシ」と言うのは簡単だろう？ ラーメンを自分で作るのは難しいけど、2杯食べ比べて「こっちがうまい」と言うのは誰でもできる。その「食べ比べの判定」から学ぶのが、この章の話だ。
:::

## 好みのデータを見る

```python
!pip install -q trl peft
!wget -q https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/bongo_prefs.jsonl
import json
prefs = [json.loads(l) for l in open("bongo_prefs.jsonl", encoding="utf-8")]
print(len(prefs), "組")
p = prefs[11]
print("質問：", p["question"])
print("良い答え：", p["chosen"])
print("悪い答え：", p["rejected"])
```

```output
29 組
質問： 勉強のやる気が出ません
良い答え： やる気は、始める前ではなく、始めた後に出てくるものなんだ。まず5分だけ、コードを1行動かしてみよう。小さな成功が次の一歩を呼ぶ。やる気スイッチは、押すまで見つからない。スイッチを探すより、とりあえずスイッチオン！
悪い答え： やる気がないなら、やめればいいと思います。
```

同じ質問に対して、**選ばれた答え**（chosen）と **選ばれなかった答え**（rejected）の組です。悪い答えには、冷たい答え、間違った答え、役に立たない答えなどを入れてあります。このデータから、モデルに「良い答えを出しやすく、悪い答えを出しにくく」させます。

## 報酬モデルと、好みの確率

まずは、RLHFの考え方から見ていきましょう。

:::theory 報酬モデル：答えに点数をつけるモデル
人間の好みを学習させるには、まず「答えの良さ」を数にする必要があります。そこで、答えを入力すると**点数（報酬）**を出す **報酬モデル**（reward model）を作ります。

報酬モデルは、好みのペアから学習します。「良い答えの点数 $r_c$ が、悪い答えの点数 $r_r$ より高くなる」ようにするのです。そのとき使われるのが、**ブラッドリー・テリーモデル** という考え方です。

$$P(\text{良い答えが選ばれる}) = \sigma(r_c - r_r)$$

点数の**差**をシグモイド関数 $\sigma$ に入れたものを、「良い答えが選ばれる確率」と考えます。スポーツのレーティング（強さの点数の差から勝率を予想する）と同じ発想です。
:::

:::math シグモイド関数
**シグモイド関数** $\sigma(x) = \dfrac{1}{1 + e^{-x}}$ は、どんな数でも0から1の間に押し込むS字の関数です。

```python
import math
for x in [-4, -2, 0, 2, 4]:
    print(f"σ({x:+d}) = {1 / (1 + math.exp(-x)):.3f}")
```

```output
σ(-4) = 0.018
σ(-2) = 0.119
σ(+0) = 0.500
σ(+2) = 0.881
σ(+4) = 0.982
```

差が0なら確率0.5（五分五分）、差が大きいほど1に近づきます。第3章のsoftmaxを「候補が2つだけ」の場合に使ったものと、実は同じです（確かめてみたい人は、$e^{r_c}/(e^{r_c}+e^{r_r})$ を変形してみましょう）。
:::

:::theory RLHF：報酬を最大にするように強化学習
報酬モデルができたら、次はLLMを **強化学習**（reinforcement learning）で鍛えます。LLMに答えを生成させ、報酬モデルで点数をつけ、点数が高い答えを出しやすくなるようにパラメータを調整する。これをくり返します（よく使われる方法が **PPO**）。人間のフィードバック（Human Feedback）から学ぶ強化学習（RL）なので、**RLHF** と呼びます。

ただし、報酬だけを追いかけると、モデルは**報酬モデルの穴をつく**ようになります。たとえば報酬モデルが「長い答え」を好むクセを持っていたら、意味のない長文を書くようになる。これを **報酬ハッキング** と言います。そこで、「元のモデル（参照モデル）からあまり離れすぎない」という罰（**KLペナルティ**）を加えます。

$$\text{目標} = \text{報酬} - \beta \times \text{元のモデルからの離れ具合（KLダイバージェンス）}$$

**KLダイバージェンス**は、2つの確率分布 $p$（今のモデル）と $q$（元のモデル）がどれくらい違うかを測る数です。

$$\mathrm{KL}(p \,\|\, q) = \sum_i p_i \log \frac{p_i}{q_i}$$

「今のモデルが選ぶ確率 $p_i$ で重みをつけて、$\log$（今の確率 ÷ 元の確率）を平均する」と読みます。数で試すと、元のモデルが次のトークン「A・B」を $q = (0.5, 0.5)$ で選び、今のモデルが $p = (0.9, 0.1)$ で選ぶなら、

$$0.9 \log\frac{0.9}{0.5} + 0.1 \log\frac{0.1}{0.5} \approx 0.9 \times 0.588 + 0.1 \times (-1.609) \approx 0.37$$

です。$p$ と $q$ が同じなら、どの $\log$ も $\log 1 = 0$ なので、KLは0です。違うほど大きくなります（マイナスにはなりません）。第5章の交差エントロピーと同じく「確率の $\log$ を平均する」仲間です。PyTorchでは `F.kl_div` で計算できます。

RLHFはとても強力ですが、報酬モデル・強化学習・生成をぐるぐる回すので、仕組みが複雑で、学習も不安定になりがちです。
:::

## DPO：報酬モデルなしで、好みを直接学ぶ

2023年に、スタンフォード大学の研究者たちが、すごいことに気づきました。上のRLHFの「目標」を数学的に変形すると、**報酬モデルも強化学習も使わずに**、好みのペアから直接LLMを学習させる損失関数が導けるのです。それが **DPO**（Direct Preference Optimization）です。

:::theory DPOの損失関数
DPOでは、学習中のモデル（**方策**、$\pi$）と、学習前のモデル（**参照モデル**、$\pi_{\text{ref}}$）の2つを使います。それぞれのモデルが、良い答え $y_c$ と悪い答え $y_r$ をどれくらいの確率で書くか（対数確率）を計算して、

$$\text{損失} = -\log \sigma\Big(\beta \big[ (\log \pi(y_c) - \log \pi_{\text{ref}}(y_c)) - (\log \pi(y_r) - \log \pi_{\text{ref}}(y_r)) \big]\Big)$$

とします。読み方は、

- $\log \pi(y_c) - \log \pi_{\text{ref}}(y_c)$：学習中のモデルが、元のモデルに比べて、良い答えを**どれだけ書きやすくなったか**
- 同じことを悪い答えについても計算し、**その差**をとる
- 差が大きいほど（良い答えだけ書きやすくなるほど）、損失は小さい

括弧の中の「元のモデルと比べた対数確率の差」が、RLHFの報酬の役目をしています（**暗黙の報酬**）。そして、元のモデルとの比で測っているので、自然に「元のモデルから離れすぎない」効果（KLペナルティの役目）も入っています。$\beta$ は、その離れにくさを決めるハイパーパラメータです。
:::

式だけだと分かりにくいので、数で計算してみましょう。

```python
import torch
import torch.nn.functional as F

def dpo_loss(pi_c, pi_r, ref_c, ref_r, beta=0.1):
    """各引数は、その答え全体の対数確率（トークンごとの log 確率の合計）"""
    margin = beta * ((pi_c - ref_c) - (pi_r - ref_r))
    return -F.logsigmoid(margin)

ref_c, ref_r = torch.tensor(-60.0), torch.tensor(-25.0)     # 学習前：悪い答え（短い）のほうが書きやすい
print("学習前（方策＝参照）：", dpo_loss(ref_c, ref_r, ref_c, ref_r).item())
print("良い答えが +10 書きやすく：", dpo_loss(ref_c + 10, ref_r, ref_c, ref_r).item())
print("悪い答えが -10 書きにくく：", dpo_loss(ref_c, ref_r - 10, ref_c, ref_r).item())
print("両方：", dpo_loss(ref_c + 10, ref_r - 10, ref_c, ref_r).item())
```

```output
学習前（方策＝参照）： 0.6931471824645996
良い答えが +10 書きやすく： 0.3132616877555847
悪い答えが -10 書きにくく： 0.3132616877555847
両方： 0.12692801654338837
```

:::theory 最初の損失は log 2
学習を始めた瞬間は、方策＝参照なので、括弧の中は0、$\sigma(0) = 0.5$、損失は $-\log 0.5 = \log 2 \approx 0.693$ です。第5章で「最初の損失は $\log V$」を確かめたのと同じで、DPOの学習ログで最初に **0.693** が出ていたら、正しく始まっている印です。

注目してほしいのは、学習前の対数確率は「悪い答え（-25）」のほうが「良い答え（-60）」より高い、つまり**悪い答えのほうが書きやすい**状態だったことです。悪い答えは短いので、確率の掛け算の回数が少ないからです。DPOは、確率そのものではなく「元からの**変化**」を比べるので、長さの違いに惑わされません。
:::

## モデルの対数確率を計算する

本物のLLMで、答え全体の対数確率を計算する関数を作ります。第20章の4択クイズで使った方法と同じです。

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

name = "Qwen/Qwen2.5-0.5B-Instruct"
device = "cuda" if torch.cuda.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(name)
ref_model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32).to(device).eval()

@torch.no_grad()
def answer_logprob(model, question, answer):
    prompt = tok.apply_chat_template([{"role": "user", "content": question}], add_generation_prompt=True, tokenize=False)
    p = tok(prompt, add_special_tokens=False)["input_ids"]
    a = tok(answer + "<|im_end|>", add_special_tokens=False)["input_ids"]
    ids = torch.tensor([p + a]).to(device)
    logprobs = torch.log_softmax(model(ids).logits[0, :-1].float(), dim=-1)
    return logprobs[len(p) - 1:].gather(1, ids[0, len(p):, None]).sum().item()

p = prefs[11]
lc, lr = answer_logprob(ref_model, p["question"], p["chosen"]), answer_logprob(ref_model, p["question"], p["rejected"])
print(f"良い答えの対数確率 {lc:.1f}  悪い答えの対数確率 {lr:.1f}")
```

```output-example
良い答えの対数確率 -142.3  悪い答えの対数確率 -21.7
```

学習前のQwenにとっては、長くて個性的なボンゴ先生の答えより、短くて素っ気ない答えのほうが、ずっと「書きやすい」ようです。

## TRLのDPOTrainerで学習する

DPOの学習は、TRLの `DPOTrainer` を使うと簡単です。データを「prompt・chosen・rejected」の形にして渡すだけです。メモリを節約するために、第19章のLoRAを使います（LoRAを使うと、参照モデルは「付せんを外した状態」として自動的に用意されるので、モデルを2つ読み込む必要がありません）。

```python
from datasets import Dataset
from peft import LoraConfig
from trl import DPOTrainer, DPOConfig

ds = Dataset.from_list([{"prompt": [{"role": "user", "content": p["question"]}],
                         "chosen": [{"role": "assistant", "content": p["chosen"]}],
                         "rejected": [{"role": "assistant", "content": p["rejected"]}]} for p in prefs])
policy = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32)
config = DPOConfig(output_dir="dpo-bongo", beta=0.1, learning_rate=5e-5, num_train_epochs=3,
                   per_device_train_batch_size=4, logging_steps=1, report_to="none", save_strategy="no",
                   bf16=False, fp16=torch.cuda.is_available())
trainer = DPOTrainer(model=policy, args=config, train_dataset=ds, processing_class=tok,
                     peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", task_type="CAUSAL_LM"))
trainer.train()
first = trainer.state.log_history[0]
print("最初の損失：", round(first["loss"], 4))
```

```output-example
{'loss': 0.6931, 'rewards/chosen': 0.0, 'rewards/rejected': 0.0, 'rewards/accuracies': 0.0, 'rewards/margins': 0.0, ...}
{'loss': 0.4213, 'rewards/chosen': 1.92, 'rewards/rejected': -1.35, 'rewards/accuracies': 0.95, 'rewards/margins': 3.27, ...}
...
最初の損失： 0.6931
```

:::theory 学習ログの読み方
- `loss`：DPOの損失。0.693（$\log 2$）から下がっていけば順調
- `rewards/chosen`：良い答えの暗黙の報酬（$\beta \times$ 元からの対数確率の変化）。上がっていくのが理想
- `rewards/rejected`：悪い答えの暗黙の報酬。下がっていくのが理想
- `rewards/margins`：その差。広がっていくほど、好みを学べている
- `rewards/accuracies`：良い答えの報酬が悪い答えより高かったペアの割合

`rewards/chosen` も一緒に下がっていく（良い答えも書きにくくなる）ことがよくあり、DPOの弱点として知られています。差が広がっていても、良い答えそのものの確率が下がりすぎると、文章がおかしくなることがあります。学習率を小さく、エポックを少なくするのが安全です。
:::

学習後のモデルで、学習前に比べて、良い答えと悪い答えの書きやすさがどう変わったか見てみましょう。

```python
trainer.model.eval()
for name_, m in [("学習前", ref_model), ("DPO後", trainer.model)]:
    lc = answer_logprob(m, p["question"], p["chosen"])
    lr = answer_logprob(m, p["question"], p["rejected"])
    print(f"{name_}：良い答え {lc:7.1f}  悪い答え {lr:7.1f}")
```

```output-example
学習前：良い答え  -142.3  悪い答え   -21.7
DPO後：良い答え  -118.6  悪い答え   -40.2
```

良い答えは書きやすく、悪い答えは書きにくくなりました。

:::try 学習していない質問で比べる
`bongo_test.jsonl` の質問（第18章）を、学習前のモデルとDPO後のモデルに答えさせて比べてみましょう。29組だけなので、ボンゴ先生の口調まで完全には身につかないかもしれません。でも、冷たい答えや失礼な答えは減っているはずです。第20章のLLM審査で、どちらが好まれるかを測ってみるのも良い練習です。
:::

## アラインメントと安全性

:::theory アラインメント
LLMを「人間の意図や価値観に沿ったふるまい」に合わせることを、**アラインメント**（alignment、整合）と言います。役に立つこと（helpful）、正直であること（honest）、害を与えないこと（harmless）の3つがよく目標に挙げられます。

- 危険な作り方を聞かれたら断る、差別的な発言をしない、といった**安全性**も、好みのデータ（「断る答え」をchosenにする）で学習させます
- 人間の代わりに、原則（憲法）を与えたAIに好みを判定させる方法（**RLAIF**、Constitutional AI）もあります
- 一方で、うまい言い回しで安全の仕組みをすり抜けようとする攻撃（**ジェイルブレイク**）もあり、守る側と破る側のいたちごっこが続いています

アラインメントは、技術だけでなく「誰の好みに合わせるのか」という社会的な問いも含む、とても大切な研究分野です。
:::

:::theory 推論モデルへの道：答えが確かめられる問題で強化学習
最近の「考えてから答える」**推論モデル**（reasoning model）は、数学やプログラミングのように**答えが正しいかを自動で確かめられる**問題で、強化学習をして作られています。人間の好みの代わりに、「答えが合っていたら報酬1、間違っていたら0」という**検証可能な報酬**（verifiable reward）を使うのです（RLVR）。モデルは、正解にたどり着くために、長く考える（考える過程のトークンを多く出す）ことを自分で学んでいきます。**GRPO** という、同じ問題に何通りも答えさせて、平均より良かった答えを強化する方法がよく使われます。第25章で、もう少し詳しく触れます。
:::

:::warn よくあるつまずき
- **損失が最初から0.693でない**：参照モデルと学習モデルが違う状態から始まっています。LoRAを使う場合は気にしなくて大丈夫ですが、自分でモデルを2つ読み込む場合は、同じ重みから始めましょう。
- **学習後に文章がおかしくなる**：学習率が大きすぎるか、エポックが多すぎます。DPOは $10^{-6}$〜$10^{-5}$ 台の小さな学習率から試すのが安全です（今回はLoRAなので少し大きめ）。
- **`CUDA out of memory`**：DPOは、1つのペアで良い答えと悪い答えの両方を計算するので、SFTよりメモリを使います。バッチを小さくしましょう。
:::

:::quiz DPOの最初の損失
DPOの学習を始めた瞬間の損失が $\log 2 \approx 0.693$ になるのはなぜ？
:::answer
最初は学習中のモデルと参照モデルが同じなので、「元からの対数確率の変化」が良い答えも悪い答えも0になり、差が0、$\sigma(0) = 0.5$、損失は $-\log 0.5 = \log 2$ になるからです。
:::

:::quiz 報酬ハッキング
報酬モデルが「長い答えほど高い点数」というクセを持っていたら、RLHFで何が起きる？ どう防ぐ？
:::answer
LLMが、中身のない長い答えを書くようになります（報酬ハッキング）。元のモデルから離れすぎないようにするKLペナルティ、報酬モデルの改善、人間によるチェックなどで防ぎます。
:::

:::quiz ブラッドリー・テリー
良い答えの報酬が3、悪い答えの報酬が1のとき、良い答えが選ばれる確率は？（$\sigma(2) \approx 0.881$）
:::answer
$\sigma(3 - 1) = \sigma(2) \approx 0.881$、約88%です。
:::

:::checklist
- 好みのペア（chosen / rejected）のデータの形を説明できる
- シグモイド関数と、報酬の差から確率を出す考え方を説明できる
- RLHF（報酬モデル→強化学習＋KLペナルティ）の流れを説明できる
- DPOの損失を自分で実装し、最初が $\log 2$ になることを確かめた
- TRLのDPOTrainerで学習させ、ログの `rewards/margins` を読んだ
- アラインメントと推論モデル（検証可能な報酬）の考え方を説明できる
:::

:::recap
- 好みの学習は「**2つを比べた判定**」から学ぶ。お手本を書くより集めやすく、細かいニュアンスを伝えられる
- **RLHF**：報酬モデル（ブラッドリー・テリー）＋強化学習（PPO）＋KLペナルティ
- **DPO**：報酬モデルなしで、好みのペアから直接学習。損失 $= -\log\sigma(\beta[\Delta_c - \Delta_r])$、最初は $\log 2$
- **報酬ハッキング**に注意。アラインメントは技術と社会の両方の問題
- **推論モデル**は、答えを確かめられる問題での強化学習（検証可能な報酬、GRPO）で作られる
:::

:::sensei
キミのLLMは、知識を持ち（事前学習）、答え方を覚え（SFT）、好みを知った（DPO）。次は、手足を与える番だ。計算機を使ったり、資料を検索したり、自分で考えて道具を選ぶ **エージェント** を作ろう。第1章で計算を間違えたLLMに、電卓を渡すときが来たよ。
:::
