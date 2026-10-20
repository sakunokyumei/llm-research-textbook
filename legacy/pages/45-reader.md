# 45 MoEと、使う計算を選ぶ設計：まとめて参照

長い参照ページです。初めて学ぶときは[小ページの順序](45-moe.html)を使い、ここへ戻って式やコードを引けます。


## 全員を毎回呼ばない

多数の専門家へ相談できるとして、毎回全員を呼ぶと費用が高くなります。Mixture of Experts（[MoE](reference.html#term-moe)）は、複数の変換器expertからrouterが一部を選ぶ構造です。TransformerではMLP部分をMoEへ置き換える例がよくあります。

入力xからrouterの点数を作り、[softmax](reference.html#term-softmax)やtop-kで選択し、選ばれたexpertの出力を重み付けして足します。ただし「expert」という名前は、人間に分かる専門分野を自動的に分担している保証ではありません。

## 大きさの二つの数え方

8個のexpertが各100万パラメータ、共有部分が200万なら総数は1000万です。一[トークン](reference.html#term-token)が2個を使うなら、この単純な模型で使う部分は400万。総パラメータ数と活性化パラメータ数は違います。全expertをどこかへ保存する必要があるので、活性化数だけで必要メモリを決められません。

routerの処理、expertへのtokenの振り分け、GPU間通信、容量制約も費用になります。人気のexpertへ入力が集中すると待ちが発生します。負荷[分散](reference.html#term-variance)の[損失](reference.html#term-loss)やバイアス調整など、複数の設計があります。容量を超えたtokenをどう扱うかもモデルと実装に依存します。

## 比較の問いをそろえる

denseモデルと比べる際は、総パラメータ数、活性化[計算量](reference.html#term-complexity)、学習トークン、実時間、メモリのどれを固定したかを明記します。同じ総パラメータでも一回の計算量が違い、同じ活性化数でも通信費用が違います。

MoEの[ablation](reference.html#term-ablation)にはexpert数、top-k、routerの温度、負荷分散の強さなどがあります。一つを変えると他の予算も変わる可能性があるため、効果の原因を慎重に解釈します。

## 二人のexpertを紙とコードで呼ぶ

まずrouterは「入力が0以上なら0番、負なら1番」と固定します。expert0は2x、expert1は−x。これは学習するMoE全体の再現ではなく、選択した部品だけを計算する最小例です。

```python
inputs = [-2., -1., 1., 2.]
counts = [0, 0]
outputs = []
for x in inputs:
    if x >= 0:
        expert = 0
        value = 2 * x
    else:
        expert = 1
        value = -x
    counts[expert] = counts[expert] + 1
    outputs.append(value)
print(counts, outputs)
```

割り当ては2件ずつ、出力は[2,1,2,4]です。入力を全て正にするとexpert0へ集中します。横に入力、縦に出力を描き、各expertを色分けします。学習するrouterへ進むには第27章の[線形層](reference.html#term-linear-layer)で点数を作り、第34章のtop-kで選ぶ計算へ置き換えます。offloadは重みなどをGPU以外へ置き、必要時に転送する方法、denseはこの文脈では選択せず通常の密な計算を行うモデルです。比較する予算は[第42章](42-distributed.html)で確認します。

## 演習

:::exercise 1・総数と使用数
4expertが各200万、共有100万、top-1の模型で総数と一トークンの使用数はいくつですか。
:::answer
総数900万、使用数300万です。router等を無視した模型の数です。
:::

:::exercise 2・偏り
全tokenの90%が同じexpertへ送られています。何を測りますか。
:::answer
expert別のtoken数、待ち時間、容量超過、品質、routerの分布を測ります。負荷分散を強くしすぎた場合の品質低下も確認します。
:::

:::exercise 3・メモリ
活性化パラメータが小さいので、一台のGPUへ全モデルが必ず入ると言えますか。
:::answer
言えません。選ばれないexpertを含む総重みの保存先が必要です。分散配置やoffloadには別の費用があります。
:::

:::exercise 4・比較
top-1からtop-2にして品質が上がりました。routing方法そのものだけの効果ですか。
:::answer
計算量も増えているため、単独の効果と断定できません。計算予算を合わせた対照も必要です。
:::

## 到達課題と出典

二つの線形expertとrouterの玩具を作り、割り当て件数と出力を可視化してください。[Switch Transformers](https://arxiv.org/abs/2101.03961)、[DeepSeek-V3](https://arxiv.org/abs/2412.19437) を参照。
