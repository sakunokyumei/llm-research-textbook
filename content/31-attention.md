{"title": "31 Attentionを手で計算する", "part": "言語モデルを作る", "goal": "Q・K・V、softmax、maskの全手順を実装する", "prereq": "14〜16・28〜30", "subpages": ["31u-002", "31u-003", "31u-004", "31u-005", "31u-006", "31u-007", "31u-008", "31u-009", "31u-010", "31u-011"], "next": "31u-002", "previous": "30u-008", "microtitle": "31-1 Attention・Query・Key", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/11ページ。今日の目標：Attention・Query・Keyの小例を一つ追う。

今日の言葉：[Attention](beginner-glossary.html#concept-31-attention)・[Query](beginner-glossary.html#concept-31-attention)・[Key](beginner-glossary.html#concept-31-attention)。

## なぜ使うか

Q・K・V、softmax、maskの全手順を実装するための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

参照先へ重みを付けて情報を混ぜる計算がAttention。探す側の数がQuery、比べる相手の数がKeyです。Query(1,0)とKey(1,0),(0,1)の内積は1,0。この点数を確率へ直す段階は別に行います。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
参照先へ重みを付けて情報を混ぜる計算がAttention。探す側の数がQuery、比べる相手の数がKeyです。Query(1,0)とKey(1,0),(0,1)の内積は1,0。この点数を確率へ直す段階は別に行います。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](30-language-model.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](31-reader.html)

<section class="resume-note" data-lesson="31-attention"><h2>次回の再開メモ</h2><label for="resume-31-attention">できたこと・止まった一文・次にすること</label><textarea id="resume-31-attention" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="30-language-model.html">前の小ページ</a><a href="31u-002.html">次の小ページ</a></nav>
