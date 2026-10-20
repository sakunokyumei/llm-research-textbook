"""Compare two locally generated Tiny Transformer checkpoints on CPU."""
import argparse
import json
from pathlib import Path
import torch


def same(a, b):
    if isinstance(a, torch.Tensor) or isinstance(b, torch.Tensor):
        return (isinstance(a, torch.Tensor) and isinstance(b, torch.Tensor)
                and a.shape == b.shape and a.dtype == b.dtype and torch.equal(a, b))
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('continuous', type=Path)
    parser.add_argument('resumed', type=Path)
    args = parser.parse_args()
    try:
        first = torch.load(args.continuous, map_location='cpu', weights_only=True)
        second = torch.load(args.resumed, map_location='cpu', weights_only=True)
    except FileNotFoundError:
        parser.exit(2, 'FileNotFoundError: checkpoint.pt not found; check the folder and filename.\n')
    fields = ['config', 'data_sha256', 'step', 'model', 'optimizer', 'sampler_rng', 'torch_rng']
    report = {k: k in first and k in second and same(first[k], second[k]) for k in fields}
    report['all_match'] = all(report.values())
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['all_match'] else 1)


if __name__ == '__main__':
    main()
