"""
Evaluate the KGQA pipeline against LC-QuAD filtered questions.

Compares pipeline answers against ground-truth SPARQL results from the dataset.

Usage:
    python -m src.evaluate [--limit N]
"""

import json
import os
import argparse
import time
from src.pipeline import run_pipeline
from src.sparql_executor import execute_sparql

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def normalize(value):
    """Normalize a value for comparison."""
    if not isinstance(value, str):
        value = str(value)
    if "dbpedia.org/resource/" in value:
        value = value.split("/resource/")[-1]
    return value.lower().replace("_", " ").strip()


def compute_overlap(predicted_values, ground_truth_values):
    """Compute overlap between predicted and ground truth value sets."""
    pred_normalized = {normalize(v) for v in predicted_values}
    gt_normalized = {normalize(v) for v in ground_truth_values}

    if not gt_normalized:
        return 1.0 if not pred_normalized else 0.0

    matches = pred_normalized & gt_normalized
    return len(matches) / len(gt_normalized)


def extract_values(results):
    """Extract all values from SPARQL result rows."""
    values = set()
    for row in results:
        for v in row.values():
            values.add(v)
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50, help="Max questions to evaluate")
    parser.add_argument("--input", default=None, help="Path to filtered LC-QuAD JSON")
    args = parser.parse_args()

    input_path = args.input or os.path.join(DATA_DIR, "lcquad_filtered.json")

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Run 'python -m src.filter_lcquad' first.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    questions = questions[:args.limit]
    print(f"Evaluating {len(questions)} questions...\n")

    stats = {"correct": 0, "partial": 0, "failed": 0, "error": 0}
    per_question = []
    total_time = 0

    for i, entry in enumerate(questions):
        q = entry["corrected_question"]
        gt_query = entry.get("sparql_query", "")

        print(f"[{i+1}/{len(questions)}] {q}")

        gt_result = execute_sparql(gt_query, timeout=15)
        if not gt_result["success"] or not gt_result["results"]:
            print(f"  Skipped (ground truth query failed)")
            continue

        gt_values = extract_values(gt_result["results"])

        start = time.time()
        pipeline_result = run_pipeline(q)
        elapsed = time.time() - start
        total_time += elapsed

        if pipeline_result["results"] and pipeline_result["results"]["success"]:
            pred_values = extract_values(pipeline_result["results"]["results"])
            overlap = compute_overlap(pred_values, gt_values)

            if overlap >= 0.8:
                label = "CORRECT"
                stats["correct"] += 1
            elif overlap > 0:
                label = "PARTIAL"
                stats["partial"] += 1
            else:
                label = "FAILED"
                stats["failed"] += 1
        else:
            overlap = 0
            label = "ERROR"
            stats["error"] += 1

        print(f"  {label} (overlap: {overlap:.0%}, time: {elapsed:.1f}s)")

        per_question.append({
            "question": q,
            "label": label,
            "overlap": round(overlap, 3),
            "time_s": round(elapsed, 2),
            "sparql_generated": pipeline_result.get("sparql", {}).get("query"),
            "sparql_ground_truth": gt_query,
        })

    total = stats["correct"] + stats["partial"] + stats["failed"] + stats["error"]
    print(f"\n{'='*50}")
    print(f"Results: {total} questions evaluated")
    print(f"  Correct (>=80% overlap): {stats['correct']}")
    print(f"  Partial (>0% overlap):   {stats['partial']}")
    print(f"  Failed (0% overlap):     {stats['failed']}")
    print(f"  Error (pipeline failed): {stats['error']}")
    if total > 0:
        print(f"  Strict accuracy:  {stats['correct']/total:.1%}")
        print(f"  Lenient accuracy: {(stats['correct']+stats['partial'])/total:.1%}")
        print(f"  Avg time/question: {total_time/total:.1f}s")

    output_path = os.path.join(DATA_DIR, "evaluation_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"summary": stats, "per_question": per_question}, f, indent=2)
    print(f"\nDetailed results saved to {output_path}")


if __name__ == "__main__":
    main()
