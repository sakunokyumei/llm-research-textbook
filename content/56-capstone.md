{"title": "56 卒業研究：再現から独自の問いへ", "part": "独自研究を形にする", "goal": "他者が実行できるコード・結果・報告書を一式完成させる", "prereq": "01〜55・実装ラボ", "subpages": ["56u-002", "56u-003", "56u-004", "56u-005", "56u-006", "56u-007", "56u-008"], "next": "56u-002", "previous": "55u-008", "microtitle": "56-1 距離に応じた採点位置・未学習距離", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "変えた距離に採点位置を合わせる"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/8ページ。

今回の用語をまとめて復習：[距離に応じた採点位置・未学習距離](beginner-glossary.html#concept-56-capstone)。

## なぜ使うか

他者が実行できるコード・結果・報告書を一式完成させるための一歩です。このページでは、変えた距離に採点位置を合わせることを練習します。

## 意味と小さな例

文書の長さを変えると正解を予測する位置も変わります。noiseが8個ならseparator位置10からコピー先11を予測。学習にnoise8を使わなければ未学習距離です。長さを変えず新しい文書を測る実験とは別です。

:::check 変えた距離に採点位置を合わせる
0始まりで[BOS,答え,noiseを6個,separator,コピー先,EOS]です。separatorとコピー先の位置はいくつですか。
:::answer
separatorは8、コピー先は9です。位置8から次の9を予測します。距離を変えても固定の位置を採点すると別の場所を測ってしまいます。
:::



## 今日の区切りと戻る場所

確認問題で「変えた距離に採点位置を合わせる」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](55u-008.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](56-reader.html)

<section class="resume-note" data-lesson="56-capstone"><h2>次回の再開メモ</h2><label for="resume-56-capstone">できたこと・止まった一文・次にすること</label><textarea id="resume-56-capstone" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="55u-008.html">前の小ページ</a><a href="56u-002.html">次の小ページ</a></nav>
