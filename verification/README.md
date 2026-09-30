# 検証記録

確認日：2026-09-30。AI（OpenAI Codex）による制作・検証。

- `site-checks.json`: 静的HTMLの内部リンク、anchor、演習記法、本文のPythonコード31本の実行。`python verify.py`で再生成。
- PyTorchテスト5件が通過：文書分割の非重複、未来参照の禁止、保存再開の一致、copy課題の学習成立、日本語系列のpaddingと因果性。
- `labs/results.csv`: 3条件×3seed、各300更新の全validation結果。
- `labs/text_results.json`: 合成日本語512文書を分割して学習した結果。固定した300更新後のtestを含む。
- 数値検証：online softmaxと通常計算、有限差分とautograd、LoRA初期勾配を照合。
- byte BPEのround trip（日本語・emoji・空文字・重複文字）、検索4問と答えなし例、bandit 3seed、対応bootstrapを実行。
- ブラウザ：desktopとmobileの幅で本文・演習・表を確認。検索、解答の開閉、目次、温度sliderを操作。mobileの本文幅がviewportを超えないことを確認。

GPU kernelと複数GPUの性能は未実測。最新論文の公表スコアの独立再現ではない。
`privacy-audit.json`は公開候補ファイルとGit作者情報を対象にした公開前点検の記録で、世界中の外部情報との再識別可能性を保証するものではない。
