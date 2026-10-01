# 42 分散学習と並列化：まとめて参照

長い参照ページです。初めて学ぶときは[小ページの順序](42-distributed.html)を使い、ここへ戻って式やコードを引けます。


## 一台に入らない、時間も足りない

複数GPUを使う方法は一つではありません。データを分ける、重みの[行列](reference.html#term-matrix)を分ける、層を分ける、文脈を分ける、expertを分ける。それぞれ転送するものと待ち時間が違います。まず単一GPUで正しい基準を作ってから[分散](reference.html#term-variance)化します。

Data Parallelでは各装置がモデルのコピーを持ち、異なるデータで[勾配](reference.html#term-gradient)を計算します。勾配を集めて平均し、同じ更新を適用します。DDPはこの方式を実現するPyTorchの仕組みです。rankは各processの番号、world sizeは参加process数です。

## 通信の基本操作

all-reduceは全員の値を合計などでまとめ、全員へ結果を渡します。all-gatherは各自の断片を全員分集めます。reduce-scatterは値を集約した結果を分割して配ります。これらをcollective通信と呼び、参加者が対応する順序で呼ぶ必要があります。一部だけが例外で抜けると、残りが待ち続ける場合があります。

FSDPやZeROの系統は、重み・勾配・[optimizer](reference.html#term-optimizer)状態の全部または一部を分割し、各装置のメモリを減らします。必要時に集めたり再計算したりするため、保存メモリと通信・計算を交換します。細かな分割方式は版と設定に依存します。

## 他の並列化

Tensor Parallelは大きな行列演算を装置間で分けます。Pipeline Parallelは層のまとまりを分け、microbatchを流します。ある装置が入力待ちになる空白をpipeline bubbleと呼びます。Context Parallelは長い系列を分け、Expert Parallelは[MoE](reference.html#term-moe)のexpertを分けます。複数方式を組み合わせる場合もあります。

Gradient checkpointingは中間結果を全て保存せず、逆伝播時に再計算してメモリを減らす方法で、複数GPUそのものとは別です。計算時間が増える可能性があります。

## 実効バッチと平均

一装置あたりバッチb、装置数g、蓄積回数aなら、均等な設定で一更新に使う例数はbgaです。b=4、g=2、a=8なら64例。各装置の有効[トークン](reference.html#term-token)数が違う場合、各装置の平均[損失](reference.html#term-loss)を単純平均すると、全トークン平均と一致しないことがあります。合計損失と総有効数の重みを合わせます。

## 二つの装置を、CPU上の二つの計算で模擬する

processは実行中のプログラムです。ここでは通信をまだ行わず、二つの同数バッチの平均勾配が結合バッチと一致することだけを確かめます。重みw=0、予測wx、二乗誤差を使います。

```python
import torch
w = torch.tensor(0., requires_grad=True)
x = torch.tensor([1., 2., 3., 4.])
y = 2 * x
loss_all = ((w * x - y) ** 2).mean()
grad_all = torch.autograd.grad(loss_all, w)[0]
loss_a = ((w * x[:2] - y[:2]) ** 2).mean()
loss_b = ((w * x[2:] - y[2:]) ** 2).mean()
grad_a = torch.autograd.grad(loss_a, w)[0]
grad_b = torch.autograd.grad(loss_b, w)[0]
combined = (grad_a + grad_b) / 2
print(grad_all.item(), combined.item())
assert torch.allclose(grad_all, combined)
```

`torch.autograd.grad(loss,w)` は指定したwの[微分](reference.html#term-derivative)を戻り値で受け取り、w.gradへ蓄積するbackwardとは使い方が違います。`[0]` は最初の対象の微分。両方−30です。バッチが2例ずつなので単純平均できました。1例と3例なら各勾配を1/4、3/4で重み付けします。通信・速度・複数GPUはこの試験では未検証です。勾配なら[第26章](26-pytorch.html)、実際のDDPは[追加実習](systems-lab.html)へ戻れます。

## 演習

:::exercise 1・バッチ数
一装置8例、4装置、蓄積2回の実効バッチはいくつですか。
:::answer
8×4×2=64例です。更新回数が同じでも一更新のデータ量が変わります。
:::

:::exercise 2・平均勾配
二装置の勾配が2と6で、例数が同じなら平均は何ですか。
:::answer
4です。sumだけを使うなら8になるので、平均化の規約を確認します。
:::

:::exercise 3・不均等な重み
一方は1トークンの平均損失1、他方は9トークンの平均損失3でした。全トークン平均はいくつですか。
:::answer
(1×1+9×3)/10=2.8です。単純平均2ではありません。
:::

:::exercise 4・メモリと時間
FSDPでメモリが減りました。必ず学習も速くなりますか。
:::answer
必ずではありません。通信や再計算が増える場合があります。装置数・モデル・ネットワーク・バッチに応じて測定します。
:::

:::exercise 5・正しさの基準
分散化が正しいか、最初にどう確認しますか。
:::answer
同じ小データ・同じ実効バッチで単一processと比較し、損失と一回の更新が許容誤差内で一致するか確認します。データの重複配布や最後の端数も調べます。
:::

## 到達課題と出典

GPUがない場合も、二つの小バッチの勾配を正しく平均し、結合バッチの勾配と一致させられます。複数GPUでの速度は未測定と明記します。[DDP](https://docs.pytorch.org/docs/stable/generated/torch.nn.parallel.DistributedDataParallel.html)、[FSDP2](https://docs.pytorch.org/tutorials/intermediate/FSDP_tutorial.html)、[ZeRO](https://arxiv.org/abs/1910.02054) を参照。
