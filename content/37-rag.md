{"title": "37 RAGを検索と生成に分ける", "part": "LLMを育てる・調整する", "goal": "検索漏れと生成の誤りを別々に測る", "prereq": "14・24・34", "subpages": ["37u-002", "37u-003", "37u-004", "37u-005", "37u-006", "37u-007", "37u-008"], "next": "37u-002", "previous": "36u-009", "microtitle": "37-1 RAG・reranking", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます"}

読む目安5〜10分／確認5〜10分。長いコードの実行はPCを使える別の回へ分けられます。時間は編集上の目安です。

この章の1/8ページ。今日の目標：RAG・rerankingの小例を一つ追う。

今日の言葉：[RAG](beginner-glossary.html#concept-37-rag)・[reranking](beginner-glossary.html#concept-37-rag)。

## なぜ使うか

検索漏れと生成の誤りを別々に測るための一歩です。今日は下の小例を自分の言葉へ直し、同じ操作を再開できるようにします。

## 意味と小さな例

検索した根拠を入力へ加える方式がRAG。検索候補を別の基準で並べ直すのがrerankingです。必要な文書が候補に入らなければ、回答側を変えてもその根拠は使えません。検索と回答を分けて採点します。

:::exercise 1・例を自分で確かめる
上の例の入力と結果、または二つの役割を紙やメモへ書き、答えを隠して理由を一文で説明してください。数字がある例では、元の値へ戻して計算を照合してください。
:::answer
検索した根拠を入力へ加える方式がRAG。検索候補を別の基準で並べ直すのがrerankingです。必要な文書が候補に入らなければ、回答側を変えてもその根拠は使えません。検索と回答を分けて採点します。 入力・途中の操作・結果の三つを対応させます。説明できなければ次の新語へ進まず、この一例へ戻れます。
:::



## 今日の区切りと戻る場所

この小例を一つ説明できたら区切れます。 分からないことは説明の順序の手掛かりです。できた扱いにせず、止まった一文をメモします。

[直前の例へ戻る](36-adaptation.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](37-reader.html)

<section class="resume-note" data-lesson="37-rag"><h2>次回の再開メモ</h2><label for="resume-37-rag">できたこと・止まった一文・次にすること</label><textarea id="resume-37-rag" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="36-adaptation.html">前の小ページ</a><a href="37u-002.html">次の小ページ</a></nav>
