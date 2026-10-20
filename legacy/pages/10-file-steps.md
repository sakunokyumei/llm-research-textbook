# ファイル保存を四つの操作へ分ける

最初は読み・手計算10〜15分。PCでの保存と実行は別に15〜30分を目安にします。[第10章の元の例](10u-011.html)へ戻る前に、今日は一段階だけを確かめてもかまいません。

## 1．辞書を文字にする

実験結果 `{"count": 6}` はPythonの辞書です。ファイルに文字として保存するため、`json.dumps`で文字列へ変えます。dumpsの最後のsは文字列を返す操作の目印です。書き込みはまだ行いません。

```python
import json
record = {"count": 6}
text = json.dumps(record)
print(text)
print(type(text).__name__)
```

出力は `{"count": 6}` と `str`。`type`は型を調べ、`.__name__`は型の名前を取り出します。見た目が辞書に似ていても、textは文字列です。

**止まったら：** `import json`はPythonに付属するJSONの機能を読み込む操作です。引用符と括弧は[第8章](08-reader.html)で確認します。

## 2．文字をファイルへ書く

Pathはファイルの場所を表す道具です。`write_text`はその場所へ文字を書きます。練習用フォルダの `practice_count.json` を使い、同名のファイルがあれば上書きされることを確認してください。

```python
import json
from pathlib import Path
record = {"count": 6}
text = json.dumps(record)
path = Path("practice_count.json")
path.write_text(text, encoding="utf-8")
print(path.name)
```

出力は `practice_count.json`。`path.name`はファイル名。encodingは文字を保存する方式の指定で、この例ではUTF-8を使います。JSONの変換と保存を別の行へ分けました。

**止まったら：** PowerShellで `dir` を使い、実行したフォルダにその名前があるかを確認します。PermissionErrorは書き込む権限がないという表示です。自分が書き込める練習用フォルダへ移り、同じ手順を試してください。

## 3．ファイルから文字を読む

`read_text`は保存された文字を読みます。まだ辞書に戻す操作ではありません。

```text
from pathlib import Path
path = Path("practice_count.json")
text = path.read_text(encoding="utf-8")
print(text)
```

**実行順：** 先に段階2を同じ作業フォルダで実行します。FileNotFoundErrorなら保存と読み込みのフォルダ・名前を照合します。この三行だけを別のフォルダで動かしても、保存物は自動で移りません。

## 4．文字を辞書へ戻す

`json.loads`はJSONの文字列をPythonの値へ戻す操作です。ここでは辞書へ戻ってから `count` を取り出します。

```python
import json
text = '{"count": 6}'
loaded = json.loads(text)
print(loaded["count"])
```

出力は6。JSONDecodeErrorは読み込んだ文字がJSONとして読めないという表示です。段階1で作った文字と比べ、手で直す前に元の辞書から作り直してください。KeyErrorなら読み戻した辞書にそのキーがあるか確認します。

|今あるもの|次の操作|操作の後|
|---|---|---|
|辞書|json.dumps|文字列|
|文字列|write_text|ファイルに残る|
|ファイル|read_text|文字列|
|文字列|json.loads|辞書|

## 一つのファイルへまとめて確かめる

上の段階は個別の練習です。保存と読み戻しをまとめると次のコードになります。`file_roundtrip.py`として[第8章の手順](08-reader.html)で保存・実行してください。

```python
import json
from pathlib import Path
record = {"count": 6, "note": "練習"}
text = json.dumps(record, ensure_ascii=False)
path = Path("practice_count.json")
path.write_text(text, encoding="utf-8")
read_back = path.read_text(encoding="utf-8")
loaded = json.loads(read_back)
print(loaded["count"])
```

`ensure_ascii=False`は日本語をそのままJSONの文字へ残す指定です。出力6を確かめたら、countだけを17へ変え、保存前に17になると予想して実行します。

[第10章の自力の問題](10-workshop.html) · [元の講義へ](10u-011.html) · [Python公式JSON](https://docs.python.org/3/library/json.html) · [Pathの読み書き](https://docs.python.org/3/library/pathlib.html#pathlib.Path.write_text)
