{"title": "43 推論サービスと投機的生成", "part": "効率と現代のアーキテクチャ", "goal": "待ち時間・処理量・cache・生成分布を別々に評価する", "prereq": "34・41・42", "subpages": ["43u-002", "43u-003", "43u-004", "43u-005", "43u-006", "43u-007", "43u-008", "43u-009"], "next": "43u-002", "previous": "42u-014", "microtitle": "43-1 prefill・TTFT・ITL", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/9ページ。今日の目標：prefill・TTFT・ITLの小例を一つ追う。

今日の言葉：[prefill](beginner-glossary.html#concept-43-serving)・[TTFT](beginner-glossary.html#concept-43-serving)・[ITL](beginner-glossary.html#concept-43-serving)。

## なぜ使うか

待ち時間・処理量・cache・生成分布を別々に評価するための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

入力の文章を処理する段階がprefill、最初の単位が出るまでがTTFT、その後の単位間の時間がITLです。最初まで1秒、その後一つ0.1秒なら別々に報告します。平均だけで待ち時間の分布は分かりません。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
入力の文章を処理する段階がprefill、最初の単位が出るまでがTTFT、その後の単位間の時間がITLです。最初まで1秒、その後一つ0.1秒なら別々に報告します。平均だけで待ち時間の分布は分かりません。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](42-distributed.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](43-reader.html)

<section class="resume-note" data-lesson="43-serving"><h2>次回の再開メモ</h2><label for="resume-43-serving">できたこと・止まった一文・次にすること</label><textarea id="resume-43-serving" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="42-distributed.html">前の小ページ</a><a href="43u-002.html">次の小ページ</a></nav>
