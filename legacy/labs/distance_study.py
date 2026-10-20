"""A CPU capstone: train on two copy distances and evaluate a held-out distance.

The protocol is written before training. This is a small synthetic study, not
evidence about natural-language LLMs. Final-test evaluation requires a flag.
"""
import argparse
import csv
import hashlib
import json
import random
import time
from pathlib import Path

import torch
from torch.nn import functional as F

from tiny_transformer import Config, setup, save_checkpoint
from paired_bootstrap import interval


TRAIN_NOISE = (4, 6)
ALL_NOISE = (4, 6, 8)
VARIANTS = ("attention", "no-position", "no-attention")
SEEDS = (0, 1, 2)


def documents(noise_count):
    if noise_count < 3:
        raise ValueError("at least three noise symbols needed for this corpus")
    rng = random.Random(31415 + noise_count)
    groups = {"train": [], "validation": [], "test": []}
    for target in range(2, 6):
        noises = set()
        while len(noises) < 64:
            noises.add(tuple(rng.randrange(2, 6) for _ in range(noise_count)))
        ordered = sorted(noises)
        rng.shuffle(ordered)
        rows = [[0, target, *noise, 1, target, 6] for noise in ordered]
        groups["train"].extend(rows[:48])
        groups["validation"].extend(rows[48:56])
        groups["test"].extend(rows[56:])
    for rows in groups.values():
        rng.shuffle(rows)
    return {name: torch.tensor(rows) for name, rows in groups.items()}


def fingerprint(data):
    text = json.dumps({str(n): {name: rows.tolist() for name, rows in group.items()}
                       for n, group in data.items()}, sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()


def train(model, optimizer, sampler, data, steps):
    model.train()
    tokens = 0
    for _ in range(steps):
        which = torch.randint(len(TRAIN_NOISE), (1,), generator=sampler).item()
        rows = data[TRAIN_NOISE[which]]["train"]
        ids = torch.randint(len(rows), (model.cfg.batch,), generator=sampler)
        batch = rows[ids]
        logits = model(batch[:, :-1])
        loss = F.cross_entropy(logits.reshape(-1, model.cfg.vocab),
                               batch[:, 1:].reshape(-1))
        if not torch.isfinite(loss):
            raise ValueError("nonfinite loss; retain the failed run")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        tokens = tokens + batch.shape[0] * (batch.shape[1] - 1)
    return tokens


@torch.no_grad()
def evaluate(model, docs):
    model.eval()
    logits = model(docs[:, :-1])
    # The separator is always third from the end, regardless of copy distance.
    separator = docs.shape[1] - 3
    assert torch.all(docs[:, separator] == 1)
    assert torch.all(docs[:, separator + 1] == docs[:, 1])
    prediction = logits[:, separator].argmax(-1)
    targets = docs[:, separator + 1]
    correct = prediction.eq(targets)
    nll = F.cross_entropy(logits.reshape(-1, model.cfg.vocab),
                          docs[:, 1:].reshape(-1)).item()
    return {"nll": nll, "copy_accuracy": correct.float().mean().item(),
            "per_example_correct": correct.int().tolist(),
            "predicted_ids": prediction.tolist(), "target_ids": targets.tolist()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--held-out-noise", type=int, default=8)
    parser.add_argument("--out", type=Path, default=Path("labs/runs/distance-study"))
    parser.add_argument("--evaluate-test", action="store_true")
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("steps must be positive")
    if args.held_out_noise < 8:
        parser.error("held-out-noise must be at least 8, beyond the training lengths")
    evaluation_noise = (*TRAIN_NOISE, args.held_out_noise)
    context = args.held_out_noise + 4
    data = {n: documents(n) for n in evaluation_noise}
    plan = {"question": "Does positional embedding affect unseen-distance copy?",
            "primary_metric": "copy_accuracy", "train_noise": TRAIN_NOISE,
            "evaluation_noise": evaluation_noise, "held_out_noise": args.held_out_noise,
            "steps": args.steps, "seeds": SEEDS, "variants": VARIANTS,
            "config": {"width": 32, "heads": 4, "layers": 2, "batch": 32,
                       "lr": 0.003, "vocab": 7, "context": context},
            "data_sha256": fingerprint(data),
            "fixed_budget": "same updates, sampled documents and training tokens",
            "not_fixed": "active FLOPs and wall-clock time",
            "test_enabled": args.evaluate_test}
    args.out.mkdir(parents=True, exist_ok=True)
    plan_path = args.out / "plan.json"
    if plan_path.exists() and json.loads(plan_path.read_text(encoding="utf-8")) != json.loads(json.dumps(plan)):
        parser.error("output already contains a different protocol; use a new folder")
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    results, csv_rows = [], []
    for variant in VARIANTS:
        for seed in SEEDS:
            cfg = Config(seed=seed, variant=variant, context=context)
            model, opt, sampler = setup(cfg)
            record = {"variant": variant, "seed": seed, "status": "pending"}
            results.append(record)
            start = time.perf_counter()
            try:
                tokens = train(model, opt, sampler, data, args.steps)
                save_checkpoint(args.out / f"{variant}-{seed}.pt", model, opt,
                                sampler, args.steps, plan["data_sha256"])
                record.update(status="ok", tokens=tokens,
                              seconds=time.perf_counter()-start,
                              parameters=sum(p.numel() for p in model.parameters()),
                              validation={}, test={})
                splits = ["validation", "test"] if args.evaluate_test else ["validation"]
                for split in splits:
                    for n in evaluation_noise:
                        metrics = evaluate(model, data[n][split])
                        record[split][str(n)] = metrics
                        csv_rows.append({"variant": variant, "seed": seed,
                                         "noise_count": n, "split": split,
                                         "steps": args.steps, "tokens": tokens,
                                         "copy_accuracy": metrics["copy_accuracy"],
                                         "nll": metrics["nll"]})
            except (ValueError, RuntimeError) as exc:
                # Do not publish exception text, which may contain local paths.
                record.update(status="failed", error_type=type(exc).__name__)
            (args.out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
            print(variant, seed, record["status"], flush=True)
    with (args.out / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        if csv_rows:
            writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
            writer.writeheader()
            writer.writerows(csv_rows)
    comparisons = []
    for seed in SEEDS:
        matched = {r["variant"]: r for r in results if r["seed"] == seed and r["status"] == "ok"}
        if "attention" not in matched or "no-position" not in matched:
            continue
        for n in evaluation_noise:
            a = matched["attention"]["validation"][str(n)]["per_example_correct"]
            b = matched["no-position"]["validation"][str(n)]["per_example_correct"]
            comparisons.append({"seed": seed, "noise_count": n, **interval(a, b)})
    (args.out / "paired_validation.json").write_text(json.dumps(comparisons, indent=2), encoding="utf-8")
    if any(r["status"] != "ok" for r in results):
        raise SystemExit("Some runs failed; inspect their recorded status before making a claim")
    print("All nine runs recorded. Results do not guarantee improvement.")


if __name__ == "__main__":
    main()
