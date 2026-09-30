{"title": "17 微分は、今ここでの変わり方", "part": "モデルを支える数学", "goal": "時間幅を小さくした変化率の数値を比較する", "prereq": "06・07", "time": "このページ：読む・手計算 15〜25分／演習 10〜20分。章全体は3回以上に分け、実装は別枠です", "next": "17b-rules", "previous": "16f-lowrank", "subpages": ["17b-rules", "17c-numerics"]}

## この章は、一回一ページで進める

全3ページです。後のページ名は行き先の案内で、今ここで暗記する用語ではありません。各回の読解・手計算・演習を分け、実装は別の回にできます。時間は初学者向けの編集上の目安で、受講者の実測値ではありません。

- [1．二点の平均から瞬間の変化へ進む](17-calculus.html)
- [2．微分の規則を一つずつ確かめる](17b-rules.html)
- [3．微分できない点と数値誤差を分ける](17c-numerics.html)

## 時間幅を小さくする

<figure class="learning-figure"><svg viewBox="0 0 360 210" role="img" aria-labelledby="slope-title"><title id="slope-title">時間幅を狭めて、傾きを調べる</title><path d="M35 175 H325 M35 175 V15" fill="none" stroke="currentColor"/><path d="M35 175 Q175 170 290 35" fill="none" stroke="#245da8" stroke-width="3"/><path d="M174 135 L290 35 M174 135 L210 111" fill="none" stroke="#a56630" stroke-width="2"/><g fill="#245da8"><circle cx="174" cy="135" r="5"/><circle cx="210" cy="111" r="5"/><circle cx="290" cy="35" r="5"/></g><g font-size="14" fill="currentColor"><text x="170" y="195">2</text><text x="274" y="195">3</text><text x="310" y="195">時間</text><text x="42" y="23">位置</text><text x="220" y="130">近い二点で比べる</text></g></svg><figcaption>図は時間幅を狭める概念図です。正確な平均変化率5、4.1、4.01は本文の数値から計算します。</figcaption></figure>

車が2時間で100km進めば平均速度は50km/hです。しかし途中で止まったかもしれません。今この瞬間の速度を知るには、見る時間幅を短くしていきます。この発想が[微分](reference.html#term-derivative)です。

位置をf(t)=t²とする模型で、t=2からt=3の平均変化率は(9−4)/(3−2)=5。t=2から2.1では(4.41−4)/0.1=4.1。幅hを使って書くと、`((2+h)²−2²)/h=4+h`です。hを0に近づけると4へ近づきます。この値をt=2の微分[係数](reference.html#term-coefficient)と呼びます。

h=0を直接[代入](reference.html#term-substitution)すると0/0になってしまいます。「0を代入する」のではなく「0へ近づくとどの値へ近づくか」を考えるのが極限です。記号limで表します。関数全体について微分係数を返す新しい関数を導関数と呼び、f'(t)と書きます。

:::exercise 1・平均変化率
f(x)=x²のx=1からx=3までの平均変化率を求めてください。
:::answer
(9−1)/(3−1)=4です。x=1の瞬間の傾き2とは異なります。
:::

:::exercise 2・差分から導く
f(x)=3x+2について、(f(x+h)−f(x))/hを整理してください。
:::answer
(3x+3h+2−3x−2)/h=3。hが0でない限り一定なので、微分係数も3です。
:::

## 今日の区切り

このページの数値例を、数字を変えて一つ説明できたら区切れます。解答を隠して確認してください。止まったら[中断・補習の手引き](learning-help.html)へ戻れます。
