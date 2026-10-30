"""Evaluate labeled prediction JSONL; no synthetic claim of model accuracy."""
import argparse
import json
import math
from pathlib import Path


def evaluate(rows, labels):
    if not labels or len(set(labels)) != len(labels):
        raise ValueError("labels must be unique and nonempty")
    matrix = [[0 for _ in labels] for _ in labels]
    latencies, ids = [], set()
    for row in rows:
        if not isinstance(row.get("id"), str) or not row["id"] or row["id"] in ids:
            raise ValueError("sample id missing/duplicate")
        ids.add(row["id"])
        scores = row["scores"]
        if set(scores) != set(labels) or row["actual"] not in labels:
            raise ValueError("class mismatch")
        if any(isinstance(v, bool) or not isinstance(v, (float, int)) or
               not math.isfinite(v) or not 0 <= v <= 1 for v in scores.values()):
            raise ValueError("invalid probability")
        if not math.isclose(sum(scores.values()), 1.0, abs_tol=0.02):
            raise ValueError("classification probabilities must sum to 1")
        latency = row.get("inference_ms")
        if latency is not None:
            if isinstance(latency, bool) or not isinstance(latency, (float, int)) or not math.isfinite(latency) or latency < 0:
                raise ValueError("invalid latency")
            latencies.append(latency)
        predicted = max(labels, key=lambda label: scores[label])
        matrix[labels.index(row["actual"])][labels.index(predicted)] += 1
    n = len(ids)
    if not n:
        raise ValueError("no prediction rows")
    metrics = {}
    for i, label in enumerate(labels):
        tp = matrix[i][i]
        support = sum(matrix[i])
        predicted = sum(row[i] for row in matrix)
        precision = tp / predicted if predicted else 0
        recall = tp / support if support else 0
        metrics[label] = dict(support=support, precision=precision, recall=recall,
                              f1=2 * precision * recall / (precision + recall) if precision + recall else 0)
    return dict(samples=n, labels=labels, confusion_matrix=matrix,
                matrix_axes="rows=actual, columns=predicted; ties use label order",
                accuracy=sum(matrix[i][i] for i in range(len(labels))) / n,
                macro_f1=sum(x["f1"] for x in metrics.values()) / len(labels),
                per_class=metrics,
                inference_ms_mean=sum(latencies) / len(latencies) if latencies else None)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("predictions")
    p.add_argument("--labels", nargs="+", required=True)
    p.add_argument("--out", default="runtime/evaluation.json")
    a = p.parse_args()
    rows = [json.loads(line) for line in Path(a.predictions).read_text(encoding="utf-8").splitlines() if line.strip()]
    result = evaluate(rows, a.labels)
    path = Path(a.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
