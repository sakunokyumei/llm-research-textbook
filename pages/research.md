# 研究を読む：基礎から2026年へ

確認日：**2026年9月30日**。まず問いを持ち、前提の講義へ戻り、論文の方法・実験・限界を読みます。以下は学習上重要な系統を選んだ読書地図です。著者の報告を独立再現したと誤解しないよう、最新報告の要約は確認できた提案の範囲に限定しています。

## 土台を作った研究

|読む論文|前提の章|読みながら確かめる問い|
|---|---|---|
|[Attention Is All You Need](https://arxiv.org/abs/1706.03762)（2017）|31–32|なぜ√dₖで割る？原論文のencoder-decoderと本ラボのdecoder-onlyはどこが違う？|
|[BERT](https://arxiv.org/abs/1810.04805)（2018）|29–32|mask予測と左からの次token予測で、見える情報はどう違う？|
|[GPT-3](https://arxiv.org/abs/2005.14165)（2020）|30・35|in-context learningは重みの更新とどう違う？|
|[Scaling Laws](https://arxiv.org/abs/2001.08361)（2020）|07・35|どの変数を固定し、どの範囲へ当てはめた経験則か？|
|[Chinchilla](https://arxiv.org/abs/2203.15556)（2022）|35|[計算量](reference.html#term-complexity)を固定すると、パラメータとデータの配分はどうなる？|
|[RAG](https://arxiv.org/abs/2005.11401)（2020）|37|検索失敗と生成失敗をどう切り分ける？|
|[LoRA](https://arxiv.org/abs/2106.09685)（2021）|16・36|低[ランク](reference.html#term-rank)更新の[shape](reference.html#term-tensor)と学習パラメータ数は？|
|[QLoRA](https://arxiv.org/abs/2305.14314)（2023）|36・44|基盤重みの[量子化](reference.html#term-quantization)とadapterの学習を区別できる？|
|[InstructGPT](https://arxiv.org/abs/2203.02155)（2022）|38–39|SFT・[報酬](reference.html#term-reward)モデル・方策最適化のデータは何か？|
|[PPO](https://arxiv.org/abs/1707.06347)（2017）|38–39|重要度比とclippingは何を抑える？|
|[DPO](https://arxiv.org/abs/2305.18290)（2023）|39|選好の組からどの[対数](reference.html#term-log)確率差を学習する？|
|[DeepSeekMath](https://arxiv.org/abs/2402.03300)（2024）|39|GRPOの群内相対評価はどう作られる？|

## 計算資源を研究対象にする

|読む論文|前提|比較時に固定する条件|
|---|---|---|
|[FlashAttention](https://arxiv.org/abs/2205.14135)（2022）|41|dtype、系列長、入出力、GPU。IO削減と近似を混同しない|
|[PagedAttention / vLLM](https://arxiv.org/abs/2309.06180)（2023）|43|request長の分布、batch、メモリ、throughputとtail latency|
|[Speculative Decoding](https://arxiv.org/abs/2211.17192)（2022）|43|draftの費用・採択率・targetの分布を保つ補正|
|[GPTQ](https://arxiv.org/abs/2210.17323)（2022）|44|校正データ、bit数、重み誤差とタスク性能|
|[AWQ](https://arxiv.org/abs/2306.00978)（2023）|44|activationから重みの重要性をどう扱うか|
|[Switch Transformers](https://arxiv.org/abs/2101.03961)（2021）|45|総パラメータとactive parameter、通信、load balance|
|[RoFormer / RoPE](https://arxiv.org/abs/2104.09864)（2021）|46|相対位置が[内積](reference.html#term-dot)へ入る導出|
|[Mamba](https://arxiv.org/abs/2312.00752)（2023）|47|固定状態の効率と情報保持、入力依存性|
|[Mamba-2](https://arxiv.org/abs/2405.21060)（2024）|47|構造化状態空間と[Attention](reference.html#term-attention)の関係|

## 推論・生成・評価の広がり

|読む論文|前提|確認すること|
|---|---|---|
|[DeepSeek-V3](https://arxiv.org/abs/2412.19437)（2024）|34・42・45|[MoE](reference.html#term-moe)、cache、学習と推論の資源配分|
|[DeepSeek-R1](https://arxiv.org/abs/2501.12948)（2025、改訂版あり）|38–40|RLのみの条件とcold-startを含む条件、評価予算|
|[Qwen3 Technical Report](https://arxiv.org/abs/2505.09388)（2025）|35・39–40|thinkingとnon-thinking、学習段階、評価条件|
|[LLaDA](https://arxiv.org/abs/2502.09992)（2025）|47|maskの過程と生成ステップ、自己回帰baselineとの公平性|
|[CLIP](https://arxiv.org/abs/2103.00020)（2021）／[LLaVA](https://arxiv.org/abs/2304.08485)（2023）|48|対照学習と指示応答の違い|
|[ReAct](https://arxiv.org/abs/2210.03629)（2022）|49|toolを使う行動ループの成否をどう測る？|
|[HELM](https://arxiv.org/abs/2211.09110)（2022）|50|複数指標と評価範囲の明示|
|[MT-Bench / Chatbot Arena](https://arxiv.org/abs/2306.05685)（2023）|50|judgeの提示順・長さ・自己選好等の偏り|
|[Toy Models of Superposition](https://arxiv.org/abs/2209.10652)（2022）|51|特徴数と表現次元、疎性の役割|
|[Extracting Training Data](https://arxiv.org/abs/2012.07805)（2020）|52|記憶・抽出・一般化はどう違う？|

## 2026年の主要技術報告と新しい方向

ここは**一次資料の書誌と要旨を確認した読書ガイド**です。全文の全実験・全実装を検証済みという意味ではありません。最先端モデルの優劣を、異なる条件のランキングから断定しません。

### DeepSeek-V4：長文脈の計算構造

[技術報告](https://arxiv.org/abs/2606.19348)はCSAとHCAを組み合わせたAttention、mHC、Muonを取り入れたMoEモデルを報告しています。31・41・45・46章から、cache容量と推論計算を減らす工夫へ進む題材です。読む課題は、圧縮する情報、品質への影響、比較する系列長・モデル・予算を表にすること。原資料の書誌表示には識別子と初回日付の不整合が見られたため、ここでは厳密な初回公開日を断定しません。

### Gemma 4：複数の規模とマルチモーダル設計

[技術報告 v2](https://arxiv.org/abs/2607.02770v2)（2026年7月）は、denseとMoE、視覚・音声、thinkingを含むモデル群を報告しています。特に12Bモデルのencoder-free設計は、48章の「encoderで特徴へ変換する」方式と比べる題材です。読む課題は、入力表現の違いが計算量・品質・必要データへどう影響するか整理すること。

### Kimi K3：長い作業とシステム全体

[技術報告](https://arxiv.org/abs/2607.24653)と[公式公開案内](https://www.kimi.com/news/kimi-k3-open-source)は、MoE・視覚・長文脈とagenticな作業を扱います。45・48・49章へ接続します。モデル単体とtool・sandbox・推論予算を含むシステム全体の改善を分け、どの比較が何を測ったか調べてください。

### Qwen3.5-Omni：音声・映像・言語をつなぐ

[技術報告 v2](https://arxiv.org/abs/2604.15804v2)は、ThinkerとTalkerのhybrid attention MoE、および文字と音声単位の整列を扱うARIAを報告しています。48章の先として、入力の時間解像度、streaming、応答遅延と品質の交換関係を読み取ります。

### Engram：計算に加えて検索型の記憶を考える

[Conditional Memory via Scalable Lookup](https://arxiv.org/abs/2601.07372)は、条件付き計算に対して条件付き記憶という方向を提案します。37・45・47章を読み、外部文書検索、expert routing、学習された記憶へのlookupの違いを図にしてください。方式の新しさと実測の改善を別々に評価します。

### DualPath：agent推論の保存・転送

[DualPath](https://arxiv.org/abs/2602.21548)は、agenticな推論でのストレージ帯域のボトルネックを扱います。41–43章の先として、計算量だけでは説明できない待ち時間を追います。比較する負荷・cache状態・ネットワーク・storageの条件を抽出するのが読書課題です。

### RISE：直近のプレプリントを批判的に読む

[RISE v1](https://arxiv.org/abs/2609.05295v1)（2026年9月4日）は、RLVRの学習軌跡から合成teacherを作り、on-policy distillationと組み合わせる提案です。39・40・44章へ接続します。**新着の研究であり、定着した結論として扱いません。** teacher更新、追加計算、RLVRのみとの比較、外部での追試を確認してください。

## 新しい論文を追う手順

問いに合う論文の引用文献と被引用研究をたどり、著者の公式リポジトリと[arXiv](reference.html#term-arxiv)の版を確認します。検索結果の要約だけで引用しません。まず一件を[論文読解の手順](54-paper-reading.html)で精読し、データ・式・コード・評価を一枚のメモへまとめます。
