{"title": "エラー辞典", "short": "エラー辞典", "subtitle": "赤い文字が出ても大丈夫。最後の行で引ける、原因と直し方"}

エラーが出たら、まず**一番下の行**（`○○Error: …`）を読み、その言葉でこのページを検索してください（パソコンなら <kbd>Ctrl</kbd> + <kbd>F</kbd>、Macなら <kbd>⌘</kbd> + <kbd>F</kbd>）。見つからなければ、[付録H](h-plan.html)のテンプレートでAIに聞くか、エラーの最後の行をそのまま検索エンジンで調べましょう。

:::sensei
エラーは、コンピュータからの手紙だ。たいていは「どこで」「何が」おかしいかを、ちゃんと書いてくれている。英語で書いてあるのが玉にきずだけど、出てくる単語は決まっている。この辞典で、よく来る手紙の読み方を覚えよう。
:::

## Colabと環境

| エラー・症状 | 原因 | 直し方 |
|---|---|---|
| 「GPUに接続できません」「使用量上限に達しました」 | 無料のGPUの枠を使い切った、または混雑 | CPUで進める／時間をおく／Kaggleを使う（[付録A](a-setup.html)） |
| 実行中に「接続が切れました」 | 操作しない時間が長い／最長時間を超えた | 再接続して上から実行し直す。大事なものはドライブに保存（第10章） |
| `NameError: name 'xxx' is not defined` | そのセルより上のセルを実行していない | 「ランタイム」→「すべてのセルを実行」 |
| `ModuleNotFoundError: No module named 'xxx'` | その道具が入っていない | `!pip install -q xxx` を実行。自分のPCならターミナルで `pip install xxx` |
| `No such file or directory: 'xxx'` | ファイルがない（ダウンロード忘れ、場所違い） | `!ls` で今のフォルダの中身を確認。`!wget` のセルを実行し直す |
| `!wget` で `ERROR 404: Not Found` | URLの打ち間違い | URLをコピーし直す |
| `The secret HF_TOKEN does not exist` | Hugging Faceのトークンが未設定 | 公開モデルなら**無視してOK**。設定方法は第17章 |
| `drive.mount` で止まる | ポップアップのブロック、許可の項目のチェック漏れ | ポップアップを許可し、全項目にチェックして「続行」 |

## Pythonの基本

詳しくは[付録B](b-python.html)の「エラーメッセージの読み方」へ。

| エラー | 意味 | よくある原因 |
|---|---|---|
| `SyntaxError: invalid syntax` | 文法の間違い | `:` の付け忘れ、かっこの閉じ忘れ、**全角の記号**（「（」「：」） |
| `SyntaxError: invalid character` | 使えない文字がある | 全角スペースや全角の記号がコードに混ざっている |
| `IndentationError` | 字下げの間違い | 字下げがそろっていない。コピー時にずれた |
| `TypeError: ... missing 1 required positional argument` | 引数が足りない | 関数を呼ぶときの引数の数を確認 |
| `KeyError: 'xxx'` | 辞書にそのキーがない | 文字トークナイザーで、辞書にない文字を `encode` した（第2・4章） |
| `IndexError: list index out of range` | リストの範囲外 | 長さを確認。`split(...)[2]` で分割数が足りない（第4章） |
| `UnicodeDecodeError: 'utf-8' codec can't decode` | 文字コードが違う | 青空文庫は `decode("cp932")`（第4章） |
| `json.decoder.JSONDecodeError` | JSONの形式が崩れている | JSONLは1行に1件。ファイルの中身を確認 |

## PyTorch：形と置き場所

| エラー | 原因 | 直し方 |
|---|---|---|
| `RuntimeError: mat1 and mat2 shapes cannot be multiplied (AxB and CxD)` | 行列の積の形が合わない（BとCが違う） | `print(x.shape)` で形を確認。第6章の形のルール $(n \times k)(k \times m)$ |
| `RuntimeError: The size of tensor a (X) must match the size of tensor b (Y)` | 足し算などで形が合わない | ブロードキャストできる形か確認。`keepdim=True` を忘れていないか |
| `RuntimeError: shape '[...]' is invalid for input of size N` | `view` で、数の個数が合わない形を指定 | `n_embd` が `n_head` で割り切れるか（第12章） |
| `RuntimeError: Expected all tensors to be on the same device` | GPUとCPUのテンソルが混ざっている | モデルを `.to(device)`、データも `.to(device)`（第13章） |
| `IndexError: index out of range in self` | 埋め込みの表の範囲外の番号 | 語彙数・`block_size` を超える入力。生成時は入力を切り詰める |
| `RuntimeError: element 0 of tensors does not require grad` | 勾配を計算できない | `requires_grad=True` の付け忘れ、`no_grad` の中で `backward` した |
| `RuntimeError: Trying to backward through the graph a second time` | 同じ計算に2回 `backward` した | 毎ステップ、損失を計算し直す |

## GPUのメモリ

| エラー・症状 | 原因 | 直し方 |
|---|---|---|
| `CUDA out of memory` / `OutOfMemoryError` | GPUのメモリが足りない | ①バッチを小さく ②`block_size`（文章の長さ）を短く ③使わないモデルを `del` して `torch.cuda.empty_cache()` ④「セッションを再起動」して上から ⑤LoRA・量子化（第19章）・勾配チェックポイント（第16章） |
| メモリがじわじわ増える | 損失をテンソルのままリストにためている | `losses.append(loss.item())` のように `.item()` で数にする |

## 学習がおかしい

[第10章の「学習の診察表」](10-training-tips.html)も参照してください。

| 症状 | 考えられる原因 | 直し方 |
|---|---|---|
| 損失が `nan` / `inf` | 学習率が大きすぎる、勾配爆発、`log(0)` | 学習率を下げる、勾配クリッピング、ウォームアップ |
| 損失がまったく下がらない | 学習率が小さすぎる、`zero_grad` 忘れ、`requires_grad` 忘れ、`ModuleList` を普通のリストにした | まず1バッチで丸暗記できるか試す（第12章） |
| 最初の損失が $\log V$ よりずっと大きい | 初期化がおかしい | 出力層の重みを小さく（第10章） |
| 訓練だけ良くなって検証が悪くなる | 過学習 | データを増やす、ドロップアウト、重み減衰、早めに止める |
| 生成が同じ言葉のくり返し | 小さなモデル・低い温度 | 温度を上げる、`repetition_penalty`、top-p（第16章） |
| 評価のたびに結果が変わる | 乱数・ドロップアウト | `model.eval()`、シードを固定、`do_sample=False` |

## Hugging Face（transformers）

| エラー・症状 | 原因 | 直し方 |
|---|---|---|
| `OSError: xxx is not a local folder and is not a valid model identifier` | モデル名の間違い、または同意が必要なモデル | つづりを確認。モデルページで規約に同意し、`HF_TOKEN` を設定（第17章） |
| `TypeError: ... got an unexpected keyword argument 'dtype'` | transformersの版が古い | `!pip install -U transformers` してランタイムを再起動。古い版では `torch_dtype=` |
| `apply_chat_template` の結果に `**` が使えない | 古い版では辞書ではなくテンソルが返る | `return_dict=True` を付ける（この教科書のコードは付けてあります） |
| `The attention mask and the pad token id were not set` という警告 | パディングの設定がない | 動作に問題はない。気になるなら `pad_token_id=tok.pad_token_id` を渡す |
| `Setting pad_token_id to eos_token_id` という警告 | 同上 | 無視してOK |
| 生成が止まらない | ベースモデルを使っている／SFTで `<\|im_end\|>` を学習させていない | チャットモデルを使う。第18章の `build_example` を確認 |

## TRL・PEFT・量子化

| エラー・症状 | 原因 | 直し方 |
|---|---|---|
| `Your setup doesn't support bf16/gpu` | T4はbfloat16に非対応 | `SFTConfig(..., bf16=False, fp16=True)`（GPUのとき）。CPUでは両方False |
| `TypeError: ... unexpected keyword argument 'tokenizer'` | TRLの版で引数の名前が変わった | `processing_class=tok` を使う |
| `TypeError: ... 'evaluation_strategy'` | 引数の名前が変わった | `eval_strategy` を使う |
| LoRAで全然変わらない | 学習率が小さすぎる、学習するパラメータが0 | 学習率 $10^{-4}$〜$10^{-3}$、`print_trainable_parameters()` を確認 |
| `bitsandbytes` のエラー | GPUがない、版が合わない | ランタイムをT4 GPUに。`!pip install -U bitsandbytes` |

## そのほか

| エラー・症状 | 原因 | 直し方 |
|---|---|---|
| グラフの日本語が「□□□」 | 日本語のフォントがない | `!pip install -q matplotlib-fontja` と `import matplotlib_fontja`（第5章） |
| `gr.ChatInterface` で `unexpected keyword argument 'type'` | Gradio 6系で引数がなくなった | `type="messages"` を消す（第24章） |
| 自作のWebページでモデルが読み込めない | `file://` で開いている | `python -m http.server` で開く（第24章） |
| GitHub Pagesが404 | 公開の設定がまだ／待ち時間 | Settings → Pages でブランチを選び、1〜2分待つ |

## それでも解決しないときの質問テンプレート

```text
『つくってわかるLLM』第◯章のコードを Google Colab（GPU：T4 ／ CPU）で実行したら、エラーが出ました。
初心者なので、原因と直し方を順番に教えてください。

【実行したコード】
（セルの中身をそのまま貼る）

【エラーメッセージ】
（赤い文字の、最後の10行くらいを貼る）

【試したこと】
（ランタイムを再起動した、エラー辞典の◯◯を試した、など）
```

:::warn 質問するときの注意
エラーメッセージやコードを貼るときは、**トークンやパスワードが含まれていないか**必ず確認してください。`hf_` で始まる文字列などが見えたら、消してから貼りましょう。
:::
