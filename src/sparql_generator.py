import re
from src.llm_client import chat_completion

SYSTEM_PROMPT = """You are a SPARQL query generator for DBpedia. You receive a natural language question, a list of linked DBpedia entity URIs, and a list of candidate relation URIs from the 1-hop neighborhood of those entities.

Your task is to write a SPARQL SELECT query that answers the question.

Rules:
- Use only the provided entity URIs and candidate relations where possible.
- Target the DBpedia SPARQL endpoint (common prefixes: dbo:, dbr:, dbp:, rdf:, rdfs:).
- Return ONLY the SPARQL query, no explanation.
- Use LIMIT 20 to avoid huge result sets.
- If the question asks for a count, use COUNT().
- If the question asks "who", "what", "where", etc., use appropriate variable names."""


def generate_sparql(question, entities, candidate_relations):
    entity_lines = "\n".join(f"- {e['text']}: <{e['uri']}>" for e in entities)
    relation_lines = "\n".join(f"- <{r}>" for r in candidate_relations[:30])

    user_msg = f"""Question: {question}

Linked Entities:
{entity_lines}

Candidate Relations:
{relation_lines}

Write the SPARQL query:"""

    try:
        response = chat_completion([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ])
        query = extract_sparql(response)
        return {"success": True, "query": query}
    except Exception as e:
        return {"success": False, "query": None, "error": str(e)}


def extract_sparql(text):
    match = re.search(r"```(?:sparql)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()
