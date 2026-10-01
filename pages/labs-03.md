# 0．実行の準備

この実習の3/11ページ。読む目安10〜20分、実行・記録は別の回へ分けます。速度や必要時間はPCによって違います。

[GitHubリポジトリ](https://github.com/sakunokyumei/llm-research-textbook)を取得します。WindowsではPowerShell、macOS/Linuxではterminalを開きます。コマンドは一行ずつ入力します。`cd`は作業フォルダを移る命令です。

```sh
git clone https://github.com/sakunokyumei/llm-research-textbook.git
cd llm-research-textbook
python -m venv .venv
```

Windowsの有効化は `.venv\Scripts\Activate.ps1`、macOS/Linuxは `source .venv/bin/activate`。Windowsで有効化が制限される場合、設定を変えず `.venv\Scripts\python.exe` を以後の`python`の代わりに使えます。Pythonが見つからない場合は[08章](08-python.html)へ戻ります。

```sh
python -m pip install torch==2.13.0 numpy==2.5.2
python -m unittest discover -s labs -v
```

制作時の実行環境はPython 3.14、PyTorch 2.13.0+cpu、NumPy 2.5.2です。OSやPython版によってwheelの提供状況が違うため、導入に失敗したら[PyTorch公式インストール案内](https://pytorch.org/get-started/locally/)で対応する組合せを確認し、実際の版を記録してください。GPUは不要です。テストは数秒〜数分を見込み、速度はPCによります。

## 今日の作業を一つ残す

コードのページでは保存して実行し、期待する出力と比べます。止まったら命令、最後のエラー、作業フォルダをメモします。読むだけで実行した扱いにしません。

[記法へ戻る](33-reader.html) · [保存と実行へ戻る](08-reader.html) · [この実習をまとめて参照](labs-reference.html)

<nav class="pager" aria-label="実習の順序"><a href="labs-02.html">前の作業</a><a href="labs-04.html">次の作業</a></nav>
