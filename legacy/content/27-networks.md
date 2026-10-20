{"title": "27 ニューラルネットワークを組み立てる", "part": "機械学習と深層学習", "goal": "線形層・活性化・正規化・残差の役割を説明する", "prereq": "15・18・26", "subpages": ["27u-002", "27u-003", "27u-004", "27u-005", "27u-006", "27u-007", "27u-008", "27u-009", "27u-010", "27u-011", "27u-012", "27u-013"], "next": "27u-002", "previous": "26u-013", "microtitle": "27-1 活性化関数・ReLU・MLP", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "ReLUを成分ごとに適用する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/13ページ。

今回の用語をまとめて復習：[活性化関数・ReLU・MLP](beginner-glossary.html#concept-27-networks)。

## なぜ使うか

線形層・活性化・正規化・残差の役割を説明するための一歩です。このページでは、ReLUを成分ごとに適用することを練習します。

## 意味と小さな例

層の間に非線形な変換を入れるのが活性化関数。ReLUは負を0、正をそのままにします。複数の層をつなぐMLPで、−2は0、3は3。直線を重ねるだけの模型から変化を作れます。

:::check ReLUを成分ごとに適用する
ReLUへ[−3,0,2]を入れた結果を書いてください。
:::answer
[0,0,2]です。負の値を0にし、正の値は残します。この折れ曲がりによって線形変換だけとは異なる表現を作れます。
:::



## 今日の区切りと戻る場所

確認問題で「ReLUを成分ごとに適用する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](26u-013.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](27-reader.html)

<section class="resume-note" data-lesson="27-networks"><h2>次回の再開メモ</h2><label for="resume-27-networks">できたこと・止まった一文・次にすること</label><textarea id="resume-27-networks" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="26u-013.html">前の小ページ</a><a href="27u-002.html">次の小ページ</a></nav>
