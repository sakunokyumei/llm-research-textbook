"""A complete byte language-model loop on generated Japanese sentences.

Run from the repository root. No private text or downloaded corpus is used.
This small grammar experiment teaches training; it is not a general chat model.
"""
import argparse
import hashlib
import json
import random
from dataclasses import asdict
from pathlib import Path

import torch
from torch.nn import functional as F
from tiny_transformer import Config, setup

BOS, EOS, PAD = 256, 257, 258


def corpus():
    subjects = ["ねこ", "いぬ", "とり", "うさぎ", "くま", "きつね", "りす", "かえる"]
    places = ["公園", "庭", "森", "家", "駅", "学校", "店", "川"]
    objects = ["赤い箱", "青い箱", "白い本", "黒い本", "小さな花", "大きな花", "丸い石", "四角い石"]
    docs = [f"{s}は{p}で{o}を見つけた。" for s in subjects for p in places for o in objects]
    random.Random(2718).shuffle(docs)
    return {"train": docs[:384], "validation": docs[384:448], "test": docs[448:]}


def encode(docs):
    rows = [[BOS] + list(s.encode("utf-8")) + [EOS] for s in docs]
    length = max(map(len, rows))
    result = torch.full((len(rows), length), PAD, dtype=torch.long)
    for i, row in enumerate(rows):
        result[i, :len(row)] = torch.tensor(row)
    return result


def loss_on(model, docs):
    logits = model(docs[:, :-1])
    return F.cross_entropy(logits.reshape(-1, 259), docs[:, 1:].reshape(-1), ignore_index=PAD)


@torch.no_grad()
def evaluate(model, docs):
    model.eval()
    # Every document is one independent sequence. Only right padding is masked in loss.
    return loss_on(model, docs).item()


@torch.no_grad()
def sample(model, prefix="ねこは", seed=99):
    model.eval()
    ids = [BOS] + list(prefix.encode("utf-8"))
    rng = torch.Generator().manual_seed(seed)
    while len(ids) < model.cfg.context:
        logits = model(torch.tensor([ids]))[0, -1].clone()
        logits[BOS] = logits[PAD] = float("-inf")
        token = torch.multinomial((logits / .7).softmax(0), 1, generator=rng).item()
        if token == EOS:
            break
        ids.append(token)
    raw = bytes(ids[1:])
    try:
        return {"text": raw.decode("utf-8"), "valid_utf8": True}
    except UnicodeDecodeError:
        return {"text": raw.decode("utf-8", errors="replace"), "valid_utf8": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--steps", type=int, default=300)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", type=Path, default=Path("labs/runs/text-lm"))
    p.add_argument("--evaluate-test", action="store_true")
    args = p.parse_args()
    if args.steps < 0:
        p.error("steps must be nonnegative")
    raw = corpus()
    assert not (set(raw["train"]) & set(raw["validation"]))
    assert not (set(raw["train"]) & set(raw["test"]))
    fingerprint = hashlib.sha256(json.dumps(raw, ensure_ascii=False).encode()).hexdigest()
    data = {k: encode(v) for k, v in raw.items()}
    cfg = Config(seed=args.seed, width=48, heads=4, layers=2, batch=16,
                 vocab=259, context=96, lr=.003)
    assert all(x.shape[1] <= cfg.context for x in data.values())
    model, optimizer, rng = setup(cfg)
    before = evaluate(model, data["validation"])
    curve = []
    for step in range(args.steps):
        model.train()
        rows = torch.randint(len(data["train"]), (cfg.batch,), generator=rng)
        loss = loss_on(model, data["train"][rows])
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
        optimizer.step()
        if (step+1) % 50 == 0:
            curve.append({"step": step+1, "train_nll": loss.item(),
                          "validation_nll": evaluate(model, data["validation"])})
    result = {"config": asdict(cfg), "steps": args.steps,
              "torch": str(torch.__version__), "device": "cpu", "data_sha256": fingerprint,
              "unit": "byte plus EOS", "validation_before": before,
              "validation_after": evaluate(model, data["validation"]),
              "curve": curve, "sample": sample(model)}
    if args.evaluate_test:
        result["test_nll"] = evaluate(model, data["test"])
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    torch.save({"config": asdict(cfg), "model": model.state_dict(),
                "optimizer": optimizer.state_dict(), "sampler_rng": rng.get_state(),
                "torch_rng": torch.get_rng_state(), "step": args.steps,
                "data_sha256": fingerprint}, args.out / "checkpoint.pt")
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
