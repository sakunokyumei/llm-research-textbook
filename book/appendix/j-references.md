{"title": "参考文献", "short": "参考文献", "subtitle": "この教科書のもとになった論文・講義・データ・道具"}

この教科書の内容は、多くの研究者・教育者・開発者の公開した成果の上に成り立っています。気になったものから、ぜひ原典に当たってみてください。論文の多くは arXiv（<https://arxiv.org/>）で無料で読めます。

## 論文

| 論文 | 著者（代表） | 年 | 関係する章 |
|---|---|---|---|
| A Mathematical Theory of Communication | C. E. Shannon | 1948 | 5 |
| A New Algorithm for Data Compression（BPEの元になった圧縮法） | P. Gage | 1994 | 14 |
| A Neural Probabilistic Language Model | Y. Bengio ほか | 2003 | 9 |
| Adam: A Method for Stochastic Optimization | D. P. Kingma, J. Ba | 2014 | 10 |
| Dropout: A Simple Way to Prevent Neural Networks from Overfitting | N. Srivastava ほか | 2014 | 10 |
| Deep Residual Learning for Image Recognition（ResNet） | K. He ほか | 2015 | 12 |
| Neural Machine Translation of Rare Words with Subword Units | R. Sennrich ほか | 2016 | 14 |
| Layer Normalization | J. L. Ba ほか | 2016 | 10 |
| Attention Is All You Need | A. Vaswani ほか | 2017 | 11, 12 |
| Decoupled Weight Decay Regularization（AdamW） | I. Loshchilov, F. Hutter | 2017 | 10 |
| Language Models are Unsupervised Multitask Learners（GPT-2） | A. Radford ほか | 2019 | 13, 15 |
| The Curious Case of Neural Text Degeneration（top-p） | A. Holtzman ほか | 2019 | 16 |
| Scaling Laws for Neural Language Models | J. Kaplan ほか | 2020 | 15 |
| Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | P. Lewis ほか | 2020 | 21 |
| GLU Variants Improve Transformer（SwiGLU） | N. Shazeer | 2020 | 25 |
| RoFormer: Enhanced Transformer with Rotary Position Embedding | J. Su ほか | 2021 | 25 |
| LoRA: Low-Rank Adaptation of Large Language Models | E. J. Hu ほか | 2021 | 19 |
| Training Compute-Optimal Large Language Models（Chinchilla） | J. Hoffmann ほか | 2022 | 15 |
| Training language models to follow instructions with human feedback | L. Ouyang ほか | 2022 | 17, 18, 22 |
| FlashAttention | T. Dao ほか | 2022 | 16 |
| ReAct: Synergizing Reasoning and Acting in Language Models | S. Yao ほか | 2022 | 23 |
| Chain-of-Thought Prompting Elicits Reasoning in Large Language Models | J. Wei ほか | 2022 | 17 |
| Constitutional AI: Harmlessness from AI Feedback | Y. Bai ほか | 2022 | 22 |
| GQA: Training Generalized Multi-Query Transformer Models | J. Ainslie ほか | 2023 | 16 |
| Direct Preference Optimization | R. Rafailov ほか | 2023 | 22 |
| QLoRA: Efficient Finetuning of Quantized LLMs | T. Dettmers ほか | 2023 | 19 |
| LIMA: Less Is More for Alignment | C. Zhou ほか | 2023 | 18 |
| Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | L. Zheng ほか | 2023 | 20 |
| Root Mean Square Layer Normalization（RMSNorm） | B. Zhang, R. Sennrich | 2019 | 25 |
| Mamba: Linear-Time Sequence Modeling with Selective State Spaces | A. Gu, T. Dao | 2023 | 25 |
| DeepSeekMath（GRPOを提案） | Z. Shao ほか | 2024 | 22, 25 |
| Qwen2.5 Technical Report | Qwen Team | 2024 | 1, 17 |

## 講義・教材

- **Stanford CS336: Language Modeling from Scratch**（<https://cs336.stanford.edu/>）：LLMをゼロから作る大学院の講義。この教科書の第2〜4部をもっと深く、大規模にやりたい人へ
- **Andrej Karpathy「Neural Networks: Zero to Hero」**（YouTubeの動画シリーズ）と **nanoGPT**（<https://github.com/karpathy/nanoGPT>）：bigramからGPTまでを一行ずつ作る。この教科書の第4〜13章の流れは、この講義のアプローチに大きな影響を受けています
- **Hugging Face LLM Course**（<https://huggingface.co/learn>）：transformers・datasets・TRLなどの使い方
- **Dive into Deep Learning**（<https://d2l.ai/>）：深層学習の教科書。コード付きで無料公開
- **R. P. Feynman「Cargo Cult Science」**（1974年のカリフォルニア工科大学の卒業式講演）：第20章・第26章の「自分をだまさない」の出典
- ファインマンの黒板の言葉 “What I cannot create, I do not understand.” は、1988年に亡くなったとき、カリフォルニア工科大学の黒板に残っていたものとして知られています

## データ

- **青空文庫**（<https://www.aozora.gr.jp/>）：著作権の切れた文学作品の電子図書館。この教科書では、夏目漱石の『こころ』『坊っちゃん』『吾輩は猫である』『三四郎』『草枕』『夢十夜』『それから』のテキストを、GitHub上の `aozorahack/aozorabunko_text` から取得しています。入力・校正をしたボランティアの皆さんに感謝します
- **ボンゴ先生のデータ**（`code/bongo_sft.jsonl` ほか）、**ボンゴ情報専門学校の資料**（`code/rag_docs.jsonl`）、**4択クイズ**（`code/mini_quiz.jsonl`）は、この教科書のために作った架空・教材用のデータです

## モデル・ライブラリ

| 名前 | 用途 | 章 |
|---|---|---|
| Qwen2.5（0.5B・1.5B、Instruct・ベース） | 事前学習済みモデル（Apache 2.0） | 1〜3, 17〜24 |
| GPT-2（OpenAI） | 重みの読み込み | 15 |
| multilingual-e5-small | 文の埋め込み | 21 |
| PyTorch | テンソル・自動微分・学習 | 3〜 |
| Hugging Face transformers / tokenizers / datasets / peft / trl | モデル・学習 | 1〜, 14, 17〜23 |
| sentence-transformers | 文の埋め込み | 21 |
| bitsandbytes | 4ビット量子化 | 19 |
| matplotlib / matplotlib-fontja | グラフと日本語表示 | 5〜 |
| Gradio | Webアプリの一時公開 | 24 |
| KaTeX | このサイトの数式表示 | — |
