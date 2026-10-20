{"title": "トークナイザーを自作する：BPE", "short": "BPE", "subtitle": "よく出るバイトの組を、くり返し合体させるだけ", "time": "2時間", "env": "cpu", "level": 4, "builds": "バイトレベルBPEトークナイザー（学習・エンコード・デコード）をゼロから実装し、Hugging Faceの `tokenizers` で作ったものと比べる", "theory": ["BPE（バイトペア符号化）のアルゴリズム", "マージ規則の順番と、エンコードの手順", "語彙サイズと系列長のトレードオフ", "トークナイザーが違うモデルの比べ方（1文字あたりの損失）", "Unicode正規化（NFKC）と日本語の注意点"], "python": ["`bytes` と `list(…)` で数の列に", "辞書の `get(キー, 初期値)`", "`max(…, key=…)`", "`bytes.decode(errors=\"replace\")`", "`tokenizers` ライブラリ"]}

:::goal
第2章で、Qwenのトークナイザーが「よく出るバイトの並びを1トークンにまとめている」ことを見ました。この章では、その仕組み **BPE**（Byte Pair Encoding）を自分で実装します。アルゴリズムは驚くほど単純で、「いちばんよく出る隣どうしのペアを合体させる」を何百回もくり返すだけ。最後に、Hugging Faceの高速な実装と比べて、自作GPTをBPEで学習させてみます。
:::

:::minato
第2章で見た「鰯」が3バイトのまま残っていた理由が、ついに分かるんですね。
:::

:::sensei
そう。BPEは、もともと1994年に「データ圧縮」の方法として考えられた。ZIPファイルの親戚だね。それが20年以上たって、LLMの入り口になった。研究の世界では、昔の小さなアイデアが、思わぬところで主役になることがよくある。キミの基本情報の勉強も、いつか思わぬところで主役になるかもしれないよ。
:::

## まずは手で体験

下のデモで、「1回合体」を何回か押してみてください。BPEのすべてがここにあります。

:::widget bpe
:::

1. 隣り合う2つのトークンの組を全部数える
2. いちばん多い組を、新しい1つのトークンに合体させる（この「合体ルール」を覚えておく）
3. 1に戻る

これだけです。合体のたびにトークン数が減り（文章が短くなり）、語彙の種類が増えます。

## 準備：文章をバイトにする

本物のBPEは、文字ではなく **UTF-8のバイト**（0〜255の数）から始めます（第2章）。こうすると、どんな文字でも最初から表せるので、「辞書にない文字」が存在しなくなります。

```python
import re, urllib.request

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

text = load_soseki()
train_text = text[:30000]               # 自作版は遅いので、最初の3万字で学習
ids = list(train_text.encode("utf-8"))
print("文字数：", len(train_text), " バイト数：", len(ids))
print("最初の12バイト：", ids[:12])
```

```output
文字数： 30000  バイト数： 89160
最初の12バイト： [228, 184, 138, 227, 128, 128, 229, 133, 136, 231, 148, 159]
```

3万字が約9万バイト。日本語は1文字がだいたい3バイトでしたね。`228, 184, 138` で「上」、`227, 128, 128` で全角空白です。

## ステップ1：ペアを数える

```python
def get_stats(ids):
    counts = {}
    for pair in zip(ids, ids[1:]):
        counts[pair] = counts.get(pair, 0) + 1
    return counts

stats = get_stats(ids)
top = sorted(stats.items(), key=lambda kv: -kv[1])[:5]
for pair, count in top:
    print(pair, count, "回 →", repr(bytes(pair).decode("utf-8", errors="replace")))
```

```output
(227, 129) 15275 回 → '�'
(227, 130) 3720 回 → '�'
(227, 128) 2119 回 → '�'
(159, 227) 1456 回 → '��'
(139, 227) 1339 回 → '��'
```

:::python get と lambda
`counts.get(pair, 0)` は「辞書に `pair` があればその値、なければ0」を返します。初めて見たペアでもエラーにならずに数え始められる、便利な書き方です。<br>
`sorted(…, key=lambda kv: -kv[1])` は「各要素 `kv` の2番目（回数）にマイナスを付けた値で並べ替える」、つまり回数の多い順です。`lambda` は、その場で使い捨ての小さな関数を作る書き方です。<br>
次の `merge` 関数で使う `while 条件:` は、「条件が正しいあいだ、くり返す」ループです。`for` と違って、何回くり返すかを先に決めずに、位置 `i` を自分で1つ進めたり2つ進めたりしたいときに使います。フローチャートの「条件つきの戻り矢印」そのものです。
:::

一番多いのは `(227, 129)` で、1万5千回以上。これはひらがなの多く（「ぁ」〜「み」あたり）に共通する、最初の2バイトです。ひらがなは日本語で一番よく出てくる文字なので、そのバイトの組も一番多いわけです。バイトの切れ端だけでは文字にならないので `�` と表示されています。4位と5位の `(159, 227)` や `(139, 227)` は、「ある文字の最後のバイト」と「次の文字の最初のバイト」の組です。BPEは文字の切れ目を知らないので、こういう組も数えます。

## ステップ2：合体させる

```python
def merge(ids, pair, new_id):
    out = []
    i = 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            out.append(new_id)     # ペアを見つけたら、新しいIDに置き換えて2つ進む
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out

print(merge([5, 6, 6, 7, 9, 6, 7], (6, 7), 99))
```

```output
[5, 6, 99, 9, 99]
```

`(6, 7)` が2か所とも `99` に置き換わりました。

## ステップ3：くり返して学習する

0〜255はバイトそのものに使っているので、新しいトークンは256番から番号をつけていきます。300回合体させて、語彙556個のトークナイザーを作りましょう。

```python
num_merges = 300
merges = {}                     # (a, b) → 新しいID（合体ルール）
vocab = {i: bytes([i]) for i in range(256)}   # ID → バイト列
work = list(ids)
for k in range(num_merges):
    stats = get_stats(work)
    pair = max(stats, key=stats.get)            # いちばん多いペア
    new_id = 256 + k
    work = merge(work, pair, new_id)
    merges[pair] = new_id
    vocab[new_id] = vocab[pair[0]] + vocab[pair[1]]

print("学習前：", len(ids), "トークン → 学習後：", len(work), "トークン")
print("圧縮率：", round(len(ids) / len(work), 2), "倍")
```

```output
学習前： 89160 トークン → 学習後： 28975 トークン
圧縮率： 3.08 倍
```

`max(stats, key=stats.get)` は「回数が最大のペア」を選ぶ書き方です。CPUで1〜2分かかります。300回の合体で、約9万バイトが約2万9千トークンに、3分の1ほどに縮みました。1トークンに平均3バイト、つまり日本語なら平均1文字ほどです。どんなトークンができたか、のぞいてみましょう。

```python
learned = [vocab[256 + k].decode("utf-8", errors="replace") for k in range(num_merges)]
print("最初の30個：", learned[:30])
print("最後の30個：", learned[-30:])
```

```output
最初の30個： ['�', '�', '�', 'の', 'た', 'い', '。', 'に', 'っ', 'は', 'な', 'て', 'し', 'か', 'で', 'た。', 'と', 'を', '、', 'る', 'う', '�', '私', 'が', 'ら', 'も', 'そ', 'れ', '�', '�']
最後の30個： ['」とい', '�', '会', '意', 'か」\n「', 'より', '知', '�', '私には', '始', 'そこ', '��', '二人', '向', 'ありません', '掛', '来た', '変', '好', '手', 'の上', 'るの', '付', '��', '外', '自分', '�', '��え', '��', '然']
```

最初のうちは、バイトの組み合わせから「の」「た」「い」などの**ひらがな1文字**や、「私」のようなよく出る漢字が作られていきます。後半になると、「ありません」「私には」「自分」「二人」「来た」のような**よく出る言葉や言い回し**がまるごと1トークンになっています。「」とい」「か」\n「」のように、会話のかぎかっこの切れ目をまたいだトークンもできていますね。誰も日本語の文法を教えていないのに、「よく出る組を合体させる」だけで、言葉らしい単位が浮かび上がってきました。

ところどころに残っている `�` は、文字の**途中までのバイト**を合体させたトークンです。たとえば、ある漢字の最初の2バイトは、その漢字の仲間（同じ部首の漢字など）に共通することがあるので、それだけで合体してしまうのです。

## エンコードとデコード

学習した合体ルールを使って、新しい文章をトークンに変える（エンコード）関数と、元に戻す（デコード）関数を作ります。

```python
def decode(token_ids):
    return b"".join(vocab[t] for t in token_ids).decode("utf-8", errors="replace")

def encode(s):
    ids = list(s.encode("utf-8"))
    while len(ids) >= 2:
        stats = get_stats(ids)
        # 学習で「先に」覚えたルール（番号が小さいもの）から順に使う
        pair = min(stats, key=lambda p: merges.get(p, float("inf")))
        if pair not in merges:
            break                       # もう使えるルールがない
        ids = merge(ids, pair, merges[pair])
    return ids

sample = "先生は奥さんと話をしていた。"
tokens = encode(sample)
print(len(sample.encode("utf-8")), "バイト →", len(tokens), "トークン")
print([decode([t]) for t in tokens])
print(decode(tokens) == sample)
```

```output
42 バイト → 8 トークン
['先生は', '奥さん', 'と', '�', '��', 'を', 'して', 'いた。']
True
```

42バイトが8トークンになりました。「先生は」「奥さん」「いた。」がまるごと1トークンです。一方、「話」は学習に使った最初の3万字にあまり出てこなかったので、`�` と `��` の2つのバイトの切れ端に分かれています（3バイトが1＋2に分かれた）。それでも最後の行の `True` のとおり、つなげて読めば元の文章に完全に戻ります。第2章の「鰯」と同じことが、自分のトークナイザーで起きたわけです。

:::theory エンコードは「学習した順番」でルールを使う
エンコードでは、文章をバイトに分解したあと、**学習したときと同じ順番**で合体ルールを適用します。「先に覚えたルール（番号が小さい）」が、学習データでよく出てきた組だからです。順番を変えると、学習時とは違う区切り方になってしまいます。

デコードはもっと簡単で、各トークンのバイト列をつなげて、UTF-8として読むだけです。`errors="replace"` は「途中で切れたバイトがあっても、エラーにせず `�` にする」指定です。LLMが生成の途中でバイトの途中までしか出していない瞬間があるので、これが必要になります。
:::

## 本格版：Hugging Faceの tokenizers

自作版は仕組みを学ぶのに最適ですが、遅すぎて本物のデータには使えません。実務では、高速に書かれたライブラリを使います。Hugging Faceの `tokenizers` は、内部がRustという言語で書かれていて、自作版の何百倍も速く動きます。『こころ』全体で、語彙4000のバイトレベルBPEを学習させてみましょう。

```python
from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders

bpe = Tokenizer(models.BPE())
bpe.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
bpe.decoder = decoders.ByteLevel()
trainer = trainers.BpeTrainer(vocab_size=4000, initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
bpe.train_from_iterator(text.split("\n"), trainer=trainer)

enc = bpe.encode("先生は奥さんと話をしていた。")
print(enc.ids)
print([bpe.decode([i]) for i in enc.ids])
```

```output
[485, 1636, 1891, 685, 264]
['先生は', '奥さんと', '話を', 'していた', '。']
```

一瞬で終わりました。『こころ』全体で学習し、語彙も大きいので、「奥さんと」「話を」「していた」がそれぞれ1トークン。文全体がたった5トークンです。

:::theory 語彙サイズのトレードオフ
語彙を大きくすると、

- 👍 同じ文章が**少ないトークン**で表せる（列が短くなり、計算が軽く、遠くまで見渡せる）
- 👎 埋め込みと出力層が大きくなる（パラメータ＝語彙数×幅）
- 👎 めったに出てこないトークンが増え、その埋め込みが十分に学習されない

実際のLLMの語彙サイズは、GPT-2が約5万、Qwen2.5が約15万、多言語のモデルほど大きい傾向です。日本語・中国語・英語……と多くの言語の「よく出る組」を入れるには、大きな辞書が必要だからです。
:::

## BPEで自作GPTを学習させる

最後に、第12章のGPTを、文字ではなくBPEのトークンで学習させてみましょう。語彙は少し小さめの2000にします。

```python
!wget -q https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/minigpt.py
import math
import torch
from minigpt import GPT

trainer = trainers.BpeTrainer(vocab_size=2000, initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
bpe.train_from_iterator(text.split("\n"), trainer=trainer)

n = int(len(text) * 0.9)
train_ids = torch.tensor(bpe.encode(text[:n]).ids)
val_ids = torch.tensor(bpe.encode(text[n:]).ids)
print("検証データ：", len(text[n:]), "文字 →", len(val_ids), "トークン")
print("1トークンあたり平均", round(len(text[n:]) / len(val_ids), 2), "文字")
```

```output
検証データ： 16247 文字 → 10531 トークン
1トークンあたり平均 1.54 文字
```

1トークンに平均1.5文字ほど詰め込めています。同じ窓の大きさ（64トークン）でも、文字で数えると約1.5倍遠くまで見渡せることになります。

```python
def get_batch(data, batch_size, T, g):
    ix = torch.randint(0, len(data) - T, (batch_size,), generator=g)
    return (torch.stack([data[i:i + T] for i in ix]),
            torch.stack([data[i + 1:i + T + 1] for i in ix]))

@torch.no_grad()
def val_loss_per_token(model, data, T):
    model.eval()
    starts = range(0, len(data) - T - 1, T)
    xs = torch.stack([data[i:i + T] for i in starts])
    ys = torch.stack([data[i + 1:i + T + 1] for i in starts])
    loss = model(xs, ys)[1].item()
    model.train()
    return loss

torch.manual_seed(0)
g = torch.Generator().manual_seed(0)
model = GPT(bpe.get_vocab_size(), block_size=64, n_embd=64, n_head=4, n_layer=2, dropout=0.1)
opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
for step in range(1501):
    x, y = get_batch(train_ids, 32, 64, g)
    _, loss = model(x, y)
    opt.zero_grad()
    loss.backward()
    opt.step()
    if step % 500 == 0:
        vl = val_loss_per_token(model, val_ids, 64)
        print(f"ステップ {step:4d}：検証（1トークンあたり）{vl:.3f}")
```

```output
ステップ    0：検証（1トークンあたり）7.533
ステップ  500：検証（1トークンあたり）4.975
ステップ 1000：検証（1トークンあたり）4.930
ステップ 1500：検証（1トークンあたり）4.976
```

:::minato
4.98……？ 第12章の文字版は3.10だったのに、ずっと悪くなってませんか？
:::

:::sensei
ここが大事な落とし穴だ！ 文字版の損失は「**1文字**あたりの驚き」、BPE版は「**1トークン**あたりの驚き」。1トークンには平均1.5文字入っているから、1トークンを当てるのは、1.5文字ぶんをまとめて当てるのと同じくらい難しい。単位が違うものを比べてはいけない。メートルとインチを比べるようなものだ。
:::

:::theory 1文字あたりの損失に直して比べる
トークナイザーが違うモデルを比べるときは、**文章全体の驚きの合計**を、**文字数**（またはバイト数）で割って比べます。

$$\text{1文字あたりの損失} = \frac{\text{1トークンあたりの損失} \times \text{トークン数}}{\text{文字数}}$$
:::

```python
per_token = val_loss_per_token(model, val_ids, 64)
per_char = per_token * len(val_ids) / len(text[n:])
print(f"1トークンあたり {per_token:.3f} → 1文字あたり {per_char:.3f}")
```

```output
1トークンあたり 4.976 → 1文字あたり 3.225
```

1文字あたりに直すと **約3.23**。第12章の文字版（同じ大きさのモデル・同じステップ数で **3.10**）と比べると、BPE版のほうが**少し悪い**、という結果になりました。

:::minato
あれ？ 本物のLLMはみんなBPEなのに、文字版に負けちゃうんですか？
:::

:::sensei
私もそう予想していた（白状すると、この章を書く前はそう信じていた）。でも、実験の結果はこれだ。予想が外れたときこそ、考えるチャンスだよ。学習の出力をよく見てごらん。1000ステップから1500ステップで、検証の損失が4.930から4.976に**悪化**している。過学習が始まっているんだ。
:::

:::theory BPEの利点が出るのは、データが多いとき
BPEにすると、語彙が2061文字から2000トークンに変わるだけでなく、**1つ1つのトークンが出てくる回数が減ります**。「話を」というトークンは、「話」という文字よりずっと出てくる回数が少ないですよね。『こころ』の14万字では、それぞれのトークンをしっかり学ぶには例が足りず、丸暗記（過学習）しやすくなるのです。

一方、データが何億・何兆トークンもあれば、どのトークンも十分に学べるので、「同じ窓で遠くまで見渡せる」「言い回しを1つの部品として扱える」というBPEの利点が勝ちます。本物のLLMがみなBPEのようなトークナイザーを使うのは、そのためです。**手法の良し悪しは、データの大きさとセットで考える**。これも大事な教訓です。
:::

:::warn 比較の注意
ただし、この比較には少しだけ「ずる」があります。BPEのトークナイザーは『こころ』**全体**（検証データの部分も含む）で学習させたので、検証データによく出る言い回しを知っています。厳密な実験では、トークナイザーも訓練データだけで作るべきです。研究で数字を比べるときは、こういう**データの漏れ**（leakage）に気をつけましょう（第20章で詳しく）。
:::

:::deep 日本語のトークナイズと、ほかの方式
- **事前分割**：GPT-2などは、BPEの前に正規表現で「単語・数字・記号」に分けておき、単語をまたぐ合体を禁止しています（第2章の `' am'` のように空白が単語の前にくっつくのはこのため）。日本語は単語の間に空白がないので、この分割があまり効きません。
- **形態素解析**：日本語では昔から、MeCabなどの辞書を使って単語（形態素）に分ける方法がよく使われてきました。日本語特化のLLMの中には、形態素解析とBPEを組み合わせるものもあります。
- **SentencePiece / Unigram**：BPEとは逆に、大きな語彙から始めて「消しても困らないトークン」を削っていく方式（Unigram言語モデル）もあります。Googleの `SentencePiece` というライブラリが有名で、多くの多言語モデルが使っています。
- **Unicode正規化**：「Ａ」（全角）と「A」（半角）、「ｶ」と「カ」のように、見た目が同じでも文字コードが違う文字があります。`unicodedata.normalize("NFKC", text)` で統一してからトークナイズすると、語彙の無駄が減ります。
:::

:::quiz 合体の順番
BPEのエンコードで、合体ルールを「学習したときと同じ順番」で使うのはなぜ？
:::answer
学習時に先に覚えたルール（番号が小さいもの）ほど、データによく出てくる組だからです。学習時と同じ順番で合体させないと、学習時とは違う区切り方になり、モデルが見たことのないトークン列になってしまいます。
:::

:::quiz 損失の単位
1トークンあたりの損失が3.0、検証データが1万文字・4000トークンでした。1文字あたりの損失は？
:::answer
$3.0 \times 4000 \div 10000 = 1.2$ です。
:::

:::checklist
- BPEのデモで、合体をくり返すと列が短くなるのを見た
- `get_stats` と `merge` を自分で書いて動かした
- 300回の合体で、「ありません」「私には」のようなトークンが生まれるのを見た
- 自作の `encode` と `decode` で、文章を往復できた
- `tokenizers` で高速にBPEを学習させた
- BPE版GPTの損失を「1文字あたり」に直して、文字版と比べた
:::

:::recap
- **BPE**：バイトから始めて、いちばん多い隣どうしのペアを合体させる、をくり返す
- 合体ルールは**学習した順番**でエンコードに使う。デコードはバイトをつなげるだけ
- 語彙サイズは、列の短さとパラメータ数のトレードオフ
- トークナイザーが違うモデルは、**1文字（1バイト）あたりの損失**に直して比べる
- データの**漏れ**に注意。トークナイザーも本当は訓練データだけで作る
:::

:::sensei
トークナイザーまで自作できた。これでキミのGPTは、部品が全部そろったことになる。次の章では、とっておきの実験をする。OpenAIが公開した**本物のGPT-2の重み**を、キミが書いたGPTのコードに読み込むんだ。キミのコードが、本物と同じ答えを出すかどうか。答え合わせの時間だ。
:::
