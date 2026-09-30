"""Paired document bootstrap for two systems' per-example correctness."""
import argparse
import json
import random


def interval(a, b, seed=0, repeats=5000):
    if len(a) != len(b) or not a:
        raise ValueError("nonempty paired results of equal length required")
    rng = random.Random(seed)
    differences = [x-y for x, y in zip(a, b)]
    means = sorted(sum(rng.choice(differences) for _ in differences)/len(differences)
                   for _ in range(repeats))
    return {"difference": sum(differences)/len(differences),
            "percentile_95_interval": [means[int(.025*repeats)], means[int(.975*repeats)]],
            "unit": "document", "resamples": repeats, "seed": seed}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("a", nargs="?")
    p.add_argument("b", nargs="?")
    args = p.parse_args()
    if bool(args.a) != bool(args.b):
        p.error("provide both metrics files or neither")
    if args.a:
        values, hashes = [], []
        for path in (args.a, args.b):
            with open(path, encoding="utf-8") as f:
                record = json.load(f)
                hashes.append(record["data_sha256"])
                values.append(record["validation"]["per_example_correct"])
        if hashes[0] != hashes[1]:
            p.error("dataset manifests differ; results cannot be paired by row")
        print(json.dumps(interval(*values)))
    else:
        print(json.dumps(interval([1, 1, 0, 1, 1, 0], [1, 0, 1, 0, 1, 0])))
