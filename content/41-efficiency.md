{"title": "41 GPU・FlashAttention・Triton", "part": "効率と現代のアーキテクチャ", "goal": "演算と転送のどちらが律速かを測り、正しさを保って改善する", "prereq": "13・16・28・31", "subpages": ["41u-002", "41u-003", "41u-004", "41u-005", "41u-006", "41u-007", "41u-008", "41u-009", "41u-010", "41u-011"], "next": "41u-002", "previous": "40u-008", "microtitle": "41-1 帯域・演算強度・Roofline", "time": "この小ページを読む目安5〜10分／確認5〜10分。章全体は複数日に分けます", "microgoal": "転送側の性能上限を計算する"}

読む目安5〜10分／確認5〜10分。時間は編集上の目安です。

この章の1/11ページ。

今回の用語をまとめて復習：[帯域・演算強度・Roofline](beginner-glossary.html#concept-41-efficiency)。

## なぜ使うか

演算と転送のどちらが律速かを測り、正しさを保って改善するための一歩です。このページでは、転送側の性能上限を計算することを練習します。

## 意味と小さな例

一秒に運べるbyte数が帯域、演算数を転送byteで割るのが演算強度。Rooflineは計算の上限と転送側の上限の小さい方を考える模型です。10演算で20byte運べば0.5演算/byte。上限を実測値とは呼びません。

:::check 転送側の性能上限を計算する
演算強度2演算/byte、帯域10byte/秒、計算上限100演算/秒の模型です。Rooflineの上限はいくつですか。
:::answer
転送側は2×10=20演算/秒で、min(20,100)=20です。実際の速度はこの理想上限以下で、実測が必要です。
:::



## 今日の区切りと戻る場所

確認問題で「転送側の性能上限を計算する」ことを試してください。答えの数だけでなく理由も照合し、違った部分から本文へ戻ります。

[直前の例へ戻る](40u-008.html) · [中断・再開の手引き](learning-help.html) · [この章をまとめて参照](41-reader.html)

<section class="resume-note" data-lesson="41-efficiency"><h2>次回の再開メモ</h2><label for="resume-41-efficiency">できたこと・止まった一文・次にすること</label><textarea id="resume-41-efficiency" rows="3" maxlength="2000"></textarea><button type="button" data-save-note>この端末へメモを保存</button><p role="status" data-note-status>端末内だけに保存します。共有PCでは個人情報を書かず、使い終わったらメモを消してください。</p><button type="button" data-clear-note>このメモを消す</button></section>

<nav class="pager" aria-label="小ページの順序"><a href="40u-008.html">前の小ページ</a><a href="41u-002.html">次の小ページ</a></nav>
