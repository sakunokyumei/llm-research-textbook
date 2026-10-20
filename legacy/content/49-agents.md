{"title": "49 ツールを使うエージェント", "part": "現代のLLMと評価", "goal": "行動ループを設計し、権限と評価をモデル出力から切り離す", "prereq": "09・10・37・40", "subpages": ["49u-002", "49u-003", "49u-004", "49u-005", "49u-006", "49u-007", "49u-008", "49u-009"], "next": "49u-002", "previous": "48u-009", "microtitle": "49-1 エージェント・tool・構造化引数", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "道具の引数を実行前に検査する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/9ページ。

今回の用語をまとめて復習：[エージェント・tool・構造化引数](beginner-glossary.html#concept-49-agents)。

## なぜ使うか

行動ループを設計し、権限と評価をモデル出力から切り離すための一歩です。このページでは、道具の引数を実行前に検査することを練習します。

## 意味と小さな例

道具を選んで作業を進める仕組みがエージェント。呼ぶ処理がtool、名前付きで渡す値が構造化引数です。足し算の道具へ{a:2,b:3}を渡すなら5。要求した道具名と型が許可範囲か確認します。

:::check 道具の引数を実行前に検査する
足し算toolへ{a:"two",b:3}が来ました。仕様が両方数なら、そのまま実行してよいですか。
:::answer
よくありません。型が仕様と違うので訂正を求める等の処理へ進みます。モデルが出した引数でも検査を省けません。
:::



## 今日の区切りと戻る場所

確認問題で「道具の引数を実行前に検査する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](48u-009.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](49-reader.html)

<section class="resume-note" data-lesson="49-agents"><h2>次回の再開メモ</h2><label for="resume-49-agents">できたこと・止まった一文・次にすること</label><textarea id="resume-49-agents" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="48u-009.html">前の小ページ</a><a href="49u-002.html">次の小ページ</a></nav>
