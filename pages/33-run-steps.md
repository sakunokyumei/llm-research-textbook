# 短い実行を保存し、次の日から続ける

説明10〜15分。実行時間はPCによります。最初の10更新は動作確認で、性能評価ではありません。[PCの準備](pc-practice.html)のテストを通してから進めます。以下はWindowsで同じ仮想環境のPythonを直接使う例です。macOS/Linuxでは起動名を `.venv/bin/python` に替えます。

## 1．10更新だけを保存する

```text
.venv\Scripts\python.exe labs/tiny_transformer.py --steps 10 --seed 0 --out labs/runs/my-first-10
```

`--steps`は更新の合計回数、`--seed`は学習に使う乱数の開始設定、`--out`は保存先です。一行だけを実行し、完了してからエクスプローラーで `labs/runs/my-first-10` を開きます。

|保存物|何を見るか|
|---|---|
|metrics.json|設定、進んだstep、測定値|
|checkpoint.pt|再開用の重み・更新の状態・乱数など|

表示された文章をメモへ残します。低い正解率でも、この段階は実行・保存の確認です。同じ保存先で繰り返すと上書きするため、新しい実験には新しいフォルダ名を付けます。

## 2．終えてから、合計20更新へ続ける

```text
.venv\Scripts\python.exe labs/tiny_transformer.py --steps 20 --resume labs/runs/my-first-10/checkpoint.pt --out labs/runs/my-resumed-20
```

`--resume`は自分で保存した再開ファイルです。合計20を指定するので、追加するのは10更新。再開では保存したモデル設定と乱数状態を引き継ぎます。別の設定を新しい実験として変える場合と区別します。

**止まったら：** FileNotFoundErrorなら元のフォルダにcheckpoint.ptがあるか確認します。`steps is smaller...` は保存時より小さい合計を指定したという意味です。10更新の保存なら20以上など、目的の合計を指定します。外部から入手した未確認のcheckpointをこの読み込みへ渡しません。

## 3．連続20更新の条件と照合する

```text
.venv\Scripts\python.exe labs/tiny_transformer.py --steps 20 --seed 0 --out labs/runs/my-continuous-20
.venv\Scripts\python.exe labs/check_resume.py labs/runs/my-continuous-20/checkpoint.pt labs/runs/my-resumed-20/checkpoint.pt
```

check_resume.pyは自分で作った二つの重みを読み、形と値を比べる小さな確認用プログラムです。版・装置・コード・データが同じ条件の照合です。表示が一致しなければ、設定や版を記録して、[本編の再現条件](33-reader.html)へ戻ります。近い正解率だけで同じ更新と判定しません。

## 次に、性能を調べる

動作と再開の確認ができたら、[本編の学習・検証](labs-06.html)で十分な更新と未知データの評価へ進みます。10・20更新の結果だけで良いモデルと主張しません。

[第33章の課題](33-workshop.html) · [一行ずつコードを読む](lab-guide.html) · [第56章の作業票](capstone-sessions.html)
