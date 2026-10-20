# 原資料との対応と補完範囲

原資料の135 Module、26 Bridge、30 Upgradeを、学ぶ順番に合わせて再編しました。以下は**テーマの対応表**です。項目が対応していることは、全テーマを同じ深さで扱い、全実装を再現したという意味ではありません。

基礎からTransformerまでは講義・手計算・実行コードを中心に、研究領域は主要な考え方・演習・一次資料を中心に構成しています。Tritonと[分散](reference.html#term-variance)の実習は[追加実習](systems-lab.html)、実行済みの範囲は[ラボ](labs.html)をご覧ください。

## 補完・修正した点

- 原資料の[Attention](reference.html#term-attention)の尺度を標準の√dₖへ修正しました。
- 一般的な繰り返し問題を、数字・条件・解答のある演習へ置き換えました。
- 因果性・データ分割・checkpoint再開を検証する実装と、3条件×3seedの実測を追加しました。
- byte BPE、検索の評価、方策[勾配](reference.html#term-gradient)、対応[bootstrap](reference.html#term-bootstrap)、[LoRA](reference.html#term-lora)の勾配を試すコードを追加しました。
- SSM・拡散言語モデル、2026年の技術報告、toolの権限境界、評価の反証条件を追加しました。
- 個人向けの記述を除き、AI利用、出典、実験済みと未検証の境界を明記しました。

## 深さと到達の確認

GPU専用kernelの実装・巨大モデルの[事前学習](reference.html#term-pretrain)・全最新論文の独立再現は、この公開版の実測範囲に含みません。対応先の課題と一次資料まで取り組み、[卒業研究の提出物](56-capstone.html)で技能を確かめます。資料の監査ガイド・解答集・Mastery試験は、各章の解答と到達課題、卒業研究の判定基準へ統合しました。付録の言語ガイドは08–13章、数式表は[早見表](reference.html)へ対応します。

## Module対応

|原資料ID|テーマ|主な対応先|
|---|---|---|
|Module 01|この本の使い方と到達基準|[01章](01-start.html)|
|Module 02|現在地診断とスキップ判定|[01章](01-start.html)|
|Module 03|コンピュータの超基礎|[02章](02-computer.html)|
|Module 04|数式と英語記号の読み方|[06章](06-functions.html)|
|Module 05|数と四則演算|[03章](03-arithmetic.html)|
|Module 06|分数|[03章](03-arithmetic.html)|
|Module 07|小数と割合・百分率|[03章](03-arithmetic.html)|
|Module 08|負の数と絶対値|[03章](03-arithmetic.html)|
|Module 09|べき乗と平方根|[04章](04-powers.html)|
|Module 10|比・比例・反比例|[04章](04-powers.html)|
|Module 11|科学記数法と桁|[04章](04-powers.html)|
|Module 12|近似・丸め・有効数字|[04章](04-powers.html)|
|Module 13|文字式と代入|[05章](05-algebra.html)|
|Module 14|一次方程式|[05章](05-algebra.html)|
|Module 15|不等式|[05章](05-algebra.html)|
|Module 16|座標とグラフ|[06章](06-functions.html)|
|Module 17|一次関数|[06章](06-functions.html)|
|Module 18|二次関数|[06章](06-functions.html)|
|Module 19|指数関数|[07章](07-logarithms.html)|
|Module 20|対数|[07章](07-logarithms.html)|
|Module 21|総和 Σ・総積 Π・添字|[06章](06-functions.html)|
|Module 22|関数と合成関数|[06章](06-functions.html)|
|Module 23|極限の直感|[17章](17-calculus.html)|
|Module 24|微分 = 瞬間の変化率|[17章](17-calculus.html)|
|Module 25|微分公式|[17章](17-calculus.html)|
|Module 26|偏微分|[18章](18-chain.html)|
|Module 27|連鎖律と計算グラフ|[18章](18-chain.html)|
|Module 28|勾配と方向微分|[18章](18-chain.html)|
|Module 29|積分の直感|[19章](19-integration.html)|
|Module 30|ベクトル|[14章](14-vectors.html)|
|Module 31|内積・ノルム・cos 類似度|[14章](14-vectors.html)|
|Module 32|行列|[15章](15-matrices.html)|
|Module 33|行列積|[15章](15-matrices.html)|
|Module 34|連立一次方程式|[15章](15-matrices.html)|
|Module 35|線形変換・基底・次元|[15章](15-matrices.html)|
|Module 36|固有値・固有ベクトル|[16章](16-tensors.html)|
|Module 37|SVD・低ランク近似|[16章](16-tensors.html)|
|Module 38|テンソルと shape 設計|[16章](16-tensors.html)|
|Module 39|場合の数と確率|[20章](20-probability.html)|
|Module 40|条件付き確率と Bayes|[20章](20-probability.html)|
|Module 41|確率変数|[21章](21-distributions.html)|
|Module 42|代表的な分布|[21章](21-distributions.html)|
|Module 43|期待値・分散・標準偏差|[21章](21-distributions.html)|
|Module 44|標本・推定・信頼区間|[22章](22-statistics.html)|
|Module 45|仮説検定と効果量|[22章](22-statistics.html)|
|Module 46|共分散・相関|[21章](21-distributions.html)|
|Module 47|Entropy・Cross Entropy|[23章](23-information.html)|
|Module 48|KL divergence・Perplexity|[23章](23-information.html)|
|Module 49|Python 環境・変数・型|[08章](08-python.html)|
|Module 50|if・for・while|[09章](09-control.html)|
|Module 51|関数・引数・return|[09章](09-control.html)|
|Module 52|list・dict・tuple・set|[10章](10-data.html)|
|Module 53|文字列・ファイル I/O|[10章](10-data.html)|
|Module 54|例外・テスト・デバッグ|[11章](11-debug.html)|
|Module 55|class・module・package|[11章](11-debug.html)|
|Module 56|NumPy|[16章](16-tensors.html)|
|Module 57|計算量 Big-O|[13章](13-algorithms.html)|
|Module 58|基本アルゴリズムとデータ構造|[13章](13-algorithms.html)|
|Module 59|Bash / Linux をゼロから|[12章](12-environment.html)|
|Module 60|Git / GitHub をゼロから|[12章](12-environment.html)|
|Module 61|SQL を研究用に使う|[13章](13-algorithms.html)|
|Module 62|Regex・CSV・JSON|[13章](13-algorithms.html)|
|Module 63|仮想環境・依存関係・再現性|[12章](12-environment.html)|
|Module 64|データセットと train/valid/test|[24章](24-learning.html)|
|Module 65|線形回帰|[25章](25-regression.html)|
|Module 66|勾配降下法|[28章](28-numerics.html)|
|Module 67|ロジスティック回帰|[25章](25-regression.html)|
|Module 68|分類指標|[24章](24-learning.html)|
|Module 69|正則化・bias/variance|[24章](24-learning.html)|
|Module 70|決定木・ensemble|[25章](25-regression.html)|
|Module 71|Clustering・PCA|[25章](25-regression.html)|
|Module 72|実験設計と baseline|[53章](53-research-design.html)|
|Module 73|Tensorと PyTorch|[26章](26-pytorch.html)|
|Module 74|Autograd|[26章](26-pytorch.html)|
|Module 75|MLP と線形層|[27章](27-networks.html)|
|Module 76|Backpropagation を自力で追う|[27章](27-networks.html)|
|Module 77|Activation・初期化|[27章](27-networks.html)|
|Module 78|Optimizer: SGD ・Adam|[28章](28-numerics.html)|
|Module 79|Normalization・Dropout|[27章](27-networks.html)|
|Module 80|Batching・GPU・mixed precision|[28章](28-numerics.html)|
|Module 81|文字列から token へ|[29章](29-tokenization.html)|
|Module 82|N-gram 言語モデル|[30章](30-language-model.html)|
|Module 83|Embedding|[29章](29-tokenization.html)|
|Module 84|Attention|[31章](31-attention.html)|
|Module 85|Self-Attention・causal mask|[31章](31-attention.html)|
|Module 86|Multi-Head・位置表現|[32章](32-transformer.html)|
|Module 87|Transformer block|[32章](32-transformer.html)|
|Module 88|Decoder-only Language Model|[32章](32-transformer.html)|
|Module 89|Transformerの学習をデバッグ|[33章](33-training.html)|
|Module 90|BPE tokenizer を自作する|[29章](29-tokenization.html)|
|Module 91|Tiny GPT をゼロから実装|[32章](32-transformer.html)|
|Module 92|事前学習データ pipeline|[35章](35-data-scaling.html)|
|Module 93|T raining loop・checkpoint|[33章](33-training.html)|
|Module 94|推論・sampling・KV cache|[34章](34-generation.html)|
|Module 95|LLM 評価|[50章](50-evaluation.html)|
|Module 96|SFT・LoRA|[36章](36-adaptation.html)|
|Module 97|RAG|[37章](37-rag.html)|
|Module 98|Alignment: preference ・DPO・RLHF|[39章](39-alignment.html)|
|Module 99|Scaling laws|[35章](35-data-scaling.html)|
|Module 100|Distributed training ・profiling|[42章](42-distributed.html)|
|Module 101|FlashAttention ・効率化の考え方|[41章](41-efficiency.html)|
|Module 102|論文の構造と読み方|[54章](54-paper-reading.html)|
|Module 103|Literature search ・関連研究|[54章](54-paper-reading.html)|
|Module 104|再現実験|[54章](54-paper-reading.html)|
|Module 105|研究質問・仮説・baseline|[53章](53-research-design.html)|
|Module 106|Ablation study|[53章](53-research-design.html)|
|Module 107|統計的比較・複数 seed|[53章](53-research-design.html)|
|Module 108|Error analysis ・data contamination|[50章](50-evaluation.html)|
|Module 109|Responsible AI ・研究倫理|[52章](52-privacy.html)|
|Module 110|研究コード・artifact|[56章](56-capstone.html)|
|Module 111|論文を書く|[55章](55-writing.html)|
|Module 112|査読への対応|[55章](55-writing.html)|
|Module 113|新規性を作る|[53章](53-research-design.html)|
|Module 114|卒業研究 Capstone|[56章](56-capstone.html)|
|Module 115|Quantization: 8bit/4bit と誤差|[44章](44-compression.html)|
|Module 116|Pruning ・Distillation・Sparsity|[44章](44-compression.html)|
|Module 117|Mixture of Experts|[45章](45-moe.html)|
|Module 118|Long Context ・RoPE 拡張|[46章](46-context.html)|
|Module 119|Speculative Decoding|[43章](43-serving.html)|
|Module 120|Inference-time Compute と Reasoning|[40章](40-reasoning.html)|
|Module 121|Synthetic Data ・Self-training|[40章](40-reasoning.html)|
|Module 122|T ool Use ・Agents|[49章](49-agents.html)|
|Module 123|LLM-as-a-Judge|[50章](50-evaluation.html)|
|Module 124|Mechanistic Interpretability 入門|[51章](51-interpretability.html)|
|Module 125|Memorization ・Privacy・Data Attribution|[52章](52-privacy.html)|
|Module 126|Multilingual LLM|[48章](48-multimodal.html)|
|Module 127|Multimodal LLM の入口|[48章](48-multimodal.html)|
|Module 128|Adversarial Evaluation ・Red T eaming|[50章](50-evaluation.html)|
|Module 129|Open-weight 研究と Release 設計|[52章](52-privacy.html)|
|Module 130|数式を英語で読む|[54章](54-paper-reading.html)|
|Module 131|Abstract を分解して読む|[54章](54-paper-reading.html)|
|Module 132|Methods 節の動詞|[54章](54-paper-reading.html)|
|Module 133|Results 節と慎重表現|[54章](54-paper-reading.html)|
|Module 134|Related Work を書く|[55章](55-writing.html)|
|Module 135|英語で研究発表・質疑|[55章](55-writing.html)|

## Bridge対応

|原資料ID|テーマ|主な対応先|
|---|---|---|
|Bridge 01|数・分数・割合を「量」として扱う|[03章](03-arithmetic.html)|
|Bridge 02|文字式・方程式・関数を「入力 → 出力」として読む|[05章](05-algebra.html)|
|Bridge 03|微分を「傾き」と「感度」として理解する|[17章](17-calculus.html)|
|Bridge 04|連鎖律と計算グラフ|[18章](18-chain.html)|
|Bridge 05|ベクトル・内積・ノルム・cos 類似度|[14章](14-vectors.html)|
|Bridge 06|行列・行列積・線形変換|[15章](15-matrices.html)|
|Bridge 07|固有値・SVD・低ランク近似の研究直観|[16章](16-tensors.html)|
|Bridge 08|確率・条件付き確率・Bayes|[20章](20-probability.html)|
|Bridge 09|期待値・分散・標準偏差|[21章](21-distributions.html)|
|Bridge 10|標本・標準誤差・信頼区間・検定|[22章](22-statistics.html)|
|Bridge 11|Entropy・Cross Entropy・KL・Perplexity|[23章](23-information.html)|
|Bridge 12|Python: 変数・型・条件・loop・関数|[09章](09-control.html)|
|Bridge 13|Python collections ・文字列・file・例外・test|[10章](10-data.html)|
|Bridge 14|Bash・Git・環境を「再現性の道具」として学ぶ|[12章](12-environment.html)|
|Bridge 15|NumPy: array ・shape・broadcast・vectorization|[16章](16-tensors.html)|
|Bridge 16|計算量 Big‑O と「制約から実装を選ぶ」|[13章](13-algorithms.html)|
|Bridge 17|train/valid/test・leakage・baseline|[24章](24-learning.html)|
|Bridge 18|線形回帰・分類・loss・metric|[25章](25-regression.html)|
|Bridge 19|Gradient Descent ・regularization・bias/variance|[28章](28-numerics.html)|
|Bridge 20|PyTorch Tensor・device・autograd|[26章](26-pytorch.html)|
|Bridge 21|MLP・Backprop・Optimizer を一周する|[27章](27-networks.html)|
|Bridge 22|数値安定性・shape・debugging の型|[28章](28-numerics.html)|
|Bridge 23|Tokenization・Embedding・N‑gram から LM へ|[29章](29-tokenization.html)|
|Bridge 24|Attention・causal mask ・Transformerの最小導出|[31章](31-attention.html)|
|Bridge 25|Decoder‑only LM の training loop|[33章](33-training.html)|
|Bridge 26|研究実験の最小プロトコル|[53章](53-research-design.html)|

## Upgrade対応

|原資料ID|テーマ|主な対応先|
|---|---|---|
|Upgrade 01|Softmax・log-sum-exp・数値安定性|[28章](28-numerics.html)|
|Upgrade 02|標本分布・標準誤差・CLT・Bootstrap|[22章](22-statistics.html)|
|Upgrade 03|仮説検定・effect size ・多重比較|[22章](22-statistics.html)|
|Upgrade 04|行列微分・Jacobian・VJP/JVP|[18章](18-chain.html)|
|Upgrade 05|FP16/BF16・Mixed Precision|[28章](28-numerics.html)|
|Upgrade 06|AdamW・warmup・schedule・gradient clipping|[28章](28-numerics.html)|
|Upgrade 07|Pre‑Norm・RMSNorm・SwiGLU|[27章](27-networks.html)|
|Upgrade 08|Q/K/V・Multi-Head Attention を誤解なく導出|[31章](31-attention.html)|
|Upgrade 09|RoPE・位置表現・長文脈|[46章](46-context.html)|
|Upgrade 10|MQA/GQA・KV cache の構造|[34章](34-generation.html)|
|Upgrade 11|Tokenizer・packing・causal labels|[29章](29-tokenization.html)|
|Upgrade 12|Pretraining data pipeline・filter・dedup|[35章](35-data-scaling.html)|
|Upgrade 13|GPU資源会計・FLOPs・memory・bandwidth・arithmetic intensity|[41章](41-efficiency.html)|
|Upgrade 14|Tritonをゼロから|[41章](41-efficiency.html)|
|Upgrade 15|FlashAttention|[41章](41-efficiency.html)|
|Upgrade 16|DDP・FSDP/ZeRO|[42章](42-distributed.html)|
|Upgrade 17|Tensor/Pipeline/Context/Expert Parallelism|[42章](42-distributed.html)|
|Upgrade 18|Serving・prefill/decode・continuous batching・PagedAttention|[43章](43-serving.html)|
|Upgrade 19|GPTQ・AWQ|[44章](44-compression.html)|
|Upgrade 20|Scaling Laws を経験則として扱う|[35章](35-data-scaling.html)|
|Upgrade 21|評価不確実性・seed|[50章](50-evaluation.html)|
|Upgrade 22|Benchmark contamination ・LLM‑as‑a‑Judge|[50章](50-evaluation.html)|
|Upgrade 23|強化学習をゼロから: policy ・reward・REINFORCE|[38章](38-reinforcement.html)|
|Upgrade 24|PPO・Advantage・KL 制約|[39章](39-alignment.html)|
|Upgrade 25|RLHF・DPO・GRPO・RLVRを混同しない|[39章](39-alignment.html)|
|Upgrade 26|Mechanistic Interpretability|[51章](51-interpretability.html)|
|Upgrade 27|Memorization・Privacy・Safety|[52章](52-privacy.html)|
|Upgrade 28|Reproducibility: seed 以上の研究工学|[33章](33-training.html)|
|Upgrade 29|Research Design: baseline ・ablation・negative result|[53章](53-research-design.html)|
|Upgrade 30|論文読解・執筆・研究 Capstone|[56章](56-capstone.html)|
