{"title":"32 Transformerを一つのモデルにする","part":"言語モデルを作る","goal":"Embeddingから語彙logitまでの形を追う","prereq":"27〜31"}

## 部品をつなげる

入力は整数のトークンID列です。Embeddingで各IDをd個の値にし、位置の情報を加え、AttentionとMLPのブロックを何層か通します。最後に各位置から語彙V個の点数を出します。この点数をlogitと呼びます。学習ではlogitと一つ先の正解トークンから交差エントロピーを計算します。

|段階|shape|
|---|---|
|ID|B,T|
|Embedding|B,T,d|
|各ブロック|B,T,d|
|出力logit|B,T,V|
|正解ID|B,T|

Bはバッチの例数、Tは系列長、dは特徴数です。最後の語彙方向にsoftmaxします。バッチ方向へ正規化してはいけません。

## Multi-Head Attention

一つの比較だけではなく、複数の射影で並行して参照するのがMulti-Head Attentionです。特徴数dをH個のヘッドへ分ける標準的な実装では、各ヘッドの幅d_h=d/H。Q,K,Vを(B,H,T,d_h)として計算し、各出力を結合してdへ戻し、出力射影を掛けます。

「あるヘッドは文法担当」と人間が割り当てるわけではありません。異なる参照を学べる構造を用意するだけです。同じ総幅でヘッド数を変えると、一ヘッドの幅も変わります。比較では何が同時に変わるかを記録します。

## 位置の情報

位置表現なしのAttentionには順序を区別しにくい性質があります。位置ごとの学習ベクトルを足す方法や、sin/cosを使う方法があります。後で扱うRoPEはQとKへ位置に応じた回転を施し、内積へ相対的な位置の構造を入れます。

単に長い入力を受け付ける実装へ変えても、学習より長い文脈を正しく使える保証はありません。位置表現と長文での評価を別に考えます。

## ブロックの中身

本教材の小モデルはPre-Normを使い、`x←x+Attention(LayerNorm(x))`、続いて`x←x+MLP(LayerNorm(x))`とします。残差の入力と出力は同じshape。MLPは各位置へ独立に適用し、位置間の混合はAttentionが担います。

2017年の元のTransformerはencoder-decoder構成で翻訳などを扱いました。本教材の小モデルは未来を隠すdecoder-onlyです。原論文のモデルそのものを完全に再現したという意味ではありません。BERT系の双方向encoderや、encoder-decoderと用途・maskの違いを整理します。

## 名前とコードをつなぐ

encoderは入力の表現を作る部分、decoderは出力を作る部分です。双方向encoderは左右両側を参照し、自己回帰decoderは既知の過去だけから次を予測します。encoder-decoderでは入力側の表現を出力側から参照するcross-attentionも使います。本教材のdecoder-onlyではその入力用encoderを別に持ちません。

ここから完成コードへ移る前に、[Pythonの橋](python-reading.html)でModuleの継承・chunk・軸交換・reshapeを、[段階ごとの解説](lab-guide.html)でID→Embedding→Attention→損失の対応を確認します。B=2,T=3,d=8,H=2ならQは(2,2,3,4)、点数は(2,2,3,3)、ヘッド結合後は(2,3,8)。紙に各軸の名前を残してからコードへ進んでください。

## 演習

:::exercise 1・ヘッド幅
d=64、H=4なら一ヘッドの幅はいくつですか。H=3へ変えると何に注意しますか。
:::answer
16です。単純に均等分割する実装では64が3で割り切れないため、そのまま使えません。
:::

:::exercise 2・logitの形
B=2、T=8、V=100ならlogitには何個の値がありますか。
:::answer
2×8×100=1600個です。各トークン位置に100候補の点数があります。
:::

:::exercise 3・重みの共有
各位置のMLPは別々のパラメータを持つのでしょうか。
:::answer
通常のTransformerでは同じMLPの重みを全位置へ適用します。位置数が増えても、この部分のパラメータ数は増えません。
:::

:::exercise 4・モデルの違い
双方向encoderをそのまま次トークン予測へ使い、未来も見せると何が起こりますか。
:::answer
予測対象の情報が入力に漏れ、自己回帰生成時には存在しない情報を使って学習してしまいます。目的に合うmaskが必要です。
:::

:::exercise 5・位置Embedding
学習可能な位置Embeddingが最大128位置なら、単に256位置の入力を渡せば使えますか。
:::answer
そのままでは存在しない行を参照します。拡張や再設計が必要で、動かせても長文能力の検証は別です。
:::

## 到達課題と出典

実装ラボのTiny Transformerで、各段階のshapeを紙に書いてからコードと照合してください。[Attention Is All You Need](https://arxiv.org/abs/1706.03762)、[RoFormer](https://arxiv.org/abs/2104.09864)、[BERT](https://aclanthology.org/N19-1423/) を参照。
