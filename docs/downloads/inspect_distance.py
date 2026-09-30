"""Inspect a self-created distance checkpoint; observe a layer, then remove hook."""
import argparse
import json
from pathlib import Path
import torch
from tiny_transformer import load_checkpoint
from distance_study import documents, fingerprint, evaluate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    # The shape information is in our own checkpoint, loaded in restricted mode.
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    held_noise = state["config"]["context"] - 4
    data = {n: documents(n) for n in (4, 6, held_noise)}
    model, _, _, step = load_checkpoint(args.checkpoint, fingerprint(data))
    docs = data[held_noise]["validation"]
    metrics = evaluate(model, docs)
    failed = []
    for i, correct in enumerate(metrics["per_example_correct"]):
        if not correct:
            failed.append({"row": i, "document": docs[i].tolist(),
                           "target": metrics["target_ids"][i],
                           "prediction": metrics["predicted_ids"][i]})
    cache = []
    def capture(module, inputs, output):
        cache.append(output.detach().clone())
    handle = model.blocks[0].register_forward_hook(capture)
    first = docs[:1].clone()
    second = first.clone()
    second[:, 1] = 2 if first[0, 1].item() != 2 else 3
    second[:, -2] = second[:, 1]
    try:
        with torch.no_grad():
            model(first[:, :-1])
            model(second[:, :-1])
    finally:
        handle.remove()
    difference = (cache[0] - cache[1]).abs().mean().item()
    print(json.dumps({"step": step, "held_noise": held_noise,
                      "copy_accuracy": metrics["copy_accuracy"],
                      "failures": failed,
                      "layer_output_shape": list(cache[0].shape),
                      "mean_absolute_activation_difference": difference,
                      "interpretation": "Observation only; no causal patching was performed"}, indent=2))


if __name__ == "__main__":
    main()
