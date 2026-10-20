{"title": "26 PyTorchと自動微分", "part": "機械学習と深層学習", "goal": "手計算した勾配をautogradで検証する", "prereq": "11・16・18・25", "subpages": ["26u-002", "26u-003", "26u-004", "26u-005", "26u-006", "26u-007", "26u-008", "26u-009", "26u-010", "26u-011", "26u-012", "26u-013"], "next": "26u-002", "previous": "25u-011", "microtitle": "26-1 torch.tensor・dtype", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "用途に合う数の型を選ぶ"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/13ページ。

今回の用語をまとめて復習：[torch.tensor・dtype](beginner-glossary.html#concept-26-pytorch)。

## なぜ使うか

手計算した勾配をautogradで検証するための一歩です。このページでは、用途に合う数の型を選ぶことを練習します。

## 意味と小さな例

Pythonの数や並びをPyTorchの数の入れ物へ変えるのがtorch.tensor。dtypeは保存する数の型です。2.0を微分するなら浮動小数点、単語番号2は整数で保存します。float64は64bitの小数の指定です。

:::check 用途に合う数の型を選ぶ
微分して更新する重み2.0と、単語ID2に、同じ整数型を使ってよいですか。
:::answer
重みは浮動小数点型、IDは整数型にします。通常の整数テンソルで重みの勾配を追跡する設計にはしません。
:::



## 今日の区切りと戻る場所

確認問題で「用途に合う数の型を選ぶ」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](25u-011.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](26-reader.html)

<section class="resume-note" data-lesson="26-pytorch"><h2>次回の再開メモ</h2><label for="resume-26-pytorch">できたこと・止まった一文・次にすること</label><textarea id="resume-26-pytorch" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="25u-011.html">前の小ページ</a><a href="26u-002.html">次の小ページ</a></nav>
