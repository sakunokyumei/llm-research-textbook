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

文章とコードはAI（OpenAI Codex）を用いて作成し、数値とテストで検証した。
