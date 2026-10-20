{"title": "Python最短ルート", "short": "Python最短ルート", "subtitle": "この教科書で使うPythonだけを、使う順に。困ったときの早見表"}

この教科書は、Pythonを「`print` くらい」しか知らなくても進めるように、新しい書き方が出てくるたびに「Pythonの道具箱」で説明しています。この付録は、それらを1か所にまとめた早見表です。順番に読んでも、困ったところだけ引いても使えます。

:::tip 一番の勉強法
読むだけより、**Colabで実際に打って、少し変えて、壊してみる**ことです。エラーが出たら、それは「Pythonが教えてくれている」サインです。
:::

## 値と変数（第1章）

```python no-run
x = 3              # 整数（int）
y = 2.5            # 小数（float）
name = "ボンゴ"    # 文字列（str）
ok = True          # 真偽値（bool）：True か False
print(x * y, name * 2, ok)   # 7.5 ボンゴボンゴ True
```

`=` は「右の値を、左の名前の箱に入れる」。数学の「等しい」ではありません。等しいかどうかを調べるのは `==` です。

| 計算 | 意味 | 例 |
|---|---|---|
| `+ - * /` | 足す・引く・掛ける・割る | `7 / 2` → `3.5` |
| `//` | 割り算の商（切り捨て） | `7 // 2` → `3` |
| `%` | 割り算の余り | `7 % 2` → `1` |
| `**` | べき乗 | `2 ** 10` → `1024` |

## 文字列（第1〜2章）

```python no-run
s = "吾輩は猫である"
print(len(s))          # 7（文字数）
print(s[0], s[-1])     # 吾 る（0番目、最後）
print(s[2:4])          # は猫（2番目から4番目の手前まで）
print(s.replace("猫", "犬"))
print(f"文字数は{len(s)}です")   # f文字列：{ } の中が値に置き換わる
print("猫".encode("utf-8"))      # b'\xe7\x8c\xab'（バイト列。第2章）
```

**スライス** `s[開始:終わり]` は「終わり」を**含まない**のがポイントです。

## リスト（第1章〜）

```python no-run
fruits = ["りんご", "みかん"]
fruits.append("ぶどう")        # 後ろに追加
print(fruits[1], len(fruits))  # みかん 3
print(fruits[-1])              # ぶどう（後ろから1番目）
print(sorted([3, 1, 2]))       # [1, 2, 3]
```

## 辞書（第1〜2章）

```python no-run
stoi = {"猫": 0, "犬": 1}
print(stoi["猫"])              # 0（キーで値を引く）
stoi["鳥"] = 2                 # 追加
print("犬" in stoi)            # True（キーがあるか）
print(stoi.get("魚", -1))      # -1（なければ初期値）
for key, value in stoi.items():
    print(key, value)
```

## 集合（第2章）

```python no-run
chars = set("あいあう")   # {'あ', 'い', 'う'}（重複が消える）
print(sorted(chars))
```

## 条件分岐 if（全体）

```python no-run
score = 75
if score >= 80:
    print("すばらしい")
elif score >= 60:
    print("合格")
else:
    print("もう一歩")
```

**字下げ（インデント）** が、「ここまでがifの中身」を表します。スペース4つが標準です。HTMLの開始タグと終了タグの代わりに、字下げで範囲を表すのがPythonの特徴です。

## くり返し for / while（第2章〜）

```python no-run
for i in range(3):            # 0, 1, 2
    print(i)

for i, ch in enumerate("猫犬"):   # 番号つきで取り出す
    print(i, ch)                  # 0 猫 / 1 犬

for a, b in zip("先生", "生と"):  # 2つを並べて取り出す
    print(a, b)

n = 0
while n < 3:                  # 条件が正しいあいだ、くり返す
    n += 1                    # n = n + 1 と同じ
```

:::fe トレースの練習
for文やwhile文の変数の変化を、表に書いて追うのは、基本情報の「トレース」そのものです。分からないコードは、`print` を入れて変数の中身を表示しながら、表を書いてみましょう。
:::

## 関数 def（第1章〜）

```python no-run
def greet(name, polite=True):     # polite は初期値つき
    if polite:
        return f"こんにちは、{name}さん"
    return f"よっ、{name}"

print(greet("ミナト"))
print(greet("ミナト", polite=False))
```

`return` で結果を返します。`return` がない関数は `None`（何もない）を返します。

## 内包表記（第2章〜）

```python no-run
squares = [x * x for x in range(5)]              # [0, 1, 4, 9, 16]
evens = [x for x in range(10) if x % 2 == 0]     # [0, 2, 4, 6, 8]
stoi = {ch: i for i, ch in enumerate("猫犬鳥")}  # 辞書も作れる
```

for文で書いたものを1行にまとめた書き方です。読みにくければ、for文で書いてかまいません。

## import（第1章〜）

```python no-run
import math                         # 道具箱をまるごと
from collections import Counter     # 道具箱から1つだけ
import torch.nn.functional as F     # 長い名前に短い別名
print(math.log(math.e), Counter("あいあ"))
```

## ファイルの読み書き（第4章）

```python no-run
with open("memo.txt", "w", encoding="utf-8") as f:   # 書き込み
    f.write("こんにちは\n")
with open("memo.txt", encoding="utf-8") as f:        # 読み込み
    text = f.read()
```

`with` を使うと、終わったときに自動でファイルを閉じてくれます。日本語を扱うときは `encoding="utf-8"` を忘れずに。

## クラス（第9章〜）

```python no-run
class Counter2:
    def __init__(self, start=0):     # 作るときの準備
        self.value = start           # self は「この実物自身」

    def up(self):
        self.value += 1
        return self.value

c = Counter2()        # 設計図から実物（インスタンス）を作る
c.up(); c.up()
print(c.value)        # 2
```

PyTorchのモデルは、`nn.Module` を土台にしたクラスで書きます（第9章）。

```python no-run
import torch.nn as nn

class Tiny(nn.Module):
    def __init__(self):
        super().__init__()           # 土台の準備（お約束）
        self.fc = nn.Linear(3, 1)    # 部品

    def forward(self, x):            # model(x) で呼ばれる計算
        return self.fc(x)
```

## エラーへの備え try / except

```python no-run
try:
    value = int("abc")
except ValueError:
    print("数字に変換できませんでした")
```

## エラーメッセージの読み方

エラーが出たら、**一番下の行**から読みます。

```text
Traceback (most recent call last):
  File "<cell>", line 3, in <module>
    print(stoi["魚"])
KeyError: '魚'
```

- `KeyError: '魚'`：辞書に「魚」というキーがない
- `line 3`：3行目で起きた

| よくあるエラー | 意味 | よくある原因 |
|---|---|---|
| `NameError` | その名前の変数・関数がない | 上のセルを実行していない、つづり間違い |
| `SyntaxError` | 文法の間違い | かっこや `:` の付け忘れ、全角の記号 |
| `IndentationError` | 字下げの間違い | スペースとタブが混ざっている |
| `TypeError` | 型が合わない | 文字列と数字を `+` した、引数の数が違う |
| `KeyError` | 辞書にキーがない | 辞書にない文字を引いた |
| `IndexError` | リストの範囲外 | 長さ3のリストの `[5]` |
| `ModuleNotFoundError` | 道具箱が入っていない | `pip install` していない |

PyTorchやLLMに特有のエラーは、[付録E エラー辞典](e-errors.html)を見てください。

:::quiz 字下げ
次のコードを実行すると、何が表示される？

```python no-run
total = 0
for i in range(1, 4):
    total += i
print(total)
```
:::answer
`6` です。`range(1, 4)` は1, 2, 3なので、1 + 2 + 3 = 6。`print` は字下げされていないので、for文が終わった後に1回だけ実行されます。
:::

:::quiz スライス
`s = "つくってわかる"` のとき、`s[4:]` は？
:::answer
`"わかる"` です。4番目（0から数えて、「わ」）から最後までです。
:::
