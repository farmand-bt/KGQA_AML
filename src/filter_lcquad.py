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
import time
from src.sparql_executor import execute_sparql

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def test_question(entry):
    """Test if a question's SPARQL query returns results on live DBpedia."""
    query = entry.get("sparql_query", "")
    if not query:
        return entry, False

    result = execute_sparql(query, timeout=60)
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
    print("(Running sequentially to avoid rate limiting — this takes ~20-30 minutes)")

    working = []
    non_working = []

    for i, entry in enumerate(questions):
        _, works = test_question(entry)
        if works:
            working.append(entry)
        else:
            non_working.append(entry)

        if (i + 1) % 25 == 0:
            print(f"  Progress: {i+1}/{len(questions)} "
                  f"({len(working)} working, {len(non_working)} non-working)")

        # Small delay to avoid overwhelming DBpedia
        time.sleep(0.3)

    print(f"\nDone! {len(working)} working, {len(non_working)} non-working "
          f"out of {len(questions)} total.")

    # Save filtered JSON
    filtered_path = os.path.join(DATA_DIR, "lcquad_filtered.json")
    with open(filtered_path, "w", encoding="utf-8") as f:
        json.dump(working, f, indent=2, ensure_ascii=False)
    print(f"Saved filtered questions to {filtered_path}")

    # Save questions.txt
    questions_path = os.path.join(DATA_DIR, "questions.txt")
    with open(questions_path, "w", encoding="utf-8") as f:
        f.write("# Manually Tested Working Questions\n")
        f.write("Who founded Microsoft?\n")
        f.write("What language is spoken in Brazil?\n")
        f.write("Where was Marie Curie born?\n")
        f.write("Who directed Inception?\n")
        f.write("What is the currency of Japan?\n")
        f.write("What is the capital of Germany?\n")
        f.write("Who is the spouse of Barack Obama?\n")
        f.write("What university did Angela Merkel attend?\n")
        f.write("How many people live in Berlin?\n")
        f.write("Who is the supreme leader of Iran?\n")
        f.write("When was the architect of the Eiffel Tower born?\n")
        f.write("\n# Manually Tested Non-Working Questions\n")
        f.write("# These fail due to missing data in DBpedia or query complexity\n")
        f.write("When did World War 2 end?\n")
        f.write("When did World War 2 start?\n")
        f.write("Which country has the largest population in Europe?\n")
        f.write(f"\n# LC-QuAD Working Questions ({len(working)} out of {len(questions)} tested against live DBpedia)\n")
        for entry in working:
            f.write(f"{entry['corrected_question']}\n")
        f.write(f"\n# LC-QuAD Non-Working Questions ({len(non_working)} total)\n")
        for entry in non_working:
            f.write(f"{entry['corrected_question']}\n")
    print(f"Saved questions list to {questions_path}")


if __name__ == "__main__":
    main()
