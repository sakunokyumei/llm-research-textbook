{"title": "32 Transformerを一つのモデルにする", "part": "言語モデルを作る", "goal": "Embeddingから語彙logitまでの形を追う", "prereq": "27〜31", "subpages": ["32u-002", "32u-003", "32u-004", "32u-005", "32u-006", "32u-007", "32u-008", "32u-009", "32u-010", "32u-011", "32u-012", "32u-013", "32u-014", "32u-015", "32u-016"], "next": "32u-002", "previous": "31u-011", "microtitle": "32-1 Transformer・Multi-Head Attention・ヘッド幅", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/16ページ。今日の目標：Transformer・Multi-Head Attention・ヘッド幅の小例を一つ追う。

今日の言葉：[Transformer](beginner-glossary.html#concept-32-transformer)・[Multi-Head Attention](beginner-glossary.html#concept-32-transformer)・[ヘッド幅](beginner-glossary.html#concept-32-transformer)。

## なぜ使うか

Embeddingから語彙logitまでの形を追うための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

Attentionと位置ごとの変換などをつなぐモデルがTransformer。複数の参照計算を並べるのがMulti-Head Attentionです。幅8を二つのヘッドへ分ければ各幅4。ヘッド数を増やすだけで重みが必ず減るわけではありません。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
Attentionと位置ごとの変換などをつなぐモデルがTransformer。複数の参照計算を並べるのがMulti-Head Attentionです。幅8を二つのヘッドへ分ければ各幅4。ヘッド数を増やすだけで重みが必ず減るわけではありません。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](31-attention.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](32-reader.html)

<section class="resume-note" data-lesson="32-transformer"><h2>次回の再開メモ</h2><label for="resume-32-transformer">できたこと・止まった一文・次にすること</label><textarea id="resume-32-transformer" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="31-attention.html">前の小ページ</a><a href="32u-002.html">次の小ページ</a></nav>
