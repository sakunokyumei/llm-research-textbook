{"title": "40 推論時の計算と合成データ", "part": "LLMを育てる・調整する", "goal": "追加計算の効果を費用と独立評価で測る", "prereq": "22・34・39", "subpages": ["40u-002", "40u-003", "40u-004", "40u-005", "40u-006", "40u-007", "40u-008"], "next": "40u-002", "previous": "39u-013", "microtitle": "40-1 best-of-N・pass@k", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "一回答の正解率と複数試行の成功を分ける"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/8ページ。

今回の用語をまとめて復習：[best-of-N・pass@k](beginner-glossary.html#concept-40-reasoning)。

## なぜ使うか

追加計算の効果を費用と独立評価で測るための一歩です。このページでは、一回答の正解率と複数試行の成功を分けることを練習します。

## 意味と小さな例

N候補を作って評価で一つ選ぶのがbest-of-N。k回の中で一つ以上正解する割合がpass@kです。四問で各二回試し、三問に少なくとも一つ正解なら3/4。回答一個の正解率とは別に報告します。

:::check 一回答の正解率と複数試行の成功を分ける
四問を各二回試し、正誤が[正,誤],[誤,正],[誤,誤],[正,正]でした。少なくとも一回正解した問の割合はいくつですか。
:::answer
3/4です。全8回答中の正解4/8とは違います。試行回数と問単位の評価を明記します。
:::



## 今日の区切りと戻る場所

確認問題で「一回答の正解率と複数試行の成功を分ける」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](39u-013.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](40-reader.html)

<section class="resume-note" data-lesson="40-reasoning"><h2>次回の再開メモ</h2><label for="resume-40-reasoning">できたこと・止まった一文・次にすること</label><textarea id="resume-40-reasoning" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="39u-013.html">前の小ページ</a><a href="40u-002.html">次の小ページ</a></nav>
