"""
Filter LC-QuAD test questions to find which ones work on the live DBpedia endpoint.

Usage:
    python -m src.filter_lcquad

Reads:  data/LCQuAD-test-data.json
Writes: data/lcquad_filtered.json       (questions whose SPARQL returns results)
        data/questions.txt               (working + non-working lists)
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.sparql_executor import execute_sparql

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def test_question(entry):
    """Test if a question's SPARQL query returns results on live DBpedia."""
    query = entry.get("sparql_query", "")
    if not query:
        return entry, False

    result = execute_sparql(query, timeout=15)
    if not result["success"]:
        return entry, False

    if "ASK" in query.upper():
        return entry, True

    return entry, len(result["results"]) > 0


def main():
    input_path = os.path.join(DATA_DIR, "LCQuAD-test-data.json")

    with open(input_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Testing {len(questions)} LC-QuAD questions against live DBpedia...")

    working = []
    non_working = []
    completed = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(test_question, q): q for q in questions}

        for future in as_completed(futures):
            entry, works = future.result()
            if works:
                working.append(entry)
            else:
                non_working.append(entry)

            completed += 1
            if completed % 50 == 0:
                print(f"  Progress: {completed}/{len(questions)} "
                      f"({len(working)} working, {len(non_working)} non-working)")

    print(f"\nDone! {len(working)} working, {len(non_working)} non-working "
          f"out of {len(questions)} total.")

    # Save filtered JSON
    filtered_path = os.path.join(DATA_DIR, "lcquad_filtered.json")
    with open(filtered_path, "w", encoding="utf-8") as f:
        json.dump(working, f, indent=2, ensure_ascii=False)
    print(f"Saved filtered questions to {filtered_path}")

    # Save questions.txt (overwrites placeholder)
    questions_path = os.path.join(DATA_DIR, "questions.txt")
    with open(questions_path, "w", encoding="utf-8") as f:
        f.write("# Working Questions (tested against live DBpedia)\n")
        for entry in working:
            f.write(f"{entry['corrected_question']}\n")
        f.write(f"\n# Non-Working Questions ({len(non_working)} total)\n")
        for entry in non_working:
            f.write(f"{entry['corrected_question']}\n")
    print(f"Saved questions list to {questions_path}")


if __name__ == "__main__":
    main()
