{"title": "ミニGPTを鍛える：GPUで本格学習", "short": "ミニGPTを鍛える", "subtitle": "漱石の小説7冊、100万字で、自分のGPTを育てる", "time": "2〜3時間（学習の待ち時間を含む）", "env": "gpu", "level": 4, "builds": "夏目漱石の7作品（約100万字）で学習した、あなただけの「漱石GPT」。トップページで動いているのと同じ設定です", "theory": ["データを増やすと過学習が減る（データの大切さ）", "GPUへの転送と混合精度（float16・autocast）", "チェックポイント（学習途中の保存）", "学習曲線で2つの実験を比べる", "マルチヘッドAttentionの役割分担"], "python": ["`!wget` でファイルを取ってくる", "自作モジュールの `import`", "`torch.autocast` と `GradScaler`", "辞書で設定をまとめて保存"]}

:::goal
いよいよ、第12章で組み立てたGPTを本格的に学習させます。データは『こころ』だけでなく、漱石の7作品・約100万字。無料のGPU（T4）なら数分で学習が終わり、あなたのGPTが「吾輩は」に続けて、漱石風の文章を書き始めます。記録表の検証損失も、ここで大きく更新されます。
:::

:::minato
ついに来ましたね、GPT！ 第1章のQwenと比べると、どれくらいの大きさなんですか？
:::

:::sensei
パラメータは約175万個。Qwen2.5-0.5Bの約280分の1だ。読ませる文章も100万字と、Qwenの数兆トークンに比べれば、太平洋に対するバスタブくらい。でも、仕組みはまったく同じGPTだ。バスタブでも、泳ぎの練習はできる。
:::

## 準備：GPUのランタイムにする

この章は **GPU** を使います。Colabのメニューで「ランタイム」→「ランタイムのタイプを変更」→「T4 GPU」を選んでから始めましょう。

```python
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
print("使う装置：", device)
if device == "cuda":
    print(torch.cuda.get_device_name(0))
```

```output-example
使う装置： cuda
Tesla T4
```

`cpu` と出た人も、この章のコードはそのまま動きます。ただし学習に1時間以上かかるので、GPUが使えるタイミング（混んでいない夜や早朝など）を狙うか、[付録A](a-setup.html)のKaggleを使うのがおすすめです。

:::tip この章の出力について
この章に載せている学習の出力は、教科書の検証用に**CPUで実際に実行した結果**です。GPUで実行すると、計算の順番や数の細かさ（後で説明する混合精度）の違いで、数値が少し変わります。小数点以下2桁目くらいまで似ていれば、正常です。
:::

## 第12章のGPTを取ってくる

第12章で一行ずつ書いたGPTのコードは、教科書のリポジトリに `minigpt.py` というファイルで置いてあります（中身は第12章のコードとまったく同じです）。`wget` というLinuxのコマンドでダウンロードして、`import` します。

```python
!wget -q https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/minigpt.py
from minigpt import GPT
print("ミニGPTの設計図を読み込みました")
```

```output
ミニGPTの設計図を読み込みました
```

:::python 自分のファイルを import する
`import torch` と同じように、同じフォルダにある `minigpt.py` は `import minigpt` や `from minigpt import GPT` で読み込めます。Pythonのファイル（**モジュール**）を分けておくと、ノートブックがすっきりします。Colabの左のフォルダアイコンを押すと、`minigpt.py` がダウンロードされているのが見えます。ダブルクリックすると中身も読めますよ。
:::

## 漱石の7作品を読み込む

第9章までと同じ `load_soseki`（下のセルで定義し直します）を使って、7作品をまとめて読み込みます。

```python
import re, math, urllib.request

def load_soseki(file_id="773_ruby_5968"):
    url = ("https://raw.githubusercontent.com/aozorahack/aozorabunko_text/master/"
           f"cards/000148/files/{file_id}/{file_id}.txt")
    text = urllib.request.urlopen(url).read().decode("cp932")
    text = text.split("-------------------------------------------------------")[2]
    text = text.split("底本：")[0]
    text = re.sub(r"《.*?》", "", text)
    text = re.sub(r"※?［＃.*?］", "", text)
    text = text.replace("｜", "").replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

works = {
    "こころ": "773_ruby_5968",
    "坊っちゃん": "752_ruby_2438",
    "吾輩は猫である": "789_ruby_5639",
    "三四郎": "794_ruby_4237",
    "草枕": "776_ruby_6020",
    "夢十夜": "799_ruby_6024",
    "それから": "56143_ruby_50824",
}
texts = {}
for title, file_id in works.items():
    texts[title] = load_soseki(file_id)
    print(f"{title}：{len(texts[title]):,} 文字")

all_text = "\n\n".join(texts.values())
chars = sorted(set(all_text))
V = len(chars)
stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for ch, i in stoi.items()}
print(f"合計：{len(all_text):,} 文字、語彙：{V} 文字")
```

```output
こころ：162,467 文字
坊っちゃん：88,997 文字
吾輩は猫である：321,104 文字
三四郎：171,888 文字
草枕：85,547 文字
夢十夜：16,197 文字
それから：174,641 文字
合計：1,020,853 文字、語彙：3665 文字
```

約102万字、語彙は3,665文字になりました。『こころ』だけのとき（2,061文字）より、使われる漢字が増えています。

次に、データを訓練用と検証用に分けます。これまでの章と成績を比べられるように、**検証データは『こころ』の最後の10%のまま**にしておきます。ほかの作品は、それぞれ前90%を訓練に使います。

```python
def encode(s):
    return torch.tensor([stoi[c] for c in s], dtype=torch.long)

kokoro = texts["こころ"]
nk = int(len(kokoro) * 0.9)
kokoro_train = encode(kokoro[:nk])
kokoro_val = encode(kokoro[nk:])          # 記録表と同じ検証データ

others = [encode(t[:int(len(t) * 0.9)]) for title, t in texts.items() if title != "こころ"]
all_train = torch.cat([kokoro_train] + others)
print("『こころ』だけの訓練データ：", len(kokoro_train))
print("7作品の訓練データ：        ", len(all_train))
```

```output
『こころ』だけの訓練データ： 146220
7作品の訓練データ：         918754
```

## 学習の道具をそろえる

ミニバッチを作る関数、検証損失を測る関数、学習率スケジュール（第10章）を用意します。検証損失は、検証データを128文字ずつに区切って**全部**で測るので、毎回同じ値になります。

```python
block_size = 128    # 何文字前まで見るか（窓の大きさ）
batch_size = 32     # 1回に何個の窓を学習するか

def get_batch(data, g):
    ix = torch.randint(0, len(data) - block_size - 1, (batch_size,), generator=g)
    x = torch.stack([data[i:i + block_size] for i in ix])
    y = torch.stack([data[i + 1:i + block_size + 1] for i in ix])
    return x.to(device), y.to(device)

@torch.no_grad()
def val_loss(model, data):
    model.eval()
    starts = range(0, len(data) - block_size - 1, block_size)
    xs = torch.stack([data[i:i + block_size] for i in starts])
    ys = torch.stack([data[i + 1:i + block_size + 1] for i in starts])
    total = 0.0
    for j in range(0, len(xs), 64):
        _, loss = model(xs[j:j + 64].to(device), ys[j:j + 64].to(device))
        total += loss.item() * len(xs[j:j + 64])
    model.train()
    return total / len(xs)

def lr_at(step, max_lr, total, warmup=200):
    if step < warmup:
        return max_lr * step / warmup
    progress = (step - warmup) / (total - warmup)
    return max_lr * 0.5 * (1 + math.cos(math.pi * progress))
```

`.to(device)` で、データをGPUのメモリに送っています。GPUで計算するには、**モデルとデータの両方**がGPUにいる必要があります。

## 学習ループ（GPU対応版）

第10章の学習ループに、GPUで速く学習するための工夫（**混合精度**）を足したものです。

```python
def train(train_data, max_iters, lr=1e-3, seed=0, log_every=500):
    torch.manual_seed(seed)
    g = torch.Generator().manual_seed(seed)
    model = GPT(V, block_size=block_size, n_embd=128, n_head=4, n_layer=4, dropout=0.1).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.1)
    scaler = torch.amp.GradScaler(device, enabled=(device == "cuda"))
    history = []
    for step in range(max_iters + 1):
        for group in opt.param_groups:
            group["lr"] = lr_at(step, lr, max_iters)
        x, y = get_batch(train_data, g)
        with torch.autocast(device_type=device, dtype=torch.float16, enabled=(device == "cuda")):
            _, loss = model(x, y)
        opt.zero_grad(set_to_none=True)              # 勾配を0にする代わりに捨てる（第8章の W.grad = None と同じ）
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt)
        scaler.update()
        if step % log_every == 0:
            vl = val_loss(model, kokoro_val)
            history.append((step, loss.item(), vl))
            print(f"ステップ {step:5d}：訓練 {loss.item():.3f}  検証（こころ）{vl:.3f}")
    return model, history
```

:::theory 混合精度：数の細かさを半分にして速くする
コンピュータの小数（浮動小数点数）には、使うビット数によって種類があります。

| 形式 | ビット数 | 1個のバイト数 | 特徴 |
|---|---|---|---|
| float32（単精度） | 32 | 4 | PyTorchの標準。正確 |
| float16（半精度） | 16 | 2 | メモリ半分。T4などのGPUで特に速い。表せる範囲が狭い |
| bfloat16 | 16 | 2 | 表せる範囲はfloat32並み、細かさは粗い。新しいGPU向け |

`torch.autocast(…, dtype=torch.float16)` の中では、行列の掛け算などの重い計算を、自動的にfloat16で行います。パラメータそのものや、細かさが大事な計算（損失の合計など）はfloat32のまま。2つの精度を混ぜて使うので **混合精度**（mixed precision）と呼びます。T4ではfloat32の何倍も速く計算できます。

float16は小さな数を表すのが苦手で、とても小さな勾配が0になってしまう（第5章のアンダーフロー！）ことがあります。そこで `GradScaler` が、損失を一時的に何千倍にもしてから `backward()` し、更新の前に元に戻します。勾配を「拡大鏡で見る」作戦です。

CPUのときは `enabled=False` なので、これらは何もしません。同じコードがCPUでもGPUでも動きます。
:::

:::fe 浮動小数点数の形式
基本情報で、浮動小数点数は「符号部・指数部・仮数部」でできていると習いましたね。float16は指数部5ビット・仮数部10ビット、bfloat16は指数部8ビット・仮数部7ビットです。指数部が多いほど**表せる範囲**が広く、仮数部が多いほど**細かさ**が高い。bfloat16は「範囲は広く、細かさは我慢」という、深層学習向けに考えられた形式です（Googleが考案しました）。第19章の量子化で、この話の続きをします。
:::

## 実験1：『こころ』だけで学習

まずは、これまでの章と同じ『こころ』だけで学習させます。これで、これまでのモデルとの公平な比較ができます。

```python test:max_iters=3000)=>max_iters=20)
model_k, hist_k = train(kokoro_train, max_iters=3000)
```

```output
ステップ     0：訓練 8.217  検証（こころ）8.207
ステップ   500：訓練 3.089  検証（こころ）3.218
ステップ  1000：訓練 2.622  検証（こころ）3.081
ステップ  1500：訓練 2.303  検証（こころ）3.075
ステップ  2000：訓練 2.233  検証（こころ）3.075
ステップ  2500：訓練 2.099  検証（こころ）3.092
ステップ  3000：訓練 2.091  検証（こころ）3.091
```

## 実験2：7作品で学習

次に、同じモデル・同じ設定で、データだけを7作品（約6.3倍）に増やします。検証データは同じ『こころ』の最後の10%です。

```python test:max_iters=5000)=>max_iters=20)
model_all, hist_all = train(all_train, max_iters=5000)
```

```output
ステップ     0：訓練 8.220  検証（こころ）8.207
ステップ   500：訓練 3.724  検証（こころ）3.465
ステップ  1000：訓練 3.371  検証（こころ）3.107
ステップ  1500：訓練 3.158  検証（こころ）2.962
ステップ  2000：訓練 3.157  検証（こころ）2.850
ステップ  2500：訓練 3.119  検証（こころ）2.767
ステップ  3000：訓練 2.972  検証（こころ）2.710
ステップ  3500：訓練 3.007  検証（こころ）2.679
ステップ  4000：訓練 2.832  検証（こころ）2.653
ステップ  4500：訓練 2.873  検証（こころ）2.638
ステップ  5000：訓練 2.876  検証（こころ）2.635
```

T4 GPUなら数分、CPUなら1時間ほどかかります。待っている間に、次の節を読んでおきましょう。

:::tip GPUが使えない日は、短く試す
CPUしか使えないときは、`max_iters=5000` を `max_iters=1000` に変えれば、15分ほどで終わります。検証損失は上の表ほどは下がりませんが、「7作品のほうが、同じステップ数でも良くなる」傾向は確かめられます。完全版は、GPUが使える日にもう一度やればOKです。
:::

## 大事なモデルを保存する

比べたり書かせたりする前に、**まず保存**しましょう。せっかく学習したモデルも、Colabのセッションが切れると消えてしまいます。保存先はGoogleドライブです（第10章と同じ手順）。今回は、モデルの中身だけでなく、**語彙と設定もいっしょに**保存します。第24章で、このファイルからブラウザで動くモデルを作ります。

```python
from google.colab import drive
drive.mount("/content/drive")
```

```python
import os
save_dir = "/content/drive/MyDrive/tsukuru-llm"
os.makedirs(save_dir, exist_ok=True)
checkpoint = {
    "model": model_all.state_dict(),
    "chars": chars,
    "config": {"vocab_size": V, "block_size": block_size, "n_embd": 128, "n_head": 4, "n_layer": 4, "dropout": 0.1},
}
torch.save(checkpoint, f"{save_dir}/soseki_gpt.pt")
print("保存しました：", round(os.path.getsize(f"{save_dir}/soseki_gpt.pt") / 1e6, 1), "MB")
```

```output
保存しました： 8.1 MB
```

:::tip チェックポイント
学習の**途中**でも、定期的に保存しておくと安心です。これを **チェックポイント** と言います。Colabの無料版は、長い学習の途中で切断されることがあります。たとえば `train` 関数の中で、検証損失が過去最良を更新したときだけ `torch.save` するようにしておけば、切断されても「一番良かったモデル」は手元に残ります。大きなモデルの学習では、チェックポイントは命綱です。
:::

:::tip Kaggleで学習した人は
Kaggleには `google.colab` がないので、`drive.mount` のセルは飛ばし、保存のセルの `save_dir` を `"/kaggle/working"` に変えて実行します。保存した `soseki_gpt.pt` は、画面右の「Output」からダウンロードして、Googleドライブに `tsukuru-llm` というフォルダを作ってアップロードしておきましょう（第24章で使います）。
:::

### 続きを別の日にやるとき

この章は長いので、ここで一度休んでもOKです。次の日に続きをやるときは、次の順にセルを実行してから、下のセルで保存したモデルを読み込みます。

1. 「準備：GPUのランタイムにする」「第12章のGPTを取ってくる」のセル
2. 「漱石の7作品を読み込む」の2つのセル（データと語彙を作り直す。保存したときと同じ語彙になります）
3. 「学習の道具をそろえる」「学習ループ（GPU対応版）」のセル（関数を作るだけなので、すぐ終わります）
4. 「大事なモデルを保存する」の節は、`drive.mount` のセル**だけ**（保存のセルは実行しない）

実験1・実験2の学習のセルと、保存のセルは**飛ばします**。

```python
save_dir = "/content/drive/MyDrive/tsukuru-llm"
ckpt = torch.load(f"{save_dir}/soseki_gpt.pt", map_location=device)
model_all = GPT(**ckpt["config"]).to(device)     # 保存した設定で、同じ形のGPTを作る
model_all.load_state_dict(ckpt["model"])         # 学習した中身を流し込む
print("読み込みました。語彙は同じ？", ckpt["chars"] == chars)
```

```output
読み込みました。語彙は同じ？ True
```

`GPT(**ckpt["config"])` の `**` は、第3章の `model(**inputs)` と同じ「辞書の中身を名前つきの引数として渡す」書き方です。`GPT(vocab_size=3665, block_size=128, …)` と書いたのと同じ意味になります。なお、次の節の「2つの実験を比べる」グラフは、学習中の記録（`hist_k` と `hist_all`）が必要なので、休んだ後は描けません。その節は `!pip install` のセルだけ実行して、グラフは教科書の図で確かめましょう。その後の「書かせてみる」「ヘッドたちの役割分担を見る」は、そのまま実行できます。

## 2つの実験を比べる

```python
!pip install -q matplotlib-fontja
```

```python
import matplotlib.pyplot as plt
import matplotlib_fontja

plt.figure(figsize=(6.5, 3.8))
for hist, label in [(hist_k, "『こころ』だけ"), (hist_all, "7作品")]:
    steps = [h[0] for h in hist]
    plt.plot(steps, [h[2] for h in hist], marker="o", label=label + "（検証）")
plt.axhline(3.177, color="gray", linestyle="--", label="第10章のMLP")
plt.xlabel("ステップ"); plt.ylabel("検証損失（こころ）")
plt.ylim(2.4, 4.5)
plt.legend(); plt.title("データを増やすと、同じモデルがもっと賢くなる")
plt.show()
```

![2つの実験の検証損失の比較。7作品で学習したほうが、最後まで検証損失が下がり続ける](img/figs/13-train-gpt/cell12_0.png)

:::theory 結局、データがいちばん効く
第10章では、過学習を抑えるためにドロップアウトや重み減衰を使いました。でも、最も強力な治療法は **データを増やすこと** です。

- 『こころ』だけ：14.6万字を何十周もするので、途中から丸暗記が始まる
- 7作品：92万字あるので、同じ文章を見る回数が少なく、丸暗記しにくい。しかも、漱石の文体という「共通の特徴」をいろいろな文章から学べる

『こころ』の検証データには『こころ』の続きが書いてあるのに、『こころ』以外の作品を読ませたほうが、それを上手に予測できるようになる。不思議ですが、人間も同じですね。同じ作家の本をたくさん読むと、その作家の次の一文が予想できるようになります。

LLMの研究で「モデルの大きさ」と同じくらい「**データの量と質**」が重視されるのは、このためです（第15章のスケーリング則で、もう少し詳しく話します）。
:::

## 書かせてみる

7作品で学習したGPTに、いろいろな書き出しを与えてみましょう。

```python
def write(model, start, n=150, temperature=0.8, seed=0):
    torch.manual_seed(seed)
    model.eval()
    idx = encode(start)[None].to(device)
    out = model.generate(idx, max_new_tokens=n, temperature=temperature)
    return "".join(itos[i] for i in out[0].tolist())

for start in ["吾輩は", "先生は", "　山路を登りながら"]:
    print(write(model_all, start))
    print("-" * 40)
```

```output
吾輩はあらず御客さんが近頃のうちに、あって、車屋へ帰りになって橋石でも婆さん、あたりするつもりではないから、元の御飯が食うと大きな声だけで、あんな食うじゃないか」
「御茶を飲んでしたか」
「うん、どうかも知れない。え？」
「ええ、よし子さんに御用はありません。この原口さんのおさんが、どこかへ行ってやっぱい
----------------------------------------
先生はある。そうかして先生のうちに、あっちからそうなりみをしているで、先生は、あたりすこぶる熊本がたいって、性の目を凹ました」「私はあの時のあいです」と言った。奥さんはまた聞いたが、「帽子のうちでも亡くなったのかい」と、しばらくすると、「あなたはどうしてもお宅から原口さんの事がないんですか」と与次郎のほう
----------------------------------------
　山路を登りながら、大きな木の中に近い寂として、あった、室の一方へ灯をとり抜いで、婆さんと車を向けた。
「ああなたは朝もう一つすが、何だか行くかい」と云った。代助は単簡に答えた。
「今度は何がたくって、大きくまで中梃なものだい」と、しばらくすると、額を手にした。
「そう。この原口さんの事がないんだ」
「わたしにしてい
----------------------------------------
```

:::python encode(start)[None]
`encode(start)` は、文字のIDを並べた1次元のテンソル（形 `[T]`）です。でもGPTは「何個かの文章をまとめて」受け取る形 `[B, T]` を期待しています。`[None]` を付けると、先頭に長さ1の軸が増えて `[1, T]`（文章1個ぶん）になります。第12章で `torch.tensor([[…]])` と、かっこを二重にしていたのと同じ意味です。
:::

:::sensei
どうだい、キミのGPTの「作品」は？ 第4章の「私は腎臓の運ばなた。」から、ずいぶん遠くまで来ただろう？ 文法はだいぶ整い、漱石らしい言い回しも出てくる。ただし、話の筋はまだ迷子だ。175万個のつまみと100万字では、このあたりが限界。ChatGPTが賢いのは、この何万倍ものつまみとデータがあるからなんだよ。
:::

## 記録表

| モデル | 章 | パラメータ | 学習データ | 検証データの損失 |
|---|---|---|---|---|
| でたらめ | 5 | — | — | 7.631 |
| bigram（数える） | 5 | — | こころ | 3.581 |
| MLP（全部の治療） | 10 | 66万 | こころ | 3.177 |
| Attention 1ヘッド | 11 | 28万 | こころ | 3.31 |
| **ミニGPT（4層・4ヘッド）** | **13** | **約175万** | **こころ** | **3.075**（1500〜2000ステップ） |
| **ミニGPT（4層・4ヘッド）** | **13** | **約175万** | **漱石7作品** | **2.635**（5000ステップ） |

※ 第13章のモデルは語彙が3,665文字に増えているので、厳密には少しだけ不利な条件での比較です。数値は教科書の検証環境（CPU）での実測値です。GPUで実行したあなたの数値も、ぜひ表に書き足してください。

第10章のMLP（3.177）から、『こころ』だけのGPTで **3.075**、7作品のGPTで **2.635**。パープレキシティにすると、24択から約14択へ。数えるbigram（36択）から比べると、迷いが半分以下になりました。

## ヘッドたちの役割分担を見る

最後に、学習したGPTの4つのヘッドが、それぞれどこに注目しているかを見てみましょう（第11章の1ヘッドとの違いに注目）。

```python
import matplotlib.pyplot as plt
import matplotlib_fontja                          # グラフで日本語を表示する（上の !pip install が必要）

sample = "先生は奥さんの顔を見て、彼女に話しかけた。"
idx = encode(sample)[None].to(device)
model_all.eval()
with torch.no_grad():
    model_all(idx)

fig, axes = plt.subplots(1, 4, figsize=(16, 4.4))
heads = model_all.blocks[-1].attn.heads          # 最後の層の4つのヘッド
for h, ax in enumerate(axes):
    ax.imshow(heads[h].wei[0].float().cpu(), cmap="Oranges")
    ax.set_xticks(range(len(sample))); ax.set_xticklabels(list(sample), fontsize=7)
    ax.set_yticks(range(len(sample))); ax.set_yticklabels(list(sample), fontsize=7)
    ax.set_title(f"ヘッド {h}")
plt.tight_layout()
plt.show()
```

![最後の層の4つのヘッドの注目の仕方。ヘッド0は文の頭の「先」を、ヘッド1と2は「先生は」の「は」をよく見て、ヘッド3は自分の近くの文字に広く注目している](img/figs/13-train-gpt/cell14_0.png)

ヘッドによって、注目の仕方が違います。上の図では、ヘッド0は文の頭の「先」を、ヘッド1と2は「先生は」の「は」（主語の区切り）をよく見ています。ヘッド3は、自分の近くの文字に広く注目しています。誰も役割を割り振っていないのに、学習の中で**自然に分業**が生まれているのです。あなたのモデルの図は、これとは違う分業になっているかもしれません。どのヘッドがどこを見ているか、観察してみましょう。

:::try GPUがあるなら、もっと大きく
GPUが使えるなら、モデルを大きくしてみましょう。`train` 関数はそのままで、次のセルを実行するだけです（大きなモデル用の `train_big` を新しく作ります）。このセルは `block_size` と `batch_size` を書き換えるので、必ず**上の保存が終わってから**試しましょう。後で保存のセルを実行し直すと、設定の記録がずれて、第24章で読み込めなくなります。

```python gpu-only
block_size = 256
batch_size = 64

def train_big(train_data, max_iters, lr=6e-4, seed=0):
    torch.manual_seed(seed)
    g = torch.Generator().manual_seed(seed)
    model = GPT(V, block_size=block_size, n_embd=384, n_head=6, n_layer=6, dropout=0.2).to(device)
    print("パラメータの数：", sum(p.numel() for p in model.parameters()))
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.1)
    scaler = torch.amp.GradScaler(device, enabled=(device == "cuda"))
    for step in range(max_iters + 1):
        for group in opt.param_groups:
            group["lr"] = lr_at(step, lr, max_iters)
        x, y = get_batch(train_data, g)
        with torch.autocast(device_type=device, dtype=torch.float16, enabled=(device == "cuda")):
            _, loss = model(x, y)
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt)
        scaler.update()
        if step % 500 == 0:
            print(f"ステップ {step:5d}：訓練 {loss.item():.3f}  検証（こころ）{val_loss(model, kokoro_val):.3f}")
    return model

model_big = train_big(all_train, max_iters=5000)
```

パラメータは約1360万個。T4で20〜30分ほどかかります（`nvidia-smi` で、GPUが働いている様子も見てみましょう）。検証損失は、さらに下がるでしょうか？ それとも、データに対してモデルが大きすぎて、過学習するでしょうか？ 予想してから試してみてください。結果は、あなただけの研究データです。
:::

:::warn よくあるつまずき
- **`RuntimeError: Expected all tensors to be on the same device`**：モデルとデータの片方だけがGPUにいます。`model.to(device)` と、`get_batch` の中の `.to(device)` を確認しましょう。
- **`CUDA out of memory`**：GPUのメモリが足りません。`batch_size` や `block_size` を半分にしてみましょう。それでもダメなら、「ランタイム」→「セッションを再起動する」でメモリを空にしてから、上から実行し直します。
- **`No such file or directory: 'minigpt.py'`** / **`ModuleNotFoundError: No module named 'minigpt'`**：`wget` のセルを実行し忘れているか、ダウンロードに失敗しています。そのセルをもう一度実行しましょう。それでも同じなら、`!wget` の行から `-q`（静かに実行する指定）を消して実行すると、失敗の理由（`ERROR 404` など）が表示されます。どうしてもダウンロードできないときは、第12章の5つのクラス（`Head` から `GPT` まで）のセルをこのノートブックに貼って実行し、`from minigpt import GPT` の行を消せば、同じように動きます。
- **学習の途中で切断された**：無料のColabではよくあります。チェックポイントの節を参考に、途中経過を保存するようにしましょう。
:::

:::quiz データとモデル
同じモデルなのに、7作品で学習したほうが『こころ』の検証損失が良くなったのはなぜ？
:::answer
データが多いと、同じ文章を何度も見て丸暗記する（過学習する）ことが減り、漱石の文体に共通する特徴をいろいろな文章から学べるからです。最も強力な過学習対策は、データを増やすことです。
:::

:::quiz 混合精度
`GradScaler` は何のために使う？
:::answer
float16では非常に小さな数が0になってしまう（アンダーフロー）ので、勾配が消えないように、損失を一時的に大きく拡大してから逆伝播し、更新の前に元の大きさに戻すためです。
:::

:::checklist
- ColabのGPU（T4）でミニGPTを学習させた（またはCPUで完走した）
- 『こころ』だけの実験と、7作品の実験を比べた
- 「データを増やすと過学習が減る」を学習曲線で確かめた
- 自分のGPTに漱石風の文章を書かせた
- 語彙・設定ごとモデルをGoogleドライブに保存した
- 記録表に、自分の実験の数値を書き足した
:::

:::recap
- GPUで学習するには、**モデルとデータを `.to(device)`** で送る
- **混合精度**（float16 ＋ `autocast` ＋ `GradScaler`）で、T4での学習が速くなる
- 同じモデルでも、**データを増やす**と過学習が減り、検証損失が大きく下がる
- 学習したモデルは、**語彙と設定もいっしょに**保存しておく（チェックポイント）
- マルチヘッドAttentionの各ヘッドは、学習の中で自然に役割を分担する
:::

:::sensei
第3部、完走おめでとう！ キミはもう「GPTをゼロから作って学習させたことがある人」だ。世界中を探しても、そう多くはない。次の第4部では、自作GPTを「本物」に近づける。まずはトークナイザー。いまは1文字＝1トークンだけど、本物のLLMはBPEを使っていた（第2章）。それを自分で作るところからだ。
:::
