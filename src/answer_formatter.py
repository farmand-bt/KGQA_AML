import json
from src.llm_client import chat_completion

SYSTEM_PROMPT = """You are a helpful assistant. Given a question, raw SPARQL query results from DBpedia, and the SPARQL query that was used, produce a concise, human-readable answer.

Rules:
- If the results are empty, say you could not find an answer.
- Clean up URIs by extracting the readable part (e.g., http://dbpedia.org/resource/Berlin -> Berlin).
- Replace underscores with spaces in resource names.
- Keep the answer to 1-3 sentences.
- Just state the facts. Do not explain how you found them.
- IMPORTANT: Check if the SPARQL query actually matches what the question asks. For example, if the question asks "when did X end?" but the query fetched a start date or a generic date, say that the specific information was not found in DBpedia rather than giving a wrong answer.
- If the query variable names or predicates suggest the results don't match the question intent, acknowledge the mismatch."""


def format_answer(question, sparql_results, sparql_query=None):
    if not sparql_results:
        return "I could not find an answer to your question in DBpedia."

    # For simple single-value results, still use LLM to validate relevance
    display_results = sparql_results[:20]
    results_str = json.dumps(display_results, indent=2)

    user_msg = f"Question: {question}\nResults: {results_str}"
    if sparql_query:
        user_msg += f"\nSPARQL query used: {sparql_query}"

    try:
        answer = chat_completion([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ])
        return answer
    except Exception:
        # Fallback: format results without LLM
        values = []
        for row in display_results:
            for v in row.values():
                values.append(_clean_uri(v))
        return ", ".join(values)


def _clean_uri(value):
    """Extract readable name from a DBpedia URI."""
    if "dbpedia.org/resource/" in value:
        return value.split("/resource/")[-1].replace("_", " ")
    return value
