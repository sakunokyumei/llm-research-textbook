# まず確率を動かしてみよう

この実習の2/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

三つの候補のscore（logit）を確率へ変換します。温度を下げる前に、どの候補がどれくらい選ばれやすくなるか予想してください。すべてのscoreへ同じ数を足したら、確率はどうなるでしょう。

<div class="playground">
<label>候補1のscore <input data-logit type="range" min="-5" max="5" step="0.5" value="2" aria-label="候補1のscore"></label><br>
<label>候補2のscore <input data-logit type="range" min="-5" max="5" step="0.5" value="1" aria-label="候補2のscore"></label><br>
<label>候補3のscore <input data-logit type="range" min="-5" max="5" step="0.5" value="0" aria-label="候補3のscore"></label><br>
<label for="temperature">温度：<output id="temperature-value">1.0</output></label>
<input id="temperature" type="range" min="0.1" max="3" step="0.1" value="1">
<div id="softmax-output" aria-live="polite"></div>

</div>

同じ数を足しても[softmax](reference.html#term-softmax)は変わりません。温度を下げると最大scoreの候補へ集中します。温度は正解率を直接表す値ではありません。[28章](28-numerics.html)・[34章](34-generation.html)

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](labs-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="labs.html">前の作業</a><a href="labs-03.html">次の作業</a></nav>
