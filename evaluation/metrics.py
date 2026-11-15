import math


def retrieval_metrics(found, relevant):
    relevant = set(relevant)
    if not relevant:
        return {"recall_at_5": None, "mrr": None, "ndcg_at_10": None, "negative_returned": len(found)}
    hits = [int(item in relevant) for item in found]
    dcg = sum(hit / math.log2(i + 2) for i, hit in enumerate(hits[:10]))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(len(relevant), 10)))
    return {
        "recall_at_5": len(set(found[:5]) & relevant) / len(relevant),
        "mrr": next((1 / (i + 1) for i, h in enumerate(hits) if h), 0),
        "ndcg_at_10": dcg / ideal,
        "negative_returned": None,
    }


def classification_metrics(gold, predicted):
    tp = sum(a and b for a, b in zip(gold, predicted))
    fp = sum(not a and b for a, b in zip(gold, predicted))
    fn = sum(a and not b for a, b in zip(gold, predicted))
    precision, recall = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    return {
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / max(precision + recall, 1e-12),
        "accuracy": sum(a == b for a, b in zip(gold, predicted)) / max(len(gold), 1),
    }


def cohens_kappa(a, b):
    if len(a) != len(b) or not a:
        raise ValueError("Paired nonempty labels required")
    categories = set(a) | set(b)
    po = sum(x == y for x, y in zip(a, b)) / len(a)
    pe = sum(a.count(c) * b.count(c) / len(a) ** 2 for c in categories)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0
