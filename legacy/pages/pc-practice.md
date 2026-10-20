# PCで、一つの実験を動かす準備

初回の導入は30〜60分以上掛かる場合があります。途中で止めても、作業番号を残して次の日から再開できます。スマホだけの日は、コードの出力予想を紙に残し、実行欄は未実行とします。家族のPCを使う場合は、書き込める自分の練習フォルダで作業してください。

## 1．Pythonが起動するかを確かめる

[第8章の保存・実行](08-reader.html)でPythonを導入し、PowerShellなどのターミナルを開きます。ターミナルは文字で操作を頼むアプリです。一行ずつ入力してEnterを押します。

```text
python --version
```

Pythonと版番号が出たら、これから使う起動名はpythonです。Windowsで見つからない場合は `py --version` を試し、そちらが動いたら次の仮想環境作成のpythonをpyに替えます。macOS/Linuxでpython3が動く場合も同様です。両方なければ[Python公式](https://www.python.org/downloads/)の使用OS向けの案内へ戻ります。

## 2．教材をフォルダごとに取得する

1. [公開GitHubリポジトリ](https://github.com/sakunokyumei/llm-research-textbook)を開きます。
2. 「Code」→「Download ZIP」で取得し、圧縮されたファイルを展開します。展開は中のファイルを普通のフォルダへ取り出す操作です。
3. 展開したフォルダの中に `labs` があり、その中に `distance_study.py` と `tiny_transformer.py` があることを確認します。
4. エクスプローラーなどで、labsの一つ上のフォルダの場所をコピーします。PowerShellで `cd "コピーした場所"` と入力します。引用符内を実際の場所に替えます。
5. `dir labs`（macOS/Linuxでは `ls labs`）でファイルを確認します。

ZIPを開いて見るだけでは実行用の普通のフォルダになりません。必ず展開してください。Gitがまだ分からなくても、最初のCPU実験はこの方法で始められます。変更履歴の練習は[第12章](12-environment.html)で行います。

## 3．教材専用のPythonを作る

仮想環境は、この教材用に追加の道具を分ける場所です。ここでは `.venv` という名前のフォルダを作ります。

```text
python -m venv .venv
```

Windowsでは、以後 `.venv\Scripts\python.exe` を使います。有効化の操作を省いて、この環境のPythonを直接指定できます。例として版を確かめます。

```text
.venv\Scripts\python.exe --version
```

macOS/Linuxでは `.venv/bin/python --version`。下のWindows用の起動名をこの名前へ替えます。pipはPythonへライブラリを追加する道具、ライブラリは他の人が用意した計算などの機能です。

<h2 id="numpy">4．NumPyを同じPythonへ追加する</h2>

第15・16章の数の表にはNumPyを使います。

```text
.venv\Scripts\python.exe -m pip install numpy
.venv\Scripts\python.exe -c "import numpy; print(numpy.__version__)"
```

二行目で版番号が出れば、このPythonから読み込めています。`-m pip`はそのPythonのpipを使う指定、`-c`は短いPythonコードを直接実行する指定、`__version__`は版の情報です。実験票へ表示された版を残してください。版が違う実行を厳密な再現と扱いません。

<h2 id="torch">5．CPUのPyTorchを追加する</h2>

[PyTorch公式の導入画面](https://pytorch.org/get-started/locally/)で、使用OS・Pip・Python・CPUに対応するコマンドを確認します。公式の `pip install ...` のpip部分を、この環境の `.venv\Scripts\python.exe -m pip` へ読み替えて実行します。Windows/LinuxのCPU版の指定は次の形です。提供される版と対応Pythonは公式案内で確認してください。

```text
.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python.exe -c "import torch; print(torch.__version__)"
```

第26章以降はこの同じ起動名を使います。再現用の制作時の版は[実装ラボの準備](labs-03.html)に記載しています。通常の学習の導入と、特定の版で同条件を再現する作業を区別します。

## 6．実行できることを小さく確認する

```text
.venv\Scripts\python.exe -m unittest discover -s labs -v
```

unittestはテストを動かす道具、discoverは指定したフォルダからテストを探す操作、`-s labs`は探す場所、`-v`は個別の結果を表示する指定です。最後にOKが出ることを確認します。FAILEDやERRORが出たら研究実験へ進む前に、テスト名と最後のエラーを残します。

## エラーの場所から一段だけ戻る

|表示|まず確認すること|戻る作業|
|---|---|---|
|起動名が見つからない|Pythonの導入と、使う起動名|1|
|can't open file / No such file|フォルダと保存名。ZIPを展開したか|2|
|No module named numpy / torch|実行した起動名と導入した起動名が同じか|4または5|
|No matching distribution found|公式の対応OS・CPUの種類・Pythonの版。対応版を新しい仮想環境へ導入する|5|
|PermissionError / Access denied|書き込める練習フォルダか。対象が別のアプリで開かれていないか|2|
|ネットワーク・証明書のエラー|回線、組織の制限、OSの時刻を確認。証明書確認を無効にして進めない|4または5|
|MemoryError / out of memory|他の大きいアプリを閉じ、短い診断を使う。更新回数だけでは最大メモリが下がらない場合がある|[短い実行](33-run-steps.html)|

導入できないPCでは実行の達成を保留します。コードの手計算・説明・実験票の準備は進められます。エラー全文に個人名などが含まれる場合は、公開前に除いてください。

[実行の続きを学ぶ](33-run-steps.html) · [第10章の読み書き](10-file-steps.html) · [第26章の自動微分](26-autograd-steps.html)
