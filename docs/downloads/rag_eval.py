"""Synthetic retrieval + extractive answering baseline; no generative model."""
import math
from collections import Counter

DOCS = {"d1": "Aster library opens at nine", "d2": "Birch library opens at ten",
        "d3": "Aster museum closes at five", "d4": "Cedar library is closed"}
QUERIES = [("Aster library opens", "d1"), ("Birch library opens", "d2"),
           ("Cedar library closed", "d4"), ("Aster museum closes", "d3")]


def vector(text):
    return Counter(text.lower().split())


def cosine(a, b):
    denom = math.sqrt(sum(v*v for v in a.values()) * sum(v*v for v in b.values()))
    return sum(v*b.get(k, 0) for k, v in a.items()) / denom if denom else 0.0


def retrieve(query):
    return sorted(DOCS, key=lambda k: (-cosine(vector(query), vector(DOCS[k])), k))


if __name__ == "__main__":
    hits, reciprocal = 0, 0
    for query, gold in QUERIES:
        ranking = retrieve(query)
        hits += ranking[0] == gold
        reciprocal += 1 / (ranking.index(gold) + 1)
        print({"query": query, "evidence_id": ranking[0], "extract": DOCS[ranking[0]]})
    print({"recall_at_1": hits/len(QUERIES), "MRR": reciprocal/len(QUERIES)})
    # Lexical retrieval cannot establish that an answer exists.
    print({"unanswerable_query": "Aster library phone number", "ranking": retrieve("Aster library phone number")})
