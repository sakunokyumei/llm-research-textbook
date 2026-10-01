{"title": "40 推論時の計算と合成データ", "part": "LLMを育てる・調整する", "goal": "追加計算の効果を費用と独立評価で測る", "prereq": "22・34・39", "subpages": ["40u-002", "40u-003", "40u-004", "40u-005", "40u-006", "40u-007", "40u-008"], "next": "40u-002", "previous": "39u-013", "microtitle": "40-1 best-of-N・pass@k", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/8ページ。今日の目標：best-of-N・pass@kの小例を一つ追う。

今日の言葉：[best-of-N](beginner-glossary.html#concept-40-reasoning)・[pass@k](beginner-glossary.html#concept-40-reasoning)。

## なぜ使うか

追加計算の効果を費用と独立評価で測るための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

N候補を作って評価で一つ選ぶのがbest-of-N。k回の中で一つ以上正解する割合がpass@kです。四問で各二回試し、三問に少なくとも一つ正解なら3/4。回答一個の正解率とは別に報告します。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
N候補を作って評価で一つ選ぶのがbest-of-N。k回の中で一つ以上正解する割合がpass@kです。四問で各二回試し、三問に少なくとも一つ正解なら3/4。回答一個の正解率とは別に報告します。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](39-alignment.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](40-reader.html)

<section class="resume-note" data-lesson="40-reasoning"><h2>次回の再開メモ</h2><label for="resume-40-reasoning">できたこと・止まった一文・次にすること</label><textarea id="resume-40-reasoning" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="39-alignment.html">前の小ページ</a><a href="40u-002.html">次の小ページ</a></nav>
