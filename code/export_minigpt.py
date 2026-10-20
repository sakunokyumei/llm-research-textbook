"""ミニGPTのチェックポイントを、ブラウザで読めるJSONに書き出す（第24章）

    python export_minigpt.py soseki_gpt.pt soseki-gpt.json

重みは行ごとに8ビット整数へ量子化（第19章のabsmax量子化）して、
base64という文字列の形でJSONに入れます。
"""
import base64
import json
import sys

import torch


def quantize_rows(w):
    """2次元の重みを、行ごとの縮尺つき int8 にする。1次元（バイアスなど）は float32 のまま。"""
    w = w.float()
    if w.dim() == 1:
        return {"shape": list(w.shape), "f32": base64.b64encode(w.numpy().tobytes()).decode()}
    scale = w.abs().amax(dim=1).clamp(min=1e-8) / 127
    q = torch.round(w / scale[:, None]).clamp(-127, 127).to(torch.int8)
    return {"shape": list(w.shape),
            "i8": base64.b64encode(q.numpy().tobytes()).decode(),
            "scale": base64.b64encode(scale.numpy().astype("float32").tobytes()).decode()}


def export(checkpoint_path, out_path):
    ck = torch.load(checkpoint_path, map_location="cpu")
    weights = {name: quantize_rows(t) for name, t in ck["model"].items() if not name.endswith("tril")}
    data = {"config": ck["config"], "chars": ck["chars"], "weights": weights}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    n = sum(t.numel() for name, t in ck["model"].items() if not name.endswith("tril"))
    return n


if __name__ == "__main__":
    n = export(sys.argv[1], sys.argv[2])
    print(f"{n:,} 個のパラメータを書き出しました → {sys.argv[2]}")
