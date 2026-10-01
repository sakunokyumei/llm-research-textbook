{"title": "45 MoEと、使う計算を選ぶ設計", "part": "効率と現代のアーキテクチャ", "goal": "総パラメータと活性化パラメータ、routingの費用を区別する", "prereq": "27・32・42", "subpages": ["45u-002", "45u-003", "45u-004", "45u-005", "45u-006", "45u-007", "45u-008", "45u-009"], "next": "45u-002", "previous": "44u-013", "microtitle": "45-1 MoE・expert・router", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "選んだexpertの出力を混ぜる"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/9ページ。

今回の用語をまとめて復習：[MoE・expert・router](beginner-glossary.html#concept-45-moe)。

## なぜ使うか

総パラメータと活性化パラメータ、routingの費用を区別するための一歩です。このページでは、選んだexpertの出力を混ぜることを練習します。

## 意味と小さな例

複数の部品expertの一部を選ぶ模型がMoE、選ぶ仕組みがrouterです。四expertのうち二つを使えば、全四つを毎回計算する方式とは違います。選んだ二つの出力へ重みも付けます。

:::check 選んだexpertの出力を混ぜる
二expertの出力2と10へ、routerが0.75と0.25を付けました。混ぜた出力はいくつですか。
:::answer
0.75×2+0.25×10=4です。二つを単純平均した6ではなく、routerの重みを使います。
:::



## 今日の区切りと戻る場所

確認問題で「選んだexpertの出力を混ぜる」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](44u-013.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](45-reader.html)

<section class="resume-note" data-lesson="45-moe"><h2>次回の再開メモ</h2><label for="resume-45-moe">できたこと・止まった一文・次にすること</label><textarea id="resume-45-moe" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="44u-013.html">前の小ページ</a><a href="45u-002.html">次の小ページ</a></nav>
