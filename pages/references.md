# 出典とファクトチェック

資料確認日：2026年9月30日。各講義末尾のリンクが、その講義の一次資料です。[研究一覧](research.html)には論文ごとの読書課題があります。説明・例題・演習はこのサイト向けに書き起こしています。

## 何をどこで確かめたか

|対象|一次資料|確認・検証の範囲|
|---|---|---|
|段階的な実装中心の構成|[Stanford CS336](https://cs336.stanford.edu/)|公開カリキュラム。初心者向け前提は本教材で追加|
|線形代数の学習範囲|[MIT 18.06](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/)|行列、線形系、基底、固有値等への接続|
|Pythonの構文・型・ファイル・例外|[Python公式tutorial](https://docs.python.org/3/tutorial/)|該当項目と実行例。本文のPythonコードを実行検査|
|NumPyのshape・broadcast|[NumPy broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)|後ろの軸からの互換条件と例|
|byteの単位|[NIST binary prefixes](https://physics.nist.gov/cuu/Units/binary.html)|十進GBと二進GiBの区別|
|自動微分・保存・再現性|[PyTorch basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)／[保存と読み込み](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)|公式APIとCPU実装。再開一致、因果性、分割、学習をテスト|
|Attentionの尺度と構造|[Transformer原論文](https://arxiv.org/abs/1706.03762)|√dₖ、QKV、head、mask。原資料のdₖ除算表記を修正|
|低ランク調整|[LoRA](https://arxiv.org/abs/2106.09685)／[QLoRA](https://arxiv.org/abs/2305.14314)|低ランク更新と量子化基盤の区別。凍結・初期勾配をCPUで確認|
|検索を使う生成|[RAG](https://arxiv.org/abs/2005.11401)|検索と生成の分離。配布ラボは検索＋抽出のみ|
|選好と方策最適化|[PPO](https://arxiv.org/abs/1707.06347)／[DPO](https://arxiv.org/abs/2305.18290)／[DeepSeekMath](https://arxiv.org/abs/2402.03300)|各目的関数の位置づけ。bandit実装はREINFORCEの最小実験|
|計算とデータの配分|[Chinchilla](https://arxiv.org/abs/2203.15556)|計算予算を固定した経験的配分。普遍法則としない|
|IOとkernel|[FlashAttention](https://arxiv.org/abs/2205.14135)／[Triton公式tutorial](https://triton-lang.org/main/getting-started/tutorials/01-vector-add.html)|online計算をCPU照合。GPU速度は未測定|
|分散学習|[PyTorch DDP](https://docs.pytorch.org/tutorials/intermediate/ddp_tutorial.html)|通信と平均化の考え方。複数GPUでの実行は未検証|
|評価の偏りと範囲|[HELM](https://arxiv.org/abs/2211.09110)／[LLM-as-a-judge](https://arxiv.org/abs/2306.05685)|複数指標、judgeの偏り。実験計画に反映|
|データの記憶|[Training data extraction](https://arxiv.org/abs/2012.07805)|抽出可能性の報告。教材では合成データを使用|
|2026年の動向|[研究を読む](research.html)|一次資料の書誌・要旨を確認。全文の全実験の独立再現とは区別|

## 数学の検証

手計算の例は小さい数で式を展開し、実行可能なコードでは配列のshape、有限差分、softmaxの別実装などで照合しています。通常の数学的定義、教育用の直感、経験則、論文著者の観測を区別します。たとえば「logの底」「確率分布のsupport」「独立同分布」「有限精度」といった条件を落とさない方針です。

## 未確認を隠さない

すべての外部リンクの将来の可用性、全機種・全OSでの動作、巨大モデルの公表スコアは保証していません。公式ドキュメントのstable版は更新されるため、実験には実際の版を記録します。最新論文には改訂・撤回・後続の反証もあり得るため、版を確認して読んでください。

## 修正の優先順

計算やコードの誤り、前提の不足、誤解を招く断定、出典との不一致、表示の不具合の順に修正します。誤りを発見した場合は、該当箇所・具体的な反例・一次資料を添えて[リポジトリ](https://github.com/sakunokyumei/llm-research-textbook)へ報告できます。
