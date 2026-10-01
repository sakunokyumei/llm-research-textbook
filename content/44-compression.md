{"title": "44 量子化・蒸留・枝刈り", "part": "効率と現代のアーキテクチャ", "goal": "保存量の削減と実速度・品質の変化を区別する", "prereq": "16・23・28・36", "subpages": ["44u-002", "44u-003", "44u-004", "44u-005", "44u-006", "44u-007", "44u-008", "44u-009", "44u-010", "44u-011", "44u-012", "44u-013"], "next": "44u-002", "previous": "43u-009", "microtitle": "44-1 対称量子化・scale・zero point", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/13ページ。今日の目標：対称量子化・scale・zero pointの小例を一つ追う。

今日の言葉：[対称量子化](beginner-glossary.html#concept-44-compression)・[scale](beginner-glossary.html#concept-44-compression)・[zero point](beginner-glossary.html#concept-44-compression)。

## なぜ使うか

保存量の削減と実速度・品質の変化を区別するための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

整数0へ実数0を合わせる対称量子化では、目盛り幅scaleで割って丸めます。0.26を幅0.1で3へ、戻すと0.3。zero pointは実数0に対応する整数の基準で、非対称方式では0以外になり得ます。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
整数0へ実数0を合わせる対称量子化では、目盛り幅scaleで割って丸めます。0.26を幅0.1で3へ、戻すと0.3。zero pointは実数0に対応する整数の基準で、非対称方式では0以外になり得ます。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](43-serving.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](44-reader.html)

<section class="resume-note" data-lesson="44-compression"><h2>次回の再開メモ</h2><label for="resume-44-compression">できたこと・止まった一文・次にすること</label><textarea id="resume-44-compression" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="43-serving.html">前の小ページ</a><a href="44u-002.html">次の小ページ</a></nav>
