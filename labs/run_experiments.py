"""Fixed validation study. The final test set is not used for design decisions."""
import csv
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
rows = []
for variant in ["attention", "no-position", "no-attention"]:
    for seed in [0, 1, 2]:
        out = root / "runs" / f"{variant}-{seed}"
        subprocess.run([sys.executable, str(root / "tiny_transformer.py"), "--steps", "300",
                        "--variant", variant, "--seed", str(seed), "--out", str(out)], check=True)
        result = json.loads((out / "metrics.json").read_text())
        rows.append({"variant": variant, "seed": seed, "steps": 300,
                     "validation_nll": result["validation"]["nll"],
                     "validation_copy_accuracy": result["validation"]["copy_accuracy"],
                     "bigram_copy_accuracy": result["bigram_validation"]["copy_accuracy"],
                     "parameters": result["parameters"], "data_sha256": result["data_sha256"]})
with (root / "results.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print("Wrote labs/results.csv; report all seeds, including negative results.")
