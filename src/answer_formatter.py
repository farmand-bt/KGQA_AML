import json
from src.llm_client import chat_completion

SYSTEM_PROMPT = """You are a helpful assistant. Given a question and raw SPARQL query results from DBpedia, produce a concise, human-readable answer.
If the results are empty, say you could not find an answer.
Clean up URIs by extracting the readable label (e.g., http://dbpedia.org/resource/Berlin -> Berlin).
Keep the answer to 1-3 sentences."""


def format_answer(question, sparql_results):
    if not sparql_results:
        return "I could not find an answer to your question in DBpedia."

    display_results = sparql_results[:20]
    results_str = json.dumps(display_results, indent=2)

    user_msg = f"Question: {question}\nResults: {results_str}"

    try:
        answer = chat_completion([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ])
        return answer
    except Exception:
        return f"Raw results: {results_str}"
