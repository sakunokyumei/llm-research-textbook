{"title": "34 生成・温度・KV cache", "part": "言語モデルを作る", "goal": "学習済みモデルから生成し、速度と分布を区別する", "prereq": "28・32・33", "subpages": ["34u-002", "34u-003", "34u-004", "34u-005", "34u-006", "34u-007", "34u-008", "34u-009", "34u-010"], "next": "34u-002", "previous": "33u-019", "microtitle": "34-1 greedy decoding・sampling・温度", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/10ページ。今日の目標：greedy decoding・sampling・温度の小例を一つ追う。

今日の言葉：[greedy decoding](beginner-glossary.html#concept-34-generation)・[sampling](beginner-glossary.html#concept-34-generation)・[温度](beginner-glossary.html#concept-34-generation)。

## なぜ使うか

学習済みモデルから生成し、速度と分布を区別するための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

最大確率を選ぶのがgreedy decoding、確率に沿ってくじで選ぶのがsamplingです。温度は点数の尺度を変えます。確率0.7,0.3でもsamplingでは後者が出ます。温度を下げても事実確認にはなりません。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
最大確率を選ぶのがgreedy decoding、確率に沿ってくじで選ぶのがsamplingです。温度は点数の尺度を変えます。確率0.7,0.3でもsamplingでは後者が出ます。温度を下げても事実確認にはなりません。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](33-training.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](34-reader.html)

<section class="resume-note" data-lesson="34-generation"><h2>次回の再開メモ</h2><label for="resume-34-generation">できたこと・止まった一文・次にすること</label><textarea id="resume-34-generation" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="33-training.html">前の小ページ</a><a href="34u-002.html">次の小ページ</a></nav>
