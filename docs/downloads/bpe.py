"""Tiny byte BPE. UTF-8 makes unseen characters encodable without an UNK token."""
from collections import Counter


def replace_pair(ids, pair, token):
    output, i = [], 0
    while i < len(ids):
        if i + 1 < len(ids) and tuple(ids[i:i+2]) == pair:
            output.append(token)
            i += 2
        else:
            output.append(ids[i])
            i += 1
    return output


def train(texts, merges=20):
    rows = [list(s.encode("utf-8")) for s in texts]
    rules = []
    for token in range(256, 256 + merges):
        counts = Counter(pair for row in rows for pair in zip(row, row[1:]))
        if not counts:
            break
        pair = min(counts, key=lambda p: (-counts[p], p))
        rules.append((pair, token))
        rows = [replace_pair(row, pair, token) for row in rows]
    return rules


def encode(text, rules):
    ids = list(text.encode("utf-8"))
    for pair, token in rules:
        ids = replace_pair(ids, pair, token)
    return ids


def decode(ids, rules):
    vocab = {i: bytes([i]) for i in range(256)}
    for (a, b), token in rules:
        vocab[token] = vocab[a] + vocab[b]
    return b"".join(vocab[i] for i in ids).decode("utf-8")


if __name__ == "__main__":
    rules = train(["banana banana", "研究は小さな疑問から。", "banana研究"])
    for text in ["banana", "未学習の文字🙂", "", "aaaaa"]:
        ids = encode(text, rules)
        assert decode(ids, rules) == text
        print(ascii(text), ids)  # also works in terminals without emoji support
