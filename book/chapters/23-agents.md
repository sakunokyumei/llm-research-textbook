{"title": "道具を使わせる：エージェント", "short": "エージェント", "subtitle": "LLMに電卓と検索を渡し、自分で考えて使わせる", "time": "90〜120分", "env": "gpu", "level": 4, "builds": "電卓・学校資料の検索・今日の日付の3つの道具を、LLMが自分で選んで使う「ボンゴ情報専門学校の案内エージェント」", "theory": ["ツール呼び出し（function calling）の仕組み", "道具の説明はJSONスキーマとしてプロンプトに入る", "エージェントのループ（フローチャート）", "ReAct：考える→行動→観察", "安全性：権限・許可リスト・プロンプトインジェクション・人の確認", "MCP（道具をつなぐ共通の約束）"], "python": ["型ヒントとdocstringで関数を説明する", "`ast` で安全に式を計算する", "正規表現と `json.loads` で出力を読み取る", "`for` と `range` で上限回数つきのループ"]}

:::goal
第1章で、LLMは「123×456」を間違えました。計算しているのではなく、それっぽい数字を予測していたからです。じゃあ、LLMに**電卓を渡せば**いい。この章では、LLMが「ここは電卓を使おう」「ここは資料を検索しよう」と**自分で判断して道具を使う**仕組み、**エージェント**を作ります。フローチャートで設計して、Pythonで組み立てます。
:::

:::minato
LLMが電卓を使うって、どうやって？ LLMには手がないですよね。
:::

:::sensei
手はないが、口はある。LLMに「電卓を使いたいときは、こういう形式で書いてね」と教えておく。LLMがその形式で「電卓：123×456」と書いたら、**プログラム（キミのPython）が代わりに電卓を叩いて**、結果をLLMに返す。LLMは司令塔、Pythonは手足。チームプレーだね。
:::

## 準備：少し大きめのモデル

道具を使うには、指示を正確に守る力が必要なので、0.5Bより一回り大きい **Qwen2.5-1.5B-Instruct**（float16で約3GB）を使います。GPUのランタイムで実行してください。

```python
!wget -q https://raw.githubusercontent.com/sakunokyumei/llm-research-textbook/main/code/rag_docs.jsonl
import ast, json, operator, re, datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

device = "cuda" if torch.cuda.is_available() else "cpu"
name = "Qwen/Qwen2.5-1.5B-Instruct"
tok = AutoTokenizer.from_pretrained(name)
llm = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float16 if device == "cuda" else torch.float32).to(device)
print("準備完了")
```

```output
準備完了
```

## 道具を作る

道具は、ふつうのPythonの関数です。ただし、LLMが「この道具は何をするのか」を理解できるように、**型ヒント**と**説明（docstring）**をきちんと書きます。

```python
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}

def calculator(expression: str) -> str:
    """四則演算の式を正確に計算する。

    Args:
        expression: 計算したい式。例：'123*456' や '(3+4)/2'
    """
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](ev(node.operand))
        raise ValueError("数字と + - * / ** ( ) 以外は使えません")
    try:
        expression = expression.replace("×", "*").replace("÷", "/")
        return str(ev(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"エラー：{e}"

docs = [json.loads(l) for l in open("rag_docs.jsonl", encoding="utf-8")]

def search_school(query: str) -> str:
    """ボンゴ情報専門学校の資料から、質問に関係する文章を探す。

    Args:
        query: 調べたいこと。例：'学食の人気メニュー'
    """
    grams = lambda s: {s[i:i + 2] for i in range(len(s) - 1)}
    q = grams(query)
    best = sorted(docs, key=lambda d: -len(q & grams(d["title"] + d["text"])))[:2]
    return "\n".join(f"[{d['id']}] {d['text']}" for d in best)

def today() -> str:
    """今日の日付を返す。"""
    return datetime.date.today().isoformat()

tools = {"calculator": calculator, "search_school": search_school, "today": today}
print(calculator("123*456"), calculator("(3+4)/2"), calculator("__import__('os')"))
```

```output
56088 3.5 エラー：数字と + - * / ** ( ) 以外は使えません
```

:::python try と isinstance
`try:` の中でエラーが起きると、プログラムを止める代わりに `except` の中が実行されます。`except Exception as e:` は「どんなエラーでも受け止めて、その内容を `e` に入れる」という意味です。電卓に変な式が渡されても、エージェント全体が止まらずに「エラー：…」という結果を返せるようにしています。<br>
`isinstance(node, ast.Constant)` は「`node` は数字や文字などの定数か？」を確かめる関数です（第12章）。式の木の、部品の種類ごとに処理を分けています。
:::

:::warn eval を使わない理由
Pythonには、文字列をそのままプログラムとして実行する `eval` という関数があります。電卓なら `eval("123*456")` で済みそうですが、**LLMの出力を `eval` してはいけません**。LLMが（あるいは、LLMをだました誰かが）`__import__('os').system('…')` のような文字列を書けば、あなたのコンピュータで好きな命令が実行されてしまいます。上の `calculator` は、式を構文の木（`ast`）に分解し、数字と四則演算だけを許可しているので、そうした攻撃を受け付けません。**道具は、できることを最小限にして作る**。これがエージェントの安全の基本です。
:::

:::fe 構文解析
`ast.parse` は、式を「木構造」（**構文木**）に分解します。`3+4*2` は、「＋」の下に「3」と「×」があり、「×」の下に「4」と「2」がある木になります。基本情報で習う「逆ポーランド記法」や「木の走査」は、まさにこの計算の仕組みです。上の `ev` 関数は、木を下からたどって計算する**再帰**の関数になっています。
:::

## 道具の説明は、プロンプトに入る

`apply_chat_template` に `tools=` で関数のリストを渡すと、関数の型ヒントとdocstringから、**道具の説明書**（JSONスキーマ）が自動で作られ、プロンプトの中に書き込まれます。LLMが実際に何を読んでいるのか、見てみましょう。

```python
messages = [{"role": "user", "content": "123×456はいくつ？"}]
prompt = tok.apply_chat_template(messages, tools=list(tools.values()), add_generation_prompt=True, tokenize=False)
print(prompt)
```

```output
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{"type": "function", "function": {"name": "calculator", "description": "四則演算の式を正確に計算する。", "parameters": {"type": "object", "properties": {"expression": {"type": "string", "description": "計算したい式。例：'123*456' や '(3+4)/2'"}}, "required": ["expression"]}, "return": {"type": "string"}}}
{"type": "function", "function": {"name": "search_school", "description": "ボンゴ情報専門学校の資料から、質問に関係する文章を探す。", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "調べたいこと。例：'学食の人気メニュー'"}}, "required": ["query"]}, "return": {"type": "string"}}}
{"type": "function", "function": {"name": "today", "description": "今日の日付を返す。", "parameters": {"type": "object", "properties": {}}, "return": {"type": "string"}}}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call><|im_end|>
<|im_start|>user
123×456はいくつ？<|im_end|>
<|im_start|>assistant
```

:::theory ツール呼び出しの正体
これが **ツール呼び出し**（tool calling、function calling）の正体です。

1. 道具の説明書（名前・何をするか・引数）が、systemの部分に**ただの文章として**書き込まれる
2. 「道具を使いたいときは `<tool_call>{"name": …, "arguments": …}</tool_call>` と書け」というルールも書いてある
3. チャットモデルは、このルールに従って `<tool_call>` を書けるように、SFT（第18章）で訓練されている

つまり、LLMは道具を「実行」しているわけではなく、「この道具をこの引数で使いたい」という**文章を書いているだけ**です。それを読み取って実際に関数を動かすのは、あなたのプログラムの仕事です。
:::

## LLMの「道具を使いたい」を読み取る

```python
def generate(messages):
    inputs = tok.apply_chat_template(messages, tools=list(tools.values()), add_generation_prompt=True,
                                     return_tensors="pt", return_dict=True).to(device)
    out = llm.generate(**inputs, max_new_tokens=200, do_sample=False, pad_token_id=tok.pad_token_id)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

def parse_tool_calls(text):
    calls = []
    # ( ) で囲んだ部分だけを取り出す。re.S は「. が改行にも当てはまる」指定（呼び出しは複数行になるため）
    for block in re.findall(r"<tool_call>(.*?)</tool_call>", text, re.S):
        try:
            calls.append(json.loads(block))
        except json.JSONDecodeError:
            pass                       # 形式が崩れていたら無視する
    return calls

reply = generate(messages)
print("LLMの返事：", reply)
print("読み取った呼び出し：", parse_tool_calls(reply))
```

```output-example
LLMの返事： <tool_call>
{"name": "calculator", "arguments": {"expression": "123*456"}}
</tool_call>
読み取った呼び出し： [{'name': 'calculator', 'arguments': {'expression': '123*456'}}]
```

LLMは自分で計算せずに、「calculatorを `123*456` で使いたい」と書きました。

## エージェントのループ

道具の結果をLLMに返し、LLMがそれを読んで、また道具を使うか、答えを書くかを決める。これをくり返すのがエージェントです。フローチャートで設計しましょう。

![エージェントのフローチャート。質問を入れ、LLMに生成させ、道具の呼び出しがあれば実行して結果を追加してLLMに戻る。なければ答えて終了。上限の回数に達したら終了。](img/agent-flow.svg)

:::fe フローチャートで設計する
基本情報で練習しているフローチャートは、エージェントの設計にそのまま使えます。特に大事なのは「**上限の回数**」の判断です。LLMが道具を呼び続けて終わらない（無限ループ）こともあるので、必ず回数の上限を決めておきます。ループには必ず出口を。これはプログラミングの鉄則ですね。
:::

フローチャートを、そのままPythonにします。

```python
def run_agent(question, max_steps=5, verbose=True):
    messages = [{"role": "user", "content": question}]
    for step in range(max_steps):
        reply = generate(messages)
        calls = parse_tool_calls(reply)
        if not calls:                                       # 道具の呼び出しがない → 答え
            return reply
        messages.append({"role": "assistant", "content": "",
                         "tool_calls": [{"type": "function", "function": c} for c in calls]})
        for c in calls:
            fn = tools.get(c.get("name"))
            try:                                            # 引数がおかしくても止まらないように
                result = fn(**c.get("arguments", {})) if fn else f"そんな道具はありません：{c.get('name')}"
            except Exception as e:
                result = f"エラー：{e}"                     # エラーの内容をLLMに返して、やり直させる
            if verbose:
                print(f"  🔧 {c.get('name')}({c.get('arguments')}) → {result[:60]}")
            messages.append({"role": "tool", "name": c.get("name"), "content": result})
    return "（上限の回数に達しました）"

print(run_agent("123×456はいくつ？"))
```

```output-example
  🔧 calculator({'expression': '123*456'}) → 56088
123×456 = 56088 です。
```

:::sensei
第1章の雪辱を果たしたぞ！ 56088。今度は「それっぽい数」ではなく、本当に計算した数だ。LLMは「計算が必要だ」と判断して、電卓の結果を読んで答えた。司令塔と手足のチームプレー、成功だね。
:::

道具を2つ組み合わせる必要がある質問も試してみましょう。

```python
print(run_agent("ボンゴ情報専門学校の学食の一番人気メニューを、3人分買うといくらになりますか？"))
```

```output-example
  🔧 search_school({'query': '学食の一番人気メニュー'}) → [3] 学食「ドコドコ食堂」の一番人気は「量子化カレー」（450円）です。ご飯の
  🔧 calculator({'expression': '450*3'}) → 1350
一番人気のメニューは「量子化カレー」（450円）で、3人分だと1350円になります。
```

検索で値段を調べ、電卓で掛け算をしました。誰も手順を教えていないのに、LLMが自分で「まず調べて、次に計算」と段取りを組んでいます。

:::theory ReAct：考える → 行動 → 観察
このように、LLMが「**考え**（Reasoning）」と「**行動**（Acting、道具を使う）」と「**観察**（道具の結果を読む）」をくり返しながら問題を解く方法を **ReAct** と呼びます（2022年の論文）。人間が調べものをするときと同じで、一度に全部を考えず、調べた結果を見ながら次の一手を決めるのです。

小さなモデルは、段取りを間違えたり、道具の名前や引数を間違えたり、同じ道具を何度も呼んだりします。うまくいかないときは、

- もっと大きなモデルを使う（3B、7Bなど。7BならQLoRAと同じ4ビット読み込みでT4に乗る）
- 道具の説明（docstring）を分かりやすく書き直す
- 道具の数を絞る（選択肢が多いほど迷う）

を試しましょう。道具の説明を書くのは、**LLMのためのUI（使い方の説明）を書く**仕事です。HTMLで分かりやすいボタンを作るのと、よく似ています。
:::

:::try 道具を増やしてみよう
「たいこ町の今日の天気」を返す（中身は固定の文字列でOK）`weather` 関数や、「単位換算」をする関数を作って `tools` に追加してみましょう。docstringの書き方しだいで、LLMがうまく使えるかどうかが変わるのを観察してください。
:::

## エージェントの安全

エージェントは、道具を通して**現実の世界に作用**できます。電卓ならまだしも、「メールを送る」「ファイルを消す」「買い物をする」道具を渡したら……？

:::warn エージェントの安全のための5か条
1. **道具の権限は最小限に**：電卓は四則演算だけ、検索は読むだけ。消したり送ったりする道具は、本当に必要なときだけ
2. **許可リスト**：使ってよい道具・引数を決めておき、それ以外は実行しない（上の `tools.get` で、知らない道具名は実行しないようにしています）
3. **取り返しのつかない操作は人が確認**：送信・削除・支払いの前には、必ず人間に「実行していいですか？」と聞く
4. **道具の結果は「データ」であって「命令」ではない**：検索結果やWebページに「これまでの指示を無視して…」と書かれていても従わない（第21章のプロンプトインジェクション）
5. **上限を決める**：回数・時間・お金の上限。無限ループや暴走を防ぐ
:::

:::deep MCP：道具をつなぐ共通の約束
道具（データベース、ファイル、Webサービスなど）とLLMのアプリをつなぐ方法は、アプリごとにバラバラでした。そこで2024年11月に、Anthropic社が **MCP**（Model Context Protocol）というオープンな共通規格を公開しました。USBのように、規格に合わせて作った道具（MCPサーバー）なら、いろいろなAIアプリ（MCPクライアント）から同じように使える、という考え方です。この章で作った「道具の説明（JSONスキーマ）を渡し、呼び出しを受け取り、結果を返す」という流れが、MCPでも基本になっています。
:::

:::quiz ツール呼び出し
LLMは、電卓の道具を「実行」しているの？
:::answer
いいえ。LLMは「この道具をこの引数で使いたい」という決まった形式の文章（`<tool_call>…</tool_call>`）を書いているだけです。それを読み取って実際に関数を実行し、結果を返すのは、周りのプログラムの仕事です。
:::

:::quiz 上限
エージェントのループに「上限の回数」が必要なのはなぜ？
:::answer
LLMが道具を呼び続けて答えを出さない（無限ループになる）ことがあるからです。時間やお金を使い続けたり、同じ操作をくり返したりするのを防ぐために、必ず出口を用意します。
:::

:::quiz eval
電卓の道具を `eval(expression)` で作ってはいけないのはなぜ？
:::answer
`eval` は文字列をPythonのプログラムとして実行するので、LLM（やLLMをだました誰か）が危険な命令を書けば、それが実行されてしまうからです。数字と四則演算だけを許可する安全な計算方法を使います。
:::

:::checklist
- 型ヒントとdocstringで道具の関数を書いた
- 道具の説明がプロンプトの中に文章として入ることを確かめた
- `<tool_call>` を読み取って関数を実行できた
- フローチャートで設計したエージェントのループを実装した
- 検索と電卓を組み合わせる質問に、エージェントが答えた
- エージェントの安全のための5か条を説明できる
:::

:::recap
- **ツール呼び出し**：道具の説明（JSONスキーマ）をプロンプトに入れ、LLMが書いた呼び出しをプログラムが実行する
- **エージェント**：生成 → 道具の実行 → 結果を返す、をくり返すループ。必ず**上限**を決める
- **ReAct**：考える・行動・観察のくり返し。道具の説明を書くのは「LLMのためのUI」作り
- 安全：**最小権限・許可リスト・人の確認・結果は命令ではない・上限**。`eval` は使わない
:::

:::sensei
キミのLLMは、知識、作法、好み、そして手足を手に入れた。次の章では、いよいよ**世界に公開**する。第13章で育てた漱石GPTを、キミが得意なHTMLとCSSで作ったWebページに載せて、誰でもブラウザで試せるようにしよう。トップページで動いていた、あれだ。
:::
