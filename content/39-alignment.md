{"title": "39 PPO・DPO・GRPOを混同しない", "part": "LLMを育てる・調整する", "goal": "各手法のデータ・目的関数・基準モデルを区別する", "prereq": "23・36・38", "subpages": ["39u-002", "39u-003", "39u-004", "39u-005", "39u-006", "39u-007", "39u-008", "39u-009", "39u-010", "39u-011", "39u-012", "39u-013"], "next": "39u-002", "previous": "38u-010", "microtitle": "39-1 RLHF・報酬モデル", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/13ページ。今日の目標：RLHF・報酬モデルの小例を一つ追う。

今日の言葉：[RLHF](beginner-glossary.html#concept-39-alignment)・[報酬モデル](beginner-glossary.html#concept-39-alignment)。

## なぜ使うか

各手法のデータ・目的関数・基準モデルを区別するための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

人の評価などを使う強化学習の枠組みがRLHF。回答へ得点を付ける学習済みの仕組みが報酬モデルです。二回答の人の好みで得点を学べても、未知の回答で常に正しい採点とは限りません。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
人の評価などを使う強化学習の枠組みがRLHF。回答へ得点を付ける学習済みの仕組みが報酬モデルです。二回答の人の好みで得点を学べても、未知の回答で常に正しい採点とは限りません。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](38-reinforcement.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](39-reader.html)

<section class="resume-note" data-lesson="39-alignment"><h2>次回の再開メモ</h2><label for="resume-39-alignment">できたこと・止まった一文・次にすること</label><textarea id="resume-39-alignment" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="38-reinforcement.html">前の小ページ</a><a href="39u-002.html">次の小ページ</a></nav>
