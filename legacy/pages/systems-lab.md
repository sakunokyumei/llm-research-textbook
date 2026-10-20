# 追加実習：GPUと分散へ進む

このページは41・42章からの実習手順です。CPUで確認したラボと区別し、**本教材の制作環境ではGPU kernelと複数GPUの性能を実測していません**。利用可能な装置を確認し、費用上限を決めてから進みます。

## Tritonの最初の一歩

Pythonのfor文で要素を一つずつ処理すると、Pythonの実行費用が支配的になります。GPUでは多数の要素を並べて処理します。TritonはGPU上で動くkernelを記述する道具です。host側のPythonがkernelを起動し、device側がblockごとの処理を行います。

まず[公式vector addition tutorial](https://triton-lang.org/main/getting-started/tutorials/01-vector-add.html)の対応環境で、二つの[ベクトル](reference.html#term-vector)の和を作ります。`program_id`は担当blockの番号、`arange`はblock内の位置、`offset = block_id * BLOCK_SIZE + arange`は全体の[添字](reference.html#term-index)です。長さがblock幅で割り切れない最後のblockでは`offset < n`をmaskにして範囲外を読み書きしません。

たとえばn=10、BLOCK_SIZE=4なら3blockを起動します。最後のblockのoffsetは8,9,10,11で、有効なのは8と9。10と11を無条件に読むのは誤りです。

実習ではn=1,10,1024,1025でPyTorchの`x+y`と比較し、最大絶対誤差を記録します。次にdtypeとblock幅を一つずつ変えます。正しさを確認してから、warmup・同期・反復測定を行います。GPU処理は非同期なので、起動だけの時間をkernel実行時間と取り違えないでください。

## FlashAttentionへ進む階段

いきなり高速kernel全体を書かず、①通常の[Attention](reference.html#term-attention)、②mask、③数値安定な[softmax](reference.html#term-softmax)、④blockごとの最大値・分母・重み付き和の更新、⑤逆伝播、の順に比較します。CPUの[math_checks.py](downloads/math_checks.py)は④の[スカラー](reference.html#term-scalar)版です。GPU実装ではtileの[shape](reference.html#term-tensor)、境界mask、dtype、保存する統計量が追加されます。

検証はランダム入力だけでなく、長さ1、極端なscore、同一score、端数の長さ、maskがあるケースを含めます。許容誤差はdtypeと演算順序に応じて説明し、「exact attentionだからbit完全一致」とはしません。

## DDPを始める

[PyTorch DDP tutorial](https://docs.pytorch.org/tutorials/intermediate/ddp_tutorial.html)の公式例を基準にします。最初は一台・二processの小さな回帰問題で、rank、world size、process group、データ分割、[勾配](reference.html#term-gradient)の集約を確認します。GPUならNCCL、CPUなら環境に応じたbackendを使い、OSの対応状況を確認します。

一台でbatch64の更新と、二台で各batch32を使う更新を比べます。[損失](reference.html#term-loss)の平均化、初期重み、データの順番を揃え、勾配と更新後の重みを比較します。dropout等の乱数や[浮動小数点](reference.html#term-finite)の演算順序の差は別に記録します。データの重複・欠落をIDで確認し、DistributedSamplerを使う場合はepochごとの扱いも確認します。

## 研究に必要な測定票

|欄|記録すること|
|---|---|
|正しさ|基準実装、入力分布、dtype、誤差、テスト|
|装置|GPU型・台数、device間接続、ソフトウェア版|
|負荷|batch、系列長、head幅、padding、同時request数|
|時間|warmup、同期方法、中央値、上位percentile|
|メモリ|重み、optimizer、activation、cache、peak|
|通信|集約する量、通信の回数、計算との重なり|
|解釈|改善した条件、悪化した条件、未確認の範囲|

速度が出なかったら、演算量・転送量・起動費用・通信待ちのどれが支配的か調べます。測定の前に最適化を決めつけないことが、システム研究の第一歩です。
