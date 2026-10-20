# 5．検索と報酬を独立に検証する

この実習の10/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

```sh
python labs/rag_eval.py
python labs/bandit.py
```

[rag_eval.py](downloads/rag_eval.py)は4文書からの語の一致に基づく検索と、根拠文の抽出を行います。制作時は4問でRecall@1とMRRが1でした。小さな意図的に簡単な集合なので、一般的な検索性能を示すものではありません。生成モデルは含みません。最後の「電話番号」という答えのない質問でも文書は返ります。検索順位が高いことと、答えがあることの違いを調べます。

[bandit.py](downloads/bandit.py)は成功確率0.2と0.8の二択でREINFORCEを実行します。3seedでよい選択肢への最終確率は約0.985、0.979、0.976でした。[報酬](reference.html#term-reward)そのものではなく、選択肢の[対数](reference.html#term-log)確率を微分します。これはLLMの[RLHF](reference.html#term-rlhf)全体の実装ではなく、方策勾配の最小実験です。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](labs-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="labs-09.html">前の作業</a><a href="labs-11.html">次の作業</a></nav>
