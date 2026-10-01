{"title": "26 PyTorchと自動微分", "part": "機械学習と深層学習", "goal": "手計算した勾配をautogradで検証する", "prereq": "11・16・18・25", "subpages": ["26u-002", "26u-003", "26u-004", "26u-005", "26u-006", "26u-007", "26u-008", "26u-009", "26u-010", "26u-011", "26u-012", "26u-013"], "next": "26u-002", "previous": "25u-011", "microtitle": "26-1 torch.tensor・dtype", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/13ページ。今日の目標：torch.tensor・dtypeの小例を一つ追う。

今日の言葉：[torch.tensor](beginner-glossary.html#concept-26-pytorch)・[dtype](beginner-glossary.html#concept-26-pytorch)。

## なぜ使うか

手計算した勾配をautogradで検証するための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

Pythonの数や並びをPyTorchの数の入れ物へ変えるのがtorch.tensor。dtypeは保存する数の型です。2.0を微分するなら浮動小数点、単語番号2は整数で保存します。float64は64bitの小数の指定です。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
Pythonの数や並びをPyTorchの数の入れ物へ変えるのがtorch.tensor。dtypeは保存する数の型です。2.0を微分するなら浮動小数点、単語番号2は整数で保存します。float64は64bitの小数の指定です。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](25-regression.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](26-reader.html)

<section class="resume-note" data-lesson="26-pytorch"><h2>次回の再開メモ</h2><label for="resume-26-pytorch">できたこと・止まった一文・次にすること</label><textarea id="resume-26-pytorch" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="25-regression.html">前の小ページ</a><a href="26u-002.html">次の小ページ</a></nav>
