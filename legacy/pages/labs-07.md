# 3．Tiny Transformerを学習する

この実習の7/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

`--steps`は追加回数ではなく最終的な合計です。resume時はcheckpointの設定を引き継ぎます。因果性・分割・連続学習との一致・学習成立を[test_labs.py](downloads/test_labs.py)で確認しています。同一CPU環境内の一致を確認したテストであり、別の機種や[ライブラリ](reference.html#term-library)版までbit単位で同じという保証ではありません。

### 日本語の文章でも学習する

```sh
python labs/text_lm.py --steps 300 --evaluate-test
```

[text_lm.py](downloads/text_lm.py)は同じTransformerを使い、「ねこは公園で赤い箱を見つけた。」のような512種類の合成文をbyteの列として学習します。384/64/64文書へ分割し、paddingの位置を[損失](reference.html#term-loss)から除きます。ダウンロードだけで実行する場合はtiny_transformer.pyも同じフォルダへ置いてください。

制作時の固定したseed0・300更新では、validation NLLが5.6787から0.1491、最終test NLLは0.1512でした。生成例は「ねこは川で小さな花を見つけた。」です。[設定・学習曲線・実測値](downloads/text_results.json)を配布します。単位はbyteとEOSであり、別のtokenizerのPPLとは直接比較しません。非常に限定された合成文法を学ぶ実験で、一般的な会話能力の証拠ではありません。

変更課題：場所や対象を増やす、学習時に一部の組合せを除く、文を長くする、の一つを選び、検証条件を先に決めます。byteを自由に生成すると不正なUTF-8になる可能性もあるため、コードはvalid_utf8を記録します。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](labs-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="labs-06.html">前の作業</a><a href="labs-08.html">次の作業</a></nav>
