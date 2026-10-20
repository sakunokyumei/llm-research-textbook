# 31 Attentionを手で計算する：まとめて参照

長い参照ページです。初めて学ぶときは[小ページの順序](31-attention.html)を使い、ここへ戻って式やコードを引けます。


## どの情報を参照すればよいか

「猫は魚を見た。それは大きかった。」の「それ」を解釈するには、前の情報を参照する必要があります。[Attention](reference.html#term-attention)は、各位置が参照先へ重みを付け、その情報を混ぜる計算です。この例は動機づけであり、Attentionの一成分が常に代名詞の意味を表すという保証ではありません。

各位置からQuery（問い合わせ）、Key（照合に使う特徴）、Value（混ぜる内容）の[ベクトル](reference.html#term-vector)を作ります。Self-Attentionでは同じ入力Xを別の重みで変換し、Q=XW_Q、K=XW_K、V=XW_Vとします。名前はたとえであり、学習後のベクトルに人間の決めた役割が固定されるわけではありません。

## 三つの数え方

まずQとKの[内積](reference.html#term-dot)で点数を作ります。次にキー次元d_kの平方根で割り、[softmax](reference.html#term-softmax)で重みにします。最後にその重みでVを加重平均します。

<div class="formula">Attention(Q,K,V) = softmax(QKᵀ / √d<sub>k</sub> + M)V</div>

Mは見ることを許す位置が0、禁止する位置が−∞のmaskです。softmaxは参照先のキー方向へ行います。原資料の演習にあった「d_kで割る」は、この標準式では「√d_kで割る」と読む必要があります。

各成分が独立で平均0・[分散](reference.html#term-variance)1という単純化した仮定なら、d_k個の積の和である内積の分散はd_kになります。√d_kで割ると尺度を調整でき、softmaxが極端に偏りやすくなるのを抑えます。この仮定を厳密に満たすと保証しているわけではありません。

## 二候補で計算する

Q=(1,0)、K₁=(1,0)、K₂=(0,1)、V₁=(2,0)、V₂=(0,4)、d_k=2とします。内積は(1,0)、調整後は(1/√2,0)。softmaxは約(0.670,0.330)。出力は0.670(2,0)+0.330(0,4)≈(1.340,1.321)です。新しい単語を検索して返すのではなく、数の並びを混ぜています。

## Causal maskで未来を隠す

三位置なら、位置0は0だけ、位置1は0と1、位置2は0と1と2を見ます。未来への重みが0になるようsoftmaxの前にmaskします。softmax後に未来だけ0にすると、再正規化しない限り行の和が1でなくなります。

## 未来を隠す表をコードにする

|queryの位置＼keyの位置|0|1|2|
|---|---|---|---|
|0|許可|隠す|隠す|
|1|許可|許可|隠す|
|2|許可|許可|許可|

次のbool表では「隠す」がTrueです。`torch.ones(3,3,dtype=torch.bool)` は全位置Trueの表を作り、`triu(...,diagonal=1)` は対角の一つ上からの上三角だけを残します。`masked_fill(mask, -inf)` はTrueの位置へ負の無限大を入れる操作。`float("-inf")` がその値です。有限な点数が一つ以上あれば、[指数](reference.html#term-power)の `exp(-inf)=0` に対応して隠した候補の確率は0になります。

`q.clone()` は別の保存領域へコピーします。二次元の `k.T` は[転置](reference.html#term-transpose)、`q.shape[-1]` の−1は末尾の軸を指します。`softmax(dim=-1)` はキーが並ぶ末尾軸で正規化します。三つの位置の全てを混ぜて一つの確率にする操作ではありません。記法の仕様は[triu](https://docs.pytorch.org/docs/stable/generated/torch.triu.html)・[masked_fill](https://docs.pytorch.org/docs/stable/generated/torch.Tensor.masked_fill.html)で確認できます。

maskを紙に書けなければ表へ、softmaxが分からなければ[第28章](28-numerics.html)、積が合わなければ[第15章](15-matrices.html)へ戻ります。コードの前に、位置0の出力が必ず(2,0)と予想してください。

```python
import torch, math
q = torch.tensor([[1., 0.], [0., 1.], [1., 1.]])
k = q.clone()
v = torch.tensor([[2., 0.], [0., 4.], [1., 1.]])
scores = q @ k.T / math.sqrt(q.shape[-1])
mask = torch.triu(torch.ones(3, 3, dtype=torch.bool), diagonal=1)
weights = scores.masked_fill(mask, float("-inf")).softmax(dim=-1)
print(weights)
print(weights @ v)
```

最初の出力は必ずV₁=(2,0)。未来を変えても最初の出力が変わらないことが重要なテストです。

## 演習

:::exercise 1・形
Qが(5,8)、Kが(7,8)、Vが(7,4)のとき、点数と出力の形を答えてください。
:::answer
QKᵀは(5,7)、重みとVの積は(5,4)です。queryとkeyの位置数が違うcross-attentionでもこの形で考えられます。
:::

:::exercise 2・均等な点数
調整後の点数が(0,0)、値が(2,0)と(0,4)なら出力は何ですか。
:::answer
重みは(0.5,0.5)、出力は(1,2)です。
:::

:::exercise 3・平方根
d_k=64の標準Attentionで内積を割る値はいくつですか。
:::answer
√64=8です。64で割る式とは別です。
:::

:::exercise 4・maskの位置
三位置のcausal maskで、真ん中の位置が見られるキー位置を答えてください。
:::answer
0と1で、自分より未来の2は見ません。出力位置1の予測対象は通常次の[トークン](reference.html#term-token)2なので、正解を隠します。
:::

:::exercise 5・因果性のテスト
未来の入力トークンだけを変え、過去位置の出力が変わりました。考えられる原因は何ですか。
:::answer
maskの向きや適用軸、未来を参照する別の処理、位置の対応の誤りなどです。評価モードで乱数による違いを除き、最小例で確認します。
:::

:::exercise 6・解釈の限界
大きいAttention重みだけを見て「この単語が判断の原因だ」と断定できますか。
:::answer
できません。Value、他のヘッド、残差、後続層の影響もあります。因果的な説明には介入実験や対照が必要です。
:::

## 到達課題と出典

重みの行和、有効位置、[shape](reference.html#term-tensor)、未来を変えても過去が変わらない性質を確認してください。[Attention Is All You Need, §3.2](https://arxiv.org/abs/1706.03762) が標準式の出典です。
