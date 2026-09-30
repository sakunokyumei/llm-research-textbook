# 検証記録

確認日：2026-10-01。AI（OpenAI Codex）による制作・検証。

- `site-checks.json`: 静的HTMLの内部リンク、anchor、演習記法、本文・補習ページのPythonコード45本の実行。`python verify.py`で再生成。
- PyTorchテスト9件が通過：既存の文書分割・因果性・保存再開・学習成立・paddingの5件と、距離実験の分割と再現性、長さとラベル、最長系列の因果性、採点位置の4件。
- `labs/results.csv`: 3条件×3seed、各300更新の全validation結果。
- `labs/text_results.json`: 合成日本語512文書を分割して学習した結果。固定した300更新後のtestを含む。
- `labs/distance_results.json`: noise4・6で学習した3条件×3seedを、未学習のnoise8と10で測った計18実行。noise8には固定条件の最終test、noise10には探索のvalidationを含む。全結果を保持し、seedごとの同じトークン予算を確認。
- 新しい説明の仕様確認：Pythonの加算代入、NumPyの整数抽出・整数配列添字・quantileは公式文書を参照。PyTorchのno_grad・masked_fill・forward hook・autograd.gradは導入版2.13.0の公開docstringとCPU実行で照合。公式サイトのstableは版が更新されるので、制作時の実行版も記録。
- 数値検証：online softmaxと通常計算、有限差分とautograd、LoRA初期勾配を照合。
- byte BPEのround trip（日本語・emoji・空文字・重複文字）、検索4問と答えなし例、bandit 3seed、対応bootstrapを実行。
- ブラウザ：desktopとmobileの幅で本文・演習・表を確認。検索、解答の開閉、目次、温度sliderを操作。mobileの本文幅がviewportを超えないことを確認。

GPU kernelと複数GPUの性能は未実測。最新論文の公表スコアの独立再現ではない。
`privacy-audit.json`は公開候補ファイルとGit作者情報を対象にした公開前点検の記録で、世界中の外部情報との再識別可能性を保証するものではない。

今回の数学の改訂：第5章は5ページ、第15章は5ページ、第16章は6ページ、第17章は3ページ、第18章は7ページへ分割。各ページに読解・手計算と演習の時間を別々に表示。時間は受講者の実測ではなく編集上の目安。

`term-audit.json`は88の登録概念の初出リンクと説明先を記録。通常の日本語や全APIまでの完全な用語網羅を保証するものではない。`math-gradient-checks.json`は新しい行列勾配の手計算値を自動微分・独立の有限差分と照合し、JVP/VJPの数値例も確認した記録。演習番号は全ソースページの重複・逆順と、分割した五章のページ間の連番をverify.pyで検査する。
