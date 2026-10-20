# 18-2 一つの経路で連鎖律を確かめる

読む・手計算の目安：15〜25分。演習は10〜20分、コード実行は別の回へ分けられます。時間は編集上の目安です。

## 値は前へ、変化率は後ろへ

<figure class="learning-figure"><svg viewBox="0 0 480 230" role="img" aria-labelledby="chain-title chain-desc"><title id="chain-title">入力から損失へ進み、変化率を戻す</title><desc id="chain-desc">x=1から2倍して1を足しu=3、二乗してL=9。戻るときはdL/du=6とdu/dx=2を掛けdL/dx=12。</desc><g fill="#e7eef9" stroke="#245da8"><rect x="10" y="65" width="100" height="52"/><rect x="188" y="65" width="100" height="52"/><rect x="366" y="65" width="100" height="52"/></g><g fill="#17243b" font-size="22" text-anchor="middle"><text x="60" y="97">x ＝ 1</text><text x="238" y="97">u ＝ 3</text><text x="416" y="97">L ＝ 9</text><text x="149" y="45">2倍＋1</text><text x="328" y="45">二乗</text><text x="150" y="155">← ×2</text><text x="328" y="155">← ×6</text><text x="240" y="204">戻る変化率：6 × 2 ＝ 12</text></g><path d="M115 88 H178 L166 80 M293 88 H356 L344 80" fill="none" stroke="#245da8" stroke-width="3"/></svg><figcaption>上側は値を計算する順、下側は損失の変化率を戻す順です。戻るときに値の9を掛けるわけではありません。</figcaption></figure>

u=2x+1、L=u²を考えます。xからuへの変化率は2、uからLへの変化率は2uです。両者を掛けると`dL/dx=(dL/du)(du/dx)=2u×2`。x=1ならu=3なので12です。これが[連鎖律](reference.html#term-chain-rule)です。

ニューラルネットワークは多数の関数をつないだものです。各部品の局所的な[微分](reference.html#term-derivative)を掛け、分岐している経路の寄与は足します。大きな式を丸ごと展開せず、計算のつながりをグラフとして保存し、出力から入力へ逆にたどると効率的です。これを逆伝播と呼びます。

:::exercise 2・連鎖律
L=(3x−1)²のx=2での微分を求めてください。
:::answer
u=3x−1=5、dL/du=2u=10、du/dx=3。したがって30です。
:::

:::exercise 3・分岐の寄与
L=x×xの微分で、片方のxだけの影響をたどると何を見落としますか。
:::answer
xから積への経路が二つあります。それぞれxの寄与があるので足して2xです。一方しか数えないとxになってしまいます。
:::

## 今日の区切り

このページの数値例を、数字を変えて一つ説明できたら区切れます。解答を隠して確認してください。止まったら[中断・補習の手引き](learning-help.html)へ戻れます。


[前の学習ページ](18-chain.html) · [次の学習ページ](18c-descent.html) · [章の地図](18-chain.html)
