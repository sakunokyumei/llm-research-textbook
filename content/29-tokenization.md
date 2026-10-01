{"title": "29 文章をトークンへ変える", "part": "言語モデルを作る", "goal": "文字・byte・BPEを区別し、データから語彙を学ぶ", "prereq": "10・13・23", "subpages": ["29u-002", "29u-003", "29u-004", "29u-005", "29u-006", "29u-007", "29u-008", "29u-009", "29u-010", "29u-011", "29u-012"], "next": "29u-002", "previous": "28u-013", "microtitle": "29-1 BPE・subword", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/12ページ。今日の目標：BPE・subwordの小例を一つ追う。

今日の言葉：[BPE](beginner-glossary.html#concept-29-tokenization)・[subword](beginner-glossary.html#concept-29-tokenization)。

## なぜ使うか

文字・byte・BPEを区別し、データから語彙を学ぶための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

文章を分ける単位を作る方法の一つがBPE。小さい文字の組で頻出する隣接組をまとめます。単語全体より小さい単位がsubwordです。a b a bなら(a,b)をまとめてab abとできます。実装で頻度と同点の規約も記録します。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
文章を分ける単位を作る方法の一つがBPE。小さい文字の組で頻出する隣接組をまとめます。単語全体より小さい単位がsubwordです。a b a bなら(a,b)をまとめてab abとできます。実装で頻度と同点の規約も記録します。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](28-numerics.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](29-reader.html)

<section class="resume-note" data-lesson="29-tokenization"><h2>次回の再開メモ</h2><label for="resume-29-tokenization">できたこと・止まった一文・次にすること</label><textarea id="resume-29-tokenization" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="28-numerics.html">前の小ページ</a><a href="29u-002.html">次の小ページ</a></nav>
