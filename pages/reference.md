# 用語・記号の早見表

初めて学ぶときは各講義の例から進んでください。このページは復習用です。

|記号・語|読み方・意味|戻る講義|
|---|---|---|
|x ∈ ℝ|xは実数の集合に属する|05・06|
|xᵢ|i番目の値。iは添字|06|
|Σᵢ xᵢ / Πᵢ xᵢ|対象の値の和／積|06|
|exp(x), log(x)|自然指数関数／自然対数|07|
|xᵀy|同じ長さのベクトルの内積|14|
|‖x‖₂|平方和の平方根。長さ|14|
|A ∈ ℝᵐˣⁿ|m行n列の実数行列|15|
|rank|独立な列（または行）の最大数|15・16|
|∂L/∂x, ∇L|偏微分／変数ごとの偏微分を並べた勾配|18|
|Jv / vᵀJ|Jacobianと方向／逆向きの感度の積|18|
|E[X], Var(X)|期待値／分散|21|
|p(A\|B)|Bの条件下でAが起きる確率|20|
|H(p)=−Σp log p|entropy。分布の不確実性|23|
|CE(p,q)=−Σp log q|cross entropy。真の分布pをqで符号化する指標|23|
|KL(p\|\|q)=Σp log(p/q)|分布のずれ。対称とは限らない|23|
|PPL=exp(平均NLL)|自然対数で計算した平均損失の指数|23|
|shape / dtype / device|配列の各軸の長さ／数値型／計算装置|16・26|
|forward / backward|出力の計算／勾配の逆伝播|26・27|
|epoch / step / batch|データ一巡／更新等の一段階／まとめて処理する例|33|
|logit|softmaxへ入れる正規化前のscore|28|
|Q / K / V|query／key／valueの射影|31|
|causal mask|未来の位置への参照を禁止するmask|31|
|prefill / decode|promptを処理する段階／次tokenを生成する段階|43|
|SFT / PEFT / LoRA|教師あり調整／一部パラメータの効率的調整／低ランク更新|36|
|RLHF / RLVR|人の選好等を使うRL／検証可能な報酬を使うRL|39|
|baseline / ablation|比較の基準／構成要素を外す比較|53|
|reproducibility|条件を明示して結果を確かめ直せる性質|12・53|

## 計算の早見表

行列積：(m×n) @ (n×k) → (m×k)。内側のnが一致します。

Attention：softmax(QKᵀ/√dₖ + mask)V。softmaxは各queryに対してkeyの軸へ適用します。

安定なsoftmax：m=max(z)、pᵢ=exp(zᵢ−m)/Σⱼexp(zⱼ−m)。温度Tを使う場合はz/Tに適用します。

勾配降下：θ←θ−η∇L。ηは学習率。勾配は増加方向なので、最小化には逆向きへ動きます。

LoRA：W'=W+(α/r)BA。Wがd_out×d_inならAはr×d_in、Bはd_out×r。

平均の標準誤差：独立同分布・有限分散の条件で概ねs/√n。標準偏差そのものとは違います。

<h2 id="term-sides">両辺</h2>

等号や不等号の左の式と右の式を合わせた呼び名。[天びんの例](05b-equations.html)。

<h2 id="term-solution">解</h2>

式に書かれた条件を満たす値。2x+3=11ではx=4が解。[確認する例](05b-equations.html)。

<h2 id="term-check-answer">検算</h2>

求めた答えを元の式などへ戻し、条件を満たすか確かめる操作。[確認する例](05b-equations.html)。

<h2 id="term-affine">アフィン変換</h2>

行列を掛ける変換と、一定のずれを加える操作を組み合わせる変換。Y=XW+b。[一出力から確認する](18f-linear.html)。

## 困ったときの順番

コードが動かないときは、エラーの最後の行→該当箇所→入力のshape・dtype・device→小さな再現例。損失が下がらないときは、ラベルのshift→mask→勾配→optimizer→小データへの過学習→データ分割を確認します。

## 初出の語から戻る辞書

各語の短い意味と、具体例を学ぶ小ページです。章に進む前提を満たしていない発展語は、説明を読むだけで習得した扱いにしないでください。

<h2 id="term-term">項</h2>

足し算で区切った式の部分。2x−3では2xと−3。 [具体例と演習](05-algebra.html)。

<h2 id="term-coefficient">係数</h2>

文字に掛かっている数。2xのxの係数は2。 [具体例と演習](05-algebra.html)。

<h2 id="term-real">実数</h2>

数直線上の値。整数、小数、分数、√2などを含む。ℝはその集合の記号。 [具体例と演習](04d-roots.html)。

<h2 id="term-power">累乗・指数・底</h2>

aを繰り返し掛けたaⁿで、aが底、nが指数。零乗や負の指数は続きのページで定義する。 [具体例と演習](04-powers.html)。

<h2 id="term-substitution">代入</h2>

式の文字へ値を入れる操作。Pythonの代入は値へ名前を割り当てる別の用法。 [具体例と演習](05-algebra.html)。

<h2 id="term-equation">方程式</h2>

左右が等しいという条件を満たす未知の値を探す式。 [具体例と演習](05b-equations.html)。

<h2 id="term-distribution-law">分配法則</h2>

a(b+c)=ab+ac。aを括弧内の両方へ掛ける。 [具体例と演習](05c-distribute.html)。

<h2 id="term-inequality">不等号・不等式</h2>

大小や範囲を示す記号と、その記号を含む条件の式。 [具体例と演習](05d-inequalities.html)。

<h2 id="term-proportion">比例・反比例</h2>

y=axとy=a/xの関係。後者ではx=0を使えない。 [具体例と演習](05e-proportion.html)。

<h2 id="term-domain">定義域・値域</h2>

入力として許す範囲と、実際の出力の範囲。 [具体例と演習](06-functions.html)。

<h2 id="term-index">添字・総和</h2>

添字はどの値かの番号。Σは指定範囲を足す記号。 [具体例と演習](06-functions.html)。

<h2 id="term-log">対数・自然対数</h2>

対数は何乗かを逆に求める。自然対数は底e、exp(x)=eˣ。 [具体例と演習](07-logarithms.html)。

<h2 id="term-type">型・type</h2>

値の種類。type(x)はその型を調べる。 [具体例と演習](08-python.html)。

<h2 id="term-indent">インデント</h2>

字下げで処理のまとまりを示す。Pythonでは動作を決める記法。 [具体例と演習](09-control.html)。

<h2 id="term-membership">in・not in</h2>

値が入れ物に含まれるか／含まれないかを判定する。辞書では鍵を調べる。 [具体例と演習](13-algorithms.html)。

<h2 id="term-set-add">集合への追加</h2>

集合のaddは値を追加する。同じ値の重複は増えない。 [具体例と演習](13-algorithms.html)。

<h2 id="term-unique">一意性</h2>

この教材のIDでは、同じIDを別の実験へ割り当てないこと。 [具体例と演習](10-data.html)。

<h2 id="term-module">モジュール</h2>

Pythonの機能をまとめた単位。importで使う。 [具体例と演習](10-data.html)。

<h2 id="term-class">クラス</h2>

関連した状態と操作をまとめる仕組み。 [具体例と演習](11-debug.html)。

<h2 id="term-finite">有限精度・浮動小数点</h2>

保存できる桁数は有限。浮動小数点は広い範囲の数を近似して保存する方式。 [具体例と演習](17c-numerics.html)。

<h2 id="term-library">ライブラリ</h2>

他の人が用意した機能の集まり。版と実行環境を記録する。 [具体例と演習](12-environment.html)。

<h2 id="term-venv">仮想環境</h2>

プロジェクトごとに追加ライブラリを分ける仕組み。 [具体例と演習](12-environment.html)。

<h2 id="term-complexity">計算量</h2>

入力が大きくなったときの操作量の増え方。秒数そのものとは違う。 [具体例と演習](13-algorithms.html)。

<h2 id="term-sql">SQL</h2>

表から必要な行・列を取り出し、集計するための言語。 [具体例と演習](13-algorithms.html)。

<h2 id="term-vector">ベクトル</h2>

順序を決めた数の並び。成分の意味と順序を記録する。 [具体例と演習](14-vectors.html)。

<h2 id="term-scalar">スカラー</h2>

この文脈では、並びではない一つの数。 [具体例と演習](14-vectors.html)。

<h2 id="term-dot">内積</h2>

対応する成分を掛けて足す。結果は一つの数。 [具体例と演習](14-vectors.html)。

<h2 id="term-norm">ノルム</h2>

値の大きさの測り方。L2は平方和の平方根、L1は絶対値の和。 [具体例と演習](14-vectors.html)。

<h2 id="term-orthogonal">直角・直交</h2>

直角は90度。内積が0のベクトル同士を直交と呼ぶ。 [具体例と演習](14-vectors.html)。

<h2 id="term-pythagoras">斜辺・ピタゴラスの定理</h2>

直角三角形の直角の向かいの辺が斜辺。その長さの二乗は他の二辺の二乗和。 [具体例と演習](14-vectors.html)。

<h2 id="term-column-vector">列ベクトル・行ベクトル</h2>

数を縦一列／横一行に並べたベクトル。n成分なら形(n,1)／(1,n)。 [具体例と演習](15-matrices.html)。

<h2 id="term-matrix">行列</h2>

数を行と列に並べた表。積では内側の長さを合わせる。 [具体例と演習](15b-product.html)。

<h2 id="term-transpose">転置</h2>

行と列を交換する。形(m,n)を(n,m)へ変える。 [具体例と演習](15c-transpose.html)。

<h2 id="term-basis">線形結合・基底</h2>

ベクトルへ数を掛けて足すのが線形結合。全体を作れ、余分な方向がない基本方向の組が基底。 [具体例と演習](15d-basis.html)。

<h2 id="term-rank">ランク</h2>

ほかの列の線形結合では作れない独立な列の最大数。行について数えても一致する。 [具体例と演習](15d-basis.html)。

<h2 id="term-tensor">テンソル・shape</h2>

この教材では多次元配列。shapeは軸ごとの長さで、軸の意味も別に記録する。 [具体例と演習](16-tensors.html)。

<h2 id="term-broadcast">broadcast</h2>

末尾の軸から長さを比較し、等しいか一方が1なら形をそろえて演算する。 [具体例と演習](16-tensors.html)。

<h2 id="term-diagonal">対角行列</h2>

左上から右下以外が全て0の行列。 [具体例と演習](16b-diagonal.html)。

<h2 id="term-eigen">固有値・固有ベクトル</h2>

0でないvについてAv=λvとなるとき、vと倍率λのこと。 [具体例と演習](16c-eigen.html)。

<h2 id="term-svd">特異値分解</h2>

行列を方向の変換・非負の倍率・方向の変換へ分けるA=UΣVᵀ。 [具体例と演習](16d-svd.html)。

<h2 id="term-derivative">微分・極限</h2>

幅を狭めた変化率を調べる。極限は近づく先を考え、0を直接割らない。 [具体例と演習](17-calculus.html)。

<h2 id="term-partial">偏微分</h2>

ほかの入力を固定して、一つの入力だけで微分する。 [具体例と演習](18-chain.html)。

<h2 id="term-gradient">勾配</h2>

各入力への偏微分を並べたベクトル。 [具体例と演習](18-chain.html)。

<h2 id="term-chain-rule">連鎖律</h2>

関数をつないだ変化率は、各経路の変化率を掛け、分岐の寄与を足す。 [具体例と演習](18b-chain.html)。

<h2 id="term-unit-vector">単位方向</h2>

長さ1の方向ベクトル。0でない方向をその長さで割って作る。 [具体例と演習](18c-descent.html)。

<h2 id="term-jacobian">ヤコビ行列</h2>

出力ごと・入力ごとの偏微分の表。行は出力、列は入力。 [具体例と演習](18d-jacobian.html)。

<h2 id="term-jvp-vjp">JVP・VJP</h2>

JVPは入力方向を出力へ送るJv。VJPは出力感度を入力へ戻すgᵀJ、列表記ではJᵀg。 [具体例と演習](18e-products.html)。

<h2 id="term-linear-layer">線形層・bias</h2>

行列積とずれの加算Y=XW+bを行う部品。b付きは数学ではアフィン変換。 [具体例と演習](18f-linear.html)。

<h2 id="term-upstream">上流の勾配</h2>

後続の損失から届く、その出力に対する損失の変化率。 [具体例と演習](18f-linear.html)。

<h2 id="term-learning-rate">学習率</h2>

勾配による更新の歩幅を調整する値。 [具体例と演習](18c-descent.html)。

<h2 id="term-integral">積分</h2>

小さい量を足し合わせる極限。符号付きの蓄積を表す。 [具体例と演習](19-integration.html)。

<h2 id="term-density">密度</h2>

範囲へ積分すると確率になる高さ。一点の確率ではない。 [具体例と演習](19-integration.html)。

<h2 id="term-bayes">Bayesの定理</h2>

条件の向きを数え直すP(A|B)=P(B|A)P(A)/P(B)。分母は正。 [具体例と演習](20-probability.html)。

<h2 id="term-expectation">期待値</h2>

値をその確率で重み付けして足した平均。 [具体例と演習](21-distributions.html)。

<h2 id="term-variance">分散・標準偏差</h2>

平均からの差の二乗の平均と、その平方根。 [具体例と演習](21-distributions.html)。

<h2 id="term-bootstrap">bootstrap</h2>

観測した標本を復元抽出し直し、統計量の揺れを調べる。 [具体例と演習](22-statistics.html)。

<h2 id="term-entropy">エントロピー</h2>

分布の自己情報量の期待値。対数の底と単位を明示する。 [具体例と演習](23-information.html)。

<h2 id="term-ml">機械学習</h2>

データから予測などの振る舞いを調整する方法。 [具体例と演習](24-learning.html)。

<h2 id="term-loss">損失</h2>

小さくしたい目的の値。何を測る関数か、平均か和かを記録する。 [具体例と演習](25-regression.html)。

<h2 id="term-overfit">過学習</h2>

訓練例への適合が、未知の例でのよい予測へつながらない状態。 [具体例と演習](24-learning.html)。

<h2 id="term-autograd">自動微分</h2>

実行した基本演算の微分を連鎖律で組み合わせる。差分近似とは異なる。 [具体例と演習](26-pytorch.html)。

<h2 id="term-optimizer">optimizer</h2>

重みをどう更新するかを管理する道具。 [具体例と演習](26-pytorch.html)。

<h2 id="term-activation">活性化関数</h2>

層の値へ非線形な変換を加える部品。 [具体例と演習](27-networks.html)。

<h2 id="term-softmax">softmax</h2>

点数の指数を、その合計で割って非負・和1の重みにする。 [具体例と演習](28-numerics.html)。

<h2 id="term-token">トークン</h2>

文章を処理用に区切る一単位。文字や単語と同じ数とは限らない。 [具体例と演習](29-tokenization.html)。

<h2 id="term-embedding">埋め込み</h2>

IDなどを数の並びへ写す表現。成分に人間の意味が固定されるとは限らない。 [具体例と演習](29-tokenization.html)。

<h2 id="term-attention">Attention・Q/K/V</h2>

参照先へ重みを付け内容を混ぜる計算。Queryは照合元、Keyは照合先、Valueは混ぜる内容。 [具体例と演習](31-attention.html)。

<h2 id="term-checkpoint">チェックポイント</h2>

学習などを再開するための状態を保存したファイル。 [具体例と演習](33-training.html)。

<h2 id="term-pretrain">事前学習</h2>

後の用途への調整前に、大きなデータなどで基礎的なモデルを学ぶ段階。 [具体例と演習](35-data-scaling.html)。

<h2 id="term-lora">LoRA</h2>

固定した重みへ低ランクの学習可能な更新を加える方法。 [具体例と演習](36-adaptation.html)。

<h2 id="term-rag">RAG</h2>

検索で取り出した情報を生成時の入力へ渡す構成。 [具体例と演習](37-rag.html)。

<h2 id="term-reward">報酬</h2>

行動結果に対して大きくしたい評価の値。 [具体例と演習](38-reinforcement.html)。

<h2 id="term-rlhf">RLHF</h2>

人の選好などに基づく報酬を使ってモデルを調整する枠組み。 [具体例と演習](39-alignment.html)。

<h2 id="term-quantization">量子化</h2>

数値を有限の目盛りへ写す。誤差と保存量と速度は別に確認する。 [具体例と演習](44-compression.html)。

<h2 id="term-moe">MoE</h2>

入力に応じて一部の専門部品を選び、出力を組み合わせる構成。 [具体例と演習](45-moe.html)。

<h2 id="term-rope">RoPE</h2>

位置に応じてベクトルの成分の組を回転し、相対位置を内積へ反映する方法。 [具体例と演習](46-context.html)。

<h2 id="term-modality">モダリティ</h2>

文章・画像・音声など、情報を表す種類。 [具体例と演習](48-multimodal.html)。

<h2 id="term-agent">エージェント</h2>

状態や目的に応じ、道具の利用など次の行動を選ぶ構成。 [具体例と演習](49-agents.html)。

<h2 id="term-rubric">rubric</h2>

何を何点とするかを明記した採点基準表。 [具体例と演習](50-evaluation.html)。

<h2 id="term-confounding">交絡</h2>

条件と別の要因も変わり、原因の効果を切り分けられないこと。 [具体例と演習](53-research-design.html)。

<h2 id="term-hook">hook</h2>

層などの処理の時点で、登録した関数を呼ぶ仕組み。 [具体例と演習](51-interpretability.html)。

<h2 id="term-ablation">ablation</h2>

構成要素や条件を外した比較で、その影響を確かめる。 [具体例と演習](53-research-design.html)。

<h2 id="term-arxiv">arXiv</h2>

論文原稿の公開場所。掲載だけでは査読済みとは限らない。 [具体例と演習](54-paper-reading.html)。


<h2 id="term-binomial">二項係数・二項分布</h2>

二項係数はn個から順序を区別せずk個を選ぶ組の数n!/[k!(n−k)!]。二項分布は、成功確率pが同じ独立なn試行の成功数の分布です。[組を数える](20-probability.html)・[分布を読む](21-distributions.html)。
