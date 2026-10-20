# 26 PyTorchと自動微分：まとめて参照

長い参照ページです。初めて学ぶときは[小ページの順序](26-pytorch.html)を使い、ここへ戻って式やコードを引けます。


## 微分を手で全部書くのは大変

パラメータが二つなら[勾配](reference.html#term-gradient)を手で書けます。しかし百万個になると、式を間違えずに実装するのが難しくなります。PyTorchは、[テンソル](reference.html#term-tensor)の演算と計算グラフに基づく[自動微分](reference.html#term-autograd)を提供する[ライブラリ](reference.html#term-library)です。自動微分は、少しずつ入力を変えて差分を取る数値[微分](reference.html#term-derivative)とは異なり、実行した基本演算の微分を[連鎖律](reference.html#term-chain-rule)で組み合わせます。

インストールは [PyTorch公式の選択画面](https://pytorch.org/get-started/locally/) でOSとCPU/GPU環境に合うコマンドを選びます。まずCPUで本章を実行できます。実装ラボには、この教材で検証した版と再現コマンドを記載します。

## NumPyから持ち込めるもの

`torch.tensor(2.0)` はPythonの数からテンソルを作る操作です。表から作る点は第15章の `np.array` に似ていますが、別のライブラリの型です。整数IDは整数型、微分する重みは[浮動小数点](reference.html#term-finite)型で扱います。`dtype=torch.float64` は数を64bitの浮動小数点として保存する指定で、ここでいうdouble精度です。[第17章の数値精度](17-calculus.html)へ戻れます。

導入後に `python -c "import torch; print(torch.__version__)"` で版を表示します。`No module named torch` は今のPythonに導入されていないという意味です。[実装ラボの準備](labs.html)に従い、インストールと実行に同じ[仮想環境](reference.html#term-venv)のPythonを使います。GPUを使えない場合も本章のCPUコードを進められます。

## 一つの値で確かめる

```python
import torch
w = torch.tensor(2.0, requires_grad=True)
loss = (w - 3) ** 2
loss.backward()
print(loss.item(), w.grad.item())
```

[損失](reference.html#term-loss)1、勾配−2です。`requires_grad=True`で微分を追跡し、`backward()`で出力から入力へたどります。`grad`が計算された勾配、`item()`は一要素のテンソルからPythonの値を取り出す操作です。整数の[添字](reference.html#term-index)テンソル自体へ通常の勾配を計算するわけではありません。

`with` は、字下げした処理の間だけ指定した管理を適用する書き方です。`with torch.no_grad():` の中では通常の演算で新しい勾配追跡を作りません。`None` は値がないことを表すPythonの値で、`w.grad = None` は古い勾配を空にします。0という勾配が計算された場合とは区別します。`w -= ...` は値をその場で更新するため、追跡中の重みを更新するこの部分をno_gradで囲みます。[公式のno_grad](https://docs.pytorch.org/docs/stable/generated/torch.no_grad.html)も参照できます。

## 更新の順番

```python
import torch
w = torch.tensor(0.0, requires_grad=True)
for step in range(20):
    loss = (w - 3) ** 2
    loss.backward()
    with torch.no_grad():
        w -= 0.1 * w.grad
    w.grad = None
print(w.item())
```

値は3へ近づきます。PyTorchの勾配は基本的に加算されるため、次の独立な更新の前に消します。`no_grad()`は更新の操作を新しい計算グラフへ追加しないために使っています。通常のモデルでは[optimizer](reference.html#term-optimizer)の`zero_grad()`と`step()`がこの役割をまとめます。

バッチは複数の例をまとめたものです。損失をバッチ平均にするか合計にするかで勾配の大きさが変わります。複数バッチの勾配を蓄積して一回更新する場合は、意図した平均になるよう重み付けをそろえます。

optimizerは重みをどう更新するかを管理する道具です。`torch.optim.AdamW(model.parameters(), lr=0.01)` はモデルの調整する値を渡し、歩幅を指定して作ります。`zero_grad()`で前回の勾配を消し、損失を作って `backward()`、`step()`で値を更新します。具体的なMLPは次章、更新式の違いは第28章で確認します。Dropoutは学習中に一部の成分をくじで0にする方法で、詳しい倍率は次章です。

## CPUとGPU、学習と評価

テンソルにはdeviceがあり、CPUとGPUの値を不用意に混ぜて計算できません。モデルと入力を同じ装置へ移します。小さい処理では転送や準備の費用の方が大きいこともあります。

`model.train()`と`model.eval()`はDropoutなどの振る舞いを切り替えます。evalは自動微分を無効化する命令ではありません。評価で勾配が不要なら`torch.no_grad()`や`torch.inference_mode()`も使います。逆にtrainはそれ自体で学習を実行する命令ではありません。

## 演習

:::exercise 1・手計算と照合
loss=(2w+1)²、w=1でlossとw.gradを予想してください。
:::answer
lossは9、勾配は2×3×2=12です。上のコードの式と初期値を変更して確認します。
:::

:::exercise 2・勾配の加算
同じwについて独立に新しいlossを作ってbackwardを二回呼び、間にgradを消しませんでした。何に注意しますか。
:::answer
勾配が足されます。二回の勾配を意図的に蓄積したいのでなければ、更新前にzero_grad等で消します。同じグラフの再利用にはまた別の制約があります。
:::

:::exercise 3・平均と合計
同じ例を四回複製してバッチにしました。損失を合計する場合と平均する場合で、勾配はどう違いますか。
:::answer
合計なら一例の4倍、平均なら一例と同じです。実効[学習率](reference.html#term-learning-rate)が変わる原因になります。
:::

:::exercise 4・evalの意味
model.eval()だけを呼んだら、勾配の追跡は止まりますか。
:::answer
止まりません。層の動作モードと勾配追跡は別です。必要に応じno_grad等を併用します。
:::

:::exercise 5・数値検証
自動微分と中央差分を比べるとき、最初にdouble精度の小さな入力で試す理由は何ですか。
:::answer
手で追える形にし、丸め誤差や巨大な計算による切り分けの難しさを減らすためです。差分の刻み幅や微分不可能な点にも注意します。
:::

## 到達課題と出典

線形回帰をPyTorchへ置き換え、手書きの勾配と同じ値になるか一回の更新で確認します。[PyTorch Autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html) と [Optimization](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html) を参照。
