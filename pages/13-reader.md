# 13 計算量・検索・SQLの入口：まとめて参照

長い参照ページです。初めて学ぶときは[小ページの順序](13-algorithms.html)を使い、ここへ戻って式やコードを引けます。


## 10件で速くても、100万件では

名簿から名前を探す方法を考えます。先頭から順に見るなら、最悪では全件を読みます。件数をnとすると、必要な操作はおおむねnに[比例](reference.html#term-proportion)します。これをO(n)と書きます。Oは、入力が大きくなったときの増え方を表す記法で、秒数そのものではありません。

全組合せを比較する二重ループならO(n²)。nが10倍になると操作量はおおむね100倍です。整列済みの名簿を半分ずつ絞る二分探索ならO(log n)。ただし並べ替えの費用や、比較の費用は別途考えます。

リストで「既に見た値か」を毎回調べると全体でO(n²)になる場合があります。ハッシュ集合setなら、通常の実装で平均的な一回の検索はO(1)を期待できます。ただし最悪ケースまで常に一定時間という保証ではありません。[計算量](reference.html#term-complexity)とメモリ量を両方見ます。

`item in seen`は「itemがseenに含まれるか」、`item not in seen`は「含まれないか」を調べます。`not in`は二語で一つの判定です。たとえばseenが{"a"}なら、"b" [not in](reference.html#term-membership) seenはTrue、"a" not in seenはFalse。`seen.add(item)`は集合へその値を追加し、既に同じ値があれば二つには増やしません。not in・集合への追加へ戻れます。仕様：[Pythonの所属判定](https://docs.python.org/3/reference/expressions.html#membership-test-operations)。

```python
items = ["a", "b", "a", "c"]
seen = set()
unique = []
for item in items:
    if item not in seen:
        seen.add(item)
        unique.append(item)
print(unique)
```

順序を保ったまま重複を取り除き、['a','b','c']になります。setだけへ変換する場合との違いを確認してください。

## 表へ質問する言語

実験ID、手法、[損失](reference.html#term-loss)を表に保存すると「手法ごとの平均を見たい」という要求が出ます。[SQL](reference.html#term-sql)は表に対する問い合わせを書く言語です。SELECTは出す列、FROMは対象の表、WHEREは行の条件、GROUP BYはまとめる単位を指定します。

下のsqlite3はPythonに付属する、表を保存・検索する道具です。connectで作業先を開き、":memory:"は今回は保存ファイルを作らず作業中だけ表を持つ指定です。executeは命令を一つ実行し、executemanyは複数のデータを順に渡します。CREATE TABLEは表を作り、TEXTとREALは文字列と[実数](reference.html#term-real)の列、INSERT INTOは行を追加します。AVGは平均、COUNT(*)は行数。fetchallは結果の全行を取り出し、closeは接続を閉じます。この小節は、表の作成→行の追加→集計の三回に分けて読めます。

```python
import sqlite3
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE runs (method TEXT, loss REAL)")
db.executemany("INSERT INTO runs VALUES (?, ?)",
               [("base", 2.0), ("base", 1.8), ("new", 1.7)])
rows = db.execute("SELECT method, AVG(loss), COUNT(*) FROM runs GROUP BY method").fetchall()
print(rows)
db.close()
```

baseは平均1.9・二件、newは1.7・一件です。一件と二件の平均だけで新手法が確実によいとは言えません。`?`は値を安全に渡すための場所です。文字列を直接つなげてSQLを作るより、値と命令を分けられます。

正規表現は文字列のパターンを表す記法です。`r"\d+"`は数字の並びに対応します。ただし正規表現一つで個人情報をすべて発見したり、日本語の意味を理解したりはできません。候補抽出の後に確認が必要です。

## 演習

:::exercise 1・増え方
O(n²)の処理で入力を3倍にすると、主な操作量は何倍になりますか。
:::answer
約9倍です。小さな入力では固定費が支配することもあり、実測秒数が厳密に9倍になるとは限りません。
:::

:::exercise 2・二分探索の前提
整列されていないリストで中央から半分ずつ捨ててよいですか。
:::answer
よくありません。捨てる側に目標がないと言える順序関係が必要です。先に整列するなら、その費用も含めます。
:::

:::exercise 3・SQLの件数
平均と一緒にCOUNT(*)を返すのはなぜですか。
:::answer
何件から計算した平均かを確認するためです。欠測や実行失敗により、一方の手法だけ集計対象が少なくなる場合もあります。
:::

:::exercise 4・検索の適用範囲
完全一致の重複をsetで除けば、言い換えた文章の重複もなくなりますか。
:::answer
なくなりません。文字列が違えば別の値です。近い文章の検出には別の類似度や検証が必要です。
:::

## 時間を測る小さな練習

`time`は時間を扱う[モジュール](reference.html#term-module)です。`time.perf_counter()`で前後の時計の値を取り、その差を秒で読みます。絶対的な日時ではなく、処理の前後の差だけを使います。

```python
import time
items = list(range(1000))
start = time.perf_counter()
seen = set()
unique = []
for item in items:
    if item not in seen:
        seen.add(item)
        unique.append(item)
elapsed = time.perf_counter() - start
print(len(unique), elapsed)
```

`list(range(1000))`は0〜999の並びをリストにします。最初の出力は1000、次は経過秒数で、機器や実行ごとに変わります。1000を2000、4000へ変えて各5回記録してください。短い処理では他のアプリの影響も大きいので、一回だけの秒数から増え方を決めません。[時計の仕様](https://docs.python.org/3/library/time.html#time.perf_counter)を参照しています。

## 到達課題と出典

1000、2000、4000件で重複除去を計測し、予測と違う原因を考えてください。時間計測は何回か繰り返し、装置と入力も記録します。[Python sqlite3](https://docs.python.org/3/library/sqlite3.html)、[Python re](https://docs.python.org/3/library/re.html) が仕様の参照先です。
