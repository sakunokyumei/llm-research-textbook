# 28 Optimizerと数値安定性：まとめて参照

長い参照ページです。初めて学ぶときは[小ページの順序](28-numerics.html)を使い、ここへ戻って式やコードを引けます。


## 大きな指数は計算機に収まらない

候補の点数zを確率へ変える[softmax](reference.html#term-softmax)は`pᵢ=exp(zᵢ)/Σⱼexp(zⱼ)`です。すべて正で合計1になります。しかしzが1000なら[exp](reference.html#term-log)(1000)は一般的な[浮動小数点](reference.html#term-finite)の範囲を超えます。

全ての点数から同じmを引いても、分子と分母の共通因子exp(−m)が打ち消されるので結果は同じです。mに最大値を選ぶと[指数](reference.html#term-power)の入力は0以下になります。log-sum-expも`m+log Σᵢexp(zᵢ−m)`と安定に計算できます。

```python
import math
z = [1000., 1001., 1002.]
m = max(z)
e = [math.exp(x - m) for x in z]
p = [x / sum(e) for x in e]
logsumexp = m + math.log(sum(e))
print(p, sum(p), logsumexp)
```

確率は約[0.0900,0.2447,0.6652]です。単に確率に小さなεを足してlogを取ると元の目的関数を変える場合があるので、通常は[ライブラリ](reference.html#term-library)の安定なlog_softmaxやcross_entropyを使います。

## これから出る略語を先に読む

maskは、計算へ含める位置と除外する位置を指定するものです。キーは[Attention](reference.html#term-attention)で参照先となる候補で、第31章で数値例を扱います。第28章では「全候補を除外したら確率の合計1を作れない」と考えてください。clip(x,a,b)はxがa未満ならa、bより大きければb、間ならxを返す操作です。[勾配](reference.html#term-gradient)の方向を保つ[ノルム](reference.html#term-norm)の縮小とは異なります。

SGDはStochastic Gradient Descent（確率的勾配降下法）の略で、全データではなく抽出した例の勾配で更新する考えです。一次モーメントは勾配の平均、二次モーメントは勾配の二乗の平均を指します。「移動平均」は古い値へ[係数](reference.html#term-coefficient)β、新しい値へ1−βを掛けて足す更新です。たとえば古い値0、新しい勾配2、β=0.9なら `m=0.9×0+0.1×2=0.2`。Adamでは開始時の0への偏りを `m/(1−β^t)` などで補正します。第1回なら0.2/0.1=2です。式のtは更新回数で、[ベクトル](reference.html#term-vector)は各成分へ適用します。

## SGDからAdamWへ

SGDは標本やミニバッチの勾配で更新します。Momentumは過去の勾配方向を蓄積し、Adamは勾配の一次モーメントmと二次モーメントvの移動平均を使って成分ごとに更新を調整します。初期値0による偏りを補正して、概略`θ←θ−η m̂/(√v̂+ε)`で更新します。

AdamWは重み減衰をこの勾配由来の更新から分離します。適応的な更新をするAdamにL2罰則を加えたものと一般には同じではありません。[学習率](reference.html#term-learning-rate)を初期に上げるwarmup、後で下げるschedule、勾配ノルムを上限へ縮めるclippingもよく使われます。これらはデータや実装の誤りを隠す万能薬ではありません。

## 精度とメモリの交換

FP32、FP16、BF16は有限ビットで[実数](reference.html#term-real)を近似する形式です。BF16はFP16より広い指数範囲を持ちますが、仮数の精度は粗くなります。mixed precisionは演算の種類に応じて精度を使い分け、速度やメモリを改善する方法です。FP16では小さい勾配のunderflow対策としてloss scalingを使うことがあります。BF16で同じ処置が常に必要とは限りません。

NaNは数として定まらない結果、infは表現範囲の超過などを示します。最初に入力、logit、[損失](reference.html#term-loss)、勾配、更新後の重みのどこで非有限値になったかを調べます。学習率を下げるだけでなく、ラベル、mask、0除算、全要素を隠したsoftmax行も確認します。

## 演習

:::exercise 1・softmaxを手計算
z=(0,ln2)のsoftmaxを求めてください。
:::answer
指数は(1,2)、合計3なので(1/3,2/3)です。
:::

:::exercise 2・平行移動
前問の両方の点数に100を足したら確率はどうなりますか。
:::answer
変わりません。共通のexp(100)が分子と分母で消えるためです。浮動小数点では安定な形で計算します。
:::

:::exercise 3・勾配のclipping
勾配が(3,4)、ノルム上限1なら、方向を保って縮めた勾配は何ですか。
:::answer
元のノルムは5なので1/5倍して(0.6,0.8)です。各成分を個別に±1へ切る方法とは異なります。
:::

:::exercise 4・全mask
softmaxへ入れる一行がすべて−∞だと、最大値を引く操作で何が起こりますか。
:::answer
−∞−(−∞)がNaNとなり得ます。少なくとも有効なキーが一つある設計にするか、空行の意味と扱いを明示します。
:::

:::exercise 5・AdamW
AdamにL2罰則を追加すれば常にAdamWと同じですか。
:::answer
同じではありません。L2由来の勾配も適応的なモーメント計算へ入る場合と、重み減衰を独立に適用する場合で更新が異なります。
:::

:::exercise 6・精度の比較
FP16で失敗しFP32で成功しました。それだけでハードウェアが故障していると結論できますか。
:::answer
できません。表現範囲・丸め・underflow・不安定な式などを調べます。最初に非有限値となる場所を特定し、小さい例で比較します。
:::

## 到達課題と出典

softmaxを[1000,1001]、[−1000,−1001]、[0,0]で試し、有限値・非負・合計1・定数加算への不変性を確認してください。[AdamW](https://arxiv.org/abs/1711.05101)、[PyTorch AMP](https://docs.pytorch.org/docs/stable/amp.html) を参照。
