# 実装ラボ

教材本文と手順は https://sakunokyumei.github.io/llm-research-textbook/labs.html を参照。

実行確認環境：Python 3.14、torch 2.13.0+cpu、numpy 2.5.2。
データはすべてプログラム内の合成データ。APIや認証は不要。

```sh
python -m unittest discover -s labs -v
python labs/math_checks.py
python labs/bpe.py
python labs/rag_eval.py
python labs/bandit.py
python labs/run_experiments.py
python labs/paired_bootstrap.py labs/runs/attention-0/metrics.json labs/runs/no-attention-0/metrics.json
```

`results.csv`は3条件×3seed、各300更新の実測。全runを保持しており、よいseedだけ選んでいない。
学習した重みや一時ログは`runs/`へ出力し、Gitには含めない。
GPU・分散の性能は未検証。小規模課題の結果を自然言語LLM全般へ一般化しない。

距離の卒業研究は `python labs/distance_study.py --steps 300`。
学習長を固定して未学習長を測り、3条件×3seedをすべて保存する。
`--held-out-noise 10 --out labs/runs/distance-10` で探索用の距離を変更できる。
最終testは設定を固定してから `--evaluate-test` を指定する。
詳しい意味と採点位置はサイトのcapstone-guide.html、報告の欄はcapstone_template.mdを参照。

文章とコードはAI（OpenAI Codex）を用いて作成し、数値とテストで検証した。
