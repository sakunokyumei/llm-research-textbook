{"title": "49 ツールを使うエージェント", "part": "現代のLLMと評価", "goal": "行動ループを設計し、権限と評価をモデル出力から切り離す", "prereq": "09・10・37・40", "subpages": ["49u-002", "49u-003", "49u-004", "49u-005", "49u-006", "49u-007", "49u-008", "49u-009"], "next": "49u-002", "previous": "48u-009", "microtitle": "49-1 エージェント・tool・構造化引数", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/9ページ。今日の目標：エージェント・tool・構造化引数の小例を一つ追う。

今日の言葉：[エージェント](beginner-glossary.html#concept-49-agents)・[tool](beginner-glossary.html#concept-49-agents)・[構造化引数](beginner-glossary.html#concept-49-agents)。

## なぜ使うか

行動ループを設計し、権限と評価をモデル出力から切り離すための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

道具を選んで作業を進める仕組みがエージェント。呼ぶ処理がtool、名前付きで渡す値が構造化引数です。足し算の道具へ{a:2,b:3}を渡すなら5。要求した道具名と型が許可範囲か確認します。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
道具を選んで作業を進める仕組みがエージェント。呼ぶ処理がtool、名前付きで渡す値が構造化引数です。足し算の道具へ{a:2,b:3}を渡すなら5。要求した道具名と型が許可範囲か確認します。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](48-multimodal.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](49-reader.html)

<section class="resume-note" data-lesson="49-agents"><h2>次回の再開メモ</h2><label for="resume-49-agents">できたこと・止まった一文・次にすること</label><textarea id="resume-49-agents" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="48-multimodal.html">前の小ページ</a><a href="49u-002.html">次の小ページ</a></nav>
