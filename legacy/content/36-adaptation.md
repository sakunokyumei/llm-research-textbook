{"title": "36 SFT・LoRA・QLoRA", "part": "LLMを育てる・調整する", "goal": "学習対象と凍結する重みを区別して追加学習する", "prereq": "16・23・33・35", "subpages": ["36u-002", "36u-003", "36u-004", "36u-005", "36u-006", "36u-007", "36u-008", "36u-009"], "next": "36u-002", "previous": "35u-008", "microtitle": "36-1 SFT・loss mask・chat template", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "損失を数える発話の位置を選ぶ"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/9ページ。

今回の用語をまとめて復習：[SFT・loss mask・chat template](beginner-glossary.html#concept-36-adaptation)。

## なぜ使うか

学習対象と凍結する重みを区別して追加学習するための一歩です。このページでは、損失を数える発話の位置を選ぶことを練習します。

## 意味と小さな例

正解の応答で調整するのがSFT。損失を取る場所の表がloss mask、会話の役割や区切りをそろえる形式がchat templateです。質問二単位、回答三単位なら回答三つへ損失を取る設計をまず紙で決めます。

:::check 損失を数える発話の位置を選ぶ
質問と回答をつないだSFTで、回答だけを教師にしたい場合、質問の位置のloss maskはどうしますか。
:::answer
質問側を損失の集計から除き、回答側を数えます。入力として質問を読ませることと、質問の生成へ損失を付けることは別です。
:::



## 今日の区切りと戻る場所

確認問題で「損失を数える発話の位置を選ぶ」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](35u-008.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](36-reader.html)

<section class="resume-note" data-lesson="36-adaptation"><h2>次回の再開メモ</h2><label for="resume-36-adaptation">できたこと・止まった一文・次にすること</label><textarea id="resume-36-adaptation" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="35u-008.html">前の小ページ</a><a href="36u-002.html">次の小ページ</a></nav>
