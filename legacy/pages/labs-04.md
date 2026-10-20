# 1．数式と自動微分

この実習の4/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

```sh
python labs/math_checks.py
```

[math_checks.py](downloads/math_checks.py)は、通常のsoftmaxとonline計算、有限差分と[自動微分](reference.html#term-autograd)、[LoRA](reference.html#term-lora)の凍結と[勾配](reference.html#term-gradient)を比較します。制作時には全assertが通り、重み付き和は約5.056113、[微分](reference.html#term-derivative)は約5.337499でした。

変更課題：scoreをすべて1000増やしても結果が変わらないか。有限差分のhを極端に小さくすると、誤差は必ず減るか。LoRAのBをゼロ以外で初期化するとAの最初の勾配はどうなるか。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](labs-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="labs-03.html">前の作業</a><a href="labs-05.html">次の作業</a></nav>
