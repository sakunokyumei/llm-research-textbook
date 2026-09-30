{"title":"10 文字列・データ構造・ファイル","part":"Pythonと研究の道具","goal":"小さなデータを読み、変換し、保存する","prereq":"09"}

## 実験の材料を整理する

点数が一つなら変数一つで十分ですが、100人分なら並びとして扱う方が便利です。順序のある可変の並びがlist、名前から値を引く対応がdict、重複しない要素を集めるのがset、変更しない並びに使うのがtupleです。

```python
scores = [80, 60, 90]
print(scores[0])
print(scores[1:3])
record = {"id": "example-1", "score": 80}
print(record["score"])
print(len(set(["cat", "cat", "dog"])))
```

出力は80、[60,90]、80、2です。添字0が最初で、スライス`[1:3]`は1番から3番の手前まで。辞書は値へアクセスする鍵を持ちます。setは重複を取り除きますが、元の順序を保存するための道具ではありません。

`a=[1,2]`として`b=a`と書くと、bは同じリストを参照します。`b.append(3)`でaも[1,2,3]に見えるのは、一つのリストへ二つの名前が付いたからです。別のリストを作るなら`b=a.copy()`を使います。内側にさらにリストがあるときの浅いコピーと深いコピーの違いにも注意します。

## 文章もデータ

文字列の`split()`は空白で区切り、`strip()`は先頭と末尾の空白を取り除きます。日本語は単語間に空白がないことが多いので、splitだけで日本語の単語分割ができるとは限りません。また、文字数とバイト数とトークン数は異なります。

```python
text = " cat dog cat \n"
words = text.strip().split()
counts = {}
for word in words:
    counts[word] = counts.get(word, 0) + 1
print(counts)
```

catが2、dogが1と数えられます。`get(word,0)`は鍵がなければ0を返します。存在しない鍵を`counts[word]`だけで読もうとするとKeyErrorになります。

## JSONとCSV

JSONは辞書やリストに似た構造を保存する形式、CSVは表を保存する形式です。CSVには引用符や改行を含む値があるため、カンマで単純にsplitするより専用のcsvモジュールを使います。JSONはjsonモジュールで読み書きします。

```python
import json
from pathlib import Path

record = {"seed": 42, "note": "最初の実験"}
path = Path("example_result.json")
path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
loaded = json.loads(path.read_text(encoding="utf-8"))
print(loaded["seed"])
```

importは既存の機能を読み込む命令です。pathlibはパス、jsonはJSON形式を扱います。encodingで文字の保存方法UTF-8を明示すると、環境による文字化けを減らせます。この例は同名ファイルを上書きするので、練習用フォルダで実行します。

## 演習

:::exercise 1・添字
xs=[10,20,30,40]のときxs[2]、xs[:2]、len(xs)を答えてください。
:::answer
30、[10,20]、4です。添字2は三番目を指します。
:::

:::exercise 2・適切な構造
実験IDから損失を引きたいとき、list・dict・setのどれを使うのが自然ですか。
:::answer
dictです。たとえば{"run-1":0.8,"run-2":0.7}。IDが重複すると以前の値を上書きするので、一意性も確認します。
:::

:::exercise 3・参照とコピー
a=[1,2]、b=a、b.append(3)の後にlen(a)はいくつですか。
:::answer
3です。b=aはリスト内容を複製していません。独立した変更が必要ならコピーを作ります。
:::

:::exercise 4・単語を数える
上の頻度計算を"red blue red red"へ適用するとどうなりますか。
:::answer
redが3、blueが1。数え終わった頻度の合計が元の単語数4と一致するかも確認できます。
:::

:::exercise 5・ファイルとメモリ
recordという辞書を変更しただけで、先ほど保存したJSONファイルも自動で変わりますか。
:::answer
変わりません。メモリ上の辞書とストレージ上のファイルは別です。更新した内容を再び書き出す必要があります。
:::

## 到達課題と出典

架空の三つの実験のIDと正解率をJSONへ保存し、読み戻して平均を計算してください。個人の情報を練習データに使う必要はありません。[Python データ構造](https://docs.python.org/3/tutorial/datastructures.html)、[入出力](https://docs.python.org/3/tutorial/inputoutput.html) を参照。
