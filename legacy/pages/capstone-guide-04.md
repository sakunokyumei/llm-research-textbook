# 3．実験票を書いてから九実行を残す

この実習の4/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

[報告書テンプレート](downloads/capstone_template.md)へ、主仮説と固定条件を書きます。例：「noise4・6で学習したとき、位置Embeddingを外すと未学習のnoise8でcopy正解率が変わる」。改善する方向まで仮説にするなら、結果を見る前に記録します。

```sh
python labs/distance_study.py --steps 300 --out labs/runs/distance-study
```

3条件（[Attention](reference.html#term-attention)あり、位置Embeddingなし、Attentionなし）×3seedです。noise4・6の文書だけで学習し、noise4・6・8を別のvalidation文書で測ります。各長さは全256文書、train192、validation32、test32。対象記号の四種類が各分割で同数になるよう作ります。noise8のtrain文書も作りますが、学習関数はその長さを選ばず、未学習の距離として扱います。

|保存物|確認すること|
|---|---|
|plan.json|開始前の仮説・設定・データhash・testを使うか|
|results.json|九実行の状態と文書別の正誤。失敗も残る|
|条件名-seed.pt|各実行の重み・optimizer・乱数・設定を保存したcheckpoint|
|results.csv|条件・seed・長さ・損失・copy正解率|
|paired_validation.json|同じ文書の条件差と再抽出区間|

同じseedの各条件は同じ更新数・同じ抽出文書・同じ処理[トークン](reference.html#term-token)数を使います。有効な演算量と実時間は条件で違うため、「[計算量](reference.html#term-complexity)まで完全に同じ」とは書きません。32文書の区間は小標本の教材例で、学習seedのばらつきを含みません。九実行を全て報告し、区間を一つの強い結論へまとめないでください。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](capstone-guide-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="capstone-guide-03.html">前の作業</a><a href="capstone-guide-05.html">次の作業</a></nav>
