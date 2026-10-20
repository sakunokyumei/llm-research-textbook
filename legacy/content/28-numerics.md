{"title": "28 Optimizerと数値安定性", "part": "機械学習と深層学習", "goal": "安定な確率計算と更新を実装し、NaNを切り分ける", "prereq": "07・18・26・27", "subpages": ["28u-002", "28u-003", "28u-004", "28u-005", "28u-006", "28u-007", "28u-008", "28u-009", "28u-010", "28u-011", "28u-012", "28u-013"], "next": "28u-002", "previous": "27u-013", "microtitle": "28-1 softmax・log-sum-exp", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "softmaxの比を計算する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/13ページ。

今回の用語をまとめて復習：[softmax・log-sum-exp](beginner-glossary.html#concept-28-numerics)。

## なぜ使うか

安定な確率計算と更新を実装し、NaNを切り分けるための一歩です。このページでは、softmaxの比を計算することを練習します。

## 意味と小さな例

点数を指数へ変えて合計で割るのがsoftmax。点数0,ln2なら指数1,2、確率1/3,2/3です。log-sum-expはその指数の合計の対数。大きな値では最大点数を引いて同じ比を安全に求めます。

:::check softmaxの比を計算する
点数(ln3,0)のsoftmaxを求めてください。両点数へ100を足しても数学上の結果は変わりますか。
:::answer
指数は(3,1)なので(3/4,1/4)です。同じ定数の追加は比で打ち消されるため変わりません。実装では大きな指数を避けます。
:::



## 今日の区切りと戻る場所

確認問題で「softmaxの比を計算する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](27u-013.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](28-reader.html)

<section class="resume-note" data-lesson="28-numerics"><h2>次回の再開メモ</h2><label for="resume-28-numerics">できたこと・止まった一文・次にすること</label><textarea id="resume-28-numerics" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="27u-013.html">前の小ページ</a><a href="28u-002.html">次の小ページ</a></nav>
