"""Meaningful invariant tests; run python -m unittest discover -s labs."""
import tempfile
import unittest
from pathlib import Path

import torch
from tiny_transformer import (Config, dataset, data_hash, setup, train_steps,
                              save_checkpoint, load_checkpoint, evaluate)


class TransformerTests(unittest.TestCase):
    def test_text_padding_does_not_change_prefix(self):
        from text_lm import corpus, encode, PAD
        raw = corpus()
        groups = [set(x) for x in raw.values()]
        self.assertTrue(all(not a & b for i, a in enumerate(groups) for b in groups[i+1:]))
        model, _, _ = setup(Config(vocab=259, context=96))
        x = encode(raw["validation"][:1])[:, :-1]
        padded = torch.cat([x, torch.full((1, 3), PAD)], dim=1)
        torch.testing.assert_close(model(x), model(padded)[:, :x.shape[1]], rtol=1e-5, atol=1e-6)

    def test_no_document_leakage(self):
        data = dataset()
        sets = [set(map(tuple, x.tolist())) for x in data.values()]
        self.assertTrue(all(not a & b for i, a in enumerate(sets) for b in sets[i+1:]))

    def test_future_does_not_change_past(self):
        model, _, _ = setup(Config())
        x = dataset()["val"][:4, :-1].clone()
        y = x.clone()
        y[:, 4:] = (y[:, 4:] + 1) % 7
        self.assertTrue(torch.equal(model(x)[:, :4], model(y)[:, :4]))

    def test_checkpoint_resume_is_exact(self):
        data = dataset()
        model, opt, rng = setup(Config())
        train_steps(model, opt, rng, data["train"], 7)
        scratch = Path(__file__).parent / "runs"
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            path = Path(folder) / "checkpoint.pt"
            save_checkpoint(path, model, opt, rng, 7, data_hash(data))
            train_steps(model, opt, rng, data["train"], 5)
            resumed, opt2, rng2, step = load_checkpoint(path, data_hash(data))
            train_steps(resumed, opt2, rng2, data["train"], 5)
        self.assertEqual(step, 7)
        self.assertTrue(all(torch.equal(v, resumed.state_dict()[k])
                            for k, v in model.state_dict().items()))

    def test_training_learns_copy(self):
        model, opt, rng = setup(Config())
        data = dataset()
        before = evaluate(model, data["val"])["nll"]
        train_steps(model, opt, rng, data["train"], 250)
        after = evaluate(model, data["val"])
        self.assertLess(after["nll"], before * 0.7)
        self.assertGreater(after["copy_accuracy"], 0.9)


if __name__ == "__main__":
    unittest.main()
