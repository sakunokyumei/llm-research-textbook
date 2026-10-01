# 30 数えるモデルから、学ぶモデルへ：まとめて参照

長い参照ページです。初めて学ぶときは[小ページの順序](30-language-model.html)を使い、ここへ戻って式やコードを引けます。


## 次に来そうなものを数える

文章の続きを予測する最も小さな模型から始めます。「aの後にbが3回、cが1回」現れたなら、aの次をbに0.75、cに0.25と予測できます。直前一つの[トークン](reference.html#term-token)だけを見るモデルをbigramと呼びます。n-gramは一定長の直前の文脈で数えるモデルです。

見たことのない組へ確率0を付けると、評価時の負[対数](reference.html#term-log)[損失](reference.html#term-loss)が無限大になります。各候補へα個分を足す加算平滑化なら、`P(y|x)=(count(x,y)+α)/(count(x)+αV)`。Vは候補数です。αは予測を均等分布側へ寄せる強さで、評価用データで最適化しません。

`collections.Counter` は出現回数を数える辞書に似た道具です。`Counter(zip(...))` で隣接組を数え、未登場の組を読むと0になります。`tokens[:-1]` は最後を除く並び、`tokens[1:]` は最初を除く並びなので、対応させると隣接組です。`sorted(set(tokens))` は重複を除いた後、昇順に並べる操作。出力の辞書も、まず普通のfor文で作ります。[添字](reference.html#term-index)は[第10章](10-data.html)、zipは[第14章](14-vectors.html)へ。

```python
from collections import Counter
tokens = ["a", "b", "a", "b", "a", "c"]
pairs = Counter(zip(tokens[:-1], tokens[1:]))
vocab = sorted(set(tokens))
alpha = 1.0
denom = sum(pairs[("a", y)] for y in vocab) + alpha * len(vocab)
probabilities = {}
for y in vocab:
    probabilities[y] = (pairs[("a", y)] + alpha) / denom
print(probabilities)
```

ここではaの後はbが2回、cが1回。平滑化後はaが1/6、bが3/6、cが2/6です。実データの文書境界を無視して最後と次の文書の最初を接続すると、意図しない組も学習するため、境界を明示します。

## ニューラルモデルも同じ問いに答える

ニューラル言語モデルは、文脈から語彙V個の点数を出し、[softmax](reference.html#term-softmax)で次トークンの確率にします。文字列「abcd」のID列が[0,1,2,3]なら、入力[0,1,2]に対して正解は[1,2,3]。一つ先へずらして対応させます。

これまでの正解の文脈を入力して次の正解を予測する学習はteacher forcingと呼ばれます。生成では自分が出したトークンを次の入力へ加えるので、学習時と生成時の条件は完全には同じではありません。

## 未来を見たら簡単すぎる

位置1で位置2の情報を直接見られるモデルへ、位置2を当てる問題を出すと、答えを見ながら試験を受けることになります。自己回帰モデルでは未来のトークンを参照させません。次章のcausal maskがこの制約を実現します。

Paddingは長さをそろえる補助トークンです。本当の文章ではない位置を損失へ含めると、PAD予測だけで見かけの損失が下がる場合があります。有効トークン数で平均し、PAD位置やSFTの非対象位置を明示的に除外します。

## 演習

:::exercise 1・頻度から予測
aの後がb=6回、c=2回なら、平滑化なしの確率は何ですか。
:::answer
bは6/8=0.75、cは2/8=0.25です。
:::

:::exercise 2・平滑化
候補がb,cの二つで、前問にα=1を使うとどうなりますか。
:::answer
bは7/10=0.7、cは3/10=0.3。分母もαV=2だけ増やします。
:::

:::exercise 3・入力と正解
ID列[4,2,9,1,7]から長さ4の入力と正解を作ってください。
:::answer
入力[4,2,9,1]、正解[2,9,1,7]です。位置ごとに一つ先を対応させます。
:::

:::exercise 4・平均の分母
二つの系列の有効トークン数が3と7なら、損失の総和を何で割って全トークン平均にしますか。
:::answer
10で割ります。系列数2やpaddingを含む長さを分母にしないよう注意します。
:::

:::exercise 5・長い文脈
bigramは「同じ直前トークンだが、それより前の文章が違う」二つの場面へ異なる予測を出せますか。
:::answer
基本的なbigramでは出せません。参照する条件が直前一つで同じだからです。より長い文脈を表すモデルが必要になります。
:::

## 到達課題と出典

bigramをtrainだけで学習し、validationの負対数損失を測ってください。後のTiny Transformerの比較対象にします。[Jurafsky & Martin, Speech and Language Processing](https://web.stanford.edu/~jurafsky/slp3/) のn-gramの章が関連します。
