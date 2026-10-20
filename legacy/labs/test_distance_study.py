"""Protect split, label alignment and future blindness across copy distances."""
import unittest
import torch
from distance_study import documents, evaluate, TRAIN_NOISE, ALL_NOISE
from tiny_transformer import Config, setup


class DistanceStudyTests(unittest.TestCase):
    def test_splits_are_disjoint_balanced_and_reproducible(self):
        for n in ALL_NOISE:
            groups = documents(n)
            again = documents(n)
            seen = set()
            for name, rows in groups.items():
                self.assertTrue(torch.equal(rows, again[name]))
                current = set(map(tuple, rows.tolist()))
                self.assertEqual(len(current), len(rows))
                self.assertFalse(seen & current)
                seen |= current
                for target in range(2, 6):
                    self.assertEqual((rows[:, 1] == target).sum().item(), len(rows)//4)
        self.assertNotIn(8, TRAIN_NOISE)

    def test_separator_labels_and_context_at_every_length(self):
        model, _, _ = setup(Config(context=12))
        for n in ALL_NOISE:
            docs = documents(n)["validation"]
            position = docs.shape[1]-3
            self.assertTrue(torch.all(docs[:, position] == 1))
            self.assertTrue(torch.equal(docs[:, position+1], docs[:, 1]))
            self.assertLessEqual(docs.shape[1]-1, model.cfg.context)
            self.assertEqual(len(evaluate(model, docs)["per_example_correct"]), len(docs))

    def test_future_cannot_leak_at_longest_context(self):
        model, _, _ = setup(Config(context=12))
        x = documents(8)["validation"][:2, :-1].clone()
        changed = x.clone()
        changed[:, 6:] = (changed[:, 6:] + 1) % 7
        self.assertTrue(torch.equal(model(x)[:, :6], model(changed)[:, :6]))

    def test_scoring_tracks_separator_instead_of_fixed_position(self):
        class AnswerAtSeparator:
            cfg = Config(context=12)
            def eval(self):
                return self
            def __call__(self, ids):
                logits = torch.zeros(*ids.shape, 7)
                separator = ids.shape[1]-2
                logits[torch.arange(len(ids)), separator, ids[:, 1]] = 10
                return logits
        for n in ALL_NOISE:
            self.assertEqual(evaluate(AnswerAtSeparator(), documents(n)["validation"])["copy_accuracy"], 1.)


if __name__ == "__main__":
    unittest.main()
