{"title": "44 量子化・蒸留・枝刈り", "part": "効率と現代のアーキテクチャ", "goal": "保存量の削減と実速度・品質の変化を区別する", "prereq": "16・23・28・36", "subpages": ["44u-002", "44u-003", "44u-004", "44u-005", "44u-006", "44u-007", "44u-008", "44u-009", "44u-010", "44u-011", "44u-012", "44u-013"], "next": "44u-002", "previous": "43u-009", "microtitle": "44-1 対称量子化・scale・zero point", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "量子化して戻した誤差を計算する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/13ページ。

今回の用語をまとめて復習：[対称量子化・scale・zero point](beginner-glossary.html#concept-44-compression)。

## なぜ使うか

保存量の削減と実速度・品質の変化を区別するための一歩です。このページでは、量子化して戻した誤差を計算することを練習します。

## 意味と小さな例

整数0へ実数0を合わせる対称量子化では、目盛り幅scaleで割って丸めます。0.26を幅0.1で3へ、戻すと0.3。zero pointは実数0に対応する整数の基準で、非対称方式では0以外になり得ます。

:::check 量子化して戻した誤差を計算する
scale=0.2、zero point=0で0.53を最も近い整数へ量子化し、元の尺度へ戻してください。
:::answer
0.53/0.2=2.65を3へ丸め、3×0.2=0.6。絶対誤差は0.07です。保存範囲に収まることも確認します。
:::



## 今日の区切りと戻る場所

確認問題で「量子化して戻した誤差を計算する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](43u-009.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](44-reader.html)

<section class="resume-note" data-lesson="44-compression"><h2>次回の再開メモ</h2><label for="resume-44-compression">できたこと・止まった一文・次にすること</label><textarea id="resume-44-compression" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="43u-009.html">前の小ページ</a><a href="44u-002.html">次の小ページ</a></nav>
