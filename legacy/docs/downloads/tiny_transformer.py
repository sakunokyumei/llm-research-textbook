"""CPU teaching experiment: copy a symbol across a distracting sequence.

No downloaded data, API keys or network access. This is a tiny language model,
not a pretrained conversational LLM. Run --help for the experiment controls.
"""
import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F


@dataclass
class Config:
    seed: int = 0
    variant: str = "attention"
    width: int = 32
    heads: int = 4
    layers: int = 2
    batch: int = 32
    lr: float = 0.003
    vocab: int = 7
    context: int = 8


# Tokens: 0=BOS, 1=separator, 2..5=content symbols, 6=EOS.
# Each document is [BOS, target, noise*4, separator, target, EOS].
# Hold out whole documents BEFORE training. Fixed manifest for every run.
def dataset():
    docs = [[0, a, b, c, d, e, 1, a, 6]
            for a in range(2, 6) for b in range(2, 6)
            for c in range(2, 6) for d in range(2, 6) for e in range(2, 6)]
    random.Random(31415).shuffle(docs)
    return {"train": torch.tensor(docs[:768]),
            "val": torch.tensor(docs[768:896]),
            "test": torch.tensor(docs[896:])}


def data_hash(data):
    return hashlib.sha256(json.dumps({k: v.tolist() for k, v in data.items()},
                                    sort_keys=True).encode()).hexdigest()


class Block(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.heads = cfg.heads
        self.variant = cfg.variant
        self.norm1 = nn.LayerNorm(cfg.width)
        self.qkv = nn.Linear(cfg.width, 3 * cfg.width)
        self.proj = nn.Linear(cfg.width, cfg.width)
        self.norm2 = nn.LayerNorm(cfg.width)
        self.mlp = nn.Sequential(nn.Linear(cfg.width, 4 * cfg.width),
                                 nn.GELU(), nn.Linear(4 * cfg.width, cfg.width))

    def forward(self, x):
        if self.variant != "no-attention":
            b, t, d = x.shape
            q, k, v = self.qkv(self.norm1(x)).chunk(3, dim=-1)
            q, k, v = [z.reshape(b, t, self.heads, d // self.heads).transpose(1, 2)
                       for z in (q, k, v)]
            scores = q @ k.transpose(-1, -2) / math.sqrt(d // self.heads)
            future = torch.ones(t, t, dtype=torch.bool, device=x.device).triu(1)
            weights = scores.masked_fill(future, float("-inf")).softmax(dim=-1)
            context = (weights @ v).transpose(1, 2).contiguous().reshape(b, t, d)
            x = x + self.proj(context)
        return x + self.mlp(self.norm2(x))


class TinyTransformer(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        if cfg.width % cfg.heads:
            raise ValueError("width must be divisible by heads")
        self.cfg = cfg
        self.token = nn.Embedding(cfg.vocab, cfg.width)
        self.position = nn.Embedding(cfg.context, cfg.width)
        self.blocks = nn.ModuleList(Block(cfg) for _ in range(cfg.layers))
        self.norm = nn.LayerNorm(cfg.width)
        self.head = nn.Linear(cfg.width, cfg.vocab, bias=False)

    def forward(self, ids):
        x = self.token(ids)
        if self.cfg.variant != "no-position":
            x = x + self.position(torch.arange(ids.shape[1], device=ids.device))
        for block in self.blocks:
            x = block(x)
        return self.head(self.norm(x))


def setup(cfg):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(cfg.seed)
    model = TinyTransformer(cfg)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=0.01)
    sampler = torch.Generator().manual_seed(cfg.seed + 1000)
    return model, optimizer, sampler


def train_steps(model, optimizer, sampler, docs, count):
    model.train()
    losses = []
    for _ in range(count):
        rows = torch.randint(len(docs), (model.cfg.batch,), generator=sampler)
        batch = docs[rows]
        logits = model(batch[:, :-1])
        loss = F.cross_entropy(logits.reshape(-1, 7), batch[:, 1:].reshape(-1))
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        losses.append(loss.item())
    return losses


@torch.no_grad()
def evaluate(model, docs):
    model.eval()
    logits = model(docs[:, :-1])
    nll = F.cross_entropy(logits.reshape(-1, 7), docs[:, 1:].reshape(-1)).item()
    prediction = logits[:, 6].argmax(-1)
    correct = prediction.eq(docs[:, 7])
    return {"nll": nll, "perplexity": math.exp(nll),
            "copy_accuracy": correct.float().mean().item(),
            "per_example_correct": correct.int().tolist()}


def bigram(train, test):
    counts = torch.ones(7, 7)  # add-one smoothing
    for row in train:
        for a, b in zip(row[:-1], row[1:]):
            counts[a, b] += 1
    probs = counts / counts.sum(-1, keepdim=True)
    nll = -probs[test[:, :-1], test[:, 1:]].log().mean().item()
    correct = probs[1].argmax().eq(test[:, 7])
    return {"nll": nll, "copy_accuracy": correct.float().mean().item()}


def save_checkpoint(path, model, optimizer, sampler, step, fingerprint):
    torch.save({"config": asdict(model.cfg), "model": model.state_dict(),
                "optimizer": optimizer.state_dict(), "sampler_rng": sampler.get_state(),
                "torch_rng": torch.get_rng_state(), "step": step,
                "data_sha256": fingerprint}, path)


def load_checkpoint(path, fingerprint):
    state = torch.load(path, map_location="cpu", weights_only=True)
    if state["data_sha256"] != fingerprint:
        raise ValueError("dataset changed; this is not the same experiment")
    cfg = Config(**state["config"])
    model, optimizer, sampler = setup(cfg)
    model.load_state_dict(state["model"])
    optimizer.load_state_dict(state["optimizer"])
    sampler.set_state(state["sampler_rng"])
    torch.set_rng_state(state["torch_rng"])
    return model, optimizer, sampler, state["step"]


@torch.no_grad()
def generate(model, prefix, seed=123):
    rng = torch.Generator().manual_seed(seed)
    ids = torch.tensor([prefix])
    while ids.shape[1] < 9:
        probs = model(ids)[:, -1].softmax(-1)
        token = torch.multinomial(probs, 1, generator=rng)
        ids = torch.cat((ids, token), dim=1)
        if token.item() == 6:
            break
    return ids[0].tolist()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--steps", type=int, default=300, help="total target steps, including resumed steps")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--variant", choices=["attention", "no-position", "no-attention"], default="attention")
    p.add_argument("--out", type=Path, default=Path("runs/tiny"))
    p.add_argument("--resume", type=Path)
    p.add_argument("--evaluate-test", action="store_true", help="use only after freezing experiment choices")
    args = p.parse_args()
    if args.steps < 0:
        p.error("steps must be nonnegative")
    data = dataset()
    fingerprint = data_hash(data)
    if args.resume:
        model, opt, rng, start = load_checkpoint(args.resume, fingerprint)
    else:
        model, opt, rng = setup(Config(seed=args.seed, variant=args.variant))
        start = 0
    if args.steps < start:
        p.error("steps is smaller than the saved checkpoint step")
    before = evaluate(model, data["val"])
    losses = train_steps(model, opt, rng, data["train"], args.steps - start)
    args.out.mkdir(parents=True, exist_ok=True)
    save_checkpoint(args.out / "checkpoint.pt", model, opt, rng, args.steps, fingerprint)
    result = {"config": asdict(model.cfg), "steps": args.steps, "start_step": start,
              "data_sha256": fingerprint, "torch": str(torch.__version__),
              "device": "cpu", "parameters": sum(x.numel() for x in model.parameters()),
              "validation_before": before, "validation": evaluate(model, data["val"]),
              "bigram_validation": bigram(data["train"], data["val"]),
              "last_train_loss": losses[-1] if losses else None,
              "sample": generate(model, [0, 2, 3, 4, 5, 3, 1])}
    if args.evaluate_test:
        result["test"] = evaluate(model, data["test"])
        result["bigram_test"] = bigram(data["train"], data["test"])
    (args.out / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"steps": args.steps, "variant": model.cfg.variant,
                      "validation_nll": result["validation"]["nll"],
                      "validation_copy_accuracy": result["validation"]["copy_accuracy"]}))


if __name__ == "__main__":
    main()
